"""
Spider evaluation runner for QueryOrchestrator.

Loads Spider dev examples and table metadata, builds a text-based schema for a
selected database, then runs all configured query models concurrently. Each
generated SQL query is evaluated through the Spider execution evaluator in a
subprocess that exits with:

- 0 when execution matches the gold query
- 1 when execution does not match
"""

import argparse, os, queue, sys, threading, time, math, random
from typing import Dict, List, Optional
from scipy.stats import pearsonr, spearmanr
from pathlib import Path
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import QUERY_MODELS, TESTS_DIR, TIMEOUT_PER_REQUEST, TMP_DIR
from src.classes.clients.database.sqlite_client import SQLiteClient
from src.classes.RAG_service.schema_store import SchemaStore
from src.classes.domain_states import QuerySession, QueryStatus, Schema, SchemaSource
from src.classes.logger import LoggerManager
from src.classes.orchestrators.query_orchestrator import QueryOrchestrator
from src.classes.datasets import BaseDataset, BirdDataset, SpiderDataset
from tests.thread_output import RequestResult
from tests.test_sql_generation import empty_tmp_dir, create_output_dir, _print_model_progress, ThreadSafeQueryStore


LoggerManager.setup_project_logger()
main_logger = LoggerManager.get_logger("dataset_test")

def select_database(tables: list[tuple[str, int]]) -> str:
    for db_name, table_count in tables:
        print(f"{db_name} ({table_count} tables)")
    
    while True:
        choice = input("Select database by name: ").strip()
        if choice in [db_name for db_name, _ in tables]:
            print(f"Using database: {choice}")
            return choice
        print("Invalid database name. Try again.")


def build_schema(
    database_name: str,
    converted_schema: dict,
    schema_source: SchemaSource
) -> tuple[Schema, SchemaStore]:

    schema = Schema(
        database_name=database_name,
        schema_source=schema_source,
        path=TESTS_DIR / "tmp",
    )
    schema.parse_response(converted_schema)

    schema_store = SchemaStore(TMP_DIR / "vector_stores")
    schema_store.add_schema(schema)

    return schema, schema_store

# ----------------------------------------------------------------------
# Printer thread function
# ----------------------------------------------------------------------
def printer_thread(
    result_queue: queue.Queue,
    num_models: int,
    num_requests: int,
    queries_dir: Path,
    output_dir: Path,
    requests: List[str],
) -> None:
    """
    Collect results from all threads, write per-request files in order,
    and finally write a statistics summary.
    """
    results_by_index: Dict[int, Dict[str, RequestResult]] = {}
    completed_indices = set()
    next_index = 1
    total_expected = num_models * num_requests
    received = 0
    model_progress = {model: 0 for model in QUERY_MODELS.keys()}

    # Use LoggerManager for printer thread
    logger = LoggerManager.get_logger("printer", log_file=output_dir / "logs" / "printer.log")
    logger.info(f"Printer started. Expecting {total_expected} results.")
    _print_model_progress(model_progress, num_requests, received, total_expected)

    while received < total_expected:
        try:
            idx, model, res = result_queue.get(timeout=1)
            received += 1
            logger.info(f"Received result for request: {idx}, model: {model}")
            if model in model_progress:
                model_progress[model] += 1
            _print_model_progress(model_progress, num_requests, received, total_expected)
            if idx not in results_by_index:
                results_by_index[idx] = {}
            results_by_index[idx][model] = res

            # Check if this index is now complete
            if len(results_by_index[idx]) == num_models:
                logger.info(f"Index {idx} completed")
                completed_indices.add(idx)

            # Write any consecutive completed indices starting from next_index
            while next_index in completed_indices:
                logger.info(f"Writing index {next_index}")
                _write_request_file(next_index, results_by_index[next_index], requests, queries_dir)
                next_index += 1

        except queue.Empty:
            # No new results, continue loop
            pass
    
    logger.info("Printer received all results. Writing statistics now.")
    # All results received – write any remaining indices in order
    for idx in sorted(results_by_index.keys()):
        if idx >= next_index:
            if len(results_by_index[idx]) == num_models:
                _write_request_file(idx, results_by_index[idx], requests, queries_dir)
            else:
                logger.warning(f"Incomplete results for index {idx} (should not happen)")

    # Write final statistics
    _write_statistics(results_by_index, num_requests, queries_dir.parent / "final_stats.txt")
    logger.info("Printer finished.")
    if sys.stdout.isatty():
        print("✅ All model requests have been processed.\n")


