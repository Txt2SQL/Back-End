"""
Spider evaluation runner for QueryOrchestrator.

Loads Spider dev examples and table metadata, builds a text-based schema for a
selected database, then runs all configured query models concurrently. Each
generated SQL query is evaluated through the Spider execution evaluator in a
subprocess that exits with:

- 0 when execution matches the gold query
- 1 when execution does not match
"""

import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import QUERY_MODELS, SPIDER_DATA, TESTS_DIR, TIMEOUT_PER_REQUEST, SPIDER_REPO
from src.classes.RAG_service.query_store import QueryStore
from src.classes.RAG_service.schema_store import SchemaStore
from src.classes.domain_states import QuerySession, QueryStatus, Schema, SchemaSource
from src.classes.logger import LoggerManager
from src.classes.orchestrators.query_orchestrator import QueryOrchestrator
from tests.output_object import RequestResult
from tests.test_sql_generation import empty_tmp_dir, printer_thread


TMP_DIR = TESTS_DIR / "tmp"
SPIDER_DEV_PATH = SPIDER_DATA / "dev.json"
SPIDER_TABLES_PATH = SPIDER_DATA / "tables.json"
SPIDER_DB_DIR = SPIDER_DATA / "database"
EVAL_FILE = SPIDER_REPO / "evaluation.py"

LoggerManager.setup_project_logger()
main_logger = LoggerManager.get_logger("spider_test")


class ThreadSafeQueryStore(QueryStore):
    def __init__(self, path: Path, lock: threading.Lock):
        super().__init__(path)
        self._lock = lock

    def store_query(self, query: QuerySession) -> None:
        with self._lock:
            super().store_query(query)


def spider_schema_to_internal(spider_schema: dict) -> dict:
    tables = spider_schema["table_names_original"]
    columns = spider_schema["column_names_original"]
    column_types = spider_schema["column_types"]
    primary_keys = set(spider_schema["primary_keys"])
    foreign_keys = spider_schema["foreign_keys"]

    type_map = {
        "text": "TEXT",
        "number": "INT",
        "time": "DATETIME",
        "boolean": "BOOLEAN",
    }

    db = {table: [] for table in tables}

    for idx, ((table_id, col_name), col_type) in enumerate(zip(columns, column_types)):
        if table_id == -1:
            continue

        table_name = tables[table_id]
        constraints = []

        if idx in primary_keys:
            constraints.append("PRIMARY KEY")

        db[table_name].append(
            {
                "name": col_name,
                "type": type_map.get(col_type, "TEXT"),
                "constraints": constraints,
            }
        )

    for fk_col, ref_col in foreign_keys:
        fk_table_id, fk_name = columns[fk_col]
        ref_table_id, ref_name = columns[ref_col]

        fk_table = tables[fk_table_id]
        ref_table = tables[ref_table_id]

        for col in db[fk_table]:
            if col["name"] == fk_name:
                col["constraints"].append(
                    f"FOREIGN KEY REFERENCES {ref_table}({ref_name})"
                )

    return {
        "tables": [
            {
                "name": table_name,
                "columns": cols,
            }
            for table_name, cols in db.items()
        ]
    }

def create_output_dir(db_name: str, output_name: str | None = None) -> tuple[Path, Path, Path]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = output_name if output_name else f"results_{timestamp}"
    output_dir = TESTS_DIR / "output" / "generations" / f"{db_name}_results" / run_name
    queries_dir = output_dir / "queries"
    logs_dir = output_dir / "logs"
    queries_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output will be written to: {output_dir}")
    return output_dir, queries_dir, logs_dir


def load_spider_dataset() -> tuple[List[dict], List[dict]]:
    with SPIDER_DEV_PATH.open("r", encoding="utf-8") as f:
        spider_data = json.load(f)

    with SPIDER_TABLES_PATH.open("r", encoding="utf-8") as f:
        spider_tables = json.load(f)

    return spider_data, spider_tables


