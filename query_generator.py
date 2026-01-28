import sqlglot, json, hashlib
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from query_feedback_store import (
    store_query_feedback,
    retrieve_failed_queries,
    build_penalty_section,
    print_query_vector_store
)
from utils_pkg import (
    get_context,
    print_schema_context
)
from mysql_linker import execute_sql_query

# === CONFIG ===
SCHEMA_FILE = "schema_canonico.json"
SCHEMA_COLLECTION_NAME = "schema_canonico"
QUERY_COLLECTION_NAME = "query_feedback"
DBS_DIR = "./vector_store/schema"
DBQ_DIR = "./vector_store/queries"

# === AVAILABLE MODELS ===
AVAILABLE_MODELS = {
    "1": "codellama:13b",
    "2": "codestral:22b",
    "3": "sqlcoder:15b",
    "4": "deepseek-coder-v2:16b"
}

def compute_schema_id(full_schema: dict) -> str:
    normalized = json.dumps(full_schema, sort_keys=True)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]

def infer_relationships(schema: dict) -> list[str]:
    """
    Infer join relationships from *_id column naming conventions.
    Returns human-readable join hints.
    """
    print("🔍 Starting relationship inference...")
    tables = schema.get("tables", [])
    
    if not tables:
        print("⚠️  No tables found in schema")
        return []
        
    # Map: column_name -> [(table, column)]
    column_index = {}

    print("\n📋 Building column index...")
    for table in tables:
        table_name = table["name"]
        for col in table["columns"]:
            col_name = col["name"]
            column_index.setdefault(col_name, []).append(table_name)

    relationships = []
        
    print("\n🔄 Analyzing foreign key patterns...")
    for col_name, table_list in column_index.items():
        # Typical FK pattern: xxx_id appears in more than one table
        if col_name.endswith("_id") and len(table_list) >= 2:
            base = col_name.replace("_id", "")
            for t in table_list:
                if t != base and base in table_list:
                    relationships.append(
                        f"{t}.{col_name} → {base}.{col_name}"
                    )

    return sorted(set(relationships))

def build_join_hints(schema: dict) -> str:
    print("=" * 50)
    print("🧠 Building join hints from schema...")
    
    relations = infer_relationships(schema)

    if not relations:
        print("\n📭 No join relationships found")
        return ""

    print(f"\n✨ Found {len(relations)} join relationship(s)")
    
    lines = ["=== JOIN PATH HINTS ==="]
    for r in relations:
        lines.append(f"- {r}")

    result = "\n".join(lines)
    
    print("\n" + "=" * 50)
    print("✅ Join hints generated successfully!")
    print("=" * 50)
    
    return result

def validate_sql_syntax(sql_query: str) -> str:
    """
    Checks if SQL compiles syntactically.
    Returns:
        - "OK" if it compiles
        - "SYNTAX_ERROR" if it fails
    """
    try:
        # Parse only, no DB execution
        sqlglot.parse_one(sql_query)
        return "OK"
    except Exception:
        return "SYNTAX_ERROR"

def print_llm_prompt(prompt_text: str) -> None:
    """
    Prints the final prompt that will be sent to the LLM.
    Useful for debugging and understanding what context the model receives.
    """
    print("\n" + "=" * 80)
    print("📋 FINAL PROMPT SENT TO LLM")
    print("=" * 80)
    print(prompt_text)
    print("=" * 80 + "\n")

def select_model() -> str:
    """
    Prompts user to select an Ollama model from available options.
    Returns the selected model name.
    """
    print("\n🤖 Available Ollama models:")
    for key, model_name in AVAILABLE_MODELS.items():
        print(f"   {key}. {model_name}")
    
    while True:
        choice = input("\n👉 Select a model (1-4): ").strip()
        if choice in AVAILABLE_MODELS:
            selected = AVAILABLE_MODELS[choice]
            print(f"✅ Selected model: {selected}\n")
            return selected
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

def get_schema_source(full_schema: dict) -> str:
    """
    Prompts user to select the schema source.
    Returns either "text_input" or "mysql_extraction".
    """
        
    if "source" in full_schema and full_schema["source"] == "mysql_extraction":
        print("ℹ️  Schema source detected: MySQL extraction.\n")
        return "mysql_extraction"
    else:
        print("ℹ️  Schema source detected: Text input.\n")
        return "text_input"

def response_cleaning(response) -> str:
    """
    Cleans the LLM response to extract only the SQL query.
    - Removes text before the first SELECT
    - Removes text after the first semicolon
    - Removes markdown fences
    Returns only the SQL code.
    """
    if isinstance(response, str):
        sql_query = response.strip()
    elif hasattr(response, "content"):
        sql_query = response.content.strip()
    else:
        sql_query = str(response).strip()

    # Remove markdown fences if present
    if sql_query.startswith("```"):
        sql_query = sql_query.split("```")[1]
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

    # Remove everything before the first SELECT (case-insensitive)
    select_index = sql_query.upper().find("SELECT")
    if select_index > 0:
        sql_query = sql_query[select_index:]
    
    # Remove everything after the first semicolon (inclusive)
    semicolon_index = sql_query.find(";")
    if semicolon_index >= 0:
        sql_query = sql_query[:semicolon_index + 1]
    
    sql_query = sql_query.strip()
    
    return sql_query

