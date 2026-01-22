from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import re

# === CONFIG ===
QUERY_COLLECTION_NAME = "query_feedback"
QUERY_DB_DIR = "./vector_store/queries"
EMBEDDING_MODEL = "mxbai-embed-large"

# === EMBEDDINGS ===
_embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

def print_query_vector_store():
    """
    Prints all documents stored in the query feedback vector store.
    Useful for debugging and inspection.
    """
    print("\n📦 QUERY FEEDBACK VECTOR STORE CONTENT\n")

    embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    store = Chroma(
        collection_name=QUERY_COLLECTION_NAME,
        persist_directory=QUERY_DB_DIR,
        embedding_function=embeddings,
    )

    # Recupera TUTTI i documenti
    data = store.get()

    if not data or not data.get("documents"):
        print("⚠️ Query vector store is empty.")
        return

    for idx, (doc, metadata) in enumerate(
        zip(data["documents"], data["metadatas"]), start=1
    ):
        print(f"--- Entry #{idx} ------------------------------")
        print(doc)
        print("\nMetadata:")
        for k, v in metadata.items():
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


# ------------------------------------------------------------------
# STORE FEEDBACK
# ------------------------------------------------------------------

def store_query_feedback(
    user_request: str,
    sql_query: str,
    status: str,
    model_name: str,
    error_message: str | None = None
) -> None:
    """
    Stores a (request, sql, outcome) tuple into the query feedback vector store.

    status values:
      - "OK"
      - "SYNTAX_ERROR"
      - "WRONG_RESULT"
    """

    page_content = f"""
User request:
{user_request}

Generated SQL query:
{sql_query}
""".strip()

    metadata = {
        "status": status,
        "model": model_name,
    }

    if error_message:
        metadata["error_message"] = error_message

    doc = Document(
        page_content=page_content,
        metadata=metadata
    )

    store = get_query_store()
    store.add_documents([doc])
    

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


def build_penalty_section(failed_docs):
    forbidden = set()

    for doc in failed_docs:
        sql = doc.page_content.split("SQL generata:")[-1]
        patterns = extract_sql_patterns(sql)
        forbidden.update(patterns)

    if not forbidden:
        return ""

    rules = "\n".join(f"- {p}" for p in forbidden)

    return f"""
AVOID THESE PATTERNS:
The following SQL patterns caused errors or incorrect results in similar past requests.
DO NOT use them.

{rules}
"""


# ------------------------------------------------------------------
# RETRIEVAL
# ------------------------------------------------------------------

def retrieve_successful_queries(user_request: str, k: int = 3):
    """
    Retrieves past successful (OK) SQL queries similar to the user request.
    """
    store = get_query_store()
    return store.similarity_search(
        user_request,
        k=k,
        filter={"status": "OK"}
    )


def retrieve_failed_queries(user_request: str, k: int = 3):
    """
    Retrieves past failed SQL queries (syntax or semantic errors)
    similar to the user request.
    """
    store = get_query_store()
    syntax_errors = store.similarity_search(
        user_request,
        k=k,
        filter={"status": "SYNTAX_ERROR"}
    )
    wrong_results = store.similarity_search(
        user_request,
        k=k,
        filter={"status": "WRONG_RESULT"}
    )
    return syntax_errors + wrong_results
