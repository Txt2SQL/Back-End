import sys, os, pytest, json, time, shutil, logging
# Add parent directory to Python path for development
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime
from langchain_chroma import Chroma
from typing import Dict, List, Tuple
from langchain_ollama import OllamaEmbeddings
from src.config.settings import AVAILABLE_MODELS, MAX_OUTPUT_LENGTH, AZURE_MODELS, LOGINFO_SEPARATOR
from src.mysql_linker import extract_schema, get_db_connection, list_databases
from src.retriver_utils import build_vector_store
from tests import generate_realistic_mysql_db as db_generator
from pathlib import Path
from src.logging_utils import (
    setup_single_project_logger, 
    setup_logger,
    truncate_request,
    add_request_log_handler,
    remove_request_log_handler,
)
from src.query_generator import (
    generate_sql_query,
    validate_sql_syntax,
    execute_sql_query,
    store_query_feedback,
    compute_schema_id,
    create_metadata,
    get_llm_model,
    create_prompt,
    generation_loop,
    evaluate_feedback_error,
    get_context,
    SCHEMA_COLLECTION_NAME,
    QUERY_COLLECTION_NAME,
)

# ==================== CONFIGURATION ====================
BASE_DIR = Path(__file__).resolve().parent
TMP_DIR = BASE_DIR / "tmp"
INPUT_FILE = "./input/requests/test_requests.txt"
OUTPUT_DIR = "./output"
TIMEOUT_PER_MODEL = 600   # 10 minutes timeout per model per request
QVS_DIR = str(TMP_DIR / "query_vector_store")
SVS_DIR = str(TMP_DIR / "schema_vector_store")

# === LOGGING SETUP ===
setup_single_project_logger()
logger = setup_logger(__name__)

# ==================== TEST FUNCTIONS ====================

DB_OPTIONS = list_databases()

def select_test_database(args_db: str | None = None) -> str:
    """
    Prompt the user to select a database for test execution.
    """
    if args_db in DB_OPTIONS:
        logger.info("Database '%s' selected via command line argument.", args_db)
        return args_db
    elif args_db is not None:
        print("Database provided not supported for the tests.")
        print(f"Supported databases: ")
        logger.warning("Unsupported database '%s' provided via command line argument.", args_db)
    else: 
        print("🔍 Select a database to use for the test:")
        logger.info("Starting interactive database selection.")

    for idx, name in enumerate(DB_OPTIONS, 1):
        print(f"  {idx}. {name}")

    while True:
        choice = input("Enter the database name or number: ").strip().lower()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(DB_OPTIONS):
                selected_db = DB_OPTIONS[idx]
                logger.info("Database '%s' selected via numeric input %s.", selected_db, choice)
                return selected_db
        elif choice in DB_OPTIONS:
            logger.info("Database '%s' selected via name input.", choice)
            return choice
        print("❌ Invalid selection. Please choose a valid database name or number.")
        logger.info("Invalid selection entered: '%s'", choice)

