"""
Test script for QueryOrchestrator.
Runs multiple requests against all configured LLM models concurrently,
writes per-request result files, and produces a summary statistics file.
"""

import argparse, sys, os, time, threading, queue, shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.classes.orchestrators.query_orchestrator import QueryOrchestrator
from src.classes.clients.mysql_client import MySQLClient
from src.classes.RAG_service.schema_store import Schema
from src.classes.RAG_service.schema_store import SchemaStore
from src.classes.RAG_service.query_store import QueryStore
from src.classes.domain_states.query import QuerySession
from src.classes.domain_states import SchemaSource, QueryStatus, Records
from src.classes.logger import LoggerManager
from config import QUERY_GENERATION_MODELS, TESTS_DIR, TIMEOUT_PER_REQUEST, VECTOR_STORE_DIR

TMP_DIR = TESTS_DIR / "tmp"

# Initialize LoggerManager at the start
LoggerManager.setup_project_logger()
main_logger = LoggerManager.get_logger("main")


@dataclass
class RequestResult:
    request_index: int
    model_name: str
    query_session: Optional[QuerySession]
    time_taken: float  # seconds
    success: bool  # whether completed without exception
    
    def format_output_content(self, index: int) -> str:
        query_session = self.query_session
        lines = []

        lines.append(f"{index}. 🤖[{self.model_name}]\n")
        lines.append(f"🧮 Query:\n\n{query_session.sql_code if query_session else 'N/A'}\n")
        # ----------------------------
        # Status + Outcome formatting
        # ----------------------------
        status_label = query_session.status.value if query_session and query_session.status else "RUNTIME_ERROR"

        execution_result = query_session.execution_result if query_session else None

        if status_label == "SUCCESS":
            rows_fetched = query_session.rows_fetched if query_session else None
            if rows_fetched is None and isinstance(execution_result, Records):
                rows_fetched = len(execution_result)

            outcome = (
                f"{rows_fetched} rows fetched"
                if rows_fetched is not None
                else "Query executed successfully"
            )
            lines.append(f"status and outcome: 🍾SUCCESS\n {outcome}\n")
            if isinstance(execution_result, Records):
                lines.append(f"{execution_result.get_preview()}\n")
            else:
                lines.append(f"{execution_result}\n")
        else:
            error_msg = execution_result if isinstance(execution_result, str) else "Unknown error"
            lines.append(f"status and outcome: ⚠️RUNTIME_ERROR - {error_msg}\n")
        # ----------------------------
        # LLM Feedback formatting
        # ----------------------------
        feedback = query_session.llm_feedback if query_session else None
        if feedback and feedback.error_category:
            explanation = feedback.explanation or ""
            lines.append(
                f"LLM Feedback: 👎INCORRECT ({feedback.error_category.value} - {explanation})\n"
            )
        else:
            lines.append("LLM Feedback: 👍CORRECT\n")

        # ----------------------------
        # Attempts + Time
        # ----------------------------
        attempts = feedback.attempt if feedback else 0
        lines.append(f"🏁Attempts: {attempts}")
        lines.append(f"⌚Request time: {self.time_taken:.2f}\n")

        return "\n".join(lines)

# ----------------------------------------------------------------------
# Thread-safe wrapper for QueryStore
# ----------------------------------------------------------------------
class ThreadSafeQueryStore(QueryStore):
    def __init__(self, path: Path, lock: threading.Lock):
        super().__init__(path)
        self._lock = lock

    def store_query(self, query: QuerySession) -> None:
        with self._lock:
            super().store_query(query)


# ----------------------------------------------------------------------
# Generator thread function
# ----------------------------------------------------------------------
def generator_thread(
    model_key: str,
    requests: List[str],
    result_queue: queue.Queue,
    schema_store: SchemaStore,
    query_store: ThreadSafeQueryStore,
    logs_dir: Path,
    schema: Schema,
) -> None:
    """
    Process all requests for a single model.
    Each model uses its own isolated logger writing to its own log file.
    """

    # Create dedicated log file for this model
    log_name = QUERY_GENERATION_MODELS[model_key]["log_file"] 
    log_file = logs_dir / f"{log_name}.log"

    # Create isolated per-model logger (thread-safe, no propagation)
    logger = LoggerManager.get_logger(
        name=f"thread_{log_name}",
        log_file=log_file
    )
    
    LoggerManager.set_thread_logger(logger)

    try:
        logger.info(f"Started generator thread for model: {model_key}")
        logger.info(f"Log file: {log_file}")

        for idx, request in enumerate(requests, start=1):
            # Set the request index for all logs in this iteration
            LoggerManager.set_request_index(f"[Request: {idx}]")

            truncated_request = LoggerManager.truncate_request(request)

            logger.info(f"Processing: {truncated_request}")

            start_time = time.time()

            try:
                logger.debug(f"Creating QueryOrchestrator")

                orch = QueryOrchestrator(
                    schema=schema,
                    schema_store=schema_store,
                    user_request=request,
                    query_store=query_store,
                    model_name=model_key,
                    max_attempts=3,
                    instance_path=TMP_DIR
                )

                logger.debug(f"Starting generation")

                result_session = orch.generation(request)

                elapsed = time.time() - start_time

                logger.debug(f"Generation completed in {elapsed:.2f}s")

                res = RequestResult(
                    request_index=idx,
                    model_name=model_key,
                    query_session=result_session,
                    time_taken=elapsed,
                    success=True,
                )

                logger.info(
                    f"Finished successfully "
                    f"(attempts={result_session.llm_feedback.attempt}, time={elapsed:.2f}s)"
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
                )
            # Send result to printer thread
            result_queue.put((idx, model_key, res))

        logger.info(f"Generator thread finished for model: {model_key}")
    finally:
        LoggerManager.clear_thread_logger()

