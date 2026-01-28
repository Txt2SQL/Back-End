import math, time, re
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from logging_utils import setup_logger
from metadata import UIMetadata

# === CONFIG ===
QUERY_COLLECTION_NAME = "query_feedback"
QUERY_DB_DIR = "./vector_store/queries"
EMBEDDING_MODEL = "mxbai-embed-large"

# === LOGGING SETUP ===
logger = setup_logger(__name__)

def print_query_vector_store(store: Chroma):
    """
    Prints the 15 most recent documents stored in the query feedback vector store.
    Useful for debugging and inspection.
    """
    print("\n📦 QUERY FEEDBACK VECTOR STORE CONTENT (15 Most Recent)\n")

    # Recupera TUTTI i documenti
    data = store.get()

    if not data or not data.get("documents"):
        print("\n⚠️ Query vector store is empty.")
        return

    # Crea lista di tuple (doc, metadata) e ordina per timestamp decrescente
    docs_with_metadata = list(zip(data["documents"], data["metadatas"]))
    docs_with_metadata.sort(
        key=lambda x: x[1].get("timestamp", 0),
        reverse=True
    )
    
    # Prendi solo i 15 più recenti
    docs_with_metadata = docs_with_metadata[:15]

    for idx, (doc, metadata) in enumerate(docs_with_metadata, start=1):
        print(f"--- Entry #{idx} ------------------------------")
        print(doc)
        print("\nMetadata:")
        for k, v in metadata.items():
            if k != "sql_query":
                print(f"  {k}: {v}")
        print("---------------------------------------------\n")

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

def query_already_exists(store: Chroma, sql_query: str) -> bool:
    """
    Checks if a SQL query already exists in the vector store.
    Comparison is done on metadata["sql_query"].
    """
    logger.info(f"🔍 Checking if query exists: {sql_query}")
    
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

# ------------------------------------------------------------------
# STORE FEEDBACK
# ------------------------------------------------------------------

def classify_error(error_message: str | None) -> str | None:
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
    qm: UIMetadata
) -> None:
    """
    Stores a (request, sql, outcome) tuple into the query feedback vector store.
    """
    logger.info(f"💾 Storing feedback for query: {sql_query}")

    if qm.error_message == "Query failed syntactic check":
        error_type = "SYNTAX"
    elif qm.error_message:
        error_type = classify_error(qm.error_message)
    else:
        error_type = None

    page_content = f"""
User request:
{qm.user_request}

Generated SQL query:
{sql_query}

Outcome: {qm.status}
""".strip()

    if qm.status == "SYNTAX_ERROR":
        knowledge_scope = "SYNTAX"
    elif detect_structural_issue(sql_query):
        knowledge_scope = "STRUCTURAL"
    else:
        knowledge_scope = "SCHEMA_SPECIFIC"

    logger.info(f"📌 Knowledge scope determined: {knowledge_scope}")

    metadata = {
        "schema_id": qm.schema_id,
        "knowledge_scope": knowledge_scope,
        "status": qm.status,
        "model": qm.model_name,
        "timestamp": time.time(),
        "sql_query": sql_query,
    }

    if qm.error_message:
        metadata["error_type"] = error_type
        logger.info(f"⚠️ Error type recorded: {error_type}")
    else:
        metadata["rows_fetched"] = qm.rows_fetched
        logger.info(f"ℹ️ Rows fetched: {qm.rows_fetched}")

    doc = Document(
        page_content=page_content,
        metadata=metadata
    )

    if query_already_exists(store, sql_query):
        logger.info("ℹ️ Query already present. Skipping insert.")
        return

    store.add_documents([doc])
    logger.info(f"✅ Query stored with status: {qm.status}")

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

# ------------------------------------------------------------------
# RETRIEVAL
# ------------------------------------------------------------------

def retrieve_failed_queries(
    user_request: str,
    store: Chroma,
    k: int = 1,
    half_life_days: int = 60
):
    logger.info(f"🔍 Retrieving failed queries for request: '{user_request}'")

    syntax_errors = store.similarity_search(
        user_request,
        k=10,
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
        k=10,
        filter={
            "$and": [
                {"status": {"$ne": "OK"}},
                {"knowledge_scope": "STRUCTURAL"}
            ]
        } # pyright: ignore[reportArgumentType]
    )
    logger.info(f"ℹ️ Found {len(structural_errors)} structural error queries.")

    docs = syntax_errors + structural_errors
    logger.info(f"ℹ️ Total failed queries before decay: {len(docs)}")

    docs = apply_time_decay(docs, half_life_days)
    logger.info(f"⏳ Applied time decay with half-life {half_life_days} days.")
    logger.info(f"✅ Returning top {k} failed queries.")

    return docs[:k]