from typing import Any, Tuple
import sqlglot, json, hashlib, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_openai import AzureChatOpenAI
from src.mysql_linker import execute_sql_query
from src.config.settings import AVAILABLE_MODELS, AZURE_MODELS, ERROR_CATEGORIES, LOGINFO_SEPARATOR
from src.logging_utils import (
    setup_logger,
    print_llm_prompt,
    print_query_vector_store,
    truncate_request
)
from src.retriver_utils import (
    store_query_feedback,
    retrieve_failed_queries,
    build_penalty_section,
    create_metadata
)
from src.config.paths import (
    VECTOR_STORE_DIR,
    SAMPLE_QUERY_PATH,
    SCHEMA_FILE
)

# === CONFIG ===
SCHEMA_COLLECTION_NAME = "schema_canonical"
QUERY_COLLECTION_NAME = "query_feedback"
VSS_DIR = str(VECTOR_STORE_DIR / "schema")
VSQ_DIR = str(VECTOR_STORE_DIR / "queries")
SAMPLE_QUERY_FILE = str(SAMPLE_QUERY_PATH)

# === LOGGING SETUP ===
logger = setup_logger(__name__)

def pretty_print_query_preview(rows: list | None | str, max_rows: int = 5, max_col_width: int = 40) -> None:
    """
    Print a compact, fancy preview of fetched rows.
    """
    if rows is None:
        print("\n📭 Query executed successfully, but no rows were returned.")
        return

    if isinstance(rows, str):
        print("\n📭 Query executed, but output is not row data.")
        return

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

def get_context(user_request: str, vector_store: Chroma) -> str:
    """
    Retrieve relevant schema fragments for the user request.
    Uses light query-intent heuristics to tune retrieval depth,
    removes duplicate chunks, and groups output by table.
    """
    logger.info("Retrieving schema context for request: '%s'", truncate_request(truncate_request(user_request)))

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
        logger.debug("Request contains aggregation terms, increasing k to %s", k)
    if has_join_intent:
        k += 1
        logger.debug("Request contains join intent, increasing k to %s", k)
    
    logger.info("Retrieval parameters - has_aggregation: %s, has_join_intent: %s, k: %s", 
                has_aggregation, has_join_intent, k)

    retriever = vector_store.as_retriever(search_kwargs={"k": k})
    relevant_docs = retriever.invoke(user_request)
    logger.debug("Retrieved %s relevant documents", len(relevant_docs))

    seen_chunks = set()
    grouped_chunks = {}

    for doc in relevant_docs:
        table_name = (doc.metadata or {}).get("table") or "unknown_table"
        content = (doc.page_content or "").strip()

        if not content:
            logger.debug("Skipping empty document")
            continue

        dedup_key = (table_name, content)
        if dedup_key in seen_chunks:
            logger.debug("Duplicate chunk found for table '%s'", table_name)
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
        logger.warning("No schema context retrieved for request: %s", truncate_request(user_request))

    return schema_context

def compute_schema_id(full_schema: dict) -> str:
    """
    Compute a unique identifier for the schema.
    """
    logger.debug("Computing schema ID")
    normalized = json.dumps(full_schema, sort_keys=True)
    schema_id = hashlib.sha256(normalized.encode()).hexdigest()[:16]
    logger.debug("Schema ID computed: %s", schema_id)
    return schema_id

def infer_relationships(schema: dict) -> list[str]:
    """
    Fetch join relationships directly from MySQL foreign key metadata.
    Returns human-readable join hints.
    """
    logger.info("🔍 Fetching relationship metadata from MySQL...")
    database_name = os.getenv("DB_NAME", "")
    if not database_name:
        logger.warning("⚠️  DB_NAME is not set; cannot load foreign keys from MySQL")
        return []

    fk_query = f"""
        SELECT
            kcu.TABLE_NAME,
            kcu.COLUMN_NAME,
            kcu.REFERENCED_TABLE_NAME,
            kcu.REFERENCED_COLUMN_NAME
        FROM information_schema.KEY_COLUMN_USAGE kcu
        WHERE kcu.TABLE_SCHEMA = '{database_name}'
          AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
        ORDER BY kcu.TABLE_NAME, kcu.COLUMN_NAME
    """

    logger.debug("Executing foreign key query for database: %s", database_name)
    status, rows = execute_sql_query(fk_query, database_name=database_name)
    if status != "OK":
        logger.warning("⚠️  Failed to query foreign key metadata: %s", rows)
        return []

    if not rows:
        logger.info("📭 No foreign key relationships found in MySQL metadata")
        return []

    logger.info("Found %s foreign key relationship(s)", len(rows))
    relationships = []
    for table_name, column_name, referenced_table, referenced_column in rows:
        relationship = (
            f"{table_name}.{column_name} → {referenced_table}.{referenced_column}"
        )
        relationships.append(relationship)

    unique_relationships = sorted(set(relationships))
    logger.info("📊 Summary:")
    logger.info("  Foreign key relationships: %s", len(unique_relationships))
    return unique_relationships

