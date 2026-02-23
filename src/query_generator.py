from xml.dom.minidom import Document
import sqlglot, json, hashlib, os, re, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import Any
from langchain_core.documents import Document
from src.classes.llm_clients.azure_client import AzureLLM
from src.classes.llm_clients.openwebui_client import OpenWebUILLM
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from src.mysql_linker import execute_sql_query, get_foreign_keys, validate_sql_syntax
from src.config import QUERY_GENERATION_MODELS, ERROR_CATEGORIES, LOGINFO_SEPARATOR
from src.prompt_factory import (
    query_generation_prompt,
    explanation_prompt,
    evaluation_prompt
)
from src.logging_utils import (
    setup_logger,
    print_llm_prompt,
    print_query_vector_store,
    truncate_request
)
from src.retriver_utils import (
    store_query_feedback,
    retrieve_failed_queries,
    create_metadata,
    get_context
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

def select_model() -> str | None:
    """
    Prompts user to select a model from available options.
    
    Returns:
        str | None: Selected model name, or None for "without_llm" mode
    """
    print("\n🤖 Available models:")
    print("   0. without_llm (no LLM, use sample query from file)")
    
    # Display numbered list of models
    models = list(QUERY_GENERATION_MODELS.keys())
    for idx, model_name in enumerate(models, 1):
        print(f"   {idx}. {model_name}")
    
    while True:
        try:
            choice = int(input("\n👉 Select a model (0-{}): ".format(len(models))).strip())
            
            if choice == 0:
                print("✅ Selected mode: without_llm\n")
                return None
            elif 1 <= choice <= len(models):
                selected = models[choice - 1]
                print(f"✅ Selected model: {selected}\n")
                return selected
            else:
                print(f"❌ Invalid choice. Please enter 0-{len(models)}.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")

def build_join_hints(database_name: str, allowed_tables: set[str] | None = None) -> str:
    logger.info(LOGINFO_SEPARATOR)
    logger.info("🧠 Building join hints from schema...")
    logger.info(LOGINFO_SEPARATOR)
    
    relations = get_foreign_keys(database_name)

    if not relations:
        logger.info("📭 No join relationships found")
        return ""

    if allowed_tables:
        filtered_relations = []
        for relation in relations:
            try:
                left, right = relation.split("→")
                left_table = left.strip().split(".", 1)[0].strip()
                right_table = right.strip().split(".", 1)[0].strip()
            except ValueError:
                continue

            if left_table in allowed_tables and right_table in allowed_tables:
                filtered_relations.append(relation)

        relations = filtered_relations
        logger.info(
            "✨ Filtered join relationships to %s based on schema context tables",
            len(relations),
        )
    else:
        logger.info("✨ Found %s join relationship(s)", len(relations))

    if not relations:
        logger.info("📭 No join relationships found after filtering")
        return ""
    
    lines = ["=== JOIN PATH HINTS ==="]
    for i, r in enumerate(relations, 1):
        lines.append(f"{i:2}. {r}")

    result = "\n".join(lines)
    
    logger.info(LOGINFO_SEPARATOR)
    logger.info("✅ Join hints generated successfully!")
    logger.info(LOGINFO_SEPARATOR)
    
    return result

def extract_table_names_from_schema_context(schema_context: str) -> set[str]:
    table_names = set()
    for match in re.finditer(r"^Table:\s*([^\n]+)", schema_context, re.MULTILINE):
        table_name = match.group(1).strip()
        if table_name:
            table_names.add(table_name)
    return table_names

def get_llm_model(choice: str | None) -> AzureLLM | OpenWebUILLM | None:
    logger.info("Getting LLM model for choice: %s", choice)
    if choice is None:
        logger.info("Selected 'none' model (no LLM)")
        return None
    elif QUERY_GENERATION_MODELS[choice]["provider"] == "azure":
        model_name = QUERY_GENERATION_MODELS[choice]["id"]
        logger.info("Selected Azure OpenAI model: %s", model_name)
        return AzureLLM(model_name)
    else:
        model_name = QUERY_GENERATION_MODELS[choice]["id"]
        logger.info("Selected OpenWebUI model: %s", model_name)
        return OpenWebUILLM(model_name)

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
    Guarantees a valid, executable SQL string.
    """
    logger.debug("Cleaning LLM response")

    sql_query = extract_llm_text(response)

    logger.debug("Original response length: %s characters", len(sql_query))

    # 2. Remove markdown fences safely
    if "```" in sql_query:
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        logger.debug("Removed markdown fences")

    # 4. Remove trailing junk after last semicolon IF present
    if ";" in sql_query:
        sql_query = sql_query[: sql_query.rfind(";") + 1].strip()

    # 5. Final validation
    if not sql_query:
        raise ValueError("LLM returned empty SQL")

    # 6. Ensure terminating semicolon (DO NOT FAIL)
    if not sql_query.endswith(";"):
        logger.warning("SQL query missing terminating semicolon, appending automatically")
        sql_query += ";"

    logger.debug("Cleaned SQL length: %s characters", len(sql_query))
    logger.debug("Final SQL:\n%s", sql_query)

    return sql_query

def build_penalty_section(failed_queries: list[Document]) -> str:
    if not failed_queries:
        logger.info("ℹ️ No failed queries to build penalties.")
        return ""

    lines = []

    for d in failed_queries:
        error_type = d.metadata.get("error_type")
        content = d.page_content

        lines.append(f"""
--- FAILURE ---
{content}

Error type: {error_type}
""")

        if error_type == "UNKNOWN_COLUMN":
            lines.append("RULE: Do NOT use columns that are not present in the schema.")
        elif error_type == "UNKNOWN_TABLE":
            lines.append("RULE: Do NOT reference tables not present in the schema.")
        elif error_type == "AMBIGUOUS_COLUMN":
            lines.append("RULE: Always qualify column names with table aliases.")
        elif error_type == "BAD_JOIN":
            lines.append("RULE: Avoid unnecessary joins.")
        else:
            lines.append("RULE: Avoid repeating this query structure.")

    logger.info(f"📋 Penalty section built for {len(failed_queries)} failures.")
    return "\n".join(lines)

def add_penalties(user_request: str, query_vs: Chroma) -> str:
    """
    Add penalty section based on failed queries.
    """
    logger.info("Adding penalty section for request: '%s'", truncate_request(user_request))
    
    # Negative examples → pattern penalization
    failed_queries = retrieve_failed_queries(user_request, query_vs)
    logger.debug("Retrieved %s failed queries for penalty section", len(failed_queries))
    
    return build_penalty_section(failed_queries)

def extract_llm_text(response: Any) -> str:
    """
    Extracts text content from an LLM response.
    """
    if isinstance(response, str):
        return response.strip()
    if hasattr(response, "content"):
        return str(response.content).strip()
    return str(response).strip()

def format_error_feedback(error_type: str, sql: str, details: str) -> str:
    """
    Formats error feedback with the current query and details.
    """
    if error_type == "SYNTAX_ERROR":
        title = "The previous SQL query caused a syntax error."
    elif error_type == "RUNTIME_ERROR":
        title = "The previous SQL query failed at runtime."
    else:
        title = "The previous SQL query was incorrect."

    return f"""{title}

SQL QUERY:
{sql}

DETAILS:
{details}
"""

def generate_sql_query(model: AzureLLM | OpenWebUILLM | None, template: str,) -> str:
    """
    Generates a SQL query using:
    - canonical schema RAG
    - past successful queries (positive examples)
    - past failed queries (negative / penalized patterns)
    """
    
    if model is None:
        logger.info("Using sample query file: %s", SAMPLE_QUERY_FILE)
        # open sample query file and read content
        with open(SAMPLE_QUERY_FILE, "r", encoding="utf-8") as f:
            sql_query = f.read().strip()
        logger.info("SQL generation skipped due to 'without_llm' mode. Retrieved from file: %s", 
                    sql_query)
    else:
        logger.info("Sending request to LLM...")
        
        response = model.generate(template)

        logger.debug("LLM response received")
        logger.debug("LLM response: %s", response)

        # ------------------------------------------------------------------
        # 4. OUTPUT CLEANUP
        # ------------------------------------------------------------------
        sql_query = response_cleaning(response)
        logger.info(f"Generated SQL query length: {len(sql_query)} characters")

    return sql_query

def llm_feedback(sql: str, request: str, context: str, execution_output: list | None | str):
    """
    Uses an Azure OpenAI model to evaluate whether the SQL query
    correctly answers the user's request based on execution results.

    Returns:
        - "CORRECT_QUERY"
        - "INCORRECT_QUERY: <suggestions>"
    """
    logger.info("°" * 80 + "\n\n")
    logger.info("Starting LLM feedback evaluation for query: \n'%s'\n\n", sql)
    logger.info("°" * 80)

    # Safety guard
    if not execution_output:
        logger.warning("Execution output is empty, cannot verify correctness")
        return (
            "INCORRECT_QUERY: The query returned no results, "
            "so correctness cannot be verified."
        )

    model = AzureLLM("gpt-4o")  # Use a strong model for evaluation

    if isinstance(execution_output, str):
        prompt = explanation_prompt(sql, context, execution_output)
    else:

        # Take only the first 20 rows to avoid token explosion
        preview_rows = execution_output[:20]
        logger.debug("Using first %s rows for evaluation", len(preview_rows))

        # Convert rows to a readable string
        rows_text = "\n".join(str(row) for row in preview_rows)

        prompt = evaluation_prompt(sql, request, context, rows_text)

        logger.info("🧠 Sending query result to LLM for correctness evaluation")

    print_llm_prompt(prompt)

    response = model.generate(prompt)
    logger.debug("LLM evaluation response received")

    verdict = extract_llm_text(response)

    logger.info(f"🧪 LLM evaluation verdict: {verdict}")

    # Hard validation to avoid silent failures
    if not verdict.startswith(("CORRECT_QUERY", "INCORRECT_QUERY")) and not isinstance(execution_output, str):
        logger.warning("⚠️ Unexpected LLM feedback format: %s", verdict)
        return "INCORRECT_QUERY: Unable to confidently evaluate correctness from the query results."

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
    context: str,
    database_name: str | None = None, 
    execution_status: str | None = None,
    execution_output: list[Any] | str | None = None,
    attempt: int = 1,
):

    """
    Evaluates the feedback error for a given SQL query and its execution result.

    Parameters:
        request (str): The original user request.
        sql (str): The generated SQL query.
        source (str): The source of the information (e.g. MySQL, text).
        context (str): The schema context for the request.
        database_name (str | None): The name of the database to execute the query against.
        execution_status (str | None): The status of the query execution.
        execution_output (list[Any] | str | None): The result of the query execution.
        attempt (int): The number of attempts made to generate the query.

    Returns:
        (syntax_status, execution_status, execution_output, error_feedback, feedback_category)
            syntax_status (str): The result of the syntax check on the query.
            execution_status (str): The status of the query execution.
            execution_output (list[Any] | str | None): The result of the query execution.
            error_feedback (str): The feedback from the second LLM model.
            feedback_category (str): The category of the error (CORRECT_QUERY, INCORRECT_QUERY, RUNTIME_ERROR, etc.).
    """
    
    logger.info("*" * 80 + "\n\n")
    logger.info("Evaluating feedback error for query: \n'%s'\n\n", sql)
    logger.info("*" * 80)
    syntax_status = validate_sql_syntax(sql)

    logger.info(f"✅ Syntax check: {syntax_status}")
    logger.info("Syntax check result: %s", syntax_status)

    error_feedback = None
    feedback_category = None
    if syntax_status != "OK":
        logger.warning("Syntax error detected: %s", syntax_status)
        details = f"Syntax status: {syntax_status}."
        error_feedback = format_error_feedback(syntax_status, sql, details)
        logger.info("Feedback error evaluation completed. Has error feedback: %s", True)
        return syntax_status, execution_status, execution_output, error_feedback, feedback_category

    if source == "mysql":
        logger.info("Executing SQL query against database: %s", database_name)
        execution_status, execution_output = execute_sql_query(sql, database_name=database_name)

        if execution_status != "OK":
            logger.warning("Runtime error detected: %s", execution_output)
            details = f"Runtime error: {execution_output}"
            if attempt == 2:
                explanation = llm_feedback(sql, request, context, execution_output)
                details = f"{details}\n\nExplanation:\n{explanation}"
            error_feedback = format_error_feedback(execution_status, sql, details)
            logger.info("Feedback error evaluation completed. Has error feedback: %s", True)
            return syntax_status, execution_status, execution_output, error_feedback, execution_status

        logger.info("Using LLM feedback for correctness evaluation")
        error_feedback = llm_feedback(sql, request, context, execution_output)
        if error_feedback.startswith("CORRECT_QUERY"):
            logger.info("Query confirmed correct by LLM.")
            return syntax_status, execution_status, execution_output, None, "CORRECT_QUERY"

        error_category, error_explanation = classify_llm_feedback(error_feedback)
        details = f"Error type: {error_category}\nExplanation: {error_explanation}"
        if attempt == 2:
            retry_hint = build_targeted_retry_instruction(error_category)
            error_feedback = f"{details}\n\n{retry_hint}"

        error_feedback = format_error_feedback("INCORRECT_QUERY", sql, details)
        return syntax_status, execution_status, execution_output, error_feedback, "INCORRECT_QUERY"
    else:
        logger.info("Non-MySQL source detected; skipping execution and LLM feedback.")
        logger.info("Feedback error evaluation completed. Has error feedback: %s", False)
        return syntax_status, execution_status, execution_output, error_feedback, feedback_category

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
    database_name: str,
    query_vs: Chroma,
    schema_vs: Chroma,
    llm_model: AzureLLM | OpenWebUILLM | None,
):
    
    """
    Generates an SQL query based on the user request and source information.
    Uses an LLM to generate queries and evaluate their correctness.
    If the query is incorrect, uses the LLM to generate a retry instruction.
    Parameters:
        user_request (str): The user's request.
        source (str): The source of the information (e.g. MySQL, text).
        database_name (str): The name of the database.
        query_vs (Chroma): The query vector store.
        schema_vs (Chroma): The schema vector store.
        llm_model (str | OllamaLLM | AzureChatOpenAI): The LLM model to use.
    Returns:
        sql (str): The generated SQL query.
        syntax_status (str): The syntax status of the query (OK or Error).
        execution_status (str): The execution status of the query (OK or Error).
        execution_output (list[Any] | str | None): The execution output of the query.
        error_feedback (str): The error feedback from the LLM.
        feedback_category (str): The category of the error (CORRECT_QUERY, INCORRECT_QUERY, RUNTIME_ERROR, etc.).
        attempt (int): The number of attempts made to generate the query.
    """
    logger.info("=" * 80)
    logger.info("=" * 80 + "\n\n")
    logger.info("Starting generation loop for request: '%s'", truncate_request(user_request))
    logger.info("Parameters - source: %s, database: %s\n\n", 
                source, database_name)
    logger.info("=" * 80)
    logger.info("=" * 80)
    
    sql = ""
    execution_status = None
    execution_output = None
    penalties = None
    error_feedback = None
    syntax_status = "UNKNOWN"
    feedback_category = None
    attempt = 0

    schema_context = get_context(user_request, schema_vs)
    logger.debug("Schema context retrieved: %s characters", len(schema_context))
    join_hints = None
    if source == "mysql":
        allowed_tables = extract_table_names_from_schema_context(schema_context)
        join_hints = build_join_hints(database_name, allowed_tables)
        penalties = add_penalties(user_request, query_vs)  # Get penalties to include in prompt if needed

    for attempt in range(1, 4):
        logger.info("-" * 80)
        logger.info("-" * 80 + "\n\n")
        logger.info(f"🔍 Generating query (attempt {attempt}/3)...\n\n")
        logger.info("-" * 80)
        logger.info("-" * 80)
                
        template = query_generation_prompt(
            user_request=user_request,
            source=source,
            schema_context=schema_context,
            previous_fail=error_feedback if error_feedback else penalties,
            join_hints=join_hints
        )
        logger.info("Prompt template created for attempt %s", attempt)
        logger.debug("Prompt template:\n%s", template)
        
        sql = generate_sql_query(llm_model, template)
        logger.info("Generated SQL: %s", sql)

        logger.info("🔎 Evaluating query syntax and semantics...")
        syntax_status, execution_status, execution_output, error_feedback, feedback_category = evaluate_feedback_error(
            user_request,
            sql,
            source,
            schema_context,
            database_name,
            execution_status,
            execution_output,
            attempt=attempt,
        )

        if feedback_category == "CORRECT_QUERY" or (source == "text" and syntax_status == "OK"):
            logger.info("Query confirmed correct by LLM.")
            break
        else:
            logger.info("Query incorrect by LLM. Retrying...")

    logger.info("=" * 80)
    logger.info("=" * 80 + "\n\n")
    logger.info("Generation loop completed.\n\n")
    logger.info("=" * 80)
    logger.info("=" * 80)
    
    return sql, syntax_status, execution_status, execution_output, feedback_category, attempt

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
            model_name = select_model()
            llm_model = get_llm_model(model_name)

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
            source = full_schema.get("source")
            database_name = full_schema.get("database")
            if source == "mysql" and not database_name:
                logger.warning("Schema source is MySQL but no database name was found in schema JSON.")
            if model_name is None:
                database_name = "supermarket"
                logger.info("Using 'supermarket' database for without_llm mode.")
            
            print(f"\n🔍 Generating query")
            
            # Generate SQL query
            sql, syntax_status, execution_status, execution_output, LLM_feedback, attempt = generation_loop(
                llm_model=llm_model,
                user_request=user_request,
                source=source,
                database_name=database_name,
                query_vs=query_vs,
                schema_vs=schema_vs,
            )

            print(f"\n💡 Generated SQL query with {attempt} attempts:\n")
            print(sql)
            print("\n" + LOGINFO_SEPARATOR)

            if execution_status == "OK":
                pretty_print_query_preview(execution_output)

            metadata = create_metadata(
                sql_query=sql,
                syntax_status=syntax_status,
                schema_id=full_schema.get("schema_id"),
                schema_source=source,
                user_request=user_request,
                model_name=model_name,
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
