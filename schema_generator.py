import json, os
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_chroma import Chroma
from mysql_linker import extract_schema
from logging_utils import (
    setup_logger,
    print_schema_preview,
    print_vector_store
)
from utils_pkg import (
    extract_json_from_response,
    validate_schema_structure
)

# === CONFIG ===
SCHEMA_FILE = "schema_canonico.json"
DB_DIR = "./vector_store/schema"
COLLECTION_NAME = "schema_canonico"
MODEL_NAME = "gemma3:12b"

# === LOGGING SETUP ===
logger = setup_logger(__name__)

# === LLM ===
model = OllamaLLM(model=MODEL_NAME)

def classify_update(text: str) -> str:
    """Recognizes if the text describes a structural or semantic modification."""

    sql_keywords = ["CREATE TABLE", "ALTER TABLE", "ADD COLUMN", "DROP TABLE", "FOREIGN KEY", "REFERENCES"]
    desc_keywords = ["means", "can assume", "contains", "represents", "describes", "equivalent to"]

    if any(k.lower() in text.lower() for k in sql_keywords):
        return "structural"
    if any(k.lower() in text.lower() for k in desc_keywords):
        return "semantic"

    prompt = """
System: You are an assistant that classifies schema updates.
User: Text provided by the user:
\"\"\"{text}\"\"\"

Question: is this text
(A) a structural modification (addition or change of tables/columns/types)?
(B) a description or semantic note?
Answer only with "A" or "B".
"""
    chain = ChatPromptTemplate.from_template(prompt) | model
    response = chain.invoke({"text": text})

    content = response if isinstance(response, str) else getattr(response, "content", str(response))
    content = content.strip().upper()

    if "A" in content:
        return "structural"
    elif "B" in content:
        return "semantic"
    return "unknown"

def update_schema_with_existing(raw_schema_text: str, current_schema: dict | None = None) -> dict:
    """
    Uses an LLM model to generate or update the canonical schema.
    If a current schema exists, it passes it as context.
    """

    current_schema_text = ""
    if current_schema:
        current_schema_text = f"Current schema:\n{json.dumps(current_schema, indent=2, ensure_ascii=False)}\n\n"

    logger.info("Raw schema text being sent to LLM:")
    logger.info(f"{raw_schema_text}")
    logger.info("="*60)

    template = """
You are an expert database schema analyst.

You have been provided with:
1. The CURRENT canonical schema (JSON format)
2. NEW text describing additional tables or modifications to existing tables

Your task:
- Analyze the new text to identify any NEW tables or MODIFIED columns in existing tables
- Preserve all existing tables and columns from the current schema
- Add only the NEW tables or merge modifications into existing tables
- Return a SINGLE, complete JSON schema that includes both the current schema and the updates

IMPORTANT RULES:
- Do NOT remove any existing tables or columns
- If a table already exists, ADD new columns or UPDATE existing ones (don't duplicate)
- Maintain the same JSON structure: {{"tables": [...], "semantic_notes": [...]}}
- Return ONLY the updated JSON schema, no other text or explanations
- Each table must have: "name", "columns" (array)
- Each column must have: "name", "type", "constraints" (array)

=== CURRENT SCHEMA ===
{current_schema_str}

=== NEW TEXT ===
{new_text}

Return the UPDATED schema JSON:
"""

    chain = ChatPromptTemplate.from_template(template) | model
    response = chain.invoke({
        "current_schema": current_schema_text,
        "raw_schema_text": raw_schema_text
    })

    if isinstance(response, str):
        content = response.strip()
    elif hasattr(response, "content"):
        content = response.content.strip()
    else:
        content = str(response).strip()

    logger.info(f"Raw LLM response: {content}")

    schema = extract_json_from_response(content)
    
    logger.info("Structural schema generated.")

    return schema

def generate_schema_canonical(raw_schema_text: str) -> dict:

    logger.info("Raw schema text being sent to LLM:")
    logger.info(f"{raw_schema_text}")
    logger.info("="*60)

    template = """
You are an expert database schema analyzer. Your task is to convert SQL DDL statements into a structured JSON schema.

IMPORTANT:
- You MUST return ONLY valid JSON.
- The JSON must be syntactically correct (no missing commas, braces, or quotes).
- Every object and array must be properly closed.
- Do NOT include comments, code blocks, or explanations.

Required JSON format:
{{
  "tables": [
    {{
      "name": "table_name",
      "columns": [
        {{"name": "column_name", "type": "SQL_TYPE", "constraints": ["PRIMARY KEY", "NOT NULL", ...]}}
      ]
    }}
  ],
  "semantic_notes": []
}}

Rules:
- Extract table names from CREATE TABLE statements
- Extract column names, types, and constraints
- Map SQL types directly (VARCHAR2 → VARCHAR2, NUMBER → NUMBER, etc.)
- Include constraints like PRIMARY KEY, NOT NULL, UNIQUE, DEFAULT, REFERENCES
- For foreign keys, use "REFERENCES" constraint

SQL DDL to process:
\"\"\"{raw_schema_text}\"\"\"

Return ONLY the JSON object:
"""

    chain = ChatPromptTemplate.from_template(template) | model
    response = chain.invoke({
        "raw_schema_text": raw_schema_text
    })

    # parsing
    if isinstance(response, str):
        content = response.strip()
    elif hasattr(response, "content"):
        content = response.content.strip()
    else:
        content = str(response).strip()

    logger.info(f"Raw LLM response: {content}")

    schema = extract_json_from_response(content)
    
    return schema

