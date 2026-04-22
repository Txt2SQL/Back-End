import math
import random
from pathlib import Path
from typing import Dict, List, Optional

from config import QUERY_MODELS
from scipy.stats import pearsonr, spearmanr
from src.classes.domain_states import QueryStatus
from tests.utils import RequestResult


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
        "not_started": 0,
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
            "not_started": 0,
            "official_evaluation": 0,
            "custom_evaluation": 0,
            "llm_judge": 0,
        }
        for model in QUERY_MODELS.keys()
    }

    def normalize_evaluation_method(method: Optional[str], status: Optional[str] = None) -> Optional[str]:
        if method == "dataset_eval":
            return "official_evaluation"
        if method == "llm_judge":
            return "llm_judge"
        if method == "sqlite_execution":
            return None if status == "error" else "custom_evaluation"  # Don't count failures
        if method == "custom_compare":
            return "custom_evaluation"
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

                evaluation_type = normalize_evaluation_method(res.evaluation_method, res.evaluation_status)
                if evaluation_type is not None:
                    evaluation_type_counts[evaluation_type] += 1
                    model_stats[model][evaluation_type] += 1
                elif query_session and query_session.status != QueryStatus.SUCCESS:
                    evaluation_type_counts["not_started"] += 1
                    model_stats[model]["not_started"] += 1

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
                elif evaluation_status == "error":
                    # Explicit tracking for evaluation failures
                    error_type_counts[("EVALUATION_ERROR", res.evaluation_method or "unknown")] = (
                        error_type_counts.get(("EVALUATION_ERROR", res.evaluation_method or "unknown"), 0) + 1
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
                    error_type_counts[(syntax_category, "SYNTAX_ERROR")] = (
                        error_type_counts.get((syntax_category, "SYNTAX_ERROR"), 0) + 1
                    )
                elif status == QueryStatus.TIMEOUT_ERROR:
                    other_errors += 1
                    timeout_category = (
                        query_session.error_type.value # pyright: ignore[reportOptionalMemberAccess]
                        if query_session and getattr(query_session, "error_type", None)
                        else QueryStatus.TIMEOUT_ERROR.value
                    )
                    error_type_counts[(timeout_category, "TIMEOUT_ERROR")] = (
                        error_type_counts.get((timeout_category, "TIMEOUT_ERROR"), 0) + 1
                    )
                elif evaluation_status not in {"success", "incorrect", "error"}:
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
                and res.evaluation_status == "success"
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

    request_complexity_counts = {"low": 0, "medium": 0, "high": 0}
    for level in request_complexity_levels.values():
        if level in request_complexity_counts:
            request_complexity_counts[level] += 1

    # Build report
    lines = []
    lines.append("/°" * 50 + "/\n")
    lines.append("📊 TEST SUMMARY")
    lines.append("\n" + "/°" * 50 + "/")
    lines.extend([
        "",
        f"Total requests tested : {total_requests}",
        f"Total model executions: {total_tests}",
        f"🟢 Low complexity requests   : {request_complexity_counts['low']}",
        f"🟡 Medium complexity requests: {request_complexity_counts['medium']}",
        f"🔴 High complexity requests  : {request_complexity_counts['high']}",
        f"🎯 Total correct %    : {total_correct_percent:.2f}%",
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
            "🏁 Evaluation table",
            ["Rank", "Model", "Not started", "Official", "Custom", "LLM Judge"],
            [
                [
                    str(i + 1),
                    model,
                    str(int(stats["not_started"])),
                    str(int(stats["official_evaluation"])),
                    str(int(stats["custom_evaluation"])),
                    str(int(stats["llm_judge"])),
                ]
                for i, (model, stats) in enumerate(
                    sorted(
                        model_stats.items(),
                        key=lambda item: (
                            -item[1]["not_started"],
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
                str(evaluation_type_counts["not_started"]),
                str(evaluation_type_counts["official_evaluation"]),
                str(evaluation_type_counts["custom_evaluation"]),
                str(evaluation_type_counts["llm_judge"]),
            ],
        )
    )

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

    for request_index, models_dict in results_by_index.items():
        request_complexity = request_complexity_scores.get(request_index)
        request_complexity_level = request_complexity_levels.get(request_index)

        for model, res in models_dict.items():
            if res.success and res.query_session:
                qs = res.query_session
                success = 1 if res.evaluation_status == "success" else 0

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

        return "true" if pvalue < 0.05 else "false"

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
        )
    )

    best_model = status_rank[0][0] if status_rank else "N/A"
    lines.append(f"\n🏆 Best overall model: {best_model}")
    lines.append("=" * 60)

    with open(stats_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))