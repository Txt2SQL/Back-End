import sys, os, pytest, json, time, shutil
# Add parent directory to Python path for development
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime
from langchain_chroma import Chroma
from typing import Dict, List, Tuple
from langchain_ollama import OllamaEmbeddings
from src.config.settings import AVAILABLE_MODELS
from src.mysql_linker import extract_schema, get_db_connection, list_databases
from src.logging_utils import (
    setup_single_project_logger, 
    setup_logger
)
from src.query_generator import (
    generate_sql_query,
    validate_sql_syntax,
    execute_sql_query,
    store_query_feedback,
    compute_schema_id,
    create_metadata,
    get_llm_model,
    SCHEMA_COLLECTION_NAME,
    QUERY_COLLECTION_NAME,
)
from src.retriver_utils import build_vector_store
from tests import generate_realistic_mysql_db as db_generator
from pathlib import Path

# ==================== CONFIGURATION ====================
BASE_DIR = Path(__file__).resolve().parent
TMP_DIR = BASE_DIR / "tmp"
INPUT_FILE = "./input/requests/test_requests.txt"
OUTPUT_FILE = f"./output/test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
MAX_OUTPUT_LENGTH = 1000  # Truncate long requests in output
TIMEOUT_PER_MODEL = 600   # 10 minutes timeout per model per request
QVS_DIR = str(TMP_DIR / "query_vector_store")
SVS_DIR = str(TMP_DIR / "schema_vector_store")

# === LOGGING SETUP ===
setup_single_project_logger()
logger = setup_logger(__name__)

# ==================== TEST FUNCTIONS ====================

DB_OPTIONS = ["supermarket", "monica", "hacker_news", "akaunting"]

def select_test_database() -> str:
    """
    Prompt the user to select a database for test execution.
    """
    print("🔍 Select a database to use for the test:")
    for idx, name in enumerate(DB_OPTIONS, 1):
        print(f"  {idx}. {name}")

    while True:
        choice = input("Enter the database name or number: ").strip().lower()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(DB_OPTIONS):
                return DB_OPTIONS[idx]
        elif choice in DB_OPTIONS:
            return choice
        print("❌ Invalid selection. Please choose a valid database name or number.")


def ensure_database_ready(db_name: str, ddl_dir: Path) -> None:
    """
    Ensure the selected database exists and is populated.
    """
    existing_dbs = list_databases()
    if db_name in existing_dbs:
        print(f"✅ Database '{db_name}' already exists. Connecting to it...")
        conn = get_db_connection(database_name=db_name)
        if conn.is_connected():
            print(f"✅ Connection to '{db_name}' established.")
        conn.close()
        return

    print(f"🛠️  Database '{db_name}' not found. Creating and populating it...")
    ddl_path = ddl_dir / f"{db_name}.sql"
    if not ddl_path.exists():
        raise FileNotFoundError(f"❌ DDL file not found for '{db_name}': {ddl_path}")

    conn = get_db_connection(database_name=None)
    cursor = conn.cursor()

    db_generator.create_database(cursor, db_name)
    cursor.execute(f"USE {db_generator.quote_identifier(db_name)}")
    db_generator.execute_sql_file(cursor, str(ddl_path))
    conn.commit()

    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()] # pyright: ignore[reportArgumentType]
    for table in tables:
        db_generator.populate_table(cursor, table)
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()

    cursor.close()
    conn.close()
    print(f"✅ Database '{db_name}' created and populated.")


def configure_run_paths(db_name: str) -> Tuple[str, str]:
    """
    Configure input and output paths for the selected database.
    """
    base_dir = Path(__file__).resolve().parent
    requests_dir = base_dir / "input" / "requests"
    output_dir = base_dir / "output" / f"{db_name}_results"
    output_dir.mkdir(parents=True, exist_ok=True)

    input_file = requests_dir / f"{db_name}_requests.txt"
    output_file = output_dir / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    return str(input_file), str(output_file)

def clear_tmp_dir(tmp_dir: Path) -> None:
    """
    Remove and recreate the tmp directory for a clean run.
    """
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

