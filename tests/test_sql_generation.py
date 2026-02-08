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

def build_schema_retriever(db_name: str) -> Tuple[dict, Chroma]:
    """
    Build schema vector store from the live database and return schema data.
    """
    logger.info("Building schema retriever for database '%s'.", db_name)
    schema = extract_schema(db_name)
    schema["database"] = db_name
    logger.info("Schema extracted for database '%s'. Number of tables: %s", db_name, len(schema.get('tables', [])))
    
    logger.info("Building vector store for schema. Persist directory: %s", SVS_DIR)
    schema_vs = build_vector_store(
        schema,
        persist_directory=SVS_DIR,
        collection_name=SCHEMA_COLLECTION_NAME,
    )

    logger.info("Schema retriever built for database '%s'. Vector store created successfully.", db_name)
    return schema, schema_vs

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

def run_single_test(
    db_name: str,
    request: str, 
    model_index: int, 
    full_schema: dict, 
    mode: str,
    query_vs: Chroma,
    schema_vs: Chroma
) -> Tuple[str, str, str | None, str | None, int]:
    """
    Run a single test: generate SQL and validate it.
    
    Returns:
        (sql_query, status, error_message)
    """
    logger.info("Starting single test execution. Request: '%s', Model: %s, Mode: %s", 
                truncate_request(request), model_index, mode)
    try:
        llm_model = get_llm_model(model_index)
        logger.info("LLM model initialized for model index %s.", model_index)
        
        logger.info("Entering generation loop for request.")
        sql, syntax_status, execution_status, execution_output, LLM_feedback, attempt = generation_loop(
            user_request=request,
            source=mode,
            database_name=db_name,
            query_vs=query_vs,
            schema_vs=schema_vs,
            llm_model=llm_model
        )

        if mode != "mysql":
            syntax_status, execution_status, _, _, LLM_feedback= evaluate_feedback_error(
                request=request,
                sql=sql,
                source=mode,
                execution_status=execution_status,
                execution_output=execution_output
            )
        
        logger.info("Generation loop completed. SQL generated (truncated): %s", truncate_request(sql))
        logger.info("Syntax status: %s, Execution status: %s", syntax_status, execution_status)
                
        schema_id = compute_schema_id(full_schema)
        logger.info("Creating metadata for test results. Schema ID: %s", schema_id)
        
        metadata = create_metadata(
            sql_query=sql,
            syntax_status=syntax_status,
            schema_id=schema_id,
            schema_source=mode,
            user_request=request,
            model_index=model_index,
            execution_status=execution_status,
            execution_output=execution_output,
            LLM_feedback=LLM_feedback
        )

        logger.info("Storing query feedback in vector store.")
        store_query_feedback(
            store=query_vs,
            sql_query=sql,
            qm=metadata
        )
        logger.info("Query feedback stored successfully.")
        
        logger.info("Test completed with status: %s", metadata.status)
        return (
            sql,
            metadata.status,
            str(metadata.rows_fetched) if metadata.status == "OK" else metadata.error_message,
            LLM_feedback,
            attempt,
        )
            
    except Exception as e:
        # Catch any unexpected errors during generation
        error_msg = f"GENERATION_ERROR: {str(e)}"
        logger.exception("Unexpected error during generation. Request: '%s'", truncate_request(request))
        return "", "GENERATION_ERROR", error_msg, "GENERATION_ERROR", 0

