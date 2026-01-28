import sqlglot, json, hashlib
from datetime import datetime
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from logging_utils import setup_logger
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
VSS_DIR = "./vector_store/schema"
VSQ_DIR = "./vector_store/queries"

# === AVAILABLE MODELS ===
AVAILABLE_MODELS = {
    "1": "codellama:13b",
    "2": "codestral:22b",
    "3": "sqlcoder:15b",
    "4": "deepseek-coder-v2:16b"
}

# === LOGGING SETUP ===
logger = setup_logger(__name__)

def compute_schema_id(full_schema: dict) -> str:
    normalized = json.dumps(full_schema, sort_keys=True)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]

def infer_relationships(schema: dict) -> list[str]:
    """
    Infer join relationships from *_id column naming conventions.
    Returns human-readable join hints.
    """
    logger.info("🔍 Starting relationship inference...")
    tables = schema.get("tables", [])
    
    if not tables:
        logger.warning("⚠️  No tables found in schema")
        return []
    
    # Extract table names for easier checking
    table_names = [t["name"] for t in tables]
    logger.info(f"📊 Found {len(tables)} tables: {table_names}")
    
    # Map: column_name -> list of table names where column appears
    column_index = {}
    total_columns = 0

    logger.info("📋 Building column index...")
    for table in tables:
        table_name = table["name"]
        columns = table.get("columns", [])
        logger.info(f"  Table '{table_name}': {len(columns)} columns")
        
        for col in columns:
            col_name = col["name"]
            column_index.setdefault(col_name, []).append(table_name)
            total_columns += 1
    
    logger.info(f"📈 Indexed {total_columns} columns across all tables")
    logger.info(f"📌 Unique column names: {len(column_index)}")
    
    # Show columns that appear in multiple tables
    multi_table_cols = {col: tables for col, tables in column_index.items() 
                       if len(tables) > 1}
    if multi_table_cols:
        logger.info("🔗 Columns appearing in multiple tables:")
        for col, tables_list in multi_table_cols.items():
            logger.info(f"  '{col}': {tables_list}")
    
    relationships = []
    candidate_fks = []
    
    logger.info("🔄 Analyzing foreign key patterns...")
    for col_name, table_list in column_index.items():
        # Typical FK pattern: xxx_id appears in more than one table
        if col_name.endswith("_id") and len(table_list) >= 2:
            candidate_fks.append(col_name)
            logger.info(f"  ✓ '{col_name}' is a potential FK (appears in {len(table_list)} tables: {table_list})")
            
            # Derive the referenced table name from the column name
            # e.g., "category_id" -> "category" (singular)
            referenced_table_singular = col_name.replace("_id", "")
            
            # Try to find the matching table (handling singular/plural)
            referenced_table = None
            match_type = "unknown"
            
            # Strategy 1: Exact match with singular
            if referenced_table_singular in table_names:
                referenced_table = referenced_table_singular
                match_type = "exact singular"
            
            # Strategy 2: Try plural version (add 's')
            elif f"{referenced_table_singular}s" in table_names:
                referenced_table = f"{referenced_table_singular}s"
                match_type = "plural (added 's')"
            
            # Strategy 3: Try other common plural forms
            elif referenced_table_singular.endswith('y'):
                # Try replacing 'y' with 'ies' (category -> categories)
                plural_ies = referenced_table_singular[:-1] + "ies"
                if plural_ies in table_names:
                    referenced_table = plural_ies
                    match_type = "plural (y -> ies)"
            
            # Strategy 4: The column name itself might be a table
            elif col_name in table_names:
                referenced_table = col_name
                match_type = "column name as table"
            
            if referenced_table:
                logger.info(f"    → Found referenced table '{referenced_table}' for FK '{col_name}' ({match_type})")
                
                # For each table containing this FK column (except the referenced table itself)
                for source_table in table_list:
                    if source_table != referenced_table:
                        # Format: source_table.fk_column → referenced_table.fk_column
                        relationship = f"{source_table}.{col_name} → {referenced_table}.{col_name}"
                        relationships.append(relationship)
                        logger.info(f"    ✓ Discovered join: {relationship}")
            else:
                logger.warning(f"    ⚠️  Could not find matching table for '{referenced_table_singular}'")
                logger.info(f"      Tried: '{referenced_table_singular}', '{referenced_table_singular}s'")
                if referenced_table_singular.endswith('y'):
                    logger.info(f"      Also tried: '{referenced_table_singular[:-1]}ies'")
                
        elif col_name.endswith("_id"):
            logger.info(f"  - '{col_name}' is *_id but only in 1 table ({table_list[0]}) - likely a PK")
    
    logger.info("📊 Summary:")
    logger.info(f"  Candidate foreign keys: {len(candidate_fks)}")
    logger.info(f"  Inferred relationships: {len(relationships)}")
    
    if relationships:
        unique_relationships = sorted(set(relationships))
        logger.info(f"  Unique relationships: {len(unique_relationships)}")
        return unique_relationships
    else:
        logger.info("  No relationships inferred")
        return []

