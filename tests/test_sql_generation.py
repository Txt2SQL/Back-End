import sys, os, pytest, json, time
# Add parent directory to Python path for development
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime
from langchain_chroma import Chroma
from typing import Dict, List, Tuple
from langchain_ollama import OllamaEmbeddings
from logging_utils import (
    setup_single_project_logger, 
    setup_logger
)
from query_generator import (
    generate_sql_query,
    validate_sql_syntax,
    execute_sql_query,
    store_query_feedback,
    compute_schema_id,
    create_metadata,
    AVAILABLE_MODELS,
    SCHEMA_COLLECTION_NAME,
    QUERY_COLLECTION_NAME,
    VSS_DIR,
    VSQ_DIR
)

# ==================== CONFIGURATION ====================
SCHEMA_FILE = "./input/schema_canonical.json"   # Adjust path to schema file
VSS_DIR = "." + VSS_DIR      # Adjust path to schema vector store
VSQ_DIR = "." + VSQ_DIR      # Adjust path to query vector store
INPUT_FILE = "test_requests.txt"
OUTPUT_FILE = f"./output/test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
MAX_OUTPUT_LENGTH = 1000  # Truncate long requests in output
TIMEOUT_PER_MODEL = 600   # 10 minutes timeout per model per request

# === LOGGING SETUP ===
setup_single_project_logger()
logger = setup_logger(__name__)

# ==================== TEST FUNCTIONS ====================

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
    model_name: str, 
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
        # Generate SQL query
        sql = generate_sql_query(request, mode, full_schema, model_name, query_vs, schema_vs)

        execution_status = None
        execution_output = None
        
        syntax_status = validate_sql_syntax(sql)

        execution_status, execution_output = execute_sql_query(sql)

        metadata = create_metadata(
            sql_query=sql,
            syntax_status=syntax_status,
            schema_id=compute_schema_id(full_schema),
            user_request=request,
            model_name=model_name,
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
    model_name: str, 
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
            result = run_single_test(request, model_name, full_schema, mode, query_vs, schema_vs)
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
            for model_name in AVAILABLE_MODELS.values():
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

def run_comprehensive_tests(mode: str):
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
    
    # 2. Load schema
    try:
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            full_schema = json.load(f)
        print(f"✅ Loaded schema from {SCHEMA_FILE}")
    except Exception as e:
        print(f"❌ Failed to load schema: {e}")
        return
    
    # Load vector stores
    embeddings = OllamaEmbeddings(model="mxbai-embed-large")

    query_vs = Chroma(
        collection_name=QUERY_COLLECTION_NAME,
        persist_directory=VSQ_DIR,
        embedding_function=embeddings,
    )

    schema_vs = Chroma(
        collection_name=SCHEMA_COLLECTION_NAME,
        persist_directory=VSS_DIR,
        embedding_function=embeddings,
    ) 
    print(f"✅ Loaded vector stores from {VSQ_DIR} and {VSS_DIR}")
    
    # 4. Run tests for each request
    all_results = []
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n{'='*60}")
        print(f"📝 Request {i}/{len(test_requests)}: {truncate_request(request)}")
        print(f"{'='*60}")
        
        model_results = {}
        request_start_time = time.time()
        
        # Test each available model
        for model_name in AVAILABLE_MODELS.values():
            print(f"\n🔄 Testing with model: {model_name}")
            model_start_time = time.time()
            
            sql_query, status, outcome = run_test_with_timeout(
                request, model_name, full_schema, mode, query_vs, schema_vs, TIMEOUT_PER_MODEL
            )
            
            model_time = time.time() - model_start_time
            print(f"   Status: {status} ({model_time:.1f}s)")
            
            if sql_query:
                print(f"   Generated SQL: {sql_query[:100]}...")
            if outcome and status not in ["OK", "SYNTAX"]:
                print(f"   Error: {outcome[:100]}...")
            
            model_results[model_name] = (sql_query, status, outcome)
        
        request_time = time.time() - request_start_time
        print(f"\n⏱️  Total time for this request: {request_time:.1f}s")
        
        all_results.append((request, model_results))
        
        # Save intermediate results after each request (optional)
        intermediate_file = f"./output/intermidiate/intermediate_results_{datetime.now().strftime('%H%M%S')}.txt"
        write_test_results([(request, model_results)], intermediate_file)
    
    # 5. Write final results
    write_test_results(all_results, OUTPUT_FILE)
    
    # 6. Print summary
    print_test_summary(all_results, OUTPUT_FILE)
    
    print(f"\n🎉 Testing completed!")
    print(f"📄 Full results saved to: {OUTPUT_FILE}")

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
        model_name="none",
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
        user_request=user_request,
        model_name="none",
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

from pathlib import Path

@pytest.fixture
def schema():
    project_root = Path(__file__).resolve().parents[1]
    schema_path = project_root / "schema_canonical.json"

    if not schema_path.exists():
        pytest.skip(f"Schema file not found: {schema_path}")

    with schema_path.open(encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def vector_stores():
    embeddings = OllamaEmbeddings(model="mxbai-embed-large")

    query_vs = Chroma(
        collection_name=QUERY_COLLECTION_NAME,
        persist_directory=VSQ_DIR,
        embedding_function=embeddings,
    )

    schema_vs = Chroma(
        collection_name=SCHEMA_COLLECTION_NAME,
        persist_directory=VSS_DIR,
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
        user_request="test success",
        model_name="test",
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
        user_request="syntax error",
        model_name="test",
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
        user_request="runtime error",
        model_name="test",
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
        model_name="none",
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
        model_name="none",
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
    parser.add_argument("--input", default=INPUT_FILE,
                       help="Input file with test requests")
    parser.add_argument("--output", default=OUTPUT_FILE,
                       help="Output file for results")
    parser.add_argument("--timeout", type=int, default=TIMEOUT_PER_MODEL,
                       help="Timeout per model per request (seconds)")
    
    args = parser.parse_args()
    
    if args.test == "run":
        # Update global variables based on args
        INPUT_FILE = args.input
        OUTPUT_FILE = args.output
        TIMEOUT_PER_MODEL = args.timeout
        
        # Run the comprehensive tests
        run_comprehensive_tests(args.mode)
    elif args.test == "execute":
        if not args.input:
            raise ValueError("❌ --test execute requires --input <sql_file>")
        execute_sample_query(args.input)
    else:
        # Run pytest
        print("Running pytest tests...")
        pytest.main([__file__, "-v", "--tb=short"])