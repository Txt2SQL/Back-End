import math, time, re, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import Any
from langchain_chroma import Chroma
from langchain_core.documents import Document
from src.logging_utils import setup_logger, truncate_request
from src.classes.metadata import QueryMetadata
from src.config.paths import VECTOR_STORE_DIR
from langchain_ollama import OllamaEmbeddings

# === CONFIG ===
DB_DIR = str(VECTOR_STORE_DIR / "schema")
COLLECTION_NAME = "schema_canonical"

# === LOGGING SETUP ===
logger = setup_logger(__name__)

# ------------------------------------------------------------------
# SCHEMA STORE
# ------------------------------------------------------------------

def build_vector_store(
    schema_data: dict,
    *,
    persist_directory: str | None = None,
    collection_name: str | None = None,
    embedding_model: str = "mxbai-embed-large",
):
    embeddings = OllamaEmbeddings(model=embedding_model)

    documents = []
    ids = []

    for table in schema_data.get("tables", []):
        table_name = table.get("name", "unknown_table")
        columns = table.get("columns", [])

        col_lines = []
        for col in columns:
            col_name = col.get("name", "unknown_column")
            col_type = col.get("type", "UNKNOWN_TYPE")
            constraints = ", ".join(col.get("constraints", []))
            col_line = f"- {col_name} ({col_type}) {constraints}".strip()
            col_lines.append(col_line)

        text = f"Table: {table_name}\nColumns:\n" + "\n".join(col_lines)
        doc = Document(page_content=text, metadata={"table": table_name})
        documents.append(doc)
        ids.append(table_name)

    logger.info(f"Created {len(documents)} documents to embed...")

    persist_directory = persist_directory or DB_DIR
    collection_name = collection_name or COLLECTION_NAME
    add_schema = not os.path.exists(persist_directory)

    vector_store = Chroma(
        collection_name=collection_name,
        persist_directory=persist_directory,
        embedding_function=embeddings,
    )

    if add_schema:
        logger.info("Creating a new vector store...")
        vector_store.add_documents(documents=documents, ids=ids)
    else:
        logger.info("Updating existing vector store...")
        # For updates, we need to handle existing documents
        existing_ids = vector_store.get()["ids"]
        if existing_ids:
            vector_store.delete(ids=existing_ids)
        vector_store.add_documents(documents=documents, ids=ids)
    
    logger.info(f"Vector store updated and saved in: {persist_directory}")

    return vector_store

# ------------------------------------------------------------------
# FEEDBACK STORE
# ------------------------------------------------------------------

def apply_time_decay(
    docs,
    half_life_days: int = 30
):
    """
    Applies exponential time decay to documents.
    Newer docs are preferred.

    half_life_days: after how many days relevance halves
    """
    now = time.time()
    half_life_seconds = half_life_days * 86400

    scored = []

    for doc in docs:
        ts = doc.metadata.get("timestamp", now)
        age = now - ts

        # exponential decay
        decay = math.exp(-age / half_life_seconds)

        scored.append((decay, doc))

    # sort by decay (descending)
    scored.sort(key=lambda x: x[0], reverse=True)

    return [doc for _, doc in scored]

def query_already_exists(store: Chroma, sql_query: str, model_name: str | None) -> bool:
    """
    Checks if a SQL query already exists in the vector store.
    Comparison is done on metadata["sql_query"].
    """
    logger.info(f"🔍 Checking if query exists: {sql_query}")
    
    if model_name is None:
        logger.info("ℹ️ Model is 'none': testing run. Skip storing")
        return False
    
    data = store.get(include=["metadatas"])

    if not data or not data.get("metadatas"):
        logger.info("ℹ️ No metadata found in store.")
        return False

    for metadata in data["metadatas"]:
        if metadata.get("sql_query") == sql_query:
            logger.info("✅ Query already exists in store.")
            return True

    logger.info("❌ Query does not exist in store.")
    return False