def build_schema_retriever(db_name: str) -> Tuple[dict, Chroma]:
    """
    Build schema vector store from the live database and return schema data.
    """
    schema = extract_schema(db_name)
    schema["database"] = db_name
    schema_vs = build_vector_store(
        schema,
        persist_directory=SVS_DIR,
        collection_name=SCHEMA_COLLECTION_NAME,
    )

    return schema, schema_vs

def load_test_requests(input_file: str) -> List[str]:
    """
    Load test requests from a text file.
    Each line is a separate request.
    """
    requests = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    requests.append(line)
        print(f"✅ Loaded {len(requests)} requests from {input_file}")
    except FileNotFoundError:
        print(f"❌ Input file not found: {input_file}")
        requests = []
    return requests


def truncate_request(request: str, max_length: int = MAX_OUTPUT_LENGTH) -> str:
    """Truncate long requests for cleaner output."""
    if len(request) <= max_length:
        return request
    return request[:max_length] + "..."


def run_single_test(
    request: str, 
    model_index: int, 
    full_schema: dict, 
    mode: str,
    query_vs: Chroma,
    schema_vs: Chroma
) -> Tuple[str, str, str | None]:
    """
    Run a single test: generate SQL and validate it.
    
    Returns:
        (sql_query, status, error_message)
    """
    try:
        llm_model = get_llm_model(model_index)
        # Generate SQL query
        sql = generate_sql_query(request, mode, full_schema, llm_model, query_vs, schema_vs)

        execution_status = None
        execution_output = None
        
        syntax_status = validate_sql_syntax(sql)

        database_name = full_schema["database"]
        error_feedback = None
        if syntax_status != "OK":
            print("♻️ Syntax non valida: rigenero la query con feedback sull'errore...")
            error_feedback=(
                "The previous SQL query failed syntax validation "
                f"(status={syntax_status})."
            )

        if syntax_status == "OK" and mode == "mysql":
            execution_status, execution_output = execute_sql_query(sql, database_name=full_schema["database"])

            if execution_status != "OK":
                error_feedback=(
                    "The previous SQL query failed at runtime with this error: "
                    f"{execution_output}."
                )

        if syntax_status != "OK" or execution_status != "OK":
            sql = generate_sql_query(
                request,
                mode,
                full_schema,
                llm_model,
                query_vs,
                schema_vs,
                error_feedback=error_feedback
            )

            syntax_status = validate_sql_syntax(sql)

            if syntax_status == "OK" and mode != "mysql":
                execution_status, execution_output = execute_sql_query(sql, database_name=database_name)

        metadata = create_metadata(
            sql_query=sql,
            syntax_status=syntax_status,
            schema_id=compute_schema_id(full_schema),
            schema_source=mode,
            user_request=request,
            model_index=model_index,
            execution_status=execution_status,
            execution_output=execution_output
        )

        store_query_feedback(
            store=query_vs,
            sql_query=sql,
            qm=metadata
        )
        
        return sql, metadata.status, str(metadata.rows_fetched) if metadata.status == "OK" else metadata.error_message
            
    except Exception as e:
        # Catch any unexpected errors during generation
        error_msg = f"GENERATION_ERROR: {str(e)}"
        return "", "GENERATION_ERROR", error_msg


def run_test_with_timeout(
    request: str, 
    model_index: int, 
    full_schema: dict,
    mode: str,
    query_vs: Chroma,
    schema_vs: Chroma,
    timeout: int = TIMEOUT_PER_MODEL
) -> Tuple[str, str, str]:
    """
    Run test with timeout to prevent hanging.
    """
    import threading
    import queue
    
    result_queue = queue.Queue()
    
    def worker():
        try:
            result = run_single_test(request, model_index, full_schema, mode, query_vs, schema_vs)
            result_queue.put(result)
        except Exception as e:
            result_queue.put(("", "TIMEOUT_OR_ERROR", str(e)))
    
    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()
    thread.join(timeout)
    
    if thread.is_alive():
        # Thread is still running - timeout occurred
        return "", "TIMEOUT", f"Test exceeded {timeout}s timeout"
    else:
        try:
            return result_queue.get_nowait()
        except queue.Empty:
            return "", "UNKNOWN_ERROR", "No result returned"


