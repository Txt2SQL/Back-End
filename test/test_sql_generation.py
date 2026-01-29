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
    SCHEMA_FILE,
    SCHEMA_COLLECTION_NAME,
    QUERY_COLLECTION_NAME,
    VSS_DIR,
    VSQ_DIR
)

# ==================== CONFIGURATION ====================
SCHEMA_FILE = "../" + SCHEMA_FILE  # Adjust path to schema file
VSS_DIR = "." + VSS_DIR      # Adjust path to schema vector store
VSQ_DIR = "." + VSQ_DIR      # Adjust path to query vector store
INPUT_FILE = "test_requests.txt"
OUTPUT_FILE = f"./test_result/test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
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
    source: str,
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
        sql = generate_sql_query(request, source, full_schema, model_name, query_vs, schema_vs)

        execution_status = None
        execution_output = None
        
        syntax_status = validate_sql_syntax(sql)

        if syntax_status == "OK" and source == "mysql_extraction":
            execution_status, execution_output = execute_sql_query(sql)

        metadata = create_metadata(
            sql_query=sql,
            syntax_status=syntax_status,
            source=source,
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
        
        return sql, metadata.status, metadata.error_message
            
    except Exception as e:
        # Catch any unexpected errors during generation
        error_msg = f"GENERATION_ERROR: {str(e)}"
        return "", "GENERATION_ERROR", error_msg


def run_test_with_timeout(
    request: str, 
    model_name: str, 
    full_schema: dict,
    source: str,
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
            result = run_single_test(request, model_name, full_schema, source, query_vs, schema_vs)
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
                       error_message: str = "") -> str:
    """
    Format a single result line according to the template.
    """
    # Clean up SQL query for output (remove newlines, truncate if too long)
    clean_sql = sql_query.replace('\n', ' ').strip()
    if len(clean_sql) > MAX_OUTPUT_LENGTH:  # Truncate very long queries
        clean_sql = clean_sql[:MAX_OUTPUT_LENGTH] + "..."
    
    if status == "RUNTIME_ERROR":
        # For other errors, include the error message
        clean_error = error_message.replace('\n', ' ').strip()
        if len(clean_error) > MAX_OUTPUT_LENGTH/4:  # Truncate long error messages
            clean_error = clean_error[:MAX_OUTPUT_LENGTH/4] + "..."
        return f"{model_name}\n\nQuery: {clean_sql}\n\nOutcome: {clean_error}\n\n"
    else:
        return f"{model_name}\n\nQuery: {clean_sql}\n\nOutcome: {error_message}"


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
                    sql, status, error = model_results[model_name]
                    line = format_result_line(model_name, sql, status, error)
                    f.write(f"{line}\n")
                else:
                    f.write(f"{model_name} [TEST NOT RUN] MODEL_NOT_AVAILABLE\n")
            
            # Add blank line between requests for readability
            f.write("\n\n\n\n")
            n += 1
    
    print(f"✅ Results written to {output_file}")


def print_test_summary(results: List[Tuple[str, Dict]]):
    """Print a summary of test results."""
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
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
            elif status == "SYNTAX":
                syntax_errors += 1
            elif status == "RUNTIME_ERROR":
                runtime_errors += 1
            elif status == "TIMEOUT":
                timeouts += 1
            else:
                other_errors += 1
    
    print(f"Total requests tested: {len(results)}")
    print(f"Total model executions: {total_tests}")
    print(f"✅ Successful queries: {passed_tests}")
    print(f"⚠️  Syntax errors: {syntax_errors}")
    print(f"❌ Runtime errors: {runtime_errors}")
    print(f"⏰ Timeouts: {timeouts}")
    print(f"🔧 Other errors: {other_errors}")
    
    if total_tests > 0:
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📈 Success rate: {success_rate:.1f}%")
    
    print("="*60)


# ==================== MAIN TEST FUNCTION ====================

def run_comprehensive_tests():
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
    
    # 3. Determine source from schema
    source = full_schema.get("source")
    print(f"📋 Schema source: {source}")
    
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
            
            sql_query, status, error_message = run_test_with_timeout(
                request, model_name, full_schema, source, query_vs, schema_vs, TIMEOUT_PER_MODEL
            )
            
            model_time = time.time() - model_start_time
            print(f"   Status: {status} ({model_time:.1f}s)")
            
            if sql_query:
                print(f"   Generated SQL: {sql_query[:100]}...")
            if error_message and status not in ["OK", "SYNTAX"]:
                print(f"   Error: {error_message[:100]}...")
            
            model_results[model_name] = (sql_query, status, error_message)
        
        request_time = time.time() - request_start_time
        print(f"\n⏱️  Total time for this request: {request_time:.1f}s")
        
        all_results.append((request, model_results))
        
        # Save intermediate results after each request (optional)
        intermediate_file = f"./test_result/intermediate_results_{datetime.now().strftime('%H%M%S')}.txt"
        write_test_results([(request, model_results)], intermediate_file)
    
    # 5. Write final results
    write_test_results(all_results, OUTPUT_FILE)
    
    # 6. Print summary
    print_test_summary(all_results)
    
    print(f"\n🎉 Testing completed!")
    print(f"📄 Full results saved to: {OUTPUT_FILE}")


# ==================== PYTEST TEST CASES ====================

class TestSQLGeneration:
    """Pytest test class for SQL generation."""
    
    @classmethod
    def setup_class(cls):
        """Setup before all tests."""
        print("\n🔧 Setting up test class...")
        cls.full_schema = None
        try:
            with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
                cls.full_schema = json.load(f)
            print("✅ Schema loaded successfully")
        except Exception as e:
            pytest.skip(f"Cannot load schema: {e}")
        
        # Load vector stores with error handling
        try:
            embeddings = OllamaEmbeddings(model="mxbai-embed-large")

            cls.query_vs = Chroma(
                collection_name=QUERY_COLLECTION_NAME,
                persist_directory=VSQ_DIR,
                embedding_function=embeddings,
            )

            cls.schema_vs = Chroma(
                collection_name=SCHEMA_COLLECTION_NAME,
                persist_directory=VSS_DIR,
                embedding_function=embeddings,
            )  
            print("✅ Vector stores loaded successfully")
        except Exception as e:
            pytest.skip(f"Cannot load vector stores: {e}")
        
        # Safely retrieve source from schema
        if cls.full_schema is not None:
            cls.source = cls.full_schema.get("source")
            if cls.source is not None:
                print(f"📋 Schema source: {cls.source}")
            else:
                pytest.skip("Schema source not found in loaded schema")
        else:
            pytest.skip("Schema was not loaded successfully")
    
    @pytest.fixture
    def sample_requests(self):
        """Provide sample test requests."""
        return [
            "Show all customers",
            "List all products with their categories",
            "Count orders per customer",
            "Find total sales amount",
            "Show employees hired in 2023"
        ]
    
    @pytest.mark.parametrize("model_name", AVAILABLE_MODELS.values())
    def test_model_generates_sql(self, model_name, sample_requests):
        """Test that each model can generate SQL for sample requests."""
        request = sample_requests[0]  # Use first sample request
        print(f"\nTesting model {model_name} with request: '{request}'")
        
        if self.full_schema is None:
            pytest.skip("Schema not loaded")
        
        try:
            sql = generate_sql_query(
                request, 
                self.source, 
                self.full_schema, 
                model_name,
                self.query_vs,
                self.schema_vs,
            )
            
            # Basic validation
            assert sql is not None, "SQL query should not be None"
            assert len(sql.strip()) > 0, "SQL query should not be empty"
            assert "SELECT" in sql.upper(), "SQL query should contain SELECT"
            
            print(f"✅ Generated SQL: {sql[:100]}...")
            
        except Exception as e:
            pytest.fail(f"Model {model_name} failed: {e}")
    
    def test_syntax_validation(self):
        """Test SQL syntax validation."""
        valid_sql = "SELECT * FROM customers WHERE id = 1"
        invalid_sql = "SELECT FROM WHERE"
        
        assert validate_sql_syntax(valid_sql) == "OK"
        assert validate_sql_syntax(invalid_sql) == "SYNTAX_ERROR"
    
    @pytest.mark.slow
    def test_execute_sql_query(self):
        """Test executing a valid SQL query."""
        if self.full_schema is None:
            pytest.skip("Schema not loaded")
        
        sql = "SELECT * FROM customers LIMIT 1"
        
        status, output = execute_sql_query(sql)
        
        assert status == "OK", f"Execution status should be OK, got {status}"
        assert isinstance(output, list), "Output should be a list of rows"
        assert len(output) <= 1, "Output should contain at most 1 row"
        
        print(f"✅ Execution output: {output}")
    
    @pytest.mark.slow
    def test_without_llm(self):
        """Test without LLM."""
        if self.full_schema is None:
            pytest.skip("Schema not loaded")

        try:
            sql = generate_sql_query(
                "request without LLM",
                self.source,
                self.full_schema,
                "none",
                self.query_vs,
                self.schema_vs,
            )

            execution_status = None
            execution_output = None
            
            syntax_status = validate_sql_syntax(sql)

            if syntax_status == "OK" and self.source == "mysql_extraction":
                execution_status, execution_output = execute_sql_query(sql)

            metadata = create_metadata(
                sql_query=sql,
                syntax_status=syntax_status,
                source=self.source,
                schema_id=compute_schema_id(self.full_schema),
                user_request="none",
                model_name="none",
                execution_status=execution_status,
                execution_output=execution_output
            )

            store_query_feedback(
                store=self.query_vs,
                sql_query=sql,
                qm=metadata
            )
            
            return sql, metadata.status, metadata.error_message

            assert sql is not None, "SQL query should not be None"
            assert len(sql.strip()) > 0, "SQL query should not be empty"
            assert "SELECT" in sql.upper(), "SQL query should contain SELECT"
            print(f"✅ Generated SQL without LLM: {sql[:100]}...")
        except Exception as e:
            pytest.fail(f"Model without LLM failed: {e}")

    @pytest.mark.slow
    def test_all_models_all_requests(self, sample_requests):
        """Comprehensive test of all models with all sample requests."""
        if self.full_schema is None:
            pytest.skip("Schema not loaded")
        
        results = []
        
        for request in sample_requests:
            request_results = {}
            for model_name in AVAILABLE_MODELS.values():
                try:
                    sql = generate_sql_query(
                        request, 
                        self.source, 
                        self.full_schema, 
                        model_name,
                        self.query_vs,
                        self.schema_vs,
                    )
                    
                    # Validate syntax
                    syntax_ok = validate_sql_syntax(sql) == "OK"
                    request_results[model_name] = (sql, syntax_ok)
                    
                except Exception as e:
                    request_results[model_name] = (None, False)
            
            results.append((request, request_results))
        
        # Log results
        for request, model_results in results:
            print(f"\nRequest: {request}")
            for model, (sql, ok) in model_results.items():
                status = "✅" if ok else "❌"
                print(f"  {model}: {status}")
        
        # At least some models should succeed
        success_count = sum(1 for _, results in results 
                           for _, (_, ok) in results.items() if ok)
        assert success_count > 0, "At least some models should generate valid SQL"


# ==================== COMMAND LINE INTERFACE ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test SQL generation with multiple models")
    parser.add_argument("--mode", choices=["run", "test"], default="run",
                       help="Mode: 'run' to execute tests, 'test' to run pytest")
    parser.add_argument("--input", default=INPUT_FILE,
                       help="Input file with test requests")
    parser.add_argument("--output", default=OUTPUT_FILE,
                       help="Output file for results")
    parser.add_argument("--timeout", type=int, default=TIMEOUT_PER_MODEL,
                       help="Timeout per model per request (seconds)")
    
    args = parser.parse_args()
    
    if args.mode == "run":
        # Update global variables based on args
        INPUT_FILE = args.input
        OUTPUT_FILE = args.output
        TIMEOUT_PER_MODEL = args.timeout
        
        # Run the comprehensive tests
        run_comprehensive_tests()
    else:
        # Run pytest
        print("Running pytest tests...")
        pytest.main([__file__, "-v", "--tb=short"])