import queue
import shutil
import sys
import threading
import time
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from classes.RAG_service.query_store import QueryStore
from config import QUERY_MODELS, TIMEOUT_PER_REQUEST, TMP_DIR
from src.classes.clients import SQLiteClient
from src.classes.datasets import BaseDataset
from src.classes.domain_states import QuerySession, QueryStatus, Schema, SchemaSource, Records
from src.classes.logger import LoggerManager
from src.classes.orchestrators import QueryOrchestrator
from src.classes.RAG_service.schema_store import SchemaStore
from tests.stats_report import ResultsByIndex, write_statistics_report

class ThreadSafeQueryStore(QueryStore):
    def __init__(self, path: Path, lock: threading.Lock):
        super().__init__(path)
        self._lock = lock

    def store_query(self, query: QuerySession) -> None:
        with self._lock:
            super().store_query(query)

@dataclass
class RequestResult:
    request_index: int
    model_name: str
    query_session: Optional[QuerySession]
    time_taken: float
    success: bool
    gold_query_sql: Optional[str] = None
    complexity: int = 0
    evaluation_method: Optional[str] = None
    evaluation_status: Optional[str] = None
    evaluation_verdict: Optional[str] = None
    evaluation_reason: Optional[str] = None

    def compute_query_complexity(self) -> None:
        sql = self.gold_query_sql

        if not sql:
            return

        score = 0
        score += len(re.findall(r"\bJOIN\b", sql, re.IGNORECASE)) * 2
        score += len(re.findall(r"\b(SUM|AVG|MIN|MAX|COUNT)\s*\(", sql, re.IGNORECASE)) * 2

        if re.search(r"\bGROUP\s+BY\b", sql, re.IGNORECASE):
            score += 2

        if re.search(r"\bHAVING\b", sql, re.IGNORECASE):
            score += 2

        score += len(re.findall(r"\bOVER\s*\(", sql, re.IGNORECASE)) * 3
        score += len(re.findall(r"\bSELECT\b", sql, re.IGNORECASE)) - 1
        self.complexity = score

    def get_query_complexity(self) -> Optional[int]:
        sql = self.gold_query_sql
        if not sql:
            return None

        if self.complexity == 0:
            self.compute_query_complexity()

        return self.complexity

    @staticmethod
    def complexity_level_from_score(score: float) -> str:
        if score <= 2:
            return "low"
        if score <= 5:
            return "medium"
        return "high"

    def get_complexity_level(self) -> Optional[str]:
        complexity = self.get_query_complexity()
        if complexity is None:
            return None

        return self.complexity_level_from_score(complexity)

    def format_output_content(self, index: int) -> str:
        query_session = self.query_session
        lines = []

        lines.append(f"{index}. 🤖[{self.model_name}]\n")
        lines.append(f"🧮 Query:\n\n{query_session.sql_code if query_session else 'N/A'}\n")

        if self.evaluation_status == "success":
            status_label = "SUCCESS"
        elif self.evaluation_status == "incorrect":
            status_label = "INCORRECT"
        elif self.evaluation_status == "error":
            status_label = "EVAL_ERROR"
        elif query_session and query_session.status:
            if query_session.status.value == "SUCCESS":
                status_label = "NOT_EVALUATED"
            else:
                status_label = query_session.status.value
        else:
            status_label = "RUNTIME_ERROR"

        execution_result = query_session.execution_result if query_session else None

        if status_label in ("SUCCESS", "INCORRECT", "NOT_EVALUATED"):
            rows_fetched = query_session.rows_fetched if query_session else None
            if rows_fetched is None and isinstance(execution_result, Records):
                rows_fetched = len(execution_result)

            if rows_fetched is not None:
                outcome = f"({rows_fetched} rows fetched)"
            else:
                if status_label == "SUCCESS":
                    outcome = "(Query executed successfully)"
                elif status_label == "INCORRECT":
                    outcome = "(Query executed)"
                else:
                    outcome = "(Query executed, dataset evaluation not available)"
            if status_label == "SUCCESS":
                status_emoji = "🍾SUCCESS"
            elif status_label == "INCORRECT":
                status_emoji = "⚠️INCORRECT"
            else:
                status_emoji = "✅NOT_EVALUATED"
        else:
            outcome = f"({execution_result})" if execution_result else ""
            status_emoji = f"❌{status_label}"

        lines.append(f"📌 Status:\n\n{status_emoji} {outcome}\n")

        if self.evaluation_method:
            lines.append(f"🧪 Eval Method:\n\n{self.evaluation_method}\n")
        if self.evaluation_verdict:
            lines.append(f"⚖️ Eval Verdict:\n\n{self.evaluation_verdict}\n")
        if self.evaluation_reason:
            lines.append(f"📝 Eval Reason:\n\n{self.evaluation_reason}\n")

        lines.append(f"⏱️ Time: {self.time_taken:.2f}s")
        return "\n".join(lines)