def configure_run_paths(db_name: str) -> Tuple[str, str]:
    """
    Configure input and output paths for the selected database.
    """
    logger.info("Configuring run paths for database '%s'.", db_name)
    base_dir = Path(__file__).resolve().parent
    requests_dir = base_dir / "input" / "requests"
    output_dir = base_dir / "output" / f"{db_name}_results" / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    logger.info("Creating output directory: %s", output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_file = requests_dir / f"{db_name}_requests.txt"
    output_file = output_dir / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    logger.info("Input file: %s", input_file)
    logger.info("Output file: %s", output_file)
    
    return str(input_file), str(output_file)

def clear_tmp_dir(tmp_dir: Path) -> None:
    """
    Remove and recreate the tmp directory for a clean run.
    """
    logger.info("Clearing temporary directory: %s", tmp_dir)
    if tmp_dir.exists():
        logger.info("Removing existing temporary directory.")
        shutil.rmtree(tmp_dir)
    logger.info("Creating new temporary directory.")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Temporary directory cleared and ready.")

def build_schema_retriever(db_name: str):
    # TODO: Build schema vector store from the live database and return schema data.
    pass

def load_test_requests(input_file: str) -> List[str]:
    """
    Load test requests from a text file.
    Each line is a separate request.
    """
    logger.info("Loading test requests from file: %s", input_file)
    requests = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    requests.append(line)
                    logger.debug("Loaded request %s: %s", idx, truncate_request(line))
        print(f"✅ Loaded {len(requests)} requests from {input_file}")
        logger.info("Loaded %s requests from %s.", len(requests), input_file)
    except FileNotFoundError:
        print(f"❌ Input file not found: {input_file}")
        logger.error("Input file not found: %s", input_file)
        requests = []
    return requests

def run_single_test():
    """
    Run a single test: generate SQL and validate it.
    
    """

def run_test_with_timeout():
    """
    Run test in a separate thread with timeout to prevent hanging.
    """

def format_result_line(
    model_name: str,
    sql_query: str,
    status: str,
    outcome: str,
    feedback_category: str,
    attempts: int,
    model_time: float,
) -> str:
    """
    Format a single result line according to the template.
    """
    # Clean up SQL query for output (preserve indentation, truncate if too long)
    clean_sql = sql_query.strip()
    if len(clean_sql) > MAX_OUTPUT_LENGTH:  # Truncate very long queries
        clean_sql = clean_sql[:MAX_OUTPUT_LENGTH].rstrip() + "..."
    
    if status != "OK":
        # For other errors, include the error message
        clean_error = outcome.replace('\n', ' ').strip()
        if len(clean_error) > MAX_OUTPUT_LENGTH / 4:  # Truncate long error messages
            clean_error = clean_error[:MAX_OUTPUT_LENGTH / 4] + "..."
        status_detail = f"{status}, {clean_error}"
    else:
        status_detail = f"{status}, {outcome} rows fetched"

    return (
        f"🤖 Model: {model_name}\n\n"
        "🧮 Query:\n\n\n"
        f"{clean_sql}\n\n\n"
        f"🏁 Status and outcome: {status_detail}\n\n"
        f"💡 LLM feedback: {feedback_category}\n\n"
        f"Attempts: {attempts}\n\n"
        f"⌚Request time: {model_time:.1f}s\n\n\n\n"
    )

def write_test_results(
    results: List[
        Tuple[str, Dict[str, Tuple[str, str, str, str, int, float]], float]
    ],
    output_file: str,
):
    """
    Write all test results grouped by request.
    """
    with open(output_file, "w", encoding="utf-8") as f:
        for req_index, (request, model_results, _) in enumerate(results, 1):
            # === Request header ===
            f.write(f"{req_index}. Request: {truncate_request(request)}\n\n")

            # === Models ===
            for model_name, (sql, status, outcome, feedback_category, attempts, model_time) in model_results.items():
                block = format_result_line(
                    model_name=model_name,
                    sql_query=sql,
                    status=status,
                    outcome=outcome,
                    feedback_category=feedback_category,
                    attempts=attempts,
                    model_time=model_time,
                )

                f.write(f"-" * 200 + "\n\n")
                f.write(block)

            f.write("\n" + "=" * 200 + "\n\n")

    print(f"✅ Results written to {output_file}")
    logger.info("Results written to %s.", output_file)


def sanitize_request_filename(request: str, max_length: int = 15) -> str:
    """
    Build a filesystem-friendly name from the request text.
    """
    clean = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in request.strip())
    clean = "_".join(filter(None, clean.split("_")))
    if not clean:
        clean = "request"
    return clean[:max_length]