def build_join_hints(schema: dict) -> str:
    logger.info(LOGINFO_SEPARATOR)
    logger.info("🧠 Building join hints from schema...")
    logger.info(LOGINFO_SEPARATOR)
    
    relations = infer_relationships(schema)

    if not relations:
        logger.info("📭 No join relationships found")
        return ""

    logger.info(f"✨ Found {len(relations)} join relationship(s)")
    
    lines = ["=== JOIN PATH HINTS ==="]
    for i, r in enumerate(relations, 1):
        lines.append(f"{i:2}. {r}")

    result = "\n".join(lines)
    
    logger.info(LOGINFO_SEPARATOR)
    logger.info("✅ Join hints generated successfully!")
    logger.info(LOGINFO_SEPARATOR)
    
    return result

def validate_sql_syntax(sql_query: str) -> str:
    """
    Checks if SQL compiles syntactically.
    Returns:
        - "OK" if it compiles
        - "SYNTAX_ERROR" if it fails
    """
    logger.debug("Validating SQL syntax for query: %s", sql_query)
    try:
        # Parse only, no DB execution
        sqlglot.parse_one(sql_query)
        logger.debug("SQL syntax validation passed")
        return "OK"
    except Exception as e:
        logger.error(f"Syntax validation failed: {e}")
        return "SYNTAX_ERROR"

def get_llm_model(choice: int) -> str | OllamaLLM | AzureChatOpenAI:
    logger.info("Getting LLM model for choice: %s", choice)
    if choice == 0 :
        logger.info("Selected 'none' model (no LLM)")
        return "none"
    elif choice < 5:
        model_name = AVAILABLE_MODELS[choice]
        logger.info("Selected Ollama model: %s", model_name)
        return OllamaLLM(model=model_name)
    else:
        model_name = AVAILABLE_MODELS[choice]
        logger.info("Selected Azure OpenAI model: %s", model_name)
        
        load_dotenv("../.env.azure")

        # === Load Azure environment ===
        AZURE_API_KEY = os.getenv("AZURE_API_KEY")
        AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
        AZURE_API_VERSION = os.getenv("AZURE_API_VERSION")

        if not AZURE_API_KEY or not AZURE_ENDPOINT:
            logger.error("❌ Missing Azure credentials in .env")
            raise ValueError("❌ Missing Azure credentials in .env")

        logger.info("Azure credentials loaded successfully")
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
    logger.debug("Determining schema source")
        
    if "source" in full_schema and full_schema["source"] == "mysql":
        logger.info("ℹ️  Schema source detected: MySQL extraction.")
        return "mysql"
    else:
        logger.info("ℹ️  Schema source detected: Text input.")
        return "text"

def response_cleaning(response) -> str:
    """
    Cleans the LLM response to extract only the SQL query.
    - Removes text before the first SELECT
    - Removes text after the first semicolon
    - Removes markdown fences
    Returns only the SQL code.
    """
    logger.debug("Cleaning LLM response")
    if isinstance(response, str):
        sql_query = response.strip()
    elif hasattr(response, "content"):
        sql_query = response.content.strip()
    else:
        sql_query = str(response).strip()

    logger.debug("Original response length: %s characters", len(sql_query))

    # Remove markdown fences if present
    if sql_query.startswith("```"):
        sql_query = sql_query.split("```")[1]
        logger.debug("Removed markdown fence from response")
    
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

    # Remove everything before the first SELECT (case-insensitive)
    select_index = sql_query.upper().find("SELECT")
    if select_index > 0:
        sql_query = sql_query[select_index:]
        logger.debug("Removed text before SELECT statement")
    
    # Remove everything after the first semicolon (inclusive)
    semicolon_index = sql_query.find(";")
    if semicolon_index >= 0:
        sql_query = sql_query[:semicolon_index + 1]
    
    sql_query = sql_query.strip()
    
    logger.debug("Cleaned response length: %s characters", len(sql_query))
    return sql_query

