
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
    data = store.get(include=["metadatas"])

    if not data or not data.get("metadatas"):
        return False

    for metadata in data["metadatas"]:
        if metadata.get("sql_query") == sql_query:
            return True

    return False

# ------------------------------------------------------------------
# STORE FEEDBACK
# ------------------------------------------------------------------

def classify_error(error_message: str | None) -> str | None:
    if not error_message:
        return None  # niente da classificare

    msg = error_message.lower()

    if "unknown column" in msg:
        return "UNKNOWN_COLUMN"
    if "unknown table" in msg:
        return "UNKNOWN_TABLE"
    if "ambiguous" in msg:
        return "AMBIGUOUS_COLUMN"
    if "syntax" in msg:
        return "SYNTAX_ERROR"
    if "join" in msg:
        return "BAD_JOIN"

    return "GENERIC_RUNTIME_ERROR"

def detect_structural_issue(sql: str) -> bool:
    sql_upper = sql.upper()
    return (
        "SELECT *" in sql_upper
        or ("JOIN" in sql_upper and " ON " not in sql_upper)
        or ("SUM(" in sql_upper and "GROUP BY" not in sql_upper)
    )

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

    status values:
      - "OK"
      - "SYNTAX_ERROR"
      - "WRONG_RESULT"
    """
    if error_message:
        error_type = classify_error(error_message)
    else:
        error_type = None


    page_content = f"""
User request:
{user_request}

Generated SQL query:
{sql_query}

Outcome:
{status}
""".strip()

    
    if status == "SYNTAX_ERROR":
        knowledge_scope = "SYNTAX"
    elif detect_structural_issue(sql_query):
        knowledge_scope = "STRUCTURAL"
    else:
        knowledge_scope = "SCHEMA_SPECIFIC"

        
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
    else:
        metadata["rows_fetched"] = rows_fetched

    doc = Document(
        page_content=page_content,
        metadata=metadata
    )

    store = get_query_store()

    if query_already_exists(store, sql_query):
        print("ℹ️  Query already present in feedback store. Skipping insert.")
        return

    store.add_documents([doc])
    print(f"\n📌 Query stored with status: {status}")
    

def extract_sql_patterns(sql: str) -> list[str]:
    patterns = []

    if "SELECT *" in sql.upper():
        patterns.append("SELECT *")

    if re.search(r"JOIN\s+\w+\s+ON\s+1\s*=\s*1", sql, re.I):
        patterns.append("cartesian join (ON 1=1)")

    if "GROUP BY" not in sql.upper() and "SUM(" in sql.upper():
        patterns.append("aggregate without GROUP BY")

    if re.search(r"WHERE\s+.+\s*=\s*'.*'", sql):
        patterns.append("string literal comparison")

    return patterns


def build_penalty_section(failed_queries: list[Document]) -> str:
    if not failed_queries:
        return ""

    lines = []
    lines.append("=== PREVIOUS FAILURES (DO NOT REPEAT THESE PATTERNS) ===")

    for d in failed_queries:
        error_type = d.metadata.get("error_type")
        content = d.page_content

        lines.append(f"""
--- FAILURE ---
{content}

ERROR TYPE: {error_type}
""")

        # 🔥 Explicit natural language penalties
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

    return "\n".join(lines)



# ------------------------------------------------------------------
# RETRIEVAL
# ------------------------------------------------------------------

def retrieve_successful_queries(
    user_request: str,
    schema_id: str,
    model: str,
    k: int = 3,
    half_life_days: int = 30
):
    store = get_query_store()

    docs = store.similarity_search(
        user_request,
        k=10,  # recupera più del necessario
        filter={
            "$and": [
                {"status": "OK"},
                {"schema_id": schema_id},
                {"knowledge_scope": "SCHEMA_SPECIFIC"},
                {"model": {"$eq": model}}  # esclude modelli troppo vecchi
            ]
        } # pyright: ignore[reportArgumentType]
    )

    docs = apply_time_decay(docs, half_life_days)

    return docs[:k]


def retrieve_failed_queries(
    user_request: str,
    k: int = 3,
    half_life_days: int = 60
):
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

    docs = syntax_errors + structural_errors
    docs = apply_time_decay(docs, half_life_days)

    return docs[:k]