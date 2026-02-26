"""
Test script for QueryOrchestrator.
Runs multiple requests against all configured LLM models concurrently,
writes per-request result files, and produces a summary statistics file.
"""

import argparse
import sys
import os
import time
import threading
import queue
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.classes.orchestrators.query_orchestrator import QueryOrchestrator
from src.classes.orchestrators.schema_orchestrator import SchemaOrchestrator
from src.classes.clients.mysql_client import MySQLClient
from src.classes.RAG_service.schema_store import SchemaStore
from src.classes.RAG_service.query_store import QueryStore
from src.classes.domain_states.query import QuerySession
from src.classes.domain_states import SchemaSource, QueryStatus, FeedbackStatus
from src.classes.logger_manager import LoggerManager
from config import QUERY_GENERATION_MODELS, TESTS_DIR, TIMEOUT_PER_REQUEST, VECTOR_STORE_DIR


# ----------------------------------------------------------------------
# Data class for request results
# ----------------------------------------------------------------------
def format_model_key(model_key: str) -> str:
    model_key = model_key.strip()
    last_colon = model_key.rfind(':')
    if last_colon != -1:
        suffix = model_key[last_colon + 1:]
        if len(suffix) > 1 and suffix[:-1].isdigit() and suffix[-1] in ('b', 'B'):
            model_key = model_key[:last_colon]

    return model_key.translate(str.maketrans({
        '<': '_', '>': '_', ':': '_', '"': '_',
        '/': '_', '\\': '_', '|': '_', '?': '_', '*': '_',
    }))

@dataclass
class RequestResult:
    request_index: int
    model_name: str
    sql_code: Optional[str]
    status: Optional[str]
    error: Optional[str]
    feedback_category: Optional[str]
    feedback_explanation: Optional[str]
    attempts: int
    time_taken: float  # seconds
    success: bool  # whether completed without exception


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
import concurrent.futures
import queue
import time
from typing import List, Dict