def _progress_bar(done: int, total: int, width: int = 26) -> str:
    """Build a unicode progress bar like █████░░░░ for terminal output."""
    if total <= 0:
        total = 1
    ratio = max(0.0, min(1.0, done / total))
    filled = int(round(ratio * width))
    return f"{'█' * filled}{'░' * (width - filled)}"


def _print_model_progress(model_progress: Dict[str, int], num_requests: int, received: int, total_expected: int) -> None:
    """Render an in-place multi-line status panel with per-model request progress."""
    if not sys.stdout.isatty():
        return

    term_width = shutil.get_terminal_size((110, 30)).columns
    header = f"✨ Live model progress | total results: {received}/{total_expected}"
    lines = [header, "─" * min(term_width, max(30, len(header)))]

    for i, model in enumerate(QUERY_GENERATION_MODELS.keys(), 1):
        done = model_progress.get(model, 0)
        pct = (done / num_requests * 100) if num_requests > 0 else 0
        bar = _progress_bar(done, num_requests)
        lines.append(f"{i:>2}. 🤖 {model:<20} [{bar}] {done:>3}/{num_requests:<3} ({pct:6.2f}%)")

    panel = "\n".join(lines)
    sys.stdout.write("\033[H\033[J")
    sys.stdout.write(panel + "\n")
    sys.stdout.flush()