def add_penalties(template: str, user_request: str) -> str:
    # ------------------------------------------------------------------
    # QUERY FEEDBACK RETRIEVAL
    # ------------------------------------------------------------------

    # Negative examples → pattern penalization
    failed_queries = retrieve_failed_queries(user_request)
    penalty_section = build_penalty_section(failed_queries)

    # ------------------------------------------------------------------
    # PROMPT
    # ------------------------------------------------------------------
    template = template + f"""

{penalty_section}

"""
    return template

def generate_sql_query(user_request: str, source: str, full_schema: dict) -> str:
    """
    Generates a SQL query using:
    - canonical schema RAG
    - past successful queries (positive examples)
    - past failed queries (negative / penalized patterns)
    """
    embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    vector_store = Chroma(
        collection_name=SCHEMA_COLLECTION_NAME,
        persist_directory=DBS_DIR,
        embedding_function=embeddings,
    )

    schema_context = get_context(user_request, vector_store)
    #print_schema_context(schema_context)
    
    join_hints = build_join_hints(full_schema)

    template = f""" 
You are an expert SQL database assistant.
You will be provided with:
1. The partial description of the database schema (only the relevant tables)
2. The user's request in natural language.
3. Examples of previous successful SQL queries

Your task is to return a **single SQL query** that satisfies the request,
using the provided tables and columns.

=== SCHEMA ===
{schema_context}

{join_hints}

=== REQUEST ===
{user_request}

IMPORTANT CONSTRAINTS BASED ON PAST FAILURES:
- Do NOT use columns outside the schema
- Do NOT invent field or table names that don't exist.
- Always qualify columns when joining
- Do NOT use SELECT *
- Do NOT add WHERE clauses or conditions unless explicitly requested.
- Do NOT join tables unless necessary for the request.
- If using aggregates, include GROUP BY    
"""
    
    if source == "mysql_extraction":
        template = add_penalties(template, user_request)

    template = template + """
Before writing the SQL query, internally determine:
- Which tables are required
- How they are joined
- Whether aggregation or grouping is required
- Which columns are selected

Do NOT output this reasoning.
Only output the final SQL query.

SQL QUERY (DO NOT ADD COMMENTS OR EXPLANATION TEXT BEFORE AND AFTER THE QUERY):
"""

    # Print the final prompt
    print_llm_prompt(template)

    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model  # pyright: ignore[reportOperatorIssue]

    response = chain.invoke({
        "schema_context": schema_context,
        "user_request": user_request
    })

    # ------------------------------------------------------------------
    # 4. OUTPUT CLEANUP
    # ------------------------------------------------------------------
    sql_query = response_cleaning(response)

    return sql_query


# === MAIN ===
if __name__ == "__main__":
    print("🤖 SQL query generator based on RAG and LLM\n")

    while True:
        print("\nChoose an option:")
        print("1️⃣  Generate SQL query")
        print("2️⃣  Show query feedback vector store")
        print("3️⃣  Empty query feedback vector store")
        print("0️⃣  Exit")

        choice = input("\n👉 Your choice: ").strip()

        if choice == "0":
            print("👋 Bye!")
            break

        elif choice == "2":
            embeddings = OllamaEmbeddings(model="mxbai-embed-large")
            store = Chroma(
                collection_name=QUERY_COLLECTION_NAME,
                persist_directory=DBQ_DIR,
                embedding_function=embeddings,
            )
            print_query_vector_store(store)
        
        elif choice == "3":
            confirm = input("⚠️  Are you sure you want to empty the query feedback vector store? (y/n): ").strip().lower()
            if confirm == "y":
                embeddings = OllamaEmbeddings(model="mxbai-embed-large")
                store = Chroma(
                    collection_name=QUERY_COLLECTION_NAME,
                    persist_directory=DBQ_DIR,
                    embedding_function=embeddings,
                )
                store.delete_collection()
                print("✅ Query feedback vector store emptied.")
            else:
                print("❌ Operation cancelled.")

        elif choice == "1":
            # Select model at runtime
            selected_model_name = select_model()
            model = OllamaLLM(model=selected_model_name)

            # Load schema
            full_schema = None
            with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
                full_schema = json.load(f)
            
            # User request
            user_request = input("\n👉 Enter a request in natural language: ")
            schema_id = compute_schema_id(full_schema)
            source = get_schema_source(full_schema)

            print("\n🔍 Generating query...")
            sql = generate_sql_query(user_request, source, full_schema)

            print("\n💡 Generated SQL query:\n")
            print(sql)
            print("\n" + "=" * 60)

            # Syntax validation
            syntax_status = validate_sql_syntax(sql)

            error_message = None
            rows_fetched = 0

            if syntax_status == "OK":
                if source == "mysql_extraction":
                    # Runtime execution
                    print("\n🚀 Executing query against the database...\n")
                    execution_status, execution_output = execute_sql_query(sql)

                    if execution_status == "OK":
                        status = "OK"
                        rows_fetched = len(execution_output) if execution_output else 0
                        print("\n📊 Query result preview:\n")
                        for row in execution_output[:10]:
                            print(row)
                    else:
                        status = "RUNTIME_ERROR"
                        error_message = execution_output
                        print(f"\n⚠️  Error: {error_message}")
                else:
                    status = "OK"
            else:
                status = "SYNTAX_ERROR"
                error_message = "Query failed syntactic check"
                print(f"\n⚠️  Error: {error_message}")

            # Store feedback
            store_query_feedback(
                user_request=user_request,
                sql_query=sql,
                status=status,
                model_name=selected_model_name,
                error_message=error_message,
                schema_id=schema_id,
                rows_fetched=rows_fetched
            )

        else:
            print("❌ Invalid option. Try again.")