def run_test_with_timeout(
    db_name: str,
    request: str, 
    model_index: int, 
    full_schema: dict,
    mode: str,
    query_vs: Chroma,
    schema_vs: Chroma,
    timeout: int = TIMEOUT_PER_MODEL
) -> Tuple[str, str, str, str | None, int]:
    """
    Run test with timeout to prevent hanging.
    """
    logger.info("Starting test with timeout. Timeout: %s seconds", timeout)
    import threading
    import queue
    
    result_queue = queue.Queue()
    
    def worker():
        try:
            logger.debug("Timeout worker thread started for request: '%s'", truncate_request(request))
            result = run_single_test(db_name, request, model_index, full_schema, mode, query_vs, schema_vs)
            result_queue.put(result)
            logger.debug("Worker thread completed successfully.")
        except Exception as e:
            logger.exception("Worker thread encountered exception.")
            result_queue.put(("", "TIMEOUT_OR_ERROR", str(e), "TIMEOUT_OR_ERROR", 0))
    
    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()
    logger.debug("Timeout thread started, waiting for completion...")
    thread.join(timeout)
    
    if thread.is_alive():
        # Thread is still running - timeout occurred
        logger.warning("Test exceeded timeout of %s seconds for request: '%s'", timeout, truncate_request(request))
        return "", "TIMEOUT", f"Test exceeded {timeout}s timeout", "TIMEOUT", 0
    else:
        try:
            result = result_queue.get_nowait()
            logger.info("Test completed within timeout. Status: %s", result[1])
            return result
        except queue.Empty:
            logger.error("No result returned from worker thread. Queue is empty.")
            return "", "UNKNOWN_ERROR", "No result returned", "UNKNOWN_ERROR", 0

