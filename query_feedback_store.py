
import math, time, re
from pydoc import doc
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# === CONFIG ===
QUERY_COLLECTION_NAME = "query_feedback"
QUERY_DB_DIR = "./vector_store/queries"
EMBEDDING_MODEL = "mxbai-embed-large"

# === EMBEDDINGS ===
_embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

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

def get_query_store() -> Chroma:
    """
    Returns (and creates if not exists) the Chroma vector store
    used to persist query feedback history.
    """
    return Chroma(
        collection_name=QUERY_COLLECTION_NAME,
        persist_directory=QUERY_DB_DIR,
        embedding_function=_embeddings,
    )

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
    print(f"🔍 Checking if query exists: {sql_query}\n")
    data = store.get(include=["metadatas"])

    if not data or not data.get("metadatas"):
        print("ℹ️ No metadata found in store.\n")
        return False

    for metadata in data["metadatas"]:
        if metadata.get("sql_query") == sql_query:
            print("✅ Query already exists in store.\n")
            return True

    print("❌ Query does not exist in store.\n")
    return False

# ------------------------------------------------------------------
# STORE FEEDBACK
# ------------------------------------------------------------------

def classify_error(error_message: str | None) -> str | None:
    if not error_message:
        print("ℹ️ No error message to classify.\n")
        return None

    msg = error_message.lower()
    print(f"🔍 Classifying error: {error_message}\n")

    if "unknown column" in msg:
        print("➡️ Classified as UNKNOWN_COLUMN\n")
        return "UNKNOWN_COLUMN"
    if "unknown table" in msg:
        print("➡️ Classified as UNKNOWN_TABLE\n")
        return "UNKNOWN_TABLE"
    if "ambiguous" in msg:
        print("➡️ Classified as AMBIGUOUS_COLUMN\n")
        return "AMBIGUOUS_COLUMN"
    if "syntax" in msg:
        print("➡️ Classified as SYNTAX_ERROR\n")
        return "SYNTAX_ERROR"
    if "join" in msg:
        print("➡️ Classified as BAD_JOIN\n")
        return "BAD_JOIN"

    print("➡️ Classified as GENERIC_RUNTIME_ERROR\n")
    return "GENERIC_RUNTIME_ERROR"

def detect_structural_issue(sql: str) -> bool:
    sql_upper = sql.upper()
    issue_detected = (
        "SELECT *" in sql_upper
        or ("JOIN" in sql_upper and " ON " not in sql_upper)
        or ("SUM(" in sql_upper and "GROUP BY" not in sql_upper)
    )
    print(f"🔍 Detecting structural issues in SQL: {issue_detected}\n")
    return issue_detected

def store_query_feedback(
    schema_id: str,
    model_name: str,
    user_request: str,
    sql_query: str,
    status: str,
    rows_fetched: int | None = None,
    error_message: str | None = None
) -> None:
    """
    Stores a (request, sql, outcome) tuple into the query feedback vector store.
    """
    print(f"💾 Storing feedback for query: {sql_query}\n")
    
    if error_message == "Query failed syntactic check":
        error_type = "SYNTAX"
    elif error_message:
        error_type = classify_error(error_message)
    else:
        error_type = None

    page_content = f"""
User request:
{user_request}

Generated SQL query:
{sql_query}

Outcome: {status}
""".strip()

    if status == "SYNTAX_ERROR":
        knowledge_scope = "SYNTAX"
    elif detect_structural_issue(sql_query):
        knowledge_scope = "STRUCTURAL"
    else:
        knowledge_scope = "SCHEMA_SPECIFIC"

    print(f"📌 Knowledge scope determined: {knowledge_scope}\n")

    metadata = {
        "schema_id": schema_id,
        "knowledge_scope": knowledge_scope,
        "status": status,
        "model": model_name,
        "timestamp": time.time(),
        "sql_query": sql_query,
    }

    if error_message:
        metadata["error_type"] = error_type
        print(f"⚠️ Error type recorded: {error_type}\n")
    else:
        metadata["rows_fetched"] = rows_fetched
        print(f"ℹ️ Rows fetched: {rows_fetched}\n")

    doc = Document(
        page_content=page_content,
        metadata=metadata
    )

    store = get_query_store()

    if query_already_exists(store, sql_query):
        print("ℹ️ Query already present. Skipping insert.\n")
        return

    store.add_documents([doc])
    print(f"✅ Query stored with status: {status}\n")

def extract_sql_patterns(sql: str) -> list[str]:
    patterns = []

    if "SELECT *" in sql.upper():
        patterns.append("SELECT *")
        print("🔍 Pattern detected: SELECT *\n")

    if re.search(r"JOIN\s+\w+\s+ON\s+1\s*=\s*1", sql, re.I):
        patterns.append("cartesian join (ON 1=1)")
        print("🔍 Pattern detected: Cartesian join\n")

    if "GROUP BY" not in sql.upper() and "SUM(" in sql.upper():
        patterns.append("aggregate without GROUP BY")
        print("🔍 Pattern detected: Aggregate without GROUP BY\n")

    if re.search(r"WHERE\s+.+\s*=\s*'.*'", sql):
        patterns.append("string literal comparison")
        print("🔍 Pattern detected: String literal comparison\n")

    return patterns

def build_penalty_section(failed_queries: list[Document]) -> str:
    if not failed_queries:
        print("ℹ️ No failed queries to build penalties.\n")
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

    print(f"📋 Penalty section built for {len(failed_queries)} failures.\n")
    return "\n".join(lines)


# ------------------------------------------------------------------
# RETRIEVAL
# ------------------------------------------------------------------

# def retrieve_successful_queries(
#     user_request: str,
#     schema_id: str,
#     model: str,
#     k: int = 3,
#     half_life_days: int = 30
# ):
#     print(f"🔍 Retrieving successful queries for request: '{user_request}'\n")
#     store = get_query_store()

#     docs = store.similarity_search(
#         user_request,
#         k=10,  # retrieve more than needed
#         filter={
#             "$and": [
#                 {"status": "OK"},
#                 {"schema_id": schema_id},
#                 {"knowledge_scope": "SCHEMA_SPECIFIC"},
#                 {"model": {"$eq": model}}  # exclude old models
#             ]
#         } # pyright: ignore[reportArgumentType]
#     )
#     print(f"ℹ️ Found {len(docs)} candidate successful queries before decay.\n")

#     docs = apply_time_decay(docs, half_life_days)
#     print(f"⏳ Applied time decay with half-life {half_life_days} days.\n")
#     print(f"✅ Returning top {k} successful queries.\n")

#     return docs[:k]


def retrieve_failed_queries(
    user_request: str,
    k: int = 1,
    half_life_days: int = 60
):
    print(f"🔍 Retrieving failed queries for request: '{user_request}'\n")
    store = get_query_store()

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
    print(f"ℹ️ Found {len(syntax_errors)} syntax error queries.\n")

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
    print(f"ℹ️ Found {len(structural_errors)} structural error queries.\n")

    docs = syntax_errors + structural_errors
    print(f"ℹ️ Total failed queries before decay: {len(docs)}\n")

    docs = apply_time_decay(docs, half_life_days)
    print(f"⏳ Applied time decay with half-life {half_life_days} days.\n")
    print(f"✅ Returning top {k} failed queries.\n")

    return docs[:k]