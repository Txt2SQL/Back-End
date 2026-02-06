import sqlglot, json, hashlib, os
from dotenv import load_dotenv
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_openai import AzureChatOpenAI
from src.mysql_linker import execute_sql_query
from src.config.settings import AVAILABLE_MODELS
from src.logging_utils import (
    setup_logger,
    print_llm_prompt,
    print_query_vector_store
)
from src.retriver_utils import (
    store_query_feedback,
    retrieve_failed_queries,
    build_penalty_section,
    create_metadata
)
from src.config.paths import (
    PROJECT_ROOT,
    VECTOR_STORE_DIR,
    SAMPLE_QUERY_PATH,
)

# === CONFIG ===
SCHEMA_FILE = str(PROJECT_ROOT / "schema_canonical.json")
SCHEMA_COLLECTION_NAME = "schema_canonical"
QUERY_COLLECTION_NAME = "query_feedback"
VSS_DIR = str(VECTOR_STORE_DIR / "schema")
VSQ_DIR = str(VECTOR_STORE_DIR / "queries")
SAMPLE_QUERY_FILE = str(SAMPLE_QUERY_PATH)

# === LOGGING SETUP ===
logger = setup_logger(__name__)

def get_context(user_request: str, vector_store: Chroma) -> str:
    """
    Retrieve relevant schema fragments for the user request.
    Uses light query-intent heuristics to tune retrieval depth,
    removes duplicate chunks, and groups output by table.
    """

    # ------------------------------------------------------------------
    # SCHEMA RETRIEVAL (RAG)
    # ------------------------------------------------------------------

    request_lower = user_request.lower()
    request_tokens = set(request_lower.replace(",", " ").replace(".", " ").split())

    aggregate_terms = {
        "avg",
        "average",
        "count",
        "group",
        "having",
        "sum",
        "total",
        "min",
        "max",
    }
    join_terms = {"join", "across", "between", "related", "each"}

    has_aggregation = bool(request_tokens.intersection(aggregate_terms))
    has_join_intent = bool(request_tokens.intersection(join_terms)) or " by " in f" {request_lower} "

    # Start with a conservative context size and increase only when complexity suggests it.
    k = 3
    if has_aggregation:
        k += 1
    if has_join_intent:
        k += 1

    retriever = vector_store.as_retriever(search_kwargs={"k": k})
    relevant_docs = retriever.invoke(user_request)

    seen_chunks = set()
    grouped_chunks = {}

    for doc in relevant_docs:
        table_name = (doc.metadata or {}).get("table") or "unknown_table"
        content = (doc.page_content or "").strip()

        if not content:
            continue

        dedup_key = (table_name, content)
        if dedup_key in seen_chunks:
            continue

        seen_chunks.add(dedup_key)
        grouped_chunks.setdefault(table_name, []).append(content)

    sections = []
    for table_name, chunks in grouped_chunks.items():
        sections.append(f"Table: {table_name}\n" + "\n".join(chunks[:2]))

    schema_context = "\n\n".join(sections)

    logger.info(
        "Schema context retrieval complete: k=%s, docs=%s, unique_tables=%s, context_chars=%s",
        k,
        len(relevant_docs),
        len(grouped_chunks),
        len(schema_context),
    )

    if not schema_context:
        logger.warning("No schema context retrieved for request: %s", user_request)

    return schema_context