# ----------------------------------------------------------------------
# Printer thread function
# ----------------------------------------------------------------------
def printer_thread(
    result_queue: queue.Queue,
    num_models: int,
    num_requests: int,
    queries_dir: Path,
    logs_dir: Path,
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
    model_progress = {model: 0 for model in QUERY_GENERATION_MODELS.keys()}

    # Use LoggerManager for printer thread
    logger = LoggerManager.get_logger("printer", log_file=logs_dir / "printer.log")
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
    _write_statistics(results_by_index, num_requests, queries_dir.parent / "final_stats.txt", requests)
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
    safe_req = request_text.replace(' ', '_')[:20]
    filename = f"{index:02d}_{safe_req}.txt"
    filepath = queries_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"❇️[Request]\n{request_text}\n\n")
        # Write results in the same order as models (from config)
        for i, model_key in enumerate(QUERY_GENERATION_MODELS.keys(), 1):
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
    requests: List[str],
) -> None:
    """Aggregate statistics and write to final_stats.txt."""
    def print_table(title: str, headers: List[str], rows: List[List[str]]) -> List[str]:
        """Build an ASCII table and return it as a list of lines."""
        lines: List[str] = []
        lines.append(f"\n{title}")
        lines.append("-" * 60)

        col_widths = [
            max(len(str(cell)) for cell in [header] + [row[i] for row in rows])
            for i, header in enumerate(headers)
        ]

        def format_row(row: List[str]) -> str:
            return " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))

        lines.append(format_row(headers))
        lines.append("-+-".join("-" * w for w in col_widths))

        for row in rows:
            lines.append(format_row(row))

        return lines

    total_requests = num_requests
    total_tests = 0
    successful_executions = 0
    correct_queries = 0
    runtime_errors = 0
    syntax_errors = 0
    other_errors = 0
    total_attempts = 0

    # Per-model stats
    model_stats = {
        model: {
            "correct": 0,
            "runtime": 0,
            "syntax": 0,
            "executions": 0,
            "total_time": 0.0,
            "attempts": 0,
            "count": 0,
        }
        for model in QUERY_GENERATION_MODELS.keys()
    }

    for _, models_dict in results_by_index.items():
        for model, res in models_dict.items():
            total_tests += 1
            model_stats[model]["executions"] += 1
            if res.success:
                query_session = res.query_session
                successful_executions += 1
                attempts = query_session.llm_feedback.attempt if query_session else 0
                total_attempts += attempts
                model_stats[model]["attempts"] += attempts
                model_stats[model]["total_time"] += res.time_taken
                model_stats[model]["count"] += 1

                status = query_session.status.value if query_session and query_session.status else None

                if status == QueryStatus.SUCCESS.value:
                    correct_queries += 1
                    model_stats[model]["correct"] += 1
                elif status == QueryStatus.RUNTIME_ERROR.value:
                    runtime_errors += 1
                    model_stats[model]["runtime"] += 1
                elif status == QueryStatus.SYNTAX_ERROR.value:
                    syntax_errors += 1
                    model_stats[model]["syntax"] += 1
                else:
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
                x[1]["correct"] / x[1]["executions"]
                if x[1]["executions"] > 0 else 0
            ),
            -x[1]["correct"],
            x[1]["runtime"],
            x[1]["syntax"],
        ),
    )

    incorrect_queries = total_tests - correct_queries
    total_correct_percent = (correct_queries / total_tests * 100) if total_tests > 0 else 0

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
        "",
    ])

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
        )
    )

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
        )
    )

    lines.extend(
        print_table(
            "🏁 Status ranking",
            ["Rank", "Model", "CORRECT", "RUNTIME", "SYNTAX", "CORRECT %"],
            [
                [
                    str(i + 1),
                    model,
                    str(int(stats["correct"])),
                    str(int(stats["runtime"])),
                    str(int(stats["syntax"])),
                    f"{(stats['correct'] / stats['executions'] * 100) if stats['executions'] > 0 else 0:.2f}%",
                ]
                for i, (model, stats) in enumerate(status_rank)
            ],
        )
    )

    best_model = status_rank[0][0] if status_rank else "N/A"
    lines.append(f"\n🏆 Best overall model: {best_model}")
    lines.append("=" * 60)

    with open(stats_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print("\n" + "\n".join(lines))
    
def select_database():
    client = MySQLClient()  # connects without specific database
    system_dbs = {"information_schema", "mysql", "performance_schema", "sys"}
    dbs = [db for db in client.list_databases() if db.lower() not in system_dbs]
    client.close_connection()
    if not dbs:
        print("No user databases available.")
        sys.exit(1)
    print("Available databases:")
    for i, db in enumerate(dbs):
        print(f"{i+1}. {db}")
    
    while True:
        choice = input("Select database by number: ").strip()
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(dbs):
            print("Invalid choice. Write again")
        else:
            db_name = dbs[int(choice) - 1]
            print(f"Using database: {db_name}")
            return db_name

def load_requests(db_name: str) -> List[str]:
    requests_file = TESTS_DIR / 'input' / 'requests' / f"{db_name}_requests.txt"
    if not requests_file.exists():
        print(f"Error: Requests file not found: {requests_file}")
        sys.exit(1)
    with open(requests_file, 'r', encoding='utf-8') as f:
        requests = [line.strip() for line in f if line.strip()]
    print(f"Loaded {len(requests)} requests.")
    return requests

def create_output_dir(db_name: str, output_name: str | None = None) -> tuple[Path, Path, Path]:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_name = output_name if output_name else f"results_{timestamp}"
    output_dir = TESTS_DIR / 'output' / 'runs' / f"{db_name}_results" / run_name
    queries_dir = output_dir / 'queries'
    logs_dir = output_dir / 'logs'
    queries_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output will be written to: {output_dir}")
    return output_dir, queries_dir, logs_dir

def empty_tmp_dir() -> None:
    """Clear and recreate the tests tmp directory used by stress tests."""
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)
        main_logger.info(f"Removed existing tmp directory: {TMP_DIR}")

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    main_logger.info(f"Created fresh tmp directory: {TMP_DIR}")

def drop_all_views(db_name: str) -> None:
    """
    Drop all views in the specified database to clean the schema before testing.
    
    Args:
        db_name: Name of the database to clean
    """
    main_logger.info(f"Starting view cleanup for database: {db_name}")
    
    client = None
    try:
        # Connect to the specific database
        client = MySQLClient(db_name)
        
        # Query to get all view names
        views_query = f"""
            SELECT TABLE_NAME 
            FROM information_schema.VIEWS 
            WHERE TABLE_SCHEMA = '{db_name}'
        """
        
        query_session = QuerySession(sql_query=views_query)
        result = client.execute_query(query_session)
        
        if result.execution_status != "SUCCESS":
            main_logger.error(f"Failed to query views: {result.execution_result}")
            return
        
        views = result.execution_result
        if not views:
            print("✅ No views found to clean up")
            main_logger.info("No views found in database")
            return
        
        view_names = [row["TABLE_NAME"] for row in views]  # type: ignore
        main_logger.info(f"Found {len(view_names)} views to drop: {', '.join(view_names)}")
        
        # Drop each view
        dropped_count = 0
        failed_count = 0
        
        for view_name in view_names:
            try:
                drop_query = f"DROP VIEW IF EXISTS `{view_name}`"
                drop_session = QuerySession(sql_query=drop_query)
                drop_result = client.execute_query(drop_session)
                
                if drop_result.execution_status == "SUCCESS":
                    main_logger.info(f"✅ Successfully dropped view: {view_name}")
                    dropped_count += 1
                else:
                    main_logger.error(f"❌ Failed to drop view {view_name}: {drop_result.execution_result}")
                    failed_count += 1
                    
            except Exception as e:
                main_logger.error(f"❌ Error dropping view {view_name}: {e}")
                print(f"  ❌ Error dropping {view_name}: {e}")
                failed_count += 1
        
        main_logger.info(f"View cleanup complete: {dropped_count} dropped, {failed_count} failed")
        
    except Exception as e:
        main_logger.error(f"❌ Error during view cleanup: {e}")
    finally:
        if client:
            client.close_connection()