def print_database_table_counts(spider_tables: List[dict]) -> List[dict]:
    ordered_tables = sorted(spider_tables, key=lambda item: item["db_id"])
    print("Available Spider databases:")
    for entry in ordered_tables:
        print(f"{entry['db_id']} {len(entry['table_names'])}")
    return ordered_tables


def select_database(spider_tables: List[dict], database_name: str | None = None) -> str:
    ordered_tables = print_database_table_counts(spider_tables)
    db_names = [entry["db_id"] for entry in ordered_tables]

    if database_name is not None:
        if database_name not in db_names:
            raise ValueError(f"Unknown Spider database: {database_name}")
        print(f"Using database: {database_name}")
        return database_name

    while True:
        choice = input("Select database by name: ").strip()
        if choice in db_names:
            print(f"Using database: {choice}")
            return choice
        print("Invalid database name. Try again.")


def build_spider_schema(
    database_name: str,
    tables_by_db: dict[str, dict],
) -> tuple[Schema, SchemaStore]:
    spider_schema = tables_by_db[database_name]
    converted_schema = spider_schema_to_internal(spider_schema)

    schema = Schema(
        database_name=database_name,
        schema_source=SchemaSource.TEXT,
        path=TESTS_DIR / "tmp",
    )
    schema.parse_response(converted_schema)

    schema_store = SchemaStore(TMP_DIR / "vector_stores")
    schema_store.add_schema(schema)

    return schema, schema_store


def evaluate_with_spider(
    database_name: str,
    request_index: int,
    model_key: str,
    gold_sql: str,
    predicted_sql: str,
    logs_dir: Path,
) -> subprocess.CompletedProcess[str]:
    eval_dir = logs_dir / "spider_eval"
    eval_dir.mkdir(parents=True, exist_ok=True)

    model_slug = QUERY_MODELS[model_key]["log_file"]
    gold_file = eval_dir / f"{request_index:04d}_{model_slug}_gold.sql"
    pred_file = eval_dir / f"{request_index:04d}_{model_slug}_pred.sql"

    gold_file.write_text(f"{gold_sql}\t{database_name}\n", encoding="utf-8")
    pred_file.write_text(f"{predicted_sql}\n", encoding="utf-8")

    return subprocess.run(
        [
            "python3",
            str(EVAL_FILE),
            "--gold",
            str(gold_file),
            "--pred",
            str(pred_file),
            "--etype",
            "exec",
            "--db",
            str(SPIDER_DB_DIR),
            "--table",
            str(SPIDER_TABLES_PATH),
        ],
        cwd=SPIDER_REPO,
        capture_output=True,
        text=True,
        check=False,
    )