def _write_request_file(
    index: int,
    results: Dict[str, RequestResult],
    requests: List[str],
    queries_dir: Path,
) -> None:
    """Write a single request output file."""
    request_text = requests[index - 1]
    safe_req = request_text.replace(' ', '_').replace('/', '')[:20] # TODO remove any / or other problematic chars
    filename = f"{index:02d}_{safe_req}.txt"
    filepath = queries_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"❇️[Request]\n{request_text}\n\n")
        # Write results in the same order as models (from config)
        for i, model_key in enumerate(QUERY_MODELS.keys(), 1):
            res = results.get(model_key)
            if res is None:
                f.write(f"{i}. 🤖[{model_key}]\n\nNo result\n\n")
                continue
                    
            f.write(res.format_output_content(i))
            f.write("\n\n")


def _write_statistics(
    results_by_index: Dict[int, Dict[str, RequestResult]],
    num_requests: int,
    stats_path: Path,
) -> None:
    """Aggregate statistics and write to final_stats.txt."""
    def print_table(title: str, headers: List[str], rows: List[List[str]], footer: Optional[List[str]] = None) -> List[str]:
        """Build an ASCII table and return it as a list of lines."""
        lines: List[str] = []
        lines.append(f"\n{title}")
        lines.append("-" * 60)

        # Calculate columns based on headers, data rows, AND the footer row
        all_data = [headers] + rows
        if footer:
            all_data.append(footer)

        col_widths = [
            max(len(str(cell)) for cell in [row[i] for row in all_data])
            for i in range(len(headers))
        ]

        def format_row(row: List[str]) -> str:
            return " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))

        lines.append(format_row(headers))
        
        separator = "-+-".join("-" * w for w in col_widths)
        lines.append(separator)

        for row in rows:
            lines.append(format_row(row))
        
        # Add footer if provided
        if footer:
            lines.append(separator)
            lines.append(format_row(footer))

        return lines

    total_requests = num_requests
    total_tests = 0
    successful_executions = 0
    correct_queries = 0
    incorrect_queries = 0
    runtime_errors = 0
    syntax_errors = 0
    other_errors = 0
    total_attempts = 0
    error_type_counts: Dict[tuple[str, str], int] = {}
    evaluation_type_counts = {
        "official_evaluation": 0,
        "custom_evaluation": 0,
        "llm_judge": 0,
    }
    
    # Global sums for footer
    global_total_time = 0.0

    # Per-model stats
    model_stats = {
        model: {
            "correct": 0,
            "incorrect": 0,
            "generation_correct": 0,
            "generation_incorrect": 0,
            "evaluation_correct": 0,
            "evaluation_incorrect": 0,
            "runtime": 0,
            "syntax": 0,
            "executions": 0,
            "total_time": 0.0,
            "attempts": 0,
            "count": 0,
            "official_evaluation": 0,
            "custom_evaluation": 0,
            "llm_judge": 0,
        }
        for model in QUERY_MODELS.keys()
    }

    def normalize_evaluation_method(method: Optional[str]) -> Optional[str]:
        if method == "dataset_eval":
            return "official_evaluation"
        if method in {"custom_compare", "sqlite_execution", "fallback"}:
            return "custom_evaluation"
        if method == "llm_judge":
            return "llm_judge"
        return None

    for _, models_dict in results_by_index.items():
        for model, res in models_dict.items():
            total_tests += 1
            model_stats[model]["executions"] += 1
            if res.success:
                query_session = res.query_session
                successful_executions += 1
                attempts = query_session.attempt if query_session else 0
                total_attempts += attempts
                
                model_stats[model]["attempts"] += attempts
                model_stats[model]["total_time"] += res.time_taken
                global_total_time += res.time_taken
                model_stats[model]["count"] += 1

                evaluation_type = normalize_evaluation_method(res.evaluation_method)
                if evaluation_type is not None:
                    evaluation_type_counts[evaluation_type] += 1
                    model_stats[model][evaluation_type] += 1

                evaluation_status = res.evaluation_status

                if evaluation_status == "success":
                    correct_queries += 1
                    model_stats[model]["correct"] += 1
                    model_stats[model]["evaluation_correct"] += 1
                elif evaluation_status == "incorrect":
                    incorrect_queries += 1
                    model_stats[model]["incorrect"] += 1
                    model_stats[model]["evaluation_incorrect"] += 1
                    error_category = "UNKNOWN_ERROR"
                    error_type_counts[(error_category, "INCORRECT")] = (
                        error_type_counts.get((error_category, "INCORRECT"), 0) + 1
                    )
                status = query_session.status if query_session and query_session.status else None

                if status == QueryStatus.SUCCESS:
                    model_stats[model]["generation_correct"] += 1
                elif status == QueryStatus.INCORRECT:
                    model_stats[model]["generation_incorrect"] += 1
                elif status == QueryStatus.RUNTIME_ERROR:
                    runtime_errors += 1
                    model_stats[model]["runtime"] += 1
                    runtime_category = (
                        query_session.error_type.value # pyright: ignore[reportOptionalMemberAccess]
                        if query_session and getattr(query_session, "error_type", None)
                        else QueryStatus.RUNTIME_ERROR.value
                    )
                    error_type_counts[(runtime_category, "RUNTIME_ERROR")] = (
                        error_type_counts.get((runtime_category, "RUNTIME_ERROR"), 0) + 1
                    )
                elif status == QueryStatus.SYNTAX_ERROR:
                    syntax_errors += 1
                    model_stats[model]["syntax"] += 1
                    syntax_category = (
                        query_session.error_type.value # pyright: ignore[reportOptionalMemberAccess]
                        if query_session and getattr(query_session, "error_type", None)
                        else QueryStatus.SYNTAX_ERROR.value
                    )
                    error_type_counts[(syntax_category, "RUNTIME_ERROR")] = (
                        error_type_counts.get((syntax_category, "RUNTIME_ERROR"), 0) + 1
                    )
                elif status == QueryStatus.TIMEOUT_ERROR:
                    other_errors += 1
                    timeout_category = (
                        query_session.error_type.value # pyright: ignore[reportOptionalMemberAccess]
                        if query_session and getattr(query_session, "error_type", None)
                        else QueryStatus.TIMEOUT_ERROR.value
                    )
                    error_type_counts[(timeout_category, "RUNTIME_ERROR")] = (
                        error_type_counts.get((timeout_category, "RUNTIME_ERROR"), 0) + 1
                    )
                elif evaluation_status not in {"success", "incorrect"}:
                    other_errors += 1
            else:
                # Exception occurred – count as other error
                other_errors += 1

    # Build rankings
    attempts_avg = sorted(
        model_stats.items(),
        key=lambda x: x[1]["attempts"] / x[1]["count"] if x[1]["count"] > 0 else float("inf"),
    )
    time_avg = sorted(
        model_stats.items(),
        key=lambda x: x[1]["total_time"] / x[1]["count"] if x[1]["count"] > 0 else float("inf"),
    )
    status_rank = sorted(
        model_stats.items(),
        key=lambda x: (
            -(
                x[1]["evaluation_correct"] / x[1]["executions"]
                if x[1]["executions"] > 0 else 0
            ),
            -x[1]["evaluation_correct"],
            x[1]["evaluation_incorrect"],
            x[1]["runtime"],
            x[1]["syntax"],
        ),
    )

    total_correct_percent = (correct_queries / total_tests * 100) if total_tests > 0 else 0
    
    # Calculate global averages for footers
    global_avg_attempts = (total_attempts / total_tests) if total_tests > 0 else 0
    global_avg_time = (global_total_time / total_tests) if total_tests > 0 else 0

    # Build report
    lines = []
    lines.append("/°" * 50 + "/\n")
    lines.append("📊 TEST SUMMARY")
    lines.append("\n" + "/°" * 50 + "/")
    lines.extend([
        "",
        f"Total requests tested : {total_requests}",
        f"Total model executions: {total_tests}",
        f"✅ Correct queries : {correct_queries}",
        f"❌ Incorrect queries  : {incorrect_queries}",
        f"⚠️  Syntax errors     : {syntax_errors}",
        f"❌ Runtime errors    : {runtime_errors}",
        f"🔧 Other errors      : {other_errors}",
        f"🟢 Completed runs    : {successful_executions}",
        f"🔁 Total attempts    : {total_attempts}",
        f"🎯 Total correct %    : {total_correct_percent:.2f}%",
        f"📏 Official evaluation count : {evaluation_type_counts['official_evaluation']}",
        f"🧪 Custom evaluation count   : {evaluation_type_counts['custom_evaluation']}",
        f"🤖 LLM judge count           : {evaluation_type_counts['llm_judge']}",
        "",
    ])

    # Table 1: Attempts Ranking
    lines.extend(
        print_table(
            "🏁 Attempts ranking (avg)",
            ["Rank", "Model", "Avg Attempts", "Total Attempts"],
            [
                [
                    str(i + 1),
                    model,
                    f"{(stats['attempts'] / stats['count']) if stats['count'] > 0 else 0:.2f}",
                    f"{stats['attempts']:.0f}",
                ]
                for i, (model, stats) in enumerate(attempts_avg)
            ],
            footer=["", "TOTAL", f"{global_avg_attempts:.2f}", f"{total_attempts:.0f}"]
        )
    )

    # Table 2: Time Ranking
    lines.extend(
        print_table(
            "🏁 Time ranking (avg)",
            ["Rank", "Model", "Avg Time (s)", "Total Time (s)"],
            [
                [
                    str(i + 1),
                    model,
                    f"{(stats['total_time'] / stats['count']) if stats['count'] > 0 else 0:.2f}",
                    f"{stats['total_time']:.1f}",
                ]
                for i, (model, stats) in enumerate(time_avg)
            ],
            footer=["", "TOTAL", f"{global_avg_time:.2f}", f"{global_total_time:.1f}"]
        )
    )

    # Table 3: Status Ranking
    lines.extend(
        print_table(
            "🏁 Status ranking",
            [
                "Rank",
                "Model",
                "SYNTAX",
                "RUNTIME",
                "GEN INCORRECT",
                "GEN CORRECT",
                "EVAL INCORRECT",
                "EVAL CORRECT",
                "CORRECT %",
            ],
            [
                [
                    str(i + 1),
                    model,
                    str(int(stats["syntax"])),
                    str(int(stats["runtime"])),
                    str(int(stats["generation_incorrect"])),
                    str(int(stats["generation_correct"])),
                    str(int(stats["evaluation_incorrect"])),
                    str(int(stats["evaluation_correct"])),
                    f"{(stats['evaluation_correct'] / stats['executions'] * 100) if stats['executions'] > 0 else 0:.2f}%",
                ]
                for i, (model, stats) in enumerate(status_rank)
            ],
            footer=[
                "", 
                "TOTAL", 
                str(syntax_errors), 
                str(runtime_errors), 
                str(sum(int(stats["generation_incorrect"]) for stats in model_stats.values())),
                str(sum(int(stats["generation_correct"]) for stats in model_stats.values())),
                str(incorrect_queries), 
                str(correct_queries), 
                f"{total_correct_percent:.2f}%"
            ]
        )
    )

    lines.extend(
        print_table(
            "🏁 Evaluation method counts",
            ["Rank", "Model", "Official", "Custom", "LLM Judge"],
            [
                [
                    str(i + 1),
                    model,
                    str(int(stats["official_evaluation"])),
                    str(int(stats["custom_evaluation"])),
                    str(int(stats["llm_judge"])),
                ]
                for i, (model, stats) in enumerate(
                    sorted(
                        model_stats.items(),
                        key=lambda item: (
                            -item[1]["official_evaluation"],
                            -item[1]["custom_evaluation"],
                            -item[1]["llm_judge"],
                            item[0],
                        ),
                    )
                )
            ],
            footer=[
                "",
                "TOTAL",
                str(evaluation_type_counts["official_evaluation"]),
                str(evaluation_type_counts["custom_evaluation"]),
                str(evaluation_type_counts["llm_judge"]),
            ],
        )
    )

    error_type_rows = [
        [str(i + 1), category, source_type, str(count)]
        for i, ((category, source_type), count) in enumerate(
            sorted(
                error_type_counts.items(),
                key=lambda item: (-item[1], item[0][1], item[0][0]),
            )
        )
    ]

    lines.extend(
        print_table(
            "🏁 Error type ranking",
            ["Rank", "Category", "Type", "Count"],
            error_type_rows,
            footer=[
                "",
                "TOTAL",
                "",
                str(sum(error_type_counts.values())),
            ],
        )
    )
    
    complexities = []
    complexity_successes = []
    attempts = []
    attempt_successes = []
    per_model_correlation_data = {
        model: {
            "attempts": [],
            "attempt_successes": [],
            "complexities": [],
            "complexity_successes": [],
        }
        for model in QUERY_MODELS.keys()
    }
    per_model_complexity_buckets = {
        model: {
            "low": [],
            "medium": [],
            "high": [],
            "total": [],
        }
        for model in QUERY_MODELS.keys()
    }

    request_complexity_scores: Dict[int, Optional[float]] = {}
    request_complexity_levels: Dict[int, Optional[str]] = {}

    for request_index in range(1, num_requests + 1):
        models_dict = results_by_index.get(request_index, {})
        correct_complexities = []
        all_complexities = []

        for res in models_dict.values():
            complexity = res.get_query_complexity()
            if complexity is None:
                continue

            all_complexities.append(complexity)

            if (
                res.success
                and res.query_session
                and res.query_session.status == QueryStatus.SUCCESS
            ):
                correct_complexities.append(complexity)

        request_complexity: Optional[float]
        if correct_complexities:
            request_complexity = float(random.choice(correct_complexities))
        elif all_complexities:
            request_complexity = sum(all_complexities) / len(all_complexities)
        else:
            request_complexity = None

        request_complexity_scores[request_index] = request_complexity
        request_complexity_levels[request_index] = (
            RequestResult.complexity_level_from_score(request_complexity)
            if request_complexity is not None
            else None
        )
    
    for request_index, models_dict in results_by_index.items():
        request_complexity = request_complexity_scores.get(request_index)
        request_complexity_level = request_complexity_levels.get(request_index)

        for model, res in models_dict.items():
            if res.success and res.query_session:
                qs = res.query_session
                success = 1 if qs.status == QueryStatus.SUCCESS else 0

                attempts.append(qs.attempt)
                attempt_successes.append(success)
                per_model_correlation_data[model]["attempts"].append(qs.attempt)
                per_model_correlation_data[model]["attempt_successes"].append(success)

                if request_complexity is not None:
                    complexities.append(request_complexity)
                    complexity_successes.append(success)
                    per_model_correlation_data[model]["complexities"].append(request_complexity)
                    per_model_correlation_data[model]["complexity_successes"].append(success)
                    per_model_complexity_buckets[model]["total"].append(success)

                    if request_complexity_level is not None:
                        per_model_complexity_buckets[model][request_complexity_level].append(success)
    
    buckets = {
        "low": [],
        "medium": [],
        "high": [],
        "total": [],
    }

    for c, s in zip(complexities, complexity_successes):
        buckets["total"].append(s)
        if c <= 2:
            buckets["low"].append(s)
        elif c <= 5:
            buckets["medium"].append(s)
        else:
            buckets["high"].append(s)

    def format_success_rate(values: List[int]) -> str:
        if not values:
            return "N/A"
        return f"{(sum(values) / len(values)):.2%}"

    complexity_rows = []
    for model in QUERY_MODELS.keys():
        model_buckets = per_model_complexity_buckets[model]
        complexity_rows.append([
            model,
            format_success_rate(model_buckets["low"]),
            format_success_rate(model_buckets["medium"]),
            format_success_rate(model_buckets["high"]),
            format_success_rate(model_buckets["total"]),
        ])

    lines.extend(
        print_table(
            "🏁 Complexity success rate by model",
            ["Model", "Low", "Medium", "High", "Total"],
            complexity_rows,
            footer=[
                "TOTAL",
                format_success_rate(buckets["low"]),
                format_success_rate(buckets["medium"]),
                format_success_rate(buckets["high"]),
                format_success_rate(buckets["total"]),
            ],
        )
    )

    def safe_corr(values: List[int], outcomes: List[int], method: str) -> str:
        if len(values) < 2 or len(outcomes) < 2:
            return "N/A"
        if len(set(values)) <= 1 or len(set(outcomes)) <= 1:
            return "N/A"

        result = pearsonr(values, outcomes) if method == "pearson" else spearmanr(values, outcomes)

        statistic = getattr(result, "statistic", None)
        pvalue = getattr(result, "pvalue", None)

        if statistic is None or pvalue is None:
            return "N/A"
        if math.isnan(statistic) or math.isnan(pvalue):
            return "N/A"

        return f"{statistic:.3f} (p={pvalue:.3f})"

    pearson_attempts_success = safe_corr(attempts, attempt_successes, "pearson")
    spearman_attempts_success = safe_corr(attempts, attempt_successes, "spearman")

    pearson_cs = safe_corr(complexities, complexity_successes, "pearson")
    spearman_cs = safe_corr(complexities, complexity_successes, "spearman")

    per_model_corr_rows = []
    for model in QUERY_MODELS.keys():
        model_data = per_model_correlation_data[model]
        per_model_corr_rows.append([
            model,
            safe_corr(model_data["attempts"], model_data["attempt_successes"], "pearson"),
            safe_corr(model_data["attempts"], model_data["attempt_successes"], "spearman"),
            safe_corr(model_data["complexities"], model_data["complexity_successes"], "pearson"),
            safe_corr(model_data["complexities"], model_data["complexity_successes"], "spearman"),
        ])

    lines.extend(
        print_table(
            "🏁 Correlation by model",
            ["Model", "Attempts Pearson", "Attempts Spearman", "Complexity Pearson", "Complexity Spearman"],
            per_model_corr_rows,
            footer=[
                "TOTAL",
                pearson_attempts_success,
                spearman_attempts_success,
                pearson_cs,
                spearman_cs,
            ],
        )
    )

    best_model = status_rank[0][0] if status_rank else "N/A"
    lines.append(f"\n🏆 Best overall model: {best_model}")
    lines.append("=" * 60)

    with open(stats_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    

def generator_thread(
    database_name: str,
    model_key: str,
    requests: List[str],
    result_queue: queue.Queue,
    schema_store: SchemaStore,
    query_store: ThreadSafeQueryStore,
    logs_dir: Path,
    schema: Schema,
    dataset: BaseDataset,
) -> None:
    """
    Process all requests for a single model.
    Each model uses its own isolated logger writing to its own log file.
    """

    # Create dedicated log file for this model
    log_name = QUERY_MODELS[model_key]["log_file"]
    log_file = logs_dir / f"{log_name}.log"

    # Create isolated per-model logger (thread-safe, no propagation)
    logger = LoggerManager.get_logger(
        name=f"thread_{log_name}",
        log_file=log_file
    )
    
    LoggerManager.set_thread_logger(logger)

    try:
        logger.info(f"Started generator thread for model: {model_key}, mode: {schema.source.value}")
        logger.info(f"Log file: {log_file}")

        db_client = SQLiteClient(database_name)
        if schema.source == SchemaSource.DB_CONNECTION:
            qs = query_store
        else:
            qs = None

        for idx, request in enumerate(requests, start=1):
            # Set the request index for all logs in this iteration
            LoggerManager.set_request_index(f"[Request: {idx}]")

            truncated_request = LoggerManager.truncate_request(request)

            logger.info(f"Processing: {truncated_request}")

            start_time = time.time()

            try:
                logger.debug(f"Creating QueryOrchestrator")

                orch = QueryOrchestrator(
                    database_name=database_name,
                    schema_store=schema_store,
                    model_name=model_key,
                    database_client=db_client if schema.source == SchemaSource.DB_CONNECTION else None,
                    query_store=qs,
                    max_attempts=3,
                    instance_path=TMP_DIR,
                )

                logger.debug(f"Starting generation")

                result_session = orch.generation(request)
                eval_result = None

                if result_session.status is not QueryStatus.SUCCESS:
                    logger.info(
                        "Skipping dataset evaluation because generation ended with status=%s",
                        result_session.status.value if result_session.status else None,
                    )
                else:
                    eval_result = dataset.evaluation(
                        predicted_query=result_session,
                        db_id=database_name,
                        question=request,
                        model_name=model_key,
                        log_dir=logs_dir,
                        db_client=db_client,
                    )

                elapsed = time.time() - start_time

                logger.debug(f"Generation completed in {elapsed:.2f}s")

                res = RequestResult(
                    request_index=idx,
                    model_name=model_key,
                    query_session=result_session,
                    gold_query_sql=eval_result.gold.sql_code if eval_result and eval_result.gold else None,
                    time_taken=elapsed,
                    success=True,
                    evaluation_method=eval_result.method if eval_result else None,
                    evaluation_status=eval_result.status if eval_result else None,
                    evaluation_verdict=eval_result.verdict if eval_result else None,
                    evaluation_reason=eval_result.reason if eval_result else None,
                )

                logger.info(
                    f"Finished successfully "
                    f"(attempts={result_session.attempt}, time={elapsed:.2f}s)"
                )

            except TimeoutError as e:

                elapsed = TIMEOUT_PER_REQUEST

                logger.exception(
                    f"Timeout after {elapsed}s"
                )

                timeout_session = QuerySession(user_request=request)
                timeout_session.execution_result = str(e)
                timeout_session.status = QueryStatus.TIMEOUT_ERROR

                res = RequestResult(
                    request_index=idx,
                    model_name=model_key,
                    query_session=timeout_session,
                    time_taken=elapsed,
                    success=False,
                    evaluation_method=None,
                )
            except Exception as e:

                elapsed = time.time() - start_time

                logger.exception(
                    f"Failed with exception after {elapsed:.2f}s"
                )

                failed_session = QuerySession(user_request=request)
                failed_session.execution_result = str(e)
                failed_session.status = QueryStatus.RUNTIME_ERROR

                res = RequestResult(
                    request_index=idx,
                    model_name=model_key,
                    query_session=failed_session,
                    time_taken=elapsed,
                    success=False,
                    evaluation_method=None,
                )
            # Send result to printer thread
            result_queue.put((idx, model_key, res))

        logger.info(f"Generator thread finished for model: {model_key}")
    finally:
        LoggerManager.clear_thread_logger()

def select_dataset() -> str:
    print("Available datasets:")
    print("1. Spider")
    print("2. BIRD")
    while True:
        choice = input("Select dataset by number: ").strip()
        if choice == "1":
            return "spider"
        elif choice == "2":
            return "bird"
        else:
            print("Invalid choice. Try again.")

def run_spider_test(database_name: str | None, dataset_name: str | None, output_name: str | None = None) -> None:
    print("=== SPIDER TEST INITIALIZATION ===")
    main_logger.info("Starting Spider test")

    if dataset_name is None:
        dataset_name = select_dataset()
    elif dataset_name not in ["spider", "bird"]:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    
    if dataset_name == "bird":
        main_logger.info("Selected dataset: BIRD")
        dataset = BirdDataset()
    else:
        main_logger.info("Selected dataset: Spider")
        dataset = SpiderDataset()

    if database_name is None:
        database_name = select_database(dataset.get_dbs())

    output_dir = create_output_dir(database_name, output_name)
    logs_dir = output_dir / "logs"
    queries_dir = output_dir / "queries"
    logs_dir.mkdir(parents=True, exist_ok=True)
    queries_dir.mkdir(parents=True, exist_ok=True)
    empty_tmp_dir()

    schema_source = SchemaSource.DB_CONNECTION if dataset_name == "bird" else SchemaSource.TEXT
    schema, schema_store = build_schema(database_name, dataset.get_schema(database_name), schema_source)
    query_store_lock = threading.Lock()
    thread_safe_query_store = ThreadSafeQueryStore(TMP_DIR / "vector_stores", query_store_lock)

    result_queue: queue.Queue = queue.Queue()
    num_models = len(QUERY_MODELS)
    requests = dataset.get_requests(database_name)

    printer = threading.Thread(
        target=printer_thread,
        args=(result_queue, num_models, len(requests), queries_dir, output_dir, requests),
    )
    printer.start()
    main_logger.info("Printer thread started")

    threads = []
    for model_key in QUERY_MODELS.keys():
        thread = threading.Thread(
            target=generator_thread,
            args=(
                database_name,
                model_key,
                requests,
                result_queue,
                schema_store,
                thread_safe_query_store,
                logs_dir,
                schema,
                dataset,
            ),
        )
        thread.start()
        threads.append(thread)
        main_logger.info("Generator thread started for model=%s", model_key)

    for thread in threads:
        thread.join()

    printer.join()

    print(f"All Spider threads finished. Output written to: {output_dir}")
    main_logger.info("Spider test completed. Output written to: %s", output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Spider evaluation across configured query models.")
    parser.add_argument(
        "--database-name",
        type=str,
        default=None,
        help="Spider database id to test. If omitted, the script prints all databases and prompts for one.",
    )
    parser.add_argument(
        "--output-name",
        type=str,
        default=None,
        help="Custom name for the output run directory. Defaults to a timestamped name.",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Dataset to run the test on. Supported values: 'spider', 'bird'.",
    )
    args = parser.parse_args()

    run_spider_test(args.database_name, args.dataset, args.output_name)


if __name__ == "__main__":
    main()
