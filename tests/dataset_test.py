import argparse, os, queue,shutil, sys, threading
from pathlib import Path
from typing import Sequence

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import QUERY_MODELS, TESTS_DIR, TMP_DIR
from src.classes.RAG_service.schema_store import SchemaStore
from src.classes.clients import SQLiteClient
from src.classes.domain_states import Schema, SchemaSource
from src.classes.logger import LoggerManager
from src.classes.datasets import BirdDataset, SpiderDataset
from tests.thread_wrappers import ThreadSafeQueryStore
from tests.thread_wrappers import generator_thread, printer_thread

LoggerManager.setup_project_logger()
main_logger = LoggerManager.get_logger("dataset_test")

def empty_tmp_dir() -> None:
    """Clear and recreate the tests tmp directory used by stress tests."""
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)
        main_logger.info(f"Removed existing tmp directory: {TMP_DIR}")

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    main_logger.info(f"Created fresh tmp directory: {TMP_DIR}")

def select_database(dataset: SpiderDataset | BirdDataset) -> str:
    tables = dataset.get_dbs()
    for db_name, table_count in tables:
        question_count = len(dataset.get_requests(db_name))
        print(f"{db_name} ({table_count} tables, {question_count} questions)")
    
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


def prepare_output_dir(database_name: str, mode: str) -> Path:
    output_dir = TESTS_DIR / "output" / "generations" / f"{database_name}_results" / mode
    output_dir.mkdir(parents=True, exist_ok=True)

    for child in output_dir.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    return output_dir

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

def run_dataset_test(
    database_name: str | None,
    dataset_name: str | None,
    mode: str,
    model_keys: Sequence[str] | None = None,
) -> None:
    print("=== DATASET TEST INITIALIZATION ===")
    main_logger.info("Starting dataset test")
    selected_models = list(model_keys) if model_keys is not None else list(QUERY_MODELS.keys())

    invalid_models = [model for model in selected_models if model not in QUERY_MODELS]
    if invalid_models:
        available_models = ", ".join(QUERY_MODELS.keys())
        raise ValueError(
            f"Unknown query model(s): {', '.join(invalid_models)}. "
            f"Available models: {available_models}"
        )
    if not selected_models:
        raise ValueError("At least one query model must be selected.")

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
        database_name = select_database(dataset)

    output_dir = prepare_output_dir(database_name, mode)
    logs_dir = output_dir / "logs"
    queries_dir = output_dir / "queries"
    logs_dir.mkdir(parents=True, exist_ok=True)
    queries_dir.mkdir(parents=True, exist_ok=True)
    empty_tmp_dir()

    if mode not in {"db_conn", "text"}:
        raise ValueError(f"Unknown mode: {mode}")

    schema_source = SchemaSource.DB_CONNECTION if mode == "db_conn" else SchemaSource.TEXT
    schema, schema_store = build_schema(database_name, dataset.get_schema(database_name), schema_source)
    query_store_lock = threading.Lock()
    thread_safe_query_store = ThreadSafeQueryStore(TMP_DIR / "vector_stores", query_store_lock)

    result_queue: queue.Queue = queue.Queue()
    num_models = len(selected_models)
    requests = dataset.get_requests(database_name)

    printer = threading.Thread(
        target=printer_thread,
        args=(
            result_queue,
            database_name,
            dataset_name,
            num_models,
            len(requests),
            queries_dir,
            output_dir,
            requests,
            schema,
            selected_models,
        ),
    )
    printer.start()
    main_logger.info("Printer thread started")

    threads = []
    for model_key in selected_models:
        db_client = SQLiteClient(database_name)
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
                db_client,
            ),
        )
        thread.start()
        threads.append(thread)
        main_logger.info("Generator thread started for model=%s", model_key)

    for thread in threads:
        thread.join()

    printer.join()

    print(f"All {dataset_name.upper()} threads finished. Output written to: {output_dir}")
    main_logger.info("%s test completed. Output written to: %s", dataset_name.upper(), output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Spider evaluation across configured query models.")
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Dataset to run the test on. Supported values: 'spider', 'bird'.",
    )
    parser.add_argument(
        "--database-name",
        type=str,
        default=None,
        help="Spider database id to test. If omitted, the script prints all databases and prompts for one.",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="db_conn",
        help="Schema loading mode. Use 'db_conn' for database connection or 'text' for basic generation.",
    )
    parser.add_argument(
        "--llm",
        dest="llms",
        action="append",
        choices=list(QUERY_MODELS.keys()),
        default=None,
        help=(
            "Query model to test. Can be provided multiple times. "
            "Defaults to all models in QUERY_MODELS."
        ),
    )

    args = parser.parse_args()

    run_dataset_test(args.database_name, args.dataset, args.mode, args.llms)


if __name__ == "__main__":
    main()