def format_result_line(
    request: str,
    model_name: str,
    sql_query: str,
    status: str,
    outcome: str,
    llm_feedback: str | None,
    attempts: int,
    request_time: float,
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

    feedback_value = llm_feedback if llm_feedback else "N/A"
    return (
        f"🤖 Model: {model_name}\n\n"
        "🧮 Query:\n\n\n"
        f"{clean_sql}\n\n\n"
        f"🏁 Status and outcome: {status_detail}\n\n"
        f"💡 LLM feedback: {feedback_value}\n\n"
        f"Attempts: {attempts}\n\n"
        f"⌚Request time: {request_time:.1f}s\n\n\n\n"
    )

def write_test_results(
    results: List[
        Tuple[str, Dict[str, Tuple[str, str, str | None, str | None, int, float]], float]
    ],
    output_file: str,
):
    """
    Write all test results grouped by request, with all models under each request.
    """
    with open(output_file, "w", encoding="utf-8") as f:
        for req_index, (request, model_results, request_time) in enumerate(results, 1):
            # === Request header ===
            f.write(f"{req_index}. Request: {truncate_request(request)}\n\n")

            # === Models ===
            for index in range(5, len(AVAILABLE_MODELS) - 1):
                model_name = AVAILABLE_MODELS[index]

                if model_name not in model_results:
                    f.write(f"🤖 Model: {model_name}\n")
                    f.write("Status and outcome: MODEL_NOT_AVAILABLE\n\n")
                    continue

                sql, status, outcome, llm_feedback, attempts, model_time = model_results[model_name]

                block = format_result_line(
                    request=request,
                    model_name=model_name,
                    sql_query=sql,
                    status=status,
                    outcome=outcome or "",
                    llm_feedback=llm_feedback,
                    attempts=attempts,
                    request_time=request_time,
                )

                f.write(f"-"*200 + "\n\n")
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
    model_results: Dict[str, Tuple[str, str, str | None, str | None, int, float]],
    output_dir: Path,
    index: int,
    request_time: float,
) -> str:
    """
    Write a single request's results to its own file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    request_slug = sanitize_request_filename(request)
    output_file = output_dir / f"{index:03d}_{request_slug}.txt"
    write_test_results([(request, model_results, request_time)], str(output_file))
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

def run_comprehensive_tests(mode: str, db_name: str, output_dir: Path):
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
    
    # 4. Run tests for each request
    all_results = []
    request_output_dir = output_dir / "intermediate"
    
    for i, request in enumerate(test_requests, 1):
        request_slug = sanitize_request_filename(request)
        request_log_file = request_output_dir / "logs" / f"{i:03d}_{request_slug}.log"
        request_log_handler = add_request_log_handler(request_log_file)
        try:
            print(f"\n{'='*60}")
            print(f"📝 Request {i}/{len(test_requests)}: {truncate_request(request)}")
            print(f"{'='*60}")
            logger.info("Starting request %s/%s: %s", i, len(test_requests), truncate_request(request))
            logger.info("Request log file: %s", request_log_file)
            
            model_results = {}
            request_start_time = time.time()
            
            # Test each available model
            for index in range(5, len(AVAILABLE_MODELS) - 1):
                name = AVAILABLE_MODELS[index]
                print(f"\nTesting with model: {name}\n")
                logger.info("!#" * 100 + "\n\n")
                logger.info("Starting Testing with model: %s\n\n", name)
                logger.info("!#" * 100)
                model_start_time = time.time()
                
                sql_query, status, outcome, llm_feedback, attempts = run_test_with_timeout(
                    db_name, request, index, full_schema, mode, query_vs, schema_vs, TIMEOUT_PER_MODEL
                )
                
                model_time = time.time() - model_start_time
                print(f"   Status: {status} ({model_time:.1f}s)\n")
                logger.info("Model %s status: %s (%.1fs)", name, status, model_time)
                
                if sql_query:
                    print(f"   Generated SQL:\n\n {sql_query}")
                    logger.info("Generated SQL: %s\n", sql_query)
                if outcome and status not in ["OK", "SYNTAX"]:
                    print(f"   Error: {outcome[:200]}...")
                    logger.warning("Error output: %s", outcome[:200])
                
                model_results[name] = (
                    sql_query,
                    status,
                    outcome,
                    llm_feedback,
                    attempts,
                    model_time
                )
            
            request_time = time.time() - request_start_time
            print(f"\n⏱️  Total time for this request: {request_time:.1f}s")
            logger.info("Total time for request: %.1fs", request_time)
            
            all_results.append((request, model_results, request_time))
            request_output_file = write_request_results(
                request,
                model_results,
                request_output_dir,
                i,
                request_time,
            )
            print(f"📄 Request log saved to: {request_output_file}")
        finally:
            remove_request_log_handler(request_log_handler)
    
    # 5. Write final aggregated results
    write_test_results(all_results, OUTPUT_FILE)
    
    # 6. Print summary
    print_test_summary(all_results, OUTPUT_FILE)
    
    print(f"\n🎉 Testing completed!")
    print(f"📄 Full results saved to: {OUTPUT_FILE}")
    print(f"📄 Per-request logs saved under: {request_output_dir}")
    logger.info("Testing completed. Full results saved to %s.", OUTPUT_FILE)
    logger.info("Per-request logs saved under %s.", request_output_dir)

def run_full_cycle_without_llm(
    *,
    user_request: str,
    mode: str,
    schema: dict,
    query_vs: Chroma,
    schema_vs: Chroma,
    execute_sql: bool,
):
    """
    Runs the full SQL generation pipeline WITHOUT calling the LLM.
    """
    template = create_prompt(
        user_request=user_request,
        source=mode,
        database_name="none",
        query_vs=query_vs,
        schema_vs=schema_vs,
    )
    sql = generate_sql_query("none", template)

    syntax_status = validate_sql_syntax(sql)

    execution_status = None
    execution_output = None

    if execute_sql and syntax_status == "OK":
        execution_status, execution_output = execute_sql_query(sql)

    qm = create_metadata(
        sql_query=sql,
        syntax_status=syntax_status,
        schema_id=compute_schema_id(schema),
        schema_source=mode,
        user_request=user_request,
        model_index=0,
        execution_status=execution_status,
        execution_output=execution_output,
    )

    store_query_feedback(query_vs, sql, qm)

    return sql, qm

def execute_sample_query(input_path: str):
    """
    Execute SQL queries from a file and write results to outcomes.txt.

    File format:
    - One or more SQL queries
    - Each query MUST end with a semicolon (;)
    """

    if not input_path:
        raise ValueError("❌ --test execute requires an input file via --input")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"❌ Input file not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        raise ValueError("❌ Input file is empty")

    # Split queries by semicolon, keeping valid SQL only
    queries = [
        q.strip() + ";"
        for q in content.split(";")
        if q.strip()
    ]

    if not queries:
        raise ValueError("❌ No valid SQL queries found in input file")

    output_file = "outcomes.txt"

    with open(output_file, "w", encoding="utf-8") as out:
        for query in queries:
            out.write("query:\n\n")
            out.write(f"{query}\n\n")

            status, result = execute_sql_query(query)

            if status == "OK":
                rows_fetched = len(result) if isinstance(result, list) else 0
                out.write(f"rows fetched: {rows_fetched} rows\n\n")
            else:
                out.write(f"error: {result}\n\n")

            out.write("\n")

    print(f"✅ Query execution completed. Results written to {output_file}")

# ==================== PYTEST TEST CASES ====================

@pytest.fixture
def schema():
    project_root = Path(__file__).resolve().parents[1]
    schema_path = project_root / "schema_canonical.json"

    if not schema_path.exists():
        pytest.skip(f"Schema file not found: {schema_path}")

    with schema_path.open(encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def vector_stores(tmp_path):
    embeddings = OllamaEmbeddings(model="mxbai-embed-large")

    query_dir = tmp_path / "vector_store" / "queries"
    schema_dir = tmp_path / "vector_store" / "schema"
    query_dir.mkdir(parents=True, exist_ok=True)
    schema_dir.mkdir(parents=True, exist_ok=True)

    query_vs = Chroma(
        collection_name=QUERY_COLLECTION_NAME,
        persist_directory=str(query_dir),
        embedding_function=embeddings,
    )

    schema_vs = Chroma(
        collection_name=SCHEMA_COLLECTION_NAME,
        persist_directory=str(schema_dir),
        embedding_function=embeddings,
    )

    return query_vs, schema_vs

@pytest.fixture(scope="class")
def load_file():
    def _load(path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return _load


@pytest.mark.execution
def test_execute_sql_success_only(load_file):
    sql = load_file("test/inputs/sql_success.sql")

    status, result = execute_sql_query(sql)

    assert status == "OK"
    assert isinstance(result, list)

@pytest.mark.execution
def test_execute_sql_success_and_store(schema, vector_stores, load_file):
    query_vs, _ = vector_stores
    sql = load_file("test/inputs/sql_success.sql")

    if schema is None:
        pytest.skip("Schema not loaded")
    syntax = validate_sql_syntax(sql)
    status, output = execute_sql_query(sql)

    qm = create_metadata(
        sql_query=sql,
        syntax_status=syntax,
        schema_id=compute_schema_id(schema),
        schema_source="mysql",
        user_request="test success",
        model_index=0,
        execution_status=status,
        execution_output=output,
    )

    store_query_feedback(query_vs, sql, qm)

    assert qm.status == "OK"
    assert qm.rows_fetched >= 0

@pytest.mark.execution
def test_syntax_error_and_store(schema, vector_stores, load_file):
    query_vs, _ = vector_stores
    sql = load_file("test/inputs/sql_syntax_error.sql")

    syntax = validate_sql_syntax(sql)

    qm = create_metadata(
        sql_query=sql,
        syntax_status=syntax,
        schema_id=compute_schema_id(schema),
        schema_source="mysql",
        user_request="syntax error",
        model_index=0,
    )

    store_query_feedback(query_vs, sql, qm)

    assert qm.status == "SYNTAX_ERROR"
    assert qm.knowledge_scope == "SYNTAX"

@pytest.mark.execution    
@pytest.mark.parametrize("sql_file", [
    "test/inputs/sql_runtime_error_fk.sql",
    "test/inputs/sql_runtime_error_column.sql",
])
def test_runtime_error_and_store(schema, vector_stores, load_file, sql_file):
    query_vs, _ = vector_stores
    sql = load_file(sql_file)

    syntax = validate_sql_syntax(sql)
    status, error = execute_sql_query(sql)

    qm = create_metadata(
        sql_query=sql,
        syntax_status=syntax,
        schema_id=compute_schema_id(schema),
        schema_source="mysql",
        user_request="runtime error",
        model_index=0,
        execution_status=status,
        execution_output=error,
    )

    store_query_feedback(query_vs, sql, qm)

    assert qm.status == "RUNTIME_ERROR"
    assert qm.error_type is not None

@pytest.mark.prompt
def test_complex_prompt_creation_only(schema, vector_stores, capsys):
    query_vs, schema_vs = vector_stores

    create_prompt(
        user_request="Show total sales by customer",
        source="mysql",
        database_name="none",
        query_vs=query_vs,
        schema_vs=schema_vs,
    )

    captured = capsys.readouterr().out

    assert "=== SCHEMA ===" in captured
    assert "IMPORTANT CONSTRAINTS" in captured
    assert "PREVIOUS FAILURES" in captured or "SQL QUERY" in captured

@pytest.mark.prompt
def test_simple_prompt_creation_only(schema, vector_stores, capsys):
    query_vs, schema_vs = vector_stores

    create_prompt(
        user_request="Show total sales by customer",
        source="text",
        database_name="none",
        query_vs=query_vs,
        schema_vs=schema_vs,
    )

    captured = capsys.readouterr().out

    assert "=== SCHEMA ===" in captured
    assert "PREVIOUS FAILURES" not in captured
    assert "join" not in captured.lower()

@pytest.mark.fullcycle
def test_simple_prompt_full_cycle_no_execution(schema, vector_stores):
    query_vs, schema_vs = vector_stores

    sql, qm = run_full_cycle_without_llm(
        user_request="List all customers",
        mode="text",
        schema=schema,
        query_vs=query_vs,
        schema_vs=schema_vs,
        execute_sql=False,
    )

    assert sql
    assert qm.status in {"OK", "UNKNOWN_ERROR"}
    assert qm.knowledge_scope != "SYNTAX"

@pytest.mark.fullcycle
def test_complex_prompt_full_cycle_with_execution(schema, vector_stores):
    query_vs, schema_vs = vector_stores

    sql, qm = run_full_cycle_without_llm(
        user_request="Show total sales by customer",
        mode="mysql",
        schema=schema,
        query_vs=query_vs,
        schema_vs=schema_vs,
        execute_sql=True,
    )

    assert sql
    assert qm.status == "OK"
    assert qm.rows_fetched >= 0

@pytest.mark.fullcycle
def test_simple_prompt_execute_and_store(schema, vector_stores):
    query_vs, schema_vs = vector_stores

    sql, qm = run_full_cycle_without_llm(
        user_request="Show all customers",
        mode="text",
        schema=schema,
        query_vs=query_vs,
        schema_vs=schema_vs,
        execute_sql=True,
    )

    assert sql
    assert qm.status == "OK"
    assert qm.rows_fetched >= 0

import threading
import queue

# @pytest.mark.llm
# @pytest.mark.slow
# @pytest.mark.parametrize("model_name", AVAILABLE_MODELS.values())
# def test_real_llm_simple_prompt_generation(schema, vector_stores, model_name):
#     """
#     Real LLM integration test:
#     - simple prompt (text)
#     - no execution
#     - no storage
#     - no prompt inspection
#     """
#     query_vs, schema_vs = vector_stores
#     user_request = "List all customers"