def text_generator_thread(
    database_name: str,
    model_key: str,
    requests: List[dict],
    result_queue: queue.Queue,
    schema_store: SchemaStore,
    query_store: ThreadSafeQueryStore,
    logs_dir: Path,
    schema: Schema,
) -> None:
    log_name = QUERY_MODELS[model_key]["log_file"]
    log_file = logs_dir / f"{log_name}.log"

    logger = LoggerManager.get_logger(name=f"spider_thread_{log_name}", log_file=log_file)
    LoggerManager.set_thread_logger(logger)

    try:
        logger.info(
            "Started Spider generator thread for model=%s schema_source=%s schema_path=%s",
            model_key,
            schema.source.value,
            schema.file_path,
        )

        for idx, request in enumerate(requests, start=1):
            question = request["question"]
            gold_sql = request["query"]

            LoggerManager.set_request_index(f"[Request: {idx}]")
            logger.info("Processing Spider request for db=%s: %s", database_name, question)

            start_time = time.time()

            try:
                orch = QueryOrchestrator(
                    database_name=database_name,
                    schema_store=schema_store,
                    model_name=model_key,
                    database_client=None,
                    query_store=query_store,
                    max_attempts=3,
                    instance_path=TMP_DIR,
                )

                result_session = orch.generation(question)

                predicted_sql = result_session.sql_code or ""
                eval_result = evaluate_with_spider(
                    database_name=database_name,
                    request_index=idx,
                    model_key=model_key,
                    gold_sql=gold_sql,
                    predicted_sql=predicted_sql,
                    logs_dir=logs_dir,
                )

                if eval_result.returncode == 0:
                    result_session.status = QueryStatus.SUCCESS
                    result_session.execution_status = QueryStatus.SUCCESS
                    result_session.execution_result = "Spider execution evaluation passed."
                    success = True
                elif eval_result.returncode == 1:
                    result_session.status = QueryStatus.INCORRECT
                    result_session.execution_status = QueryStatus.INCORRECT
                    stderr = eval_result.stderr.strip()
                    stdout = eval_result.stdout.strip()
                    result_session.execution_result = stderr or stdout or "Spider execution evaluation failed."
                    success = True
                else:
                    result_session.status = QueryStatus.RUNTIME_ERROR
                    stderr = eval_result.stderr.strip()
                    stdout = eval_result.stdout.strip()
                    result_session.execution_result = stderr or stdout or "Spider evaluator subprocess failed."
                    success = False

                elapsed = time.time() - start_time
                res = RequestResult(
                    request_index=idx,
                    model_name=model_key,
                    query_session=result_session,
                    time_taken=elapsed,
                    success=success,
                )

                logger.info(
                    "Completed Spider request with status=%s in %.2fs",
                    result_session.status.value,
                    elapsed,
                )

            except TimeoutError as exc:
                elapsed = TIMEOUT_PER_REQUEST
                logger.exception("Timeout after %ss", elapsed)

                timeout_session = QuerySession(user_request=question)
                timeout_session.execution_result = str(exc)
                timeout_session.status = QueryStatus.TIMEOUT_ERROR

                res = RequestResult(
                    request_index=idx,
                    model_name=model_key,
                    query_session=timeout_session,
                    time_taken=elapsed,
                    success=False,
                )
            except Exception as exc:
                elapsed = time.time() - start_time
                logger.exception("Failed after %.2fs", elapsed)

                failed_session = QuerySession(user_request=question)
                failed_session.execution_result = str(exc)
                failed_session.status = QueryStatus.RUNTIME_ERROR

                res = RequestResult(
                    request_index=idx,
                    model_name=model_key,
                    query_session=failed_session,
                    time_taken=elapsed,
                    success=False,
                )

            result_queue.put((idx, model_key, res))

        logger.info("Spider generator thread finished for model=%s", model_key)
    finally:
        LoggerManager.clear_thread_logger()


def run_spider_test(database_name: str | None, output_name: str | None = None) -> None:
    print("=== SPIDER TEST INITIALIZATION ===")
    main_logger.info("Starting Spider test")

    spider_data, spider_tables = load_spider_dataset()
    tables_by_db = {entry["db_id"]: entry for entry in spider_tables}

    db_name = select_database(spider_tables, database_name)
    requests = [example for example in spider_data if example["db_id"] == db_name]
    request_texts = [example["question"] for example in requests]

    if not requests:
        raise ValueError(f"No Spider dev requests found for database: {db_name}")

    main_logger.info("Loaded %s Spider requests for db=%s", len(requests), db_name)

    output_dir, queries_dir, logs_dir = create_output_dir(db_name, output_name)
    empty_tmp_dir()

    schema, schema_store = build_spider_schema(db_name, tables_by_db)
    query_store_lock = threading.Lock()
    thread_safe_query_store = ThreadSafeQueryStore(TMP_DIR / "vector_stores", query_store_lock)

    result_queue: queue.Queue = queue.Queue()
    num_models = len(QUERY_MODELS)

    printer = threading.Thread(
        target=printer_thread,
        args=(result_queue, num_models, len(requests), queries_dir, logs_dir, request_texts),
    )
    printer.start()
    main_logger.info("Printer thread started")

    threads = []
    for model_key in QUERY_MODELS.keys():
        thread = threading.Thread(
            target=text_generator_thread,
            args=(
                db_name,
                model_key,
                requests,
                result_queue,
                schema_store,
                thread_safe_query_store,
                logs_dir,
                schema,
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
    args = parser.parse_args()

    run_spider_test(args.database_name, args.output_name)


if __name__ == "__main__":
    main()