def add_penalties(template: str, user_request: str, query_vs: Chroma) -> str:
    """
    Add penalty section based on failed queries.
    """
    logger.info("Adding penalty section for request: '%s'", truncate_request(user_request))
    
    # Negative examples → pattern penalization
    failed_queries = retrieve_failed_queries(user_request, query_vs)
    logger.debug("Retrieved %s failed queries for penalty section", len(failed_queries))
    
    penalty_section = build_penalty_section(failed_queries)
    
    template = template + f"""

{penalty_section}

"""
    logger.info("Penalty section added to template")
    return template

def create_prompt(
    user_request: str,
    source: str,
    full_schema: dict,
    query_vs: Chroma,
    schema_vs: Chroma,
    error_feedback: str | None = None,
) -> str:
    """
    Create prompt for SQL generation.
    """
    logger.info("Creating prompt for request: '%s', source: %s", user_request, source)
    
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
        logger.info("MySQL source detected, adding join hints")
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

    if source == "mysql" and error_feedback is not None:
        template = add_penalties(template, user_request, query_vs)
        logger.info("Added penalty section for MySQL extraction schema")
    else:
        logger.info("Adding error feedback to prompt")
        template = template + f"""
=== PREVIOUS QUERY ERROR TO FIX ===
{error_feedback}

You must correct the query considering this error.
Do NOT repeat the same mistake.
"""

    template = template + f"""

Before writing the SQL query, internally determine:
- Which tables are required
- How they are joined
- Whether aggregation or grouping is required
- Which columns are selected

Do NOT output this reasoning.
Only output the final SQL query.
    
SQL QUERY (DO NOT ADD COMMENTS OR EXPLANATION TEXT BEFORE AND AFTER THE QUERY):
"""

    logger.info("Prompt created successfully. Total length: %s characters", len(template))
    return template

def generate_sql_query(
    model: str | OllamaLLM | AzureChatOpenAI, 
    template: str,
) -> str:
    """
    Generates a SQL query using:
    - canonical schema RAG
    - past successful queries (positive examples)
    - past failed queries (negative / penalized patterns)
    """
    # Log the final prompt
    print_llm_prompt(template)
    
    if model == "none":
        logger.info("Using sample query file: %s", SAMPLE_QUERY_FILE)
        # open sample query file and read content
        with open(SAMPLE_QUERY_FILE, "r", encoding="utf-8") as f:
            sql_query = f.read().strip()
        logger.info("SQL generation skipped due to 'without_llm' mode. Retrieved from file: %s", 
                    sql_query)
    else:
        logger.info("Sending request to LLM...")
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | model # pyright: ignore[reportOperatorIssue]

        response = chain.invoke({})
        logger.debug("LLM response received")

        # ------------------------------------------------------------------
        # 4. OUTPUT CLEANUP
        # ------------------------------------------------------------------
        sql_query = response_cleaning(response)
        logger.info(f"Generated SQL query length: {len(sql_query)} characters")
        logger.debug("Generated SQL: %s", sql_query)

    return sql_query

def extract_llm_text(response: Any) -> str:
    """
    Extracts text content from an LLM response.
    """
    if isinstance(response, str):
        return response.strip()
    if hasattr(response, "content"):
        return str(response.content).strip()
    return str(response).strip()

def format_error_feedback(title: str, sql: str, details: str) -> str:
    """
    Formats error feedback with the current query and details.
    """
    return f"""{title}

SQL QUERY:
{sql}

DETAILS:
{details}
"""