def pretty_print_query_preview(rows: list | None, max_rows: int = 5, max_col_width: int = 40) -> None:
    """
    Print a compact, fancy preview of fetched rows.
    """
    if not rows:
        print("\n📭 Query executed successfully, but no rows were returned.")
        return

    sample = rows[:max_rows]
    normalized = [list(r) if isinstance(r, tuple) else ([r] if not isinstance(r, list) else r) for r in sample]
    num_cols = max(len(r) for r in normalized) if normalized else 0

    headers = [f"col_{i + 1}" for i in range(num_cols)]

    def fmt(value):
        value_str = str(value)
        return value_str if len(value_str) <= max_col_width else value_str[: max_col_width - 3] + "..."

    col_widths = [len(h) for h in headers]
    for row in normalized:
        for idx in range(num_cols):
            cell = fmt(row[idx] if idx < len(row) else "")
            col_widths[idx] = max(col_widths[idx], len(cell))

    border = "┼".join("─" * (w + 2) for w in col_widths)
    top = "┌" + border.replace("┼", "┬") + "┐"
    mid = "├" + border + "┤"
    bottom = "└" + border.replace("┼", "┴") + "┘"

    def render_row(values):
        cells = []
        for idx in range(num_cols):
            v = fmt(values[idx] if idx < len(values) else "")
            cells.append(f" {v:<{col_widths[idx]}} ")
        return "│" + "│".join(cells) + "│"

    print(f"\n✨ Query preview ({len(rows)} row(s) fetched, showing up to {max_rows}):")
    print(top)
    print(render_row(headers))
    print(mid)
    for row in normalized:
        print(render_row(row))
    print(bottom)

    if len(rows) > max_rows:
        print(f"… and {len(rows) - max_rows} more row(s).")

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

def select_model() -> int:
    """
    Prompts user to select an Ollama model from available options.
    Returns the selected model name.
    """
    print("\n🤖 Available Ollama models:")
    for key, model_name in AVAILABLE_MODELS.items():
        print(f"   {key}. {model_name}")
    
    while True:
        choice = int(input("\n👉 Select a model (0-6): ").strip())
        if choice in AVAILABLE_MODELS:
            selected = AVAILABLE_MODELS[choice]
            print(f"✅ Selected model: {selected}\n")
            return choice
        elif choice == 0:
            print("✅ Selected mode: without_llm\n")
            return 0
        else:
            logger.error("❌ Invalid choice. Please enter 1, 2, or 3.")

def get_llm_model(choice: int) -> str | OllamaLLM | AzureChatOpenAI:
    if choice == 0 :
        return "none"
    elif choice < 5:
        model_name = AVAILABLE_MODELS[choice]
        return OllamaLLM(model=model_name)
    else:
        model_name = AVAILABLE_MODELS[choice]
        
        load_dotenv(".env.azure")

        # === Load Azure environment ===
        AZURE_API_KEY = os.getenv("AZURE_API_KEY")
        AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
        AZURE_API_VERSION = os.getenv("AZURE_API_VERSION")

        if not AZURE_API_KEY or not AZURE_ENDPOINT:
            raise ValueError("❌ Missing Azure credentials in .env")

        return AzureChatOpenAI(
            azure_deployment=model_name,
            api_version=AZURE_API_VERSION,
            api_key=AZURE_API_KEY, # pyright: ignore[reportArgumentType]
            azure_endpoint=AZURE_ENDPOINT
        )

def get_schema_source(full_schema: dict) -> str:
    """
    Returns the schema source.
    Returns either "text_input" or "mysql_extraction".
    """
        
    if "source" in full_schema and full_schema["source"] == "mysql":
        logger.info("ℹ️  Schema source detected: MySQL extraction.\n")
        return "mysql"
    else:
        logger.info("ℹ️  Schema source detected: Text input.\n")
        return "text"

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

Before writing the SQL query, internally determine:
- Which tables are required
- How they are joined
- Whether aggregation or grouping is required
- Which columns are selected

Do NOT output this reasoning.
Only output the final SQL query.
"""
    return template

def generate_sql_query(
    user_request: str, 
    source: str, 
    full_schema: dict, 
    model: str | OllamaLLM | AzureChatOpenAI, 
    query_vs: Chroma, 
    schema_vs: Chroma,
    error_feedback: str | None = None,
) -> str:
    """
    Generates a SQL query using:
    - canonical schema RAG
    - past successful queries (positive examples)
    - past failed queries (negative / penalized patterns)
    """
    logger.info(f"🚀 Starting SQL generation with model: {model}")

    schema_context = get_context(user_request, schema_vs)
    logger.debug(f"Schema context retrieved: {len(schema_context)} characters")
    
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
  
"""    
    if source == "mysql":
        join_hints = build_join_hints(full_schema)
        template = template + f"""
{join_hints}
"""

    template = template + f"""

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

    if source == "mysql":
        template = add_penalties(template, user_request, query_vs)
        logger.info("Added penalty section for MySQL extraction schema")

    template = template + f"""
    
