import json
import os
import re
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_chroma import Chroma
from utils_pkg  import (
    print_schema_preview,
    extract_json_from_response,
    create_schema_manually,
    validate_schema_structure
)

# === CONFIG ===
SCHEMA_FILE = "schema_canonico.json"
DB_DIR = "./vector_store"
COLLECTION_NAME = "schema_canonico"
MODEL_NAME = "gemma3:12b"

# === LLM ===
model = OllamaLLM(model=MODEL_NAME)
    
def extract_json_from_response(content: str) -> dict:
    """Extract JSON from LLM response using multiple methods"""
    
    # Method 1: Direct JSON parsing
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Method 2: Extract JSON between curly braces
    try:
        # Find the first { and last }
        start = content.find('{')
        end = content.rfind('}') + 1
        
        if start >= 0 and end > start:
            json_str = content[start:end]
            # Clean up common issues
            json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
            json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays
            return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Method 3: Look for code blocks
    try:
        json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
    except (json.JSONDecodeError, AttributeError):
        pass
    
    # Method 4: Manual parsing as fallback
    print("⚠️ Could not parse JSON automatically, creating schema manually...")
    return create_schema_manually(content)

def create_schema_manually(content: str) -> dict:
    """Create a basic schema structure manually as fallback"""
    schema = {
        "tables": [],
        "semantic_notes": ["Schema generated manually due to parsing issues"]
    }
    
    # Simple table detection from CREATE TABLE statements
    create_table_pattern = r'CREATE TABLE\s+(\w+)\s*\('
    tables = re.findall(create_table_pattern, content, re.IGNORECASE)
    
    for table_name in tables:
        schema["tables"].append({
            "name": table_name,
            "columns": []
        })
    
    print(f"🛠️  Manually created schema with {len(tables)} tables")
    return schema

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

# === 1️⃣ Semantic classification function ===
def classify_update(text: str) -> str:
    """Recognizes if the text describes a structural or semantic modification."""

    sql_keywords = ["CREATE TABLE", "ALTER TABLE", "ADD COLUMN", "DROP TABLE", "FOREIGN KEY", "REFERENCES"]
    desc_keywords = ["means", "can assume", "contains", "represents", "describes", "equivalent to"]

    # Fast heuristics
    if any(k.lower() in text.lower() for k in sql_keywords):
        return "structural"
    if any(k.lower() in text.lower() for k in desc_keywords):
        return "semantic"

    # Fallback via LLM
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


# === 2️⃣ Function to generate/update canonical schema ===
def update_schema_with_existing(raw_schema_text: str, current_schema: dict | None = None) -> dict:
    """
    Uses an LLM model to generate or update the canonical schema.
    If a current schema exists, it passes it as context.
    """

    current_schema_text = ""
    if current_schema:
        current_schema_text = f"Current schema:\n{json.dumps(current_schema, indent=2, ensure_ascii=False)}\n\n"

    print("\n📄 Raw schema text being sent to LLM:\n")
    print(raw_schema_text)
    print("\n" + "="*60 + "\n")

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

    # parsing
    if isinstance(response, str):
        content = response.strip()
    elif hasattr(response, "content"):
        content = response.content.strip()
    else:
        content = str(response).strip()

    print(f"📄 Raw LLM response: {content}")  # Debug output

    # Try to extract JSON with multiple methods
    schema = extract_json_from_response(content)
    
    print("✅ Structural schema generated.")

    return schema

# === 2️⃣ Function to generate/update canonical schema ===
def generate_schema_canonical(raw_schema_text: str) -> dict:
    """
    Uses an LLM model to generate the canonical schema.
    """

    print("\n📄 Raw schema text being sent to LLM:\n")
    print(raw_schema_text)
    print("\n" + "="*60 + "\n")

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
- If no current schema, create new one
- If current schema exists, update it with new tables/columns

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

    print(f"📄 Raw LLM response: {content}")  # Debug output

    # Try to extract JSON with multiple methods
    schema = extract_json_from_response(content)
    
    return schema