def llm_feedback(
    sql: str,
    request: str,
    execution_output: list | None | str,
    context: dict | None = None,
) -> str:
    """
    Uses an Azure OpenAI model to evaluate whether the SQL query
    correctly answers the user's request based on execution results.

    Returns:
        - "CORRECT_QUERY"
        - "INCORRECT_QUERY: <suggestions>"
    """
    logger.info("Starting LLM feedback evaluation for query: '%s'", sql)

    # Safety guard
    if not execution_output:
        logger.warning("Execution output is empty, cannot verify correctness")
        return (
            "INCORRECT_QUERY: The query returned no results, "
            "so correctness cannot be verified."
        )

    load_dotenv(".env.azure")
    logger.debug("Loaded Azure environment variables")

    model = AzureChatOpenAI(
        azure_deployment="gpt-4o",
        api_version=os.getenv("AZURE_API_VERSION"),
        api_key=os.getenv("AZURE_API_KEY"),  # pyright: ignore[reportArgumentType]
        azure_endpoint=os.getenv("AZURE_ENDPOINT"),
        temperature=0,
    )

    if isinstance(execution_output, str):
        evaluation_prompt = f"""
You are an expert SQL debugger.
Explain why the following SQL query produced this runtime error.
Be concise and do NOT rewrite the query.

--- CONTEXT ---
{context}

--- SQL QUERY ---
{sql}

--- RUNTIME ERROR ---
{execution_output}

Provide a clear explanation of the cause.
"""
        logger.info("Requesting runtime error explanation from LLM.")
    else:

        # Take only the first 20 rows to avoid token explosion
        preview_rows = execution_output[:20]
        logger.debug("Using first %s rows for evaluation", len(preview_rows))

        # Convert rows to a readable string
        rows_text = "\n".join(str(row) for row in preview_rows)

        evaluation_prompt = f"""
You are an expert SQL reviewer.

Your task is to evaluate whether the SQL query correctly answers
the user's request, based ONLY on the query results shown.

--- USER REQUEST ---
{request}

--- SQL QUERY ---
{sql}

--- QUERY RESULT (first 20 rows) ---
{rows_text}

--- INSTRUCTIONS ---
Respond in EXACTLY one of the following formats:

1) If the query is correct:
CORRECT_QUERY

2) If the query is incorrect:
INCORRECT_QUERY: <clear explanation of what is wrong and how to fix it>

Rules:
- Do NOT rewrite the full SQL query.
- Be concise and precise.
- Judge correctness, not syntax or performance.
"""

        logger.info("🧠 Sending query result to LLM for correctness evaluation")

    response = model.invoke(evaluation_prompt)
    logger.debug("LLM evaluation response received")

    verdict = extract_llm_text(response)

    logger.info(f"🧪 LLM evaluation verdict: {verdict}")

    # Hard validation to avoid silent failures
    if not verdict.startswith(("CORRECT_QUERY", "INCORRECT_QUERY")):
        logger.warning("⚠️ Unexpected LLM feedback format: %s", verdict)
        return (
            "INCORRECT_QUERY: Unable to confidently evaluate correctness "
            "from the query results."
        )

    return verdict

def classify_llm_feedback(feedback: str | None) -> tuple[str, str | None]:
    """
    Classifies an INCORRECT_QUERY LLM feedback string.

    Returns:
        (error_category, error_detail)
    """
    logger.debug("Classifying LLM feedback: %s", feedback)
    
    if not feedback:
        logger.debug("No feedback provided, returning NO_ERROR")
        return ("NO_ERROR", None)

    feedback_lower = feedback.lower()
    if not feedback_lower.startswith("incorrect_query"):
        logger.debug("Feedback is not incorrect_query, returning NO_ERROR")
        return ("NO_ERROR", None)

    # Strip prefix
    explanation = feedback.split(":", 1)[-1].strip()
    explanation_lower = explanation.lower()
    logger.debug("Extracted explanation: %s", explanation)

    for category, keywords in ERROR_CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in explanation_lower:
                logger.info("Feedback classified as: %s", category)
                return (category, explanation)

    # Fallback if nothing matches
    logger.warning("Feedback did not match any known error category, classifying as UNKNOWN_ERROR")
    return ("UNKNOWN_ERROR", explanation)

def evaluate_feedback_error(
    request: str,
    sql: str, 
    source: str, 
    database_name: str | None = None, 
    execution_status: str | None = None,
    execution_output: list[Any] | str | None = None,
    attempt: int = 1,
    llm_model: str | OllamaLLM | AzureChatOpenAI = "none",
    ):
    """
    Evaluate feedback and errors for SQL query.
    """
    logger.info("Evaluating feedback error for request: '%s'", truncate_request(request))
    
    syntax_status = validate_sql_syntax(sql)

    logger.info(f"✅ Syntax check: {syntax_status}")
    logger.info("Syntax check result: %s", syntax_status)

    error_feedback = None
    error_category = None
    if syntax_status != "OK":
        logger.warning("Syntax error detected: %s", syntax_status)
        error_feedback = format_error_feedback(
            "The previous SQL query caused a syntax error.",
            sql,
            f"Syntax status: {syntax_status}.",
        )
        logger.info("Feedback error evaluation completed. Has error feedback: %s", True)
        return syntax_status, execution_status, execution_output, error_feedback, error_category

    if source != "mysql":
        logger.info("Non-MySQL source detected; skipping execution and LLM feedback.")
        logger.info("Feedback error evaluation completed. Has error feedback: %s", False)
        return syntax_status, execution_status, execution_output, error_feedback, error_category

    if source == "mysql":
        logger.info("Executing SQL query against database: %s", database_name)
        execution_status, execution_output = execute_sql_query(sql, database_name=database_name)

        if execution_status != "OK":
            logger.warning("Runtime error detected: %s", execution_output)
            details = f"Runtime error: {execution_output}"
            if attempt >= 2:
                explanation = llm_feedback(sql, request, execution_output)
                details = f"{details}\n\nExplanation:\n{explanation}"
            error_feedback = format_error_feedback(
                "The previous SQL query failed at runtime.",
                sql,
                details,
            )
            logger.info("Feedback error evaluation completed. Has error feedback: %s", True)
            return syntax_status, execution_status, execution_output, error_feedback, error_category

        logger.info("Using LLM feedback for correctness evaluation")
        error_feedback = llm_feedback(sql, request, execution_output)
        if error_feedback.startswith("CORRECT_QUERY"):
            logger.info("Query confirmed correct by LLM.")
            return syntax_status, execution_status, execution_output, None, "CORRECT_QUERY"

        error_category, _ = classify_llm_feedback(error_feedback)
        if attempt >= 2:
            retry_hint = build_targeted_retry_instruction(error_category)
            error_feedback = f"{error_feedback}\n\n{retry_hint}"

        error_feedback = format_error_feedback(
            "The previous SQL query was incorrect.",
            sql,
            error_feedback,
        )

    logger.info("Feedback error evaluation completed. Has error feedback: %s", True)
    return syntax_status, execution_status, execution_output, error_feedback, error_category