SQL QUERY (DO NOT ADD COMMENTS OR EXPLANATION TEXT BEFORE AND AFTER THE QUERY):
"""

    if error_feedback:
        template = template + f"""

PREVIOUS QUERY ERROR TO FIX:
{error_feedback}

You must correct the query considering this error.
Do NOT repeat the same mistake.
"""

    # Log the final prompt
    print_llm_prompt(template)
    
    if model == "none":
        # open sample query file and read content
        with open(SAMPLE_QUERY_FILE, "r", encoding="utf-8") as f:
            sql_query = f.read().strip()
        logger.info("SQL generation skipped due to 'without_llm' mode")
    else:
        logger.info("Sending request to LLM...")
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | model # pyright: ignore[reportOperatorIssue]

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
            model_index = select_model()
            llm_model = get_llm_model(model_index)

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
            source = get_schema_source(full_schema)
            database_name = full_schema.get("database") if source == "mysql" else None
            if source == "mysql" and not database_name:
                logger.warning("Schema source is MySQL but no database name was found in schema JSON.")

            print("\n🔍 Generating query...")
            sql = generate_sql_query(user_request, source, full_schema, llm_model, query_vs, schema_vs)

            print("\n💡 Generated SQL query:\n")
            print(sql)
            print("\n" + "=" * 60)

            execution_status = None
            execution_output = None
            
            syntax_status = validate_sql_syntax(sql)
            print()
            print(f"✅ Syntax check: {syntax_status}")

            error_feedback = None
            if syntax_status != "OK":
                print("♻️ Syntax non valida: rigenero la query con feedback sull'errore...")
                error_feedback=(
                    "The previous SQL query failed syntax validation "
                    f"(status={syntax_status})."
                )

            if syntax_status == "OK" and source == "mysql":
                print()
                print("🚀 Executing query against the database...")
                print()
                execution_status, execution_output = execute_sql_query(sql, database_name=database_name)

                if execution_status != "OK":
                    print("♻️ Runtime error: rigenero la query con feedback dell'errore di esecuzione...")
                    error_feedback=(
                        "The previous SQL query failed at runtime with this error: "
                        f"{execution_output}."
                    )

            if syntax_status != "OK" or execution_status != "OK":
                sql = generate_sql_query(
                    user_request,
                    source,
                    full_schema,
                    llm_model,
                    query_vs,
                    schema_vs,
                    error_feedback=error_feedback
                )
                print("\n💡 Regenerated SQL query after runtime feedback:\n")
                print(sql)
                print("\n" + "=" * 60)

                syntax_status = validate_sql_syntax(sql)
                print()
                print(f"✅ Syntax check after runtime retry: {syntax_status}")

                if syntax_status == "OK":
                    print()
                    print("🚀 Executing regenerated query against the database...")
                    print()
                    execution_status, execution_output = execute_sql_query(sql, database_name=database_name)

            if execution_status == "OK":
                pretty_print_query_preview(execution_output)

            metadata = create_metadata(
                sql_query=sql,
                syntax_status=syntax_status,
                schema_id=compute_schema_id(full_schema),
                schema_source=source,
                user_request=user_request,
                model_index=model_index,
                execution_status=execution_status,
                execution_output=execution_output
            )

            store_query_feedback(
                store=query_vs,
                sql_query=sql,
                qm=metadata
            )
            print(f"Feedback stored with status: {metadata.status}")

        else:
            print("❌ Invalid option. Try again.")

# === ENTRY POINT ===
if __name__ == "__main__":
    main()