def create_metadata(
    sql_query: str,
    syntax_status: str,
    schema_id: str,
    schema_source: str,
    user_request: str,
    model_name: str | None,
    execution_status: str | None = None,
    execution_output: Any | None = None,
    LLM_feedback: str | None = None
) -> QueryMetadata:
    
    """
    Creates a QueryMetadata object for storing query execution results.

    Args:
        - sql_query: the SQL query executed
        - syntax_status: the result of the syntax check on the query
        - schema_id: the identifier of the schema on which the query is executed
        - schema_source: the source of the schema (e.g. database, text, etc.)
        - user_request: the original user request
        - model_index: the index of the model used to generate the query
        - execution_status: the status of the query execution
        - execution_output: the result of the query execution
        - LLM_feedback: the feedback from the second LLM model

    Returns:
        - QueryMetadata object containing the execution results
    """
    logger.info("📝 Creating metadata for query execution...")

    # -----------------------------
    # STATUS
    # -----------------------------
    if syntax_status != "OK":
        if not sql_query.strip().upper().startswith("SELECT"):
            status = "SKIP"
        else:
            status = syntax_status
    elif schema_source == "text":
        status = "UNKNOWN"
    else:
        status = execution_status if execution_status is not None else "UNKNOWN_ERROR"
    logger.info(f"📊 Status determined: {status}")

    # -----------------------------
    # ERROR MESSAGE
    # -----------------------------
    error_message = None
    if status == "SYNTAX_ERROR":
        error_message = "Query failed syntactic check"
    elif status == "RUNTIME_ERROR":
        error_message = execution_output

    # -----------------------------
    # ROWS FETCHED
    # -----------------------------
    rows_fetched = (
        len(execution_output)
        if status == "OK" and execution_output
        else 0
    )
    logger.info(f"🔢 Rows fetched: {rows_fetched}")

    # -----------------------------
    # ERROR TYPE
    # -----------------------------
    error_type = None
    if error_message == "RUNTIME_ERROR":
        error_type = classify_error(error_message)
        logger.info(f"🐛 Error type classified as: {error_type}")

    # -----------------------------
    # KNOWLEDGE SCOPE
    # -----------------------------
    if status == "SYNTAX_ERROR":
        knowledge_scope = "SYNTAX"
    elif detect_structural_issue(sql_query):
        knowledge_scope = "STRUCTURAL"
    else:
        knowledge_scope = "SCHEMA_SPECIFIC"
    logger.info(f"🧠 Knowledge scope determined: {knowledge_scope}")

    # -----------------------------
    # ERROR CATEGORY (SECOND LLM)
    # -----------------------------
    feedback_category = None
    if syntax_status == "OK" and execution_status == "OK":
        feedback_category = LLM_feedback
    logger.info(f"🏷️ Error category stored: {feedback_category}")
    
    return QueryMetadata(
        schema_id=schema_id,
        schema_source=schema_source,
        user_request=user_request,
        model_name=model_name,
        status=status,
        rows_fetched=rows_fetched,
        error_message=error_message,
        knowledge_scope=knowledge_scope,
        error_type=error_type,
        LLM_feedback=feedback_category
    )

def classify_error(error_message: str | None) -> str | None:
    """
    Classify the error message into one of the following categories:

    - UNKNOWN_COLUMN
    - UNKNOWN_TABLE
    - AMBIGUOUS_COLUMN
    - SYNTAX_ERROR
    - BAD_JOIN
    - GENERIC_RUNTIME_ERROR

    If no error message is provided, return None.

    :param error_message: The error message to classify.
    :type error_message: str | None
    :return: The classified error category, or None if no error message is provided.
    :rtype: str | None
    """
    
    if not error_message:
        logger.info("ℹ️ No error message to classify.")
        return None

    msg = error_message.lower()
    logger.info(f"🔍 Classifying error: {error_message}")

    if "unknown column" in msg:
        logger.info("➡️ Classified as UNKNOWN_COLUMN")
        return "UNKNOWN_COLUMN"
    if "unknown table" in msg:
        logger.info("➡️ Classified as UNKNOWN_TABLE")
        return "UNKNOWN_TABLE"
    if "ambiguous" in msg:
        logger.info("➡️ Classified as AMBIGUOUS_COLUMN")
        return "AMBIGUOUS_COLUMN"
    if "syntax" in msg:
        logger.info("➡️ Classified as SYNTAX_ERROR")
        return "SYNTAX_ERROR"
    if "join" in msg:
        logger.info("➡️ Classified as BAD_JOIN")
        return "BAD_JOIN"

    logger.info("➡️ Classified as GENERIC_RUNTIME_ERROR")
    return "GENERIC_RUNTIME_ERROR"

def detect_structural_issue(sql: str) -> bool:
    sql_upper = sql.upper()
    issue_detected = (
        "SELECT *" in sql_upper
        or ("JOIN" in sql_upper and " ON " not in sql_upper)
        or ("SUM(" in sql_upper and "GROUP BY" not in sql_upper)
    )
    logger.info(f"🔍 Detecting structural issues in SQL: {issue_detected}")
    return issue_detected

def store_query_feedback(
    store: Chroma,
    sql_query: str,
    qm: QueryMetadata
) -> None:
    logger.info(f"💾 Storing feedback for query")

    if qm.status == "SKIP":
        logger.info("ℹ️ Query status is SKIP. Skipping insert.")
        return

    if query_already_exists(store, sql_query, qm.model_name):
        logger.info("ℹ️ Query already present. Skipping insert.")
        return

    doc = Document(
        page_content=qm.to_page_content(sql_query),
        metadata=qm.to_document_metadata()
    )

    store.add_documents([doc])
    logger.info(f"✅ Query stored with status: {qm.status}")

