import sys, sqlglot, json, hashlib
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from query_feedback_store import (
    store_query_feedback,
    retrieve_failed_queries,
    retrieve_successful_queries,
    build_penalty_section,
    print_query_vector_store
)
from utils_pkg  import (
    print_schema_context
)

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

def compute_schema_id() -> str:
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema_dict = json.load(f)
    normalized = json.dumps(schema_dict, sort_keys=True)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]

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

model = None


def generate_sql_query(user_request: str, schema_id: str) -> str:
    """
    Generates a SQL query using:
    - canonical schema RAG
    - past successful queries (positive examples)
    - past failed queries (negative / penalized patterns)
    """

    # ------------------------------------------------------------------
    # 1. SCHEMA RETRIEVAL (RAG)
    # ------------------------------------------------------------------
    embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    vector_store = Chroma(
        collection_name=SCHEMA_COLLECTION_NAME,
        persist_directory=DBS_DIR,
        embedding_function=embeddings,
    )

    retriever = vector_store.as_retriever(search_kwargs={"k": 3})
    relevant_docs = retriever.invoke(user_request)

    schema_context = "\n\n".join(
        [f"Table: {d.metadata.get('table')}\n{d.page_content}" for d in relevant_docs]
    )

    print_schema_context(schema_context)

    # ------------------------------------------------------------------
    # 2. QUERY FEEDBACK RETRIEVAL
    # ------------------------------------------------------------------
    # Positive examples
    similar_queries = retrieve_successful_queries(
        user_request,
        schema_id=schema_id,
        k=3
    )
    past_examples = "\n\n".join(d.page_content for d in similar_queries)

    examples_section = ""
    if past_examples.strip():
        examples_section = f"""
=== PAST SUCCESSFUL EXAMPLES ===
{past_examples}
"""

    # Negative examples → pattern penalization
    failed_queries = retrieve_failed_queries(user_request, k=3)
    penalty_section = build_penalty_section(failed_queries)

    # ------------------------------------------------------------------
    # 3. PROMPT
    # ------------------------------------------------------------------
    template = f"""
You are an expert SQL database assistant.
You will be provided with:
1. The partial description of the database schema (only the relevant tables)
2. The user's request in natural language.
3. Examples of previous successful SQL queries

Your task is to return a **single SQL query** that satisfies the request,
using the provided tables and columns.

CRITICAL RULES:
- Use ONLY the tables and columns present in the schema provided.
- Do NOT invent field or table names that don't exist.
- Do NOT add WHERE clauses or conditions unless explicitly requested.
- Do NOT join tables unless necessary for the request.
- Return **only the SQL query**, without comments or additional text.
- Make the query as simple as possible to satisfy the request.

{penalty_section}

=== SCHEMA ===
{schema_context}

=== REQUEST ===
{user_request}

{examples_section}

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

    return sql_query


# === MAIN ===
if __name__ == "__main__":
    print("🤖 SQL query generator based on RAG and LLM\n")

    while True:
        print("\nChoose an option:")
        print("1️⃣  Generate SQL query")
        print("2️⃣  Show query feedback vector store")
        print("0️⃣  Exit")

        choice = input("\n👉 Your choice: ").strip()

        if choice == "0":
            print("👋 Bye!")
            break

        elif choice == "2":
            print_query_vector_store()

        elif choice == "1":
            # Select model at runtime
            selected_model_name = select_model()
            model = OllamaLLM(model=selected_model_name)

            # User request
            user_request = input("\n👉 Enter a request in natural language: ")
            schema_id = compute_schema_id()

            print("\n🔍 Generating query...")
            sql = generate_sql_query(user_request, schema_id)

            print("\n💡 Generated SQL query:\n")
            print(sql)
            print("\n" + "=" * 60)

            # Syntax validation
            status = validate_sql_syntax(sql)
            error_message = None if status == "OK" else "Query failed syntactic check"

            # Store feedback
            store_query_feedback(
                user_request=user_request,
                sql_query=sql,
                status=status,
                model_name=selected_model_name,
                error_message=error_message,
                schema_id=schema_id
            )

            print(f"\n📌 Query stored with status: {status}")

        else:
            print("❌ Invalid option. Try again.")