def build_targeted_retry_instruction(error_category: str) -> str:
    """
    Build targeted retry instruction based on error category.
    """
    logger.info("Building targeted retry instruction for error category: %s", error_category)
    
    instructions = {
        "AGGREGATION_ERROR": (
            "The query has incorrect aggregation logic. "
            "Re-check GROUP BY clauses and aggregated columns."
        ),
        "JOIN_ERROR": (
            "The query has incorrect or missing joins. "
            "Re-evaluate join paths using foreign keys."
        ),
        "FILTER_ERROR": (
            "The query applies incorrect filtering. "
            "Review WHERE conditions carefully."
        ),
        "PROJECTION_ERROR": (
            "The selected columns do not match the request."
        ),
        "SEMANTIC_ERROR": (
            "The query does not answer the user's request correctly."
        ),
        "SCHEMA_ERROR": (
            "The query references invalid tables or columns."
        ),
        "UNKNOWN_ERROR": (
            "Re-evaluate the query carefully to match the request."
        ),
    }

    instruction = instructions.get(error_category, instructions["UNKNOWN_ERROR"])
    logger.debug("Retry instruction: %s", instruction)
    return instruction

def generation_loop(
    user_request: str,
    source: str,
    full_schema: dict,
    database_name: str | None,
    query_vs: Chroma,
    schema_vs: Chroma,
    llm_model: str | OllamaLLM | AzureChatOpenAI,
):
    """
    Main generation loop with retry logic.
    """
    logger.info("Starting generation loop for request: '%s'", truncate_request(user_request))
    logger.info("Parameters - source: %s, database: %s", 
                source, database_name)
    
    sql = ""
    execution_status = None
    execution_output = None
    error_feedback = None
    syntax_status = "UNKNOWN"
    error_category = None

    for attempt in range(1, 4):
        template = create_prompt(
            user_request=user_request,
            source=source,
            full_schema=full_schema,
            query_vs=query_vs,
            schema_vs=schema_vs,
            error_feedback=error_feedback,
        )

        logger.info(f"🔍 Generating query (attempt {attempt}/3)...")
        sql = generate_sql_query(llm_model, template)

        syntax_status, execution_status, execution_output, error_feedback, error_category = evaluate_feedback_error(
            user_request,
            sql,
            source,
            database_name,
            execution_status,
            execution_output,
            attempt=attempt,
            llm_model=llm_model,
        )

        if error_category == "CORRECT_QUERY" or (source == "text" and syntax_status == "OK"):
            break

    return sql, syntax_status, execution_status, execution_output, error_category

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
            if model_index == 0:
                database_name = "supermarket"
                logger.info("Using 'supermarket' database for without_llm mode.")
            
            print(f"\n🔍 Generating query")
            
            # Generate SQL query
            sql, syntax_status, execution_status, execution_output, LLM_feedback = generation_loop(
                llm_model=llm_model,
                user_request=user_request,
                source=source,
                full_schema=full_schema,
                database_name=database_name,
                query_vs=query_vs,
                schema_vs=schema_vs,
            )

            print("\n💡 Generated SQL query:\n")
            print(sql)
            print("\n" + LOGINFO_SEPARATOR)

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
                execution_output=execution_output,
                LLM_feedback=LLM_feedback
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
