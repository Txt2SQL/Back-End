import os
import json
import sys
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# === CONFIG ===
COLLECTION_NAME = "schema_canonico"
DB_DIR = "./chroma_langchain_db"

# === AVAILABLE MODELS ===
AVAILABLE_MODELS = {
    "1": "codellama:13b",
    "2": "mistral",
    "3": "sqlcoder:7b"
}

# === LLM MODEL ===
def select_model() -> str:
    """
    Prompts user to select an Ollama model from available options.
    Returns the selected model name.
    """
    print("\n🤖 Available Ollama models:")
    for key, model_name in AVAILABLE_MODELS.items():
        print(f"   {key}. {model_name}")
    
    while True:
        choice = input("\n👉 Select a model (1-3): ").strip()
        if choice in AVAILABLE_MODELS:
            selected = AVAILABLE_MODELS[choice]
            print(f"✅ Selected model: {selected}\n")
            return selected
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

model = None  # Will be initialized based on user selection


# === FUNCTION: GENERATE SQL QUERY ===
def generate_sql_query(user_request: str) -> str:
    """
    Uses the canonical schema (if available) or infers the schema from the request.
    """
    schema_context = ""
    
    embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=DB_DIR,
        embedding_function=embeddings,
    )
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    # Use the new invoke method instead of deprecated get_relevant_documents
    relevant_docs = retriever.invoke(user_request)

    schema_context = "\n\n".join(
        [f"Table: {d.metadata.get('table')}\n{d.page_content}" for d in relevant_docs]
    )

    # 🆕 Display the schema context content
    print("\n==================== 📘 SCHEMA CONTEXT ====================")
    if schema_context.strip():
        print(schema_context)
    else:
        print("(No schema context found — retriever returned empty results)")
    print("===========================================================\n")

    template = f"""
You are an expert SQL database assistant.
You will be provided with:
1. The partial description of the database schema (only the relevant tables)
2. The user's request in natural language.

Your task is to return a **single SQL query** that satisfies the request,
using the provided tables and columns.

CRITICAL RULES:
- Use ONLY the tables and columns present in the schema provided.
- Do NOT invent field or table names that don't exist.
- Do NOT add WHERE clauses or conditions unless explicitly requested.
- Do NOT join tables unless necessary for the request.
- Return **only the SQL query**, without comments or additional text.
- Make the query as simple as possible to satisfy the request.

=== SCHEMA ===
{schema_context}

=== REQUEST ===
{user_request}

SQL QUERY:
"""

    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model

    response = chain.invoke({
        "schema_context": schema_context,
        "user_request": user_request
    })

    if isinstance(response, str):
        sql_query = response.strip()
    elif hasattr(response, "content"):
        sql_query = response.content.strip()
    else:
        sql_query = str(response).strip()

    # Clean up the query - remove any markdown code blocks
    if sql_query.startswith("```sql"):
        sql_query = sql_query[6:]
    if sql_query.endswith("```"):
        sql_query = sql_query[:-3]
    sql_query = sql_query.strip()

    return sql_query


# === FUNCTION: VALIDATE SCHEMA ===
def validate_schema_structure(schema: dict) -> bool:
    """Validate that the schema has the expected structure"""
    if not isinstance(schema, dict):
        return False
    if "tables" not in schema:
        return False
    if not isinstance(schema["tables"], list):
        return False
    
    # Check if tables have proper structure
    for table in schema["tables"]:
        if not isinstance(table, dict):
            return False
        if "name" not in table:
            return False
        if "columns" not in table or not isinstance(table["columns"], list):
            return False
    
    return True


# === MAIN ===
if __name__ == "__main__":
    print("🤖 SQL query generator based on RAG and LLM\n")

    # Select model at runtime
    selected_model_name = select_model()
    model = OllamaLLM(model=selected_model_name)

    # User request
    user_request = input("\n👉 Enter a request in natural language: ")

    print("\n🔍 Generating query...")
    sql = generate_sql_query(user_request)

    print("\n💡 Generated SQL query:\n")
    print(sql)
    print("\n" + "="*60)