def format_result_line(model_name: str, sql_query: str, status: str, 
                       outcome: str) -> str:
    """
    Format a single result line according to the template.
    """
    # Clean up SQL query for output (remove newlines, truncate if too long)
    clean_sql = sql_query.replace('\n', ' ').strip()
    if len(clean_sql) > MAX_OUTPUT_LENGTH:  # Truncate very long queries
        clean_sql = clean_sql[:MAX_OUTPUT_LENGTH] + "..."
    
    if status != "OK":
        # For other errors, include the error message
        clean_error = outcome.replace('\n', ' ').strip()
        if len(clean_error) > MAX_OUTPUT_LENGTH/4:  # Truncate long error messages
            clean_error = clean_error[:MAX_OUTPUT_LENGTH/4] + "..."
        return f"🤖{model_name}\n\n🧮Query: {clean_sql}\n\n⚠️Error: {clean_error}\n\n"
    else:
        return f"🤖{model_name}\n\n🧮Query: \n{clean_sql}\n\n💥Rows fetched: {outcome}\n\n"


def write_test_results(results: List[Tuple[str, Dict]], output_file: str):
    """
    Write all test results to output file following the template.
    """
    n = 1
    with open(output_file, 'w', encoding='utf-8') as f:
        for request, model_results in results:
            # Write request
            truncated_request = truncate_request(request)
            f.write(f"{n}. {truncated_request}\n\n")
            
            # Write results for each model
            for index in range(1, len(AVAILABLE_MODELS) + 1):
                model_name = AVAILABLE_MODELS[index]
                if model_name in model_results:
                    sql, status, outcome = model_results[model_name]
                    line = format_result_line(model_name, sql, status, outcome)
                    f.write(f"{line}\n")
                else:
                    f.write(f"{model_name} [TEST NOT RUN] MODEL_NOT_AVAILABLE\n")
            
            # Add blank line between requests for readability
            f.write("\n\n\n\n")
            n += 1
    
    print(f"✅ Results written to {output_file}")


def sanitize_request_filename(request: str, max_length: int = 60) -> str:
    """
    Build a filesystem-friendly name from the request text.
    """
    clean = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in request.strip())
    clean = "_".join(filter(None, clean.split("_")))
    if not clean:
        clean = "request"
    return clean[:max_length]