def build_join_hints(schema: dict) -> str:
    logger.info("=" * 50)
    logger.info("🧠 Building join hints from schema...")
    logger.info("=" * 50)
    
    relations = infer_relationships(schema)

    if not relations:
        logger.info("📭 No join relationships found")
        return ""

    logger.info(f"✨ Found {len(relations)} join relationship(s)")
    
    lines = ["=== JOIN PATH HINTS ==="]
    for i, r in enumerate(relations, 1):
        lines.append(f"{i:2}. {r}")

    result = "\n".join(lines)
    
    logger.info("\n" + "=" * 50)
    logger.info("✅ Join hints generated successfully!")
    logger.info("=" * 50)
    
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
    except Exception as e:
        logger.error(f"Syntax validation failed: {e}")
        return "SYNTAX_ERROR"

def print_llm_prompt(prompt_text: str) -> None:
    """
    Logs the final prompt that will be sent to the LLM.
    Useful for debugging and understanding what context the model receives.
    """
    logger.info("\n" + "=" * 80)
    logger.info("📋 FINAL PROMPT SENT TO LLM")
    logger.info("=" * 80)
    logger.info(prompt_text)
    logger.info("=" * 80 + "\n")

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
            logger.error("❌ Invalid choice. Please enter 1, 2, or 3.")

def get_schema_source(full_schema: dict) -> str:
    """
    Returns the schema source.
    Returns either "text_input" or "mysql_extraction".
    """
        
    if "source" in full_schema and full_schema["source"] == "mysql_extraction":
        logger.info("ℹ️  Schema source detected: MySQL extraction.\n")
        return "mysql_extraction"
    else:
        logger.info("ℹ️  Schema source detected: Text input.\n")
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

def add_penalties(template: str, user_request: str, query_vs: Chroma) -> str:

    # Negative examples → pattern penalization
    failed_queries = retrieve_failed_queries(user_request, query_vs)
    penalty_section = build_penalty_section(failed_queries)
    
    template = template + f"""

{penalty_section}

"""
    return template

def generate_sql_query(
    user_request: str, 
    source: str, 
    full_schema: dict, 
    model_name: str, 
    query_vs: Chroma, 
    schema_vs: Chroma
) -> str:
    """
    Generates a SQL query using:
    - canonical schema RAG
    - past successful queries (positive examples)
    - past failed queries (negative / penalized patterns)
    """
    logger.info(f"🚀 Starting SQL generation with model: {model_name}")

    schema_context = get_context(user_request, schema_vs)
    logger.debug(f"Schema context retrieved: {len(schema_context)} characters")
    
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
        template = add_penalties(template, user_request, query_vs)
        logger.info("Added penalty section for MySQL extraction schema")

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

    # Log the final prompt
    print_llm_prompt(template)

    prompt = ChatPromptTemplate.from_template(template)
    model = OllamaLLM(model=model_name)
    chain = prompt | model

    logger.info("Sending request to LLM...")
    response = chain.invoke({
        "schema_context": schema_context,
        "user_request": user_request
    })

    # ------------------------------------------------------------------
    # 4. OUTPUT CLEANUP
    # ------------------------------------------------------------------
    sql_query = response_cleaning(response)
    logger.info(f"Generated SQL query length: {len(sql_query)} characters")

    return sql_query

def main():
    """Main function to handle the interactive workflow."""
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
                persist_directory=VSQ_DIR,
                embedding_function=embeddings,
            )
            print_query_vector_store(store)
        
        elif choice == "3":
            confirm = input("⚠️  Are you sure you want to empty the query feedback vector store? (y/n): ").strip().lower()
            if confirm == "y":
                embeddings = OllamaEmbeddings(model="mxbai-embed-large")
                store = Chroma(
                    collection_name=QUERY_COLLECTION_NAME,
                    persist_directory=VSQ_DIR,
                    embedding_function=embeddings,
                )
                store.delete_collection()
                print("✅ Query feedback vector store emptied.")
            else:
                print("❌ Operation cancelled.")

        elif choice == "1":
            # Select model at runtime
            selected_model_name = select_model()

            # Load schema
            full_schema = None
            with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
                full_schema = json.load(f)
            
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
            # User request
            user_request = input("\n👉 Enter a request in natural language: ")
            schema_id = compute_schema_id(full_schema)
            source = get_schema_source(full_schema)

            print("\n🔍 Generating query...")
            sql = generate_sql_query(user_request, source, full_schema, selected_model_name, query_vs, schema_vs)

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
                store=query_vs,
                user_request=user_request,
                sql_query=sql,
                status=status,
                model_name=selected_model_name,
                error_message=error_message,
                schema_id=schema_id,
                rows_fetched=rows_fetched
            )
            print(f"Feedback stored with status: {status}")

        else:
            print("❌ Invalid option. Try again.")

# === ENTRY POINT ===
if __name__ == "__main__":
    main()