# ------------------------------------------------------------------
# RETRIEVAL
# ------------------------------------------------------------------

def get_context(user_request: str, vector_store: Chroma) -> str:
    """
    Retrieve relevant schema fragments for the user request.
    Uses light query-intent heuristics to tune retrieval depth,
    removes duplicate chunks, and groups output by table.
    """
    logger.info("Retrieving schema context for request: '%s'", truncate_request(user_request))

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

def extract_sql_patterns(sql: str) -> list[str]:
    patterns = []

    if "SELECT *" in sql.upper():
        patterns.append("SELECT *")
        logger.info("🔍 Pattern detected: SELECT *")

    if re.search(r"JOIN\s+\w+\s+ON\s+1\s*=\s*1", sql, re.I):
        patterns.append("cartesian join (ON 1=1)")
        logger.info("🔍 Pattern detected: Cartesian join")

    if "GROUP BY" not in sql.upper() and "SUM(" in sql.upper():
        patterns.append("aggregate without GROUP BY")
        logger.info("🔍 Pattern detected: Aggregate without GROUP BY")

    if re.search(r"WHERE\s+.+\s*=\s*'.*'", sql):
        patterns.append("string literal comparison")
        logger.info("🔍 Pattern detected: String literal comparison")

    return patterns

def build_penalty_section(failed_queries: list[Document]) -> str:
    if not failed_queries:
        logger.info("ℹ️ No failed queries to build penalties.")
        return ""

    lines = []
    lines.append("=== PREVIOUS FAILURES (DO NOT REPEAT THESE PATTERNS) ===")

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

def retrieve_failed_queries(
    user_request: str,
    store: Chroma,
    k: int = 1,
    half_life_days: int = 60
):
    """
    Retrieve recent, relevant failed queries to build negative guidance.
    Prioritizes syntax and structural failures, then fills with schema-specific
    runtime failures when available.
    """
    logger.info(f"🔍 Retrieving failed queries for request: '{user_request}'")

    retrieval_pool = max(10, k * 6)

    syntax_errors = store.similarity_search(
        user_request,
        k=retrieval_pool,
        filter={
            "$and": [
                {"status": "SYNTAX_ERROR"},
                {"knowledge_scope": "SYNTAX"}
            ]
        } # pyright: ignore[reportArgumentType]
    )
    logger.info(f"ℹ️ Found {len(syntax_errors)} syntax error queries.")

    structural_errors = store.similarity_search(
        user_request,
        k=retrieval_pool,
        filter={
            "$and": [
                {"status": {"$ne": "OK"}},
                {"knowledge_scope": "STRUCTURAL"}
            ]
        } # pyright: ignore[reportArgumentType]
    )
    logger.info(f"ℹ️ Found {len(structural_errors)} structural error queries.")

    schema_specific_errors = store.similarity_search(
        user_request,
        k=retrieval_pool,
        filter={
            "$and": [
                {"status": "RUNTIME_ERROR"},
                {"knowledge_scope": "SCHEMA_SPECIFIC"}
            ]
        } # pyright: ignore[reportArgumentType]
    )
    logger.info(f"ℹ️ Found {len(schema_specific_errors)} schema-specific runtime errors.")

    candidates = syntax_errors + structural_errors + schema_specific_errors
    logger.info(f"ℹ️ Total failed query candidates before dedupe: {len(candidates)}")

    # Deduplicate by SQL metadata fallback to raw page content.
    unique_docs = []
    seen = set()
    for doc in candidates:
        metadata = doc.metadata or {}
        key = metadata.get("sql_query") or doc.page_content
        if key in seen:
            continue
        seen.add(key)
        unique_docs.append(doc)

    logger.info(f"ℹ️ Unique failed queries after dedupe: {len(unique_docs)}")

    # Prefer recently-seen failures.
    decayed = apply_time_decay(unique_docs, half_life_days)
    logger.info(f"⏳ Applied time decay with half-life {half_life_days} days.")

    # Keep diversity of failure causes when possible.
    selected = []
    used_error_types = set()
    for doc in decayed:
        error_type = (doc.metadata or {}).get("error_type")
        if error_type and error_type in used_error_types and len(decayed) > k:
            continue
        selected.append(doc)
        if error_type:
            used_error_types.add(error_type)
        if len(selected) == k:
            break

    # Fallback fill if diversity filtering was too restrictive.
    if len(selected) < k:
        selected_keys = {(d.metadata or {}).get("sql_query") or d.page_content for d in selected}
        for doc in decayed:
            key = (doc.metadata or {}).get("sql_query") or doc.page_content
            if key in selected_keys:
                continue
            selected.append(doc)
            selected_keys.add(key)
            if len(selected) == k:
                break

    logger.info(f"✅ Returning {len(selected)} failed queries (requested k={k}).")

    return selected