# === FUNCTION: COMPLETE SCHEMA UPDATE WORKFLOW ===
def update_schema_with_vector_store(new_text: str) -> dict:
    """
    Main orchestrator function that handles schema updates when a vector store exists.
    
    Workflow:
    1. Load the current schema from file
    2. Generate an updated schema using LLM prompt with current schema + new text
    3. Save the updated schema to file
    4. Validate the schema structure
    5. Recreate the vector store
    
    Returns the updated schema.
    """
    # Step 1: Load current schema
    if not os.path.exists(SCHEMA_FILE):
        raise FileNotFoundError(f"Schema file '{SCHEMA_FILE}' not found. Please create a schema first.")
    
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        current_schema = json.load(f)
    
    print("\n📘 Current schema loaded:")
    print_schema_preview(current_schema)
    
    # Step 2: Generate updated schema
    print("\n🔄 Updating schema with new information...")
    updated_schema = update_schema_with_existing(new_text, current_schema)
    
    return updated_schema

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

def update_schema(raw_text: str, current_schema: dict) :
    print("\n✅ Existing schema and vector store detected!")
    print(f"📂 Found: {SCHEMA_FILE}")
    print(f"📂 Found: {DB_DIR}\n")

    # Load current schema
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        current_schema = json.load(f)

    print("📘 Current schema:")
    print_schema_preview(current_schema)

    # === CLASSIFY THE UPDATE ===
    print("\n🔍 Classifying the update...")
    update_type = classify_update(raw_text)
    print(f"📊 Update type classified as: {update_type}\n")

    if update_type == "semantic":
        # === SEMANTIC UPDATE: Add notes to existing schema ===
        print("📝 Processing SEMANTIC update (adding notes to existing schema)...")
        
        # Add new semantic notes to the existing schema
        if "semantic_notes" not in current_schema:
            current_schema["semantic_notes"] = []
        
        current_schema["semantic_notes"].append(raw_text)
        
        print("✅ Semantic notes added to schema.")
        return current_schema

    else:  # structural update
        # === STRUCTURAL UPDATE: Generate new schema ===
        print("🔧 Processing STRUCTURAL update (generating new schema)...")
        
        return update_schema_with_existing(raw_text, current_schema)    

# === MAIN ===
if __name__ == "__main__":
    print("🤖 Interactive canonical schema management (phase 1)")
    print("👉 Paste below the text that describes or updates the schema (press ENTER twice to finish):\n")

    # Reads multiline input
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == "":
                break
            lines.append(line)
        except EOFError:
            break

    raw_text = "\n".join(lines)

    if not raw_text.strip():
        print("❌ No text provided. Exiting.")
        exit()

    # === CHECK IF SCHEMA FILE AND VECTOR STORE EXIST ===
    schema_exists = os.path.exists(SCHEMA_FILE) and os.path.getsize(SCHEMA_FILE) > 0
    vector_store_exists = os.path.exists(DB_DIR) and os.path.isdir(DB_DIR)

    if schema_exists and vector_store_exists:
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            current_schema = json.load(f)
        schema = update_schema(raw_text, current_schema)

    else:
        # === NO EXISTING SCHEMA/VECTOR STORE: Generate from scratch ===
        print("\n❌ No existing schema or vector store found.")
        print("🆕 Generating schema from scratch...\n")
        
        schema = generate_schema_canonical(raw_text)
        print("✅ New schema generated.")

    # === SAVE AND VALIDATE SCHEMA ===
    with open(SCHEMA_FILE, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Schema saved to '{SCHEMA_FILE}'")

    print("\n📘 Final schema preview:")
    print_schema_preview(schema)
    
    if validate_schema_structure(schema):
        print("\n✅ Schema validation passed.")
        print(f"📊 Found {len(schema.get('tables', []))} tables in schema.")
        
        # Build/recreate vector store
        print("\n🔨 Building/recreating vector store...")
        build_vector_store(schema)
        print("\n✅ Workflow completed successfully!")
    else:
        print("\n❌ Schema validation failed. Schema has invalid structure.")
        schema = None