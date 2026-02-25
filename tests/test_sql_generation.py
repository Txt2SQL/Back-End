import argparse
import os
import re
import sys
import tempfile
import threading
import time
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_DIR)
sys.path.insert(0, os.path.join(PROJECT_DIR, 'src'))

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from src.classes.clients.database_client import DatabaseClient
from src.classes.domain_states.enums import QueryStatus, SchemaSource
from src.classes.domain_states.schema import Schema
from src.classes.orchestrators.query_orchestrator import QueryOrchestrator
from src.classes.RAG_service.query_store import QueryStore
from src.classes.RAG_service.schema_store import SchemaStore
from src.config import PROJECT_ROOT, QUERY_GENERATION_MODELS


@dataclass
class RunResult:
    request_index: int
    request_text: str
    model_name: str
    sql_code: str
    query_status: str
    outcome: str
    llm_feedback: str
    attempts: int
    request_time_seconds: float


def create_temp_instances_dir() -> str:
    tmp_dir = tempfile.mkdtemp(prefix="query_orchestrator_instances_")
    print(f"🧪 Temporary instances folder created: {tmp_dir}")
    return tmp_dir


def choose_database(database_client: DatabaseClient, selected_db: str | None) -> str:
    available = [
        db
        for db in database_client.list_databases()
        if db not in {"information_schema", "performance_schema", "mysql", "sys"}
    ]

    if not available:
        raise RuntimeError("No user databases found in MySQL server.")

    if selected_db:
        if selected_db not in available:
            raise ValueError(f"Database '{selected_db}' is not available.")
        return selected_db

    print("\n🗂️ Available databases:")
    for index, db_name in enumerate(available, start=1):
        print(f"  {index}. {db_name}")

    while True:
        choice = input("\n👉 Select a database by number or exact name: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(available):
            return available[int(choice) - 1]
        if choice in available:
            return choice
        print("❌ Invalid selection, try again.")


def initialize_output_structure(database_name: str) -> Dict[str, Path]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    root = PROJECT_ROOT / "output" / "runs" / f"{database_name}_results" / f"results_{timestamp}"
    query_dir = root / "querys"
    logs_dir = root / "logs"

    query_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    return {
        "root": root,
        "query_dir": query_dir,
        "logs_dir": logs_dir,
        "stats": root / "final_stats.txt",
    }


def load_requests(input_file: Path) -> List[str]:
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    lines = [line.strip() for line in input_file.read_text(encoding="utf-8").splitlines()]
    return [line for line in lines if line and not line.startswith("#")]


def build_schema_and_rag(database_name: str, schema_store: SchemaStore) -> Schema:
    database_client = DatabaseClient(database_name)
    mysql_schema = database_client.extract_schema()

    schema = Schema(database_name=database_name, schema_source=SchemaSource.MYSQL)
    schema.parse_response(mysql_schema)
    schema_store.add_schema(schema)

    return schema


def slug_request_fragment(text: str, limit: int = 28) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    if not cleaned:
        cleaned = "request"
    return cleaned[:limit]


def format_run_result(indexed_pos: int, result: RunResult) -> str:
    body = [
        f"{indexed_pos}. {result.model_name}",
        "",
        "Query:",
        result.sql_code or "<empty>",
        "",
        f"status and outcome: {result.query_status}, {result.outcome}",
        f"llm_feedback: {result.llm_feedback}",
        f"attempts: {result.attempts} attempt",
        f"request time: {result.request_time_seconds:.3f}s",
        "",
    ]
    return "\n".join(body)


def run_single_generation(
    database_name: str,
    request_index: int,
    request_text: str,
    model_name: str,
    query_store: QueryStore,
    schema_store: SchemaStore,
    log_path: Path,
    log_lock: threading.Lock,
) -> RunResult:
    start = time.perf_counter()
    orchestrator = QueryOrchestrator(
        database_name=database_name,
        query_store=query_store,
        schema_store=schema_store,
        user_request=request_text,
        model_name=model_name,
    )

    query_session = orchestrator.generation(request_text)
    elapsed = time.perf_counter() - start

    feedback = query_session.llm_feedback.feedback_status.value
    if query_session.llm_feedback.explanation:
        feedback = f"{feedback}: {query_session.llm_feedback.explanation}"

    result = RunResult(
        request_index=request_index,
        request_text=request_text,
        model_name=model_name,
        sql_code=query_session.sql_code or "",
        query_status=query_session.status.value,
        outcome=str(query_session.execution_result),
        llm_feedback=feedback,
        attempts=query_session.llm_feedback.attempt,
        request_time_seconds=elapsed,
    )

    with log_lock:
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(
                (
                    f"[{datetime.now().isoformat()}] model={model_name} "
                    f"status={result.query_status} attempts={result.attempts} "
                    f"time={result.request_time_seconds:.3f}s\n"
                )
            )

    return result


def write_request_outputs(query_file: Path, request_text: str, results: List[RunResult]) -> None:
    parts = [f"{request_text}\n"]
    for idx, run in enumerate(results, start=1):
        parts.append(format_run_result(idx, run))

    query_file.write_text("\n".join(parts), encoding="utf-8")


def write_final_statistics(
    output_file: Path,
    request_count: int,
    execution_count: int,
    all_results: List[RunResult],
    model_names: List[str],
) -> None:
    correct = sum(1 for r in all_results if r.query_status == QueryStatus.SUCCESS.value)
    runtime = sum(1 for r in all_results if r.query_status == QueryStatus.RUNTIME_ERROR.value)
    syntax = sum(1 for r in all_results if r.query_status == QueryStatus.SYNTAX_ERROR.value)
    other = execution_count - correct - runtime - syntax
    attempts_total = sum(r.attempts for r in all_results)

    ranking_lines: List[str] = []
    aggregated = []
    for model_name in model_names:
        model_runs = [r for r in all_results if r.model_name == model_name]
        if not model_runs:
            continue

        avg_time = sum(r.request_time_seconds for r in model_runs) / len(model_runs)
        avg_attempts = sum(r.attempts for r in model_runs) / len(model_runs)
        success_rate = (
            sum(1 for r in model_runs if r.query_status == QueryStatus.SUCCESS.value)
            / len(model_runs)
        )

        aggregated.append((model_name, avg_time, avg_attempts, success_rate))

    aggregated.sort(key=lambda row: (-row[3], row[1], row[2]))

    for pos, (model_name, avg_time, avg_attempts, success_rate) in enumerate(aggregated, start=1):
        ranking_lines.append(
            f"{pos}. {model_name} | success_rate={success_rate:.2%} | avg_time={avg_time:.3f}s | avg_attempts={avg_attempts:.2f}"
        )

    content = "\n".join(
        [
            "Final statistics",
            "================",
            f"Number of requests loaded: {request_count}",
            f"Number of executions launched: {execution_count}",
            f"Correct queries: {correct}",
            f"Queries with runtime errors: {runtime}",
            f"Queries with syntax errors: {syntax}",
            f"Other errors: {other}",
            f"Total sum of attempts across all executions: {attempts_total}",
            "",
            "Model rankings",
            "--------------",
            *ranking_lines,
            "",
        ]
    )

    output_file.write_text(content, encoding="utf-8")


def run_workflow(input_file: Path, selected_db: str | None) -> Path:
    create_temp_instances_dir()

    bootstrap_client = DatabaseClient()
    database_name = choose_database(bootstrap_client, selected_db)

    output_paths = initialize_output_structure(database_name)
    requests = load_requests(input_file)

    schema_store = SchemaStore()
    query_store = QueryStore()

    # Schema retrieval from MySQL and RAG setup for schema/query memory.
    build_schema_and_rag(database_name, schema_store)

    models = list(QUERY_GENERATION_MODELS.keys())

    all_results: List[RunResult] = []
    futures = []
    result_map: Dict[int, List[RunResult]] = {index: [] for index in range(1, len(requests) + 1)}

    log_locks: Dict[int, threading.Lock] = {}
    log_paths: Dict[int, Path] = {}
    query_paths: Dict[int, Path] = {}

    for index, request in enumerate(requests, start=1):
        suffix = slug_request_fragment(request)
        log_paths[index] = output_paths["logs_dir"] / f"{index:02d}_{suffix}.log"
        query_paths[index] = output_paths["query_dir"] / f"{index:02d}_{suffix}.txt"
        log_locks[index] = threading.Lock()

    with ThreadPoolExecutor(max_workers=max(4, len(models))) as pool:
        for index, request in enumerate(requests, start=1):
            for model_name in models:
                futures.append(
                    pool.submit(
                        run_single_generation,
                        database_name,
                        index,
                        request,
                        model_name,
                        query_store,
                        schema_store,
                        log_paths[index],
                        log_locks[index],
                    )
                )

        for future in as_completed(futures):
            result = future.result()
            result_map[result.request_index].append(result)
            all_results.append(result)

    for index, request in enumerate(requests, start=1):
        ordered_results = sorted(result_map[index], key=lambda r: r.model_name)
        write_request_outputs(query_paths[index], request, ordered_results)

    write_final_statistics(
        output_paths["stats"],
        request_count=len(requests),
        execution_count=len(futures),
        all_results=all_results,
        model_names=models,
    )

    return output_paths["root"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run end-to-end QueryOrchestrator SQL generation workflow")
    parser.add_argument(
        "--input",
        type=str,
        default=str(PROJECT_ROOT / "data" / "sample_query.sql"),
        help="Input file containing one request per line",
    )
    parser.add_argument("--db", type=str, default=None, help="Database name to use")

    args = parser.parse_args()
    output_root = run_workflow(Path(args.input), args.db)
    print(f"✅ Workflow completed. Output directory: {output_root}")


if __name__ == "__main__":
    main()