def write_request_results(request: str, model_results: Dict, output_dir: Path, index: int) -> str:
    """
    Write a single request's results to its own file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    request_slug = sanitize_request_filename(request)
    output_file = output_dir / f"{index:03d}_{request_slug}.txt"
    write_test_results([(request, model_results)], str(output_file))
    return str(output_file)


def print_test_summary(results: List[Tuple[str, Dict]], output_file: str):
    """Print a summary of test results."""
    summary_lines = []
    summary_lines.append("\n" + "="*60)
    summary_lines.append("📊 TEST SUMMARY")
    summary_lines.append("="*60)
    
    total_tests = 0
    passed_tests = 0
    syntax_errors = 0
    runtime_errors = 0
    timeouts = 0
    other_errors = 0
    
    for request, model_results in results:
        for model_name, (sql, status, error) in model_results.items():
            total_tests += 1
            if status == "OK":
                passed_tests += 1
            elif status == "SYNTAX_ERROR":
                syntax_errors += 1
            elif status == "RUNTIME_ERROR":
                runtime_errors += 1
            elif status == "TIMEOUT":
                timeouts += 1
            else:
                other_errors += 1
    
    summary_lines.append(f"Total requests tested: {len(results)}")
    summary_lines.append(f"Total model executions: {total_tests}")
    summary_lines.append(f"✅ Successful queries: {passed_tests}")
    summary_lines.append(f"⚠️  Syntax errors: {syntax_errors}")
    summary_lines.append(f"❌ Runtime errors: {runtime_errors}")
    summary_lines.append(f"⏰ Timeouts: {timeouts}")
    summary_lines.append(f"🔧 Other errors: {other_errors}")
    
    if total_tests > 0:
        success_rate = (passed_tests / total_tests) * 100
        summary_lines.append(f"\n📈 Success rate: {success_rate:.1f}%")
    
    summary_lines.append("="*60)

    with open(output_file, 'a', encoding='utf-8') as f:
        for line in summary_lines:
            print(line)
            f.write(line + "\n")

# ==================== MAIN TEST FUNCTION ====================

def run_comprehensive_tests(mode: str, db_name: str):
    """
    Main function to run comprehensive tests.
    """
    print("🤖 Starting comprehensive SQL generation tests")
    print("="*60)
    
    # 1. Load test requests
    test_requests = load_test_requests(INPUT_FILE)
    if not test_requests:
        print("❌ No test requests found. Exiting.")
        return
    
    # 2. Load schema (from DB when available)
    full_schema, schema_vs = build_schema_retriever(db_name)
    print(f"✅ Retrieved schema from database '{db_name}'")

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
    
    # 4. Run tests for each request
    all_results = []
    per_request_output_dir = Path(OUTPUT_FILE).with_suffix("")
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n{'='*60}")
        print(f"📝 Request {i}/{len(test_requests)}: {truncate_request(request)}")
        print(f"{'='*60}")
        
        model_results = {}
        request_start_time = time.time()
        
        # Test each available model
        for index in range(1, len(AVAILABLE_MODELS) + 1):
            name = AVAILABLE_MODELS[index]
            print(f"\nTesting with model: {name}")
            model_start_time = time.time()
            
            sql_query, status, outcome = run_test_with_timeout(
                request, index, full_schema, mode, query_vs, schema_vs, TIMEOUT_PER_MODEL
            )
            
            model_time = time.time() - model_start_time
            print(f"   Status: {status} ({model_time:.1f}s)")
            
            if sql_query:
                print(f"   Generated SQL: {sql_query}")
            if outcome and status not in ["OK", "SYNTAX"]:
                print(f"   Error: {outcome[:200]}...")
            
            model_results[name] = (sql_query, status, outcome)
        
        request_time = time.time() - request_start_time
        print(f"\n⏱️  Total time for this request: {request_time:.1f}s")
        
        all_results.append((request, model_results))
        request_output_file = write_request_results(request, model_results, per_request_output_dir, i)
        print(f"📄 Request log saved to: {request_output_file}")
    
    # 5. Write final aggregated results
    write_test_results(all_results, OUTPUT_FILE)
    
    # 6. Print summary
    print_test_summary(all_results, OUTPUT_FILE)
    
    print(f"\n🎉 Testing completed!")
    print(f"📄 Full results saved to: {OUTPUT_FILE}")
    print(f"📄 Per-request logs saved under: {per_request_output_dir}")

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
    sql = generate_sql_query(
        user_request=user_request,
        source=mode,
        full_schema=schema,
        model="none",
        query_vs=query_vs,
        schema_vs=schema_vs,
    )

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

    generate_sql_query(
        user_request="Show total sales by customer",
        source="mysql",
        full_schema=schema,
        model="none",
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

    generate_sql_query(
        user_request="List all customers",
        source="text",
        full_schema=schema,
        model="none",
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
    parser.add_argument("--input", default=False,
                       help="Input file with test requests")
    parser.add_argument("--output", default=False,
                       help="Output file for results")
    parser.add_argument("--timeout", type=int, default=TIMEOUT_PER_MODEL,
                       help="Timeout per model per request (seconds)")
    
    args = parser.parse_args()
    
    if args.test == "run":        
        clear_tmp_dir(TMP_DIR)
        selected_db = select_test_database()
        ddl_dir = Path(__file__).resolve().parent / "input" / "existing_ddl"
        ensure_database_ready(selected_db, ddl_dir)

        input_file, output_file = configure_run_paths(selected_db)
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"❌ Input file not found: {input_file}")

        # Update global variables based on args
        INPUT_FILE = args.input if args.input else input_file
        OUTPUT_FILE = args.output if args.output else output_file
        TIMEOUT_PER_MODEL = args.timeout
        
        # Run the comprehensive tests
        run_comprehensive_tests(args.mode, db_name=selected_db)
    elif args.test == "execute":
        if not args.input:
            raise ValueError("❌ --test execute requires --input <sql_file>")
        execute_sample_query(args.input)
    else:
        # Run pytest
        print("Running pytest tests...")
        pytest.main([__file__, "-v", "--tb=short"])