def write_request_results(
    request: str,
    model_results: Dict[str, Tuple[str, str, str, str, int, float]],
    output_dir: Path,
    index: int,
) -> str:
    """
    Write a single request's results to its own file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    request_slug = sanitize_request_filename(request)
    output_file = output_dir / f"{index:03d}_{request_slug}.txt"
    write_test_results([(request, model_results, 0.0)], str(output_file))
    logger.info("Request results written to %s.", output_file)
    return str(output_file)

def print_table(title: str, headers: list[str], rows: list[list[str]]) -> list[str]:
    """
    Build an ASCII table and return it as a list of lines.
    """
    lines = []
    lines.append(f"\n{title}")
    lines.append("-" * 60)

    col_widths = [
        max(len(str(cell)) for cell in [header] + [row[i] for row in rows])
        for i, header in enumerate(headers)
    ]

    def format_row(row):
        return " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))

    lines.append(format_row(headers))
    lines.append("-+-".join("-" * w for w in col_widths))

    for row in rows:
        lines.append(format_row(row))

    return lines

def print_test_summary(
    results: List[
        Tuple[str, Dict[str, Tuple[str, str, str | None, str | None, int, float]], float]
    ],
    output_file: str,
):
    summary_lines = []
    summary_lines.append("/°" * 200 + "/\n\n")
    summary_lines.append("📊 TEST SUMMARY")
    summary_lines.append("\n\n" + "/°" * 200 + "/")
    
    total_tests = 0
    passed_tests = 0
    syntax_errors = 0
    runtime_errors = 0
    timeouts = 0
    other_errors = 0
    total_attempts = 0
    total_time = 0.0

    model_stats: Dict[str, Dict[str, float]] = {}

    for request, model_results, request_time in results:
        total_time += request_time
        for model_name, (_, status, _, _, attempts, model_time) in model_results.items():
            stats = model_stats.setdefault(
                model_name,
                dict(
                    ok=0,
                    runtime=0,
                    syntax=0,
                    attempts_total=0,
                    attempts_count=0,
                    time_total=0,
                    time_count=0,
                ),
            )

            total_tests += 1
            total_attempts += attempts
            stats["attempts_total"] += attempts
            stats["attempts_count"] += 1
            stats["time_total"] += model_time
            stats["time_count"] += 1

            if status == "OK":
                passed_tests += 1
                stats["ok"] += 1
            elif status == "SYNTAX_ERROR":
                syntax_errors += 1
                stats["syntax"] += 1
            elif status == "RUNTIME_ERROR":
                runtime_errors += 1
                stats["runtime"] += 1
            elif status == "TIMEOUT":
                timeouts += 1
            else:
                other_errors += 1

    # === GLOBAL STATS ===
    summary_lines.extend([
        "",
        f"Total requests tested : {len(results)}",
        f"Total model executions: {total_tests}",
        f"✅ Successful queries : {passed_tests}",
        f"⚠️  Syntax errors     : {syntax_errors}",
        f"❌ Runtime errors    : {runtime_errors}",
        f"⏰ Timeouts          : {timeouts}",
        f"🔧 Other errors      : {other_errors}",
        f"🔁 Total attempts    : {total_attempts}",
        f"⏱️  Total time        : {total_time:.1f}s",
        "",
    ])

    # === BUILD RANKINGS ===
    attempts_avg = sorted(
        model_stats.items(),
        key=lambda x: x[1]["attempts_total"] / x[1]["attempts_count"],
    )

    time_avg = sorted(
        model_stats.items(),
        key=lambda x: x[1]["time_total"] / x[1]["time_count"],
    )

    status_rank = sorted(
        model_stats.items(),
        key=lambda x: (-x[1]["ok"], x[1]["runtime"], x[1]["syntax"]),
    )

    # === TABLES ===
    summary_lines.extend(
        print_table(
            "🏁 Attempts ranking (avg)",
            ["Rank", "Model", "Avg Attempts", "Total Attempts"],
            [
                [
                    str(i + 1),
                    model,
                    f"{stats['attempts_total'] / stats['attempts_count']:.2f}",
                    f"{stats['attempts_total']:.0f}",
                ]
                for i, (model, stats) in enumerate(attempts_avg)
            ],
        )
    )

    summary_lines.extend(
        print_table(
            "🏁 Time ranking (avg)",
            ["Rank", "Model", "Avg Time (s)", "Total Time (s)"],
            [
                [
                    str(i + 1),
                    model,
                    f"{stats['time_total'] / stats['time_count']:.2f}",
                    f"{stats['time_total']:.1f}",
                ]
                for i, (model, stats) in enumerate(time_avg)
            ],
        )
    )

    summary_lines.extend(
        print_table(
            "🏁 Status ranking",
            ["Rank", "Model", "OK", "RUNTIME", "SYNTAX"],
            [
                [
                    str(i + 1),
                    model,
                    str(int(stats["ok"])),
                    str(int(stats["runtime"])),
                    str(int(stats["syntax"])),
                ]
                for i, (model, stats) in enumerate(status_rank)
            ],
        )
    )

    # === BEST MODEL ===
    best_model = status_rank[0][0] if status_rank else "N/A"
    summary_lines.append(f"\n🏆 Best overall model: {best_model}")
    summary_lines.append("=" * 60)

    # === OUTPUT ===
    with open(output_file, "a", encoding="utf-8") as f:
        for line in summary_lines:
            print(line)
            f.write(line + "\n")

# ==================== MAIN TEST FUNCTION ====================

def run_stress_tests(mode: str, db_name: str, output_dir: Path):
    """
    Main function to run comprehensive tests.
    """
    print("🤖 Starting comprehensive SQL generation tests")
    print("="*60)
    logger.info("Starting comprehensive SQL generation tests (mode=%s, db=%s).", mode, db_name)
    
    # 1. Load test requests
    test_requests = load_test_requests(INPUT_FILE)
    if not test_requests:
        print("❌ No test requests found. Exiting.")
        return
    
    # 2. Load schema (from DB when available)
    full_schema, schema_vs = build_schema_retriever(db_name)
    print(f"✅ Retrieved schema from database '{db_name}'")
    logger.info("Retrieved schema from database '%s'.", db_name)

    embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    schema_vs = Chroma(
        collection_name=SCHEMA_COLLECTION_NAME,
        persist_directory=SVS_DIR,
        embedding_function=embeddings,
    )

    # Load query vector store
    embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    query_vs = Chroma(
        collection_name=QUERY_COLLECTION_NAME,
        persist_directory=QVS_DIR,
        embedding_function=embeddings,
    )
    print(f"✅ Loaded vector stores from {QVS_DIR} and {SVS_DIR}")
    logger.info("Loaded vector stores from %s and %s.", QVS_DIR, SVS_DIR)
    
    # 4. Select all SQL-capable models and initialize them outside worker threads
    testable_models = [
        (idx, model_name)
        for idx, model_name in AZURE_MODELS.items()
        if idx != 0 and "embed" not in model_name.lower()
    ]
    if not testable_models:
        raise RuntimeError("❌ No testable model found in AVAILABLE_MODELS")

    selected_model_names = ", ".join(model_name for _, model_name in testable_models)
    print(f"✅ Models selected for this run: {selected_model_names}")
    logger.info("Models selected for this run: %s", selected_model_names)

    # 5. Run tests model-first: for each model, execute all requests
    all_results_map = {
        i: {
            "request": request,
            "model_results": {},
            "request_time": 0.0,
        }
        for i, request in enumerate(test_requests, 1)
    }
    request_output_dir = output_dir / "intermediate"

    for model_idx, model_name in testable_models:
        print(f"\n{'#' * 60}")
        print(f"🤖 Running all requests with model: {model_name}")
        print(f"{'#' * 60}")
        logger.info("Running all requests for model: %s (index=%s)", model_name, model_idx)
        llm_model = get_llm_model(model_idx)

        for i, request in enumerate(test_requests, 1):
            request_slug = sanitize_request_filename(request)
            request_log_file = request_output_dir / "logs" / f"{i:03d}_{request_slug}.log"
            request_log_handler = add_request_log_handler(request_log_file)
            try:
                print(f"\n{'='*60}")
                print(f"📝 Request {i}/{len(test_requests)}: {truncate_request(request)}")
                print(f"{'='*60}")
                logger.info("/°" * 100)
                logger.info("/°" * 100 + "\n\n\n\n")
                logger.info(
                    "Starting request %s/%s for model %s: %s",
                    i,
                    len(test_requests),
                    model_name,
                    truncate_request(request),
                )
                logger.info("Request log file: %s\n\n\n\n", request_log_file)
                logger.info("/°" * 100)
                logger.info("/°" * 100)

                print(f"\nTesting with model: {model_name}\n")
                logger.info("!#" * 100)
                logger.info("!#" * 100 + "\n\n\n")
                logger.info("Starting Testing with model: %s\n\n\n", model_name)
                logger.info("!#" * 100)
                logger.info("!#" * 100)
                model_start_time = time.time()

                _ = run_test_with_timeout()

                model_time = time.time() - model_start_time
                print(f"   Status: {status} ({model_time:.1f}s)\n")
                logger.info("Model %s status: %s (%.1fs)", model_name, status, model_time)

                if sql_query:
                    print(f"   Generated SQL:\n\n {sql_query}")
                    logger.info("Generated SQL: %s\n", sql_query)
                if outcome and status not in ["OK", "SYNTAX"]:
                    print(f"   Error: {outcome[:200]}...")
                    logger.warning("Error output: %s", outcome[:200])

                req_entry = all_results_map[i]
                req_entry["model_results"][model_name] = ( _
                    model_time,
                )
                req_entry["request_time"] += model_time

                print(f"\n⏱️  Aggregated time for this request: {req_entry['request_time']:.1f}s")
                logger.info(
                    "Aggregated request time for request %s after model %s: %.1fs",
                    i,
                    model_name,
                    req_entry["request_time"],
                )

                request_output_file = write_request_results(
                    request,
                    req_entry["model_results"],
                    request_output_dir,
                    i,
                )
                print(f"📄 Request log saved to: {request_output_file}")
            finally:
                remove_request_log_handler(request_log_handler)

    all_results = [
        (
            data["request"],
            data["model_results"],
            data["request_time"],
        )
        for _, data in sorted(all_results_map.items())
    ]

    # 6. Write final aggregated results
    write_test_results(all_results, OUTPUT_FILE)
    
    # 7. Print summary
    print_test_summary(all_results, OUTPUT_FILE)
    
    print(f"\n🎉 Testing completed!")
    print(f"📄 Full results saved to: {OUTPUT_FILE}")
    print(f"📄 Per-request logs saved under: {request_output_dir}")
    logger.info("Testing completed. Full results saved to %s.", OUTPUT_FILE)
    logger.info("Per-request logs saved under %s.", request_output_dir)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test SQL generation with multiple models")
    parser.add_argument("--test", choices=["run", "execute"], default="run",
                       help="Test type: 'run' to execute tests, 'execute' to execute a bunch of SQL queries from a file")
    parser.add_argument("--mode", choices=["mysql", "text"], default="text",
                       help="Mode: 'mysql' for MySQL mode, 'base' for base mode")
    parser.add_argument("--db", default=False, help="Database name")
    parser.add_argument("--input", default=False, help="Input file with test requests")
    parser.add_argument("--output", default=False, help="Output file for results")
    parser.add_argument("--timeout", type=int, default=TIMEOUT_PER_MODEL,
                       help="Timeout per model per request (seconds)")
    
    args = parser.parse_args()
    
    if args.test == "run":        
        clear_tmp_dir(TMP_DIR)
        selected_db = select_test_database(args.db)

        input_file, output_file = configure_run_paths(selected_db)
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"❌ Input file not found: {input_file}")

        # Update global variables based on args
        INPUT_FILE = args.input if args.input else input_file
        OUTPUT_FILE = args.output if args.output else output_file
        output_dir = Path(OUTPUT_DIR) / f"{selected_db}_results" / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        TIMEOUT_PER_MODEL = args.timeout
        
        # Run the comprehensive tests
        run_stress_tests(args.mode, db_name=selected_db, output_dir=output_dir)
    else:
        raise ValueError(f"❌ Invalid test type: {args.test}")