def build_schema_rag(db_name: str, source: SchemaSource) -> tuple[Schema, SchemaStore]: # always acquire the schema from mysql but put inside the schema the source specified in the args 
    print("Acquiring schema from MySQL...")
    drop_all_views(db_name)
    main_logger.info(f"Acquiring schema from {db_name}")
    schema = Schema(database_name=db_name, schema_source=source, path=TMP_DIR / "schema")
    schema_dict = MySQLClient(db_name).extract_schema()
    schema.parse_response(schema_dict)
    schema_store = SchemaStore(TMP_DIR / "vector_stores")
    schema_store.add_schema(schema)
    print("Schema acquired and saved successfully.")
    main_logger.info("Schema acquired and saved successfully")
    return schema, schema_store
    
def run_stress_test(mode: str, database_name: str, output_name: str | None = None) -> None:
    # ------------------------------------------------------------------
    # PHASE ONE: Initialization
    # ------------------------------------------------------------------
    print("=== PHASE ONE: Initialization ===")

    main_logger.info("Starting stress test")

    # 1. Database selection
    db_name = database_name
    if db_name is None:
        db_name = select_database()
    main_logger.info(f"Using database: {db_name}")

    # 2. Load requests
    requests = load_requests(db_name)
    main_logger.info(f"Loaded {len(requests)} requests")

    # 3. Create output directories
    output_dir, queries_dir, logs_dir = create_output_dir(db_name, output_name)
    main_logger.info("Output directories created")

    # 3.5 Clear tmp directory to avoid cross-run artifacts
    empty_tmp_dir()
    main_logger.info("Temporary stress test directory reset")

    # 4. Acquire schema from MySQL and store in vector store
    source = SchemaSource.MYSQL if mode == 'mysql' else SchemaSource.TEXT
    schema, schema_store = build_schema_rag(db_name, source)

    # 5. Initialize shared query store with lock
    query_store_lock = threading.Lock()
    thread_safe_query_store = ThreadSafeQueryStore(TMP_DIR / "vector_stores", query_store_lock)

    # ------------------------------------------------------------------
    # PHASE TWO: Core Execution
    # ------------------------------------------------------------------
    print("=== PHASE TWO: Core Execution ===")
    main_logger.info("Starting core execution phase")

    result_queue = queue.Queue()
    num_models = len(QUERY_GENERATION_MODELS)

    # Start printer thread
    printer = threading.Thread(
        target=printer_thread,
        args=(result_queue, num_models, len(requests), queries_dir, logs_dir, requests)
    )
    printer.start()
    main_logger.info("Printer thread started")

    # Start generator threads (one per model)
    threads = []
    for model_key in QUERY_GENERATION_MODELS.keys():
        t = threading.Thread(
            target=generator_thread,
            args=(model_key, 
                  requests, result_queue,
                  schema_store, thread_safe_query_store, 
                  logs_dir, schema)
        )
        t.start()
        threads.append(t)
        main_logger.info(f"Generator thread started for model: {model_key}")

    # Wait for all generator threads to finish
    for t in threads:
        t.join()

    # Wait for printer to finish processing all results
    printer.join()

    print("All threads finished. Output written to:", output_dir)
    main_logger.info(f"Stress test completed. Output written to: {output_dir}")

# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Test QueryOrchestrator with multiple models.")
    parser.add_argument('--mode', choices=['mysql', 'text'], default='mysql',
                        help="Schema source mode (mysql or text). Default: mysql")
    parser.add_argument('--database-name', type=str, default=None,
                        help="Name of the database. If not provided, list available databases.")
    parser.add_argument('--output-name', type=str, default=None,
                        help="Custom name for the output run directory. Defaults to a timestamped name.")
    args = parser.parse_args()

    run_stress_test(args.mode, args.database_name, args.output_name)

if __name__ == "__main__":
    main()