def update_schema_with_vector_store(new_text: str) -> dict:
    if not os.path.exists(SCHEMA_FILE):
        raise FileNotFoundError(f"Schema file '{SCHEMA_FILE}' not found. Please create a schema first.")
    
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        current_schema = json.load(f)
    
    logger.info("Current schema loaded:")
    print_schema_preview(current_schema)
    
    logger.info("Updating schema with new information...")
    updated_schema = update_schema_with_existing(new_text, current_schema)
    
    return updated_schema

def build_vector_store(schema_data: dict):
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

    logger.info(f"Created {len(documents)} documents to embed...")

    add_schema = not os.path.exists(DB_DIR)

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=DB_DIR,
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
    
    logger.info(f"Vector store updated and saved in: {DB_DIR}")

    return vector_store

def update_schema(raw_text: str, current_schema: dict):

    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        current_schema = json.load(f)

    logger.info("Current schema:")
    print_schema_preview(current_schema)

    logger.info("Classifying the update...")
    update_type = classify_update(raw_text)
    logger.info(f"Update type classified as: {update_type}")

    if update_type == "semantic":
        logger.info("Processing SEMANTIC update (adding notes to existing schema)...")
        
        if "semantic_notes" not in current_schema:
            current_schema["semantic_notes"] = []
        
        current_schema["semantic_notes"].append(raw_text)
        
        logger.info("Semantic notes added to schema.")
        return current_schema

    else:
        logger.info("Processing STRUCTURAL update (generating new schema)...")
        
        return update_schema_with_existing(raw_text, current_schema)

def acquire_schema_from_text(raw_text: str):

    schema_exists = os.path.exists(SCHEMA_FILE) and os.path.getsize(SCHEMA_FILE) > 0
    vector_store_exists = os.path.exists(DB_DIR) and os.path.isdir(DB_DIR)

    if schema_exists and vector_store_exists:
        logger.info("Existing schema and vector store detected!")
        logger.info(f"Found: {SCHEMA_FILE}")
        logger.info(f"Found: {DB_DIR}")

        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            current_schema = json.load(f)

        return update_schema(raw_text, current_schema)

    logger.info("No existing schema found. Generating from scratch...")
    schema = generate_schema_canonical(raw_text)
    schema["source"] = "text"
    
    logger.info("New schema generated.")
    return schema

def acquire_schema_from_mysql():
    logger.info("Connecting to MySQL database to retrieve schema...")
    schema = extract_schema()
    schema["source"] = "mysql"
    logger.info("Generating schema from database schema...")
    logger.info("New schema generated.")
    return schema

def save_validate_and_build(schema):
    with open(SCHEMA_FILE, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    logger.info(f"Schema saved to '{SCHEMA_FILE}'")
    logger.info("Final schema preview:")
    print_schema_preview(schema)

    if not validate_schema_structure(schema):
        logger.error("Schema validation failed. Invalid structure.")
        return

    logger.info("Schema validation passed.")
    logger.info(f"Found {len(schema.get('tables', []))} tables in schema.")

    logger.info("Building/recreating vector store...")
    vector_store = build_vector_store(schema)
    print_vector_store(vector_store) # pyright: ignore[reportArgumentType]

    logger.info("Vector store built successfully!")
    logger.info("Workflow completed successfully!")

def main():
    """Main function to handle the interactive workflow."""
    print("🤖 Interactive canonical schema management (phase 1)")
    print("\nChoose how to acquire the database schema:")
    print("1️⃣  via text input (DDL statements or descriptions)")
    print("2️⃣  via MySQL database connection")

    method = input("\n👉 Your choice: ").strip()

    if method not in {"1", "2"}:
        logger.error("Invalid method choice. Exiting.")
        exit(1)

    while True:
        if method == "1":
            print("👉 Paste below the text that describes or updates the schema (press ENTER twice to finish):\n")

            lines = []
            while True:
                try:
                    line = input()
                    if line.strip() == "":
                        break
                    lines.append(line)
                except EOFError:
                    break

            raw_text = "\n".join(lines).strip()
            
            if not raw_text:
                logger.error("No text provided.")
                break
            else:
                schema = acquire_schema_from_text(raw_text)
        else:
            schema = acquire_schema_from_mysql()

        if schema:
            save_validate_and_build(schema)

        if method != "1":
            break

        print("\nChoose an option:")
        print("0️⃣  Exit")
        print("1️⃣  Provide more text to update the schema")

        choice = input("\n👉 Your choice: ").strip()
        if choice == "0":
            print("👋 Exiting. Goodbye!")
            break

# === ENTRY POINT ===
if __name__ == "__main__":
    main()