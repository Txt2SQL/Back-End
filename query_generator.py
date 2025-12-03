import os
import json
import sys
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# === CONFIG ===
DB_DIR = "./chroma_langchain_db"
COLLECTION_NAME = "schema_canonico"
SCHEMA_FILE = "schema_canonico.json"

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

# === FUNCTION: VECTOR STORE CONSTRUCTION / UPDATE ===
def build_vector_store(schema_data: dict):
    """
    Builds or updates the vector store (RAG) starting from the canonical schema.
    """
    embeddings = OllamaEmbeddings(model="mxbai-embed-large")

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

    print(f"\n📄 Created {len(documents)} documents to embed...")

    add_schema = not os.path.exists(DB_DIR)

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=DB_DIR,
        embedding_function=embeddings,
    )

    if add_schema:
        print("🧠 Creating a new vector store...")
        vector_store.add_documents(documents=documents, ids=ids)
    else:
        print("🔄 Updating existing vector store...")
        # For updates, we need to handle existing documents
        existing_ids = vector_store.get()["ids"]
        if existing_ids:
            vector_store.delete(ids=existing_ids)
        vector_store.add_documents(documents=documents, ids=ids)
    
    vector_store.persist()
    print("✅ Vector store updated and saved in:", DB_DIR)

    # Confirmation print
    print("\n🔎 Current content of the vector store:")
    all_docs = vector_store.get(include=["metadatas", "documents"])

    for i, (doc_text, meta) in enumerate(zip(all_docs["documents"], all_docs["metadatas"])):  # type: ignore
        print(f"\n🧱 Document #{i+1}")
        print("📘 Table:", meta.get("table", "N/A"))
        print("📄 Content:")
        print(doc_text)
        print("-" * 50)

    return vector_store


# === FUNCTION: GENERATE SQL QUERY ===
def generate_sql_query(user_request: str, schema_data: dict | None = None) -> str:
    """
    Uses the canonical schema (if available) or infers the schema from the request.
    """
    schema_context = ""
    
    if schema_data:
        # If schema exists → use RAG
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
    else:
        # If no schema exists → special prompt for schema inference
        print("⚠️ No canonical schema available! I will try to deduce the schema from the request...")
        template = f"""
You are an expert SQL database assistant.
You don't have access to a defined schema, but you can deduce the database structure
from the user's request.

CRITICAL RULES:
- Analyze the request semantically and hypothesize the necessary tables and columns.
- Build a coherent SQL query based on what you deduced.
- Do NOT add WHERE clauses or conditions unless explicitly requested.
- Return **only the SQL query**, without comments or additional text.

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

    # Load schema if available
    schema = None
    if os.path.exists(SCHEMA_FILE) and os.path.getsize(SCHEMA_FILE) > 0:
        try:
            with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
                schema = json.load(f)
            
            if validate_schema_structure(schema):
                print("📂 schema_canonico.json file loaded and validated.")
                print(f"📊 Found {len(schema.get('tables', []))} tables in schema.")
                
                # If schema exists, build/update RAG
                print("\n🔨 Building/updating RAG (vector store)...")
                build_vector_store(schema)
            else:
                print("❌ Schema file has invalid structure. Proceeding without schema.")
                schema = None
                
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing schema file: {e}")
            schema = None
    else:
        schema = None
        print("⚠️ No canonical schema found or file empty.")

    # User request
    user_request = input("\n👉 Enter a request in natural language: ")

    print("\n🔍 Generating query...")
    sql = generate_sql_query(user_request, schema)

    print("\n💡 Generated SQL query:\n")
    print(sql)
    print("\n" + "="*60)

    # Show explanation
    if schema:
        print("📋 Schema used for generation:")
        relevant_tables = []
        for table in schema.get("tables", []):
            table_name = table.get("name", "")
            if table_name.lower() in sql.lower():
                relevant_tables.append(table_name)
        if relevant_tables:
            print(f"   Tables: {', '.join(relevant_tables)}")
        else:
            print("   (No specific tables detected in query)")


def generate_query(user_request: str, model_name: str = "codellama:13b") -> str:
    """
    Wrapper for API usage: loads schema, updates RAG and generates SQL query.
    
    Args:
        user_request: The natural language request
        model_name: The Ollama model to use (default: "codellama:13b")
    """
    global model
    model = OllamaLLM(model=model_name)
    
    if os.path.exists(SCHEMA_FILE) and os.path.getsize(SCHEMA_FILE) > 0:
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            schema = json.load(f)
    else:
        schema = None

    if schema and validate_schema_structure(schema):
        build_vector_store(schema)

    sql = generate_sql_query(user_request, schema)
    return sql