#     result_queue: queue.Queue[str | Exception] = queue.Queue()

#     def worker():
#         try:
#             sql = generate_sql_query(
#                 user_request=user_request,
#                 source="text",
#                 full_schema=schema,
#                 model_name=model_name,
#                 query_vs=query_vs,
#                 schema_vs=schema_vs,
#             )
#             result_queue.put(sql)
#         except Exception as e:
#             result_queue.put(e)

#     thread = threading.Thread(target=worker, daemon=True)
#     thread.start()
#     thread.join(timeout=120)  # ⏱️ 2 minutes per model

#     if thread.is_alive():
#         pytest.fail(f"LLM model '{model_name}' timed out")

#     result = result_queue.get()

#     if isinstance(result, Exception):
#         pytest.fail(f"LLM model '{model_name}' failed: {result}")

#     sql = result

#     # --- minimal but meaningful assertions ---
#     assert isinstance(sql, str)
#     assert sql.strip()
#     assert "select" in sql.lower()


# ==================== COMMAND LINE INTERFACE ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test SQL generation with multiple models")
    parser.add_argument("--test", choices=["run", "pytest, execute"], default="run",
                       help="Test type: 'run' to execute tests, 'pytest' to run the pytest suite, 'execute' ")
    parser.add_argument("--mode", choices=["mysql", "base"], default="base",
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
        run_comprehensive_tests(args.mode, db_name=selected_db, output_dir=output_dir)
    elif args.test == "execute":
        if not args.input:
            raise ValueError("❌ --test execute requires --input <sql_file>")
        execute_sample_query(args.input)
    else:
        # Run pytest
        print("Running pytest tests...")
        pytest.main([__file__, "-v", "--tb=short"])
