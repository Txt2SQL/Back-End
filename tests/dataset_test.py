"""
Spider evaluation runner for QueryOrchestrator.

Loads Spider dev examples and table metadata, builds a text-based schema for a
selected database, then runs all configured query models concurrently. Each
generated SQL query is evaluated through the Spider execution evaluator in a
subprocess that exits with:

- 0 when execution matches the gold query
- 1 when execution does not match
"""

import argparse, os, queue, sys, threading, time
from dataclasses import dataclass
from pathlib import Path
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from classes.clients.mysql_client import MySQLClient
from config import QUERY_MODELS, TESTS_DIR, TIMEOUT_PER_REQUEST
from src.classes.RAG_service.schema_store import SchemaStore
from src.classes.domain_states import QuerySession, QueryStatus, Schema, SchemaSource
from src.classes.logger import LoggerManager
from src.classes.orchestrators.query_orchestrator import QueryOrchestrator
from src.classes.datasets import BaseDataset, BirdDataset, SpiderDataset
from tests.thread_output import RequestResult
from tests.test_sql_generation import empty_tmp_dir, printer_thread, create_output_dir, ThreadSafeQueryStore


TMP_DIR = TESTS_DIR / "tmp"

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


def build_spider_schema(
    database_name: str,
    converted_schema: dict,
) -> tuple[Schema, SchemaStore]:

    schema = Schema(
        database_name=database_name,
        schema_source=SchemaSource.TEXT,
        path=TESTS_DIR / "tmp",
    )
    schema.parse_response(converted_schema)

    schema_store = SchemaStore(TMP_DIR / "vector_stores")
    schema_store.add_schema(schema)

    return schema, schema_store


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

        if schema.source == SchemaSource.MYSQL:
            db_client = MySQLClient(database_name)
            qs = query_store
        else:
            db_client = None
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
                    database_client=db_client,
                    query_store=qs,
                    max_attempts=3,
                    instance_path=TMP_DIR,
                )

                logger.debug(f"Starting generation")

                result_session = orch.generation(request)
                
                eval_result = dataset.evaluation(
                    predicted_sql=result_session.sql_code or "",
                    db_id=database_name,
                    question=request
                )

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

    if dataset_name not in ["spider", "bird"]:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    elif dataset_name is None:
        dataset_name = select_dataset()

    if dataset_name == "bird":
        main_logger.info("Selected dataset: BIRD")
        dataset = BirdDataset()
    else:
        main_logger.info("Selected dataset: Spider")
        dataset = SpiderDataset()

    if database_name is None:
        database_name = select_database(dataset.get_dbs())

    output_dir, queries_dir, logs_dir = create_output_dir(database_name, output_name)
    empty_tmp_dir()

    schema, schema_store = build_spider_schema(database_name, dataset.get_schema(database_name))
    query_store_lock = threading.Lock()
    thread_safe_query_store = ThreadSafeQueryStore(TMP_DIR / "vector_stores", query_store_lock)

    result_queue: queue.Queue = queue.Queue()
    num_models = len(QUERY_MODELS)
    requests = dataset.get_requests(database_name)

    printer = threading.Thread(
        target=printer_thread,
        args=(result_queue, num_models, len(requests), queries_dir, logs_dir, requests),
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