def generator_thread(
    model_key: str,
    requests: List[str],
    result_queue: queue.Queue,
    schema_store: SchemaStore,
    query_store: ThreadSafeQueryStore,
    logs_dir: Path,
    db_name: str,
) -> None:
    """
    Process all requests for a single model.
    For each request, run QueryOrchestrator and put a RequestResult into the queue.
    """
    # Setup per-thread log file
    log_file = logs_dir / QUERY_GENERATION_MODELS[model_key]["log_file"]
    logger = logging.getLogger(f"thread_{model_key}")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logger.addHandler(fh)
    logger.info(f"Started thread for model {model_key}")

    for idx, request in enumerate(requests, start=1):
        logger.info(f"Processing request {idx}: {request[:50]}...")
        start_time = time.time()
        try:
            # Create orchestrator for this request
            orch = QueryOrchestrator(
                database_name=db_name,
                schema_store=schema_store,
                user_request=request,
                query_store=query_store,          # thread-safe wrapper
                model_name=model_key,
                max_attempts=3,                   # could be made configurable
            )

            # Run generation (blocking)
            result_session = orch.generation(request)

            elapsed = time.time() - start_time
            feedback = result_session.llm_feedback
            res = RequestResult(
                request_index=idx,
                model_name=model_key,
                sql_code=result_session.sql_code,
                status=result_session.status.value if result_session.status else None,
                error=result_session.execution_result if isinstance(result_session.execution_result, str)
                else str(result_session.execution_result) if result_session.execution_result else None,
                feedback_category=feedback.error_category.value if feedback.error_category else None,
                feedback_explanation=feedback.explanation,
                attempts=feedback.attempt,
                time_taken=elapsed,
                success=True,
            )
            logger.info(f"Finished request {idx} in {elapsed:.2f}s")
        except TimeoutError as e:
            logger.exception(f"Timeout processing request {idx}")
            res = RequestResult(
                request_index=idx,
                model_name=model_key,
                sql_code=None,
                status="TIMEOUT",
                error=str(e),
                feedback_category=None,
                feedback_explanation=None,
                attempts=0,
                time_taken=TIMEOUT_PER_REQUEST,
                success=False,
            )
        except Exception as e:
            logger.exception(f"Error processing request {idx}")
            elapsed = time.time() - start_time
            res = RequestResult(
                request_index=idx,
                model_name=model_key,
                sql_code=None,
                status="ERROR",
                error=str(e),
                feedback_category=None,
                feedback_explanation=None,
                attempts=0,
                time_taken=elapsed,
                success=False,
            )
        result_queue.put((idx, model_key, res))

    logger.info("Thread finished all requests.")


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

    logger = logging.getLogger("printer")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(logs_dir / "printer.log", encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logger.addHandler(fh)

    logger.info(f"Printer started. Expecting {total_expected} results.")

    while received < total_expected:
        try:
            idx, model, res = result_queue.get(timeout=1)
            received += 1
            if idx not in results_by_index:
                results_by_index[idx] = {}
            results_by_index[idx][model] = res

            # Check if this index is now complete
            if len(results_by_index[idx]) == num_models:
                completed_indices.add(idx)

            # Write any consecutive completed indices starting from next_index
            while next_index in completed_indices:
                _write_request_file(next_index, results_by_index[next_index], requests, queries_dir)
                next_index += 1

        except queue.Empty:
            # No new results, continue loop
            pass

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
        f.write(f"[Request]\n{request_text}\n\n")
        # Write results in the same order as models (from config)
        for i, model_key in enumerate(QUERY_GENERATION_MODELS.keys(), 1):
            res = results.get(model_key)
            if res is None:
                f.write(f"{i}. [{model_key}]\n\nNo result\n\n")
                continue
            f.write(f"{i}. [{model_key}]\n\n")
            f.write(f"Query:\n{res.sql_code or 'N/A'}\n\n")
            f.write(f"Status and outcome: {res.status}, {res.error or 'N/A'}\n")
            f.write(f"LLM Feedback: {res.feedback_category or 'N/A'} {res.feedback_explanation or ''}\n")
            f.write(f"Attempts: {res.attempts}\n")
            f.write(f"Request time: {res.time_taken:.2f}s\n\n")


def _write_statistics(
    results_by_index: Dict[int, Dict[str, RequestResult]],
    num_requests: int,
    stats_path: Path,
    requests: List[str],
) -> None:
    """Aggregate statistics and write to final_stats.txt."""
    total_requests = num_requests
    successful_executions = 0
    correct_queries = 0
    runtime_errors = 0
    syntax_errors = 0
    other_errors = 0
    total_attempts = 0

    # Per-model stats
    model_stats = {model: {"correct": 0, "total_time": 0.0, "attempts": 0, "count": 0}
                   for model in QUERY_GENERATION_MODELS.keys()}

    for idx, models_dict in results_by_index.items():
        for model, res in models_dict.items():
            if res.success:
                successful_executions += 1
                total_attempts += res.attempts
                model_stats[model]["attempts"] += res.attempts
                model_stats[model]["total_time"] += res.time_taken
                model_stats[model]["count"] += 1

                if res.status == QueryStatus.SUCCESS.value:
                    correct_queries += 1
                    model_stats[model]["correct"] += 1
                elif res.status == QueryStatus.RUNTIME_ERROR.value:
                    runtime_errors += 1
                elif res.status == QueryStatus.SYNTAX_ERROR.value:
                    syntax_errors += 1
                else:
                    other_errors += 1
            else:
                # Exception occurred – count as other error
                other_errors += 1

    # Build report
    lines = []
    lines.append("=== FINAL STATISTICS ===\n")
    lines.append(f"Total input requests: {total_requests}")
    lines.append(f"Successful executions (no exception): {successful_executions}")
    lines.append(f"Correct queries: {correct_queries}")
    lines.append(f"Runtime errors: {runtime_errors}")
    lines.append(f"Syntax errors: {syntax_errors}")
    lines.append(f"Other errors: {other_errors}")
    lines.append(f"Total attempts across all executions: {total_attempts}\n")

    lines.append("Model rankings (by time, attempts, success rate):")
    for model, stats in model_stats.items():
        avg_time = stats["total_time"] / stats["count"] if stats["count"] > 0 else 0
        avg_attempts = stats["attempts"] / stats["count"] if stats["count"] > 0 else 0
        success_rate = (stats["correct"] / stats["count"] * 100) if stats["count"] > 0 else 0
        lines.append(f"  {model}:")
        lines.append(f"    Avg time: {avg_time:.2f}s")
        lines.append(f"    Avg attempts: {avg_attempts:.2f}")
        lines.append(f"    Success rate: {success_rate:.1f}% ({stats['correct']}/{stats['count']})")

    with open(stats_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print("\n" + "\n".join(lines))
    
def select_database():
    client = MySQLClient()  # connects without specific database
    dbs = client.list_databases()
    client.close_connection()
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

def run_stress_test(mode: str, database_name: str, timeout: int) -> None:
    # ------------------------------------------------------------------
    # PHASE ONE: Initialization
    # ------------------------------------------------------------------
    print("=== PHASE ONE: Initialization ===")

    # 1. Database selection
    db_name = database_name
    if db_name is None:
        db_name = select_database()

    # 2. Load requests
    requests = load_requests(db_name)

    # 3. Create output directories
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = TESTS_DIR / 'output' / 'runs' / f"{db_name}_results" / f"results_{timestamp}"
    queries_dir = output_dir / 'queries'
    logs_dir = output_dir / 'logs'
    queries_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output will be written to: {output_dir}")

    # 4. Acquire schema from MySQL and store in vector store
    source = SchemaSource.MYSQL if mode == 'mysql' else SchemaSource.TEXT
    print("Acquiring schema from MySQL...")
    schema_orc = SchemaOrchestrator(database_name=db_name, source=source)
    schema = schema_orc.acquire_schema()  # This also saves JSON and adds to vector store
    schema_store = schema_orc.schema_store
    print("Schema acquisition completed.")

    # 5. Initialize shared query store with lock
    query_store_lock = threading.Lock()
    thread_safe_query_store = ThreadSafeQueryStore(VECTOR_STORE_DIR, query_store_lock)

    # ------------------------------------------------------------------
    # PHASE TWO: Core Execution
    # ------------------------------------------------------------------
    print("=== PHASE TWO: Core Execution ===")

    result_queue = queue.Queue()
    num_models = len(QUERY_GENERATION_MODELS)

    # Start printer thread
    printer = threading.Thread(
        target=printer_thread,
        args=(result_queue, num_models, len(requests), queries_dir, logs_dir, requests)
    )
    printer.start()

    # Start generator threads (one per model)
    threads = []
    for model_key in QUERY_GENERATION_MODELS.keys():
        t = threading.Thread(
            target=generator_thread,
            args=(format_model_key(model_key), 
                  requests, result_queue, timeout,
                  schema_store, thread_safe_query_store, 
                  logs_dir, db_name)
        )
        t.start()
        threads.append(t)

    # Wait for all generator threads to finish
    for t in threads:
        t.join()

    # Wait for printer to finish processing all results
    printer.join()

    print("All threads finished. Output written to:", output_dir)
# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Test QueryOrchestrator with multiple models.")
    parser.add_argument('--mode', choices=['mysql', 'text'], default='mysql',
                        help="Schema source mode (mysql or text). Default: mysql")
    parser.add_argument('--database_name', type=str, default=None,
                        help="Name of the database. If not provided, list available databases.")
    parser.add_argument('--timeout', type=int, default=TIMEOUT_PER_REQUEST,
                        help="Timeout per request in seconds.")
    args = parser.parse_args()

    run_stress_test(args.mode, args.database_name, args.timeout)

if __name__ == "__main__":
    main()