def _progress_bar(done: int, total: int, width: int = 26) -> str:
    """Build a unicode progress bar like █████░░░░ for terminal output."""
    if total <= 0:
        total = 1
    ratio = max(0.0, min(1.0, done / total))
    filled = int(round(ratio * width))
    return f"{'█' * filled}{'░' * (width - filled)}"


def _print_model_progress(
    database_name: str,
    model_progress: Dict[str, int],
    num_requests: int,
    received: int,
    total_expected: int,
) -> None:
    """Render an in-place multi-line status panel with per-model request progress."""
    if not sys.stdout.isatty():
        return

    term_width = shutil.get_terminal_size((110, 30)).columns
    header = (
        f"✨ Live model progress | database: {database_name} | "
        f"total results: {received}/{total_expected}"
    )
    lines = [header, "─" * min(term_width, max(30, len(header)))]

    for i, model in enumerate(QUERY_MODELS.keys(), 1):
        done = model_progress.get(model, 0)
        pct = (done / num_requests * 100) if num_requests > 0 else 0
        bar = _progress_bar(done, num_requests)
        lines.append(f"{i:>2}. 🤖 {model:<20} [{bar}] {done:>3}/{num_requests:<3} ({pct:6.2f}%)")

    panel = "\n".join(lines)
    sys.stdout.write("\033[H\033[J")
    sys.stdout.write(panel + "\n")
    sys.stdout.flush()

def _write_request_file(
    index: int,
    results: Dict[str, RequestResult],
    requests: List[str],
    queries_dir: Path,
) -> None:
    """Write a single request output file."""
    request_text = requests[index - 1]
    safe_req = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', '', request_text)
    safe_req = re.sub(r'\s+', '_', safe_req).strip(' ._')
    if not safe_req:
        safe_req = "request"
    safe_req = safe_req[:20]
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

# ----------------------------------------------------------------------
# Printer thread function
# ----------------------------------------------------------------------
def printer_thread(
    result_queue: queue.Queue,
    database_name: str,
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
    results_by_index: ResultsByIndex = {}
    completed_indices = set()
    next_index = 1
    total_expected = num_models * num_requests
    received = 0
    model_progress = {model: 0 for model in QUERY_MODELS.keys()}

    # Use LoggerManager for printer thread
    logger = LoggerManager.get_logger("printer", log_file=output_dir / "logs" / "printer.log")
    logger.info(f"Printer started. Expecting {total_expected} results.")
    _print_model_progress(database_name, model_progress, num_requests, received, total_expected)

    while received < total_expected:
        try:
            idx, model, res = result_queue.get(timeout=1)
            received += 1
            logger.info(f"Received result for request: {idx}, model: {model}")
            if model in model_progress:
                model_progress[model] += 1
            _print_model_progress(database_name, model_progress, num_requests, received, total_expected)
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
    write_statistics_report(results_by_index, num_requests, queries_dir.parent / "final_stats.txt")
    logger.info("Printer finished.")
    if sys.stdout.isatty():
        print("✅ All model requests have been processed.\n")
        
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
