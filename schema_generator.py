import json
import os
import re
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

# === CONFIG ===
SCHEMA_FILE = "schema_canonico.json"
MODEL_NAME = "gemma3:12b"

# === LLM ===
model = OllamaLLM(model=MODEL_NAME)

# === Function for schema preview ===
def print_schema_preview(schema: dict):
    """Prints a readable preview of the canonical schema"""
    print("\n🔎 Canonical schema preview:")
    print("=" * 60)
    
    # Print tables
    if "tables" in schema and schema["tables"]:
        print(f"\n📊 FOUND {len(schema['tables'])} TABLES:")
        for i, table in enumerate(schema["tables"], 1):
            print(f"\n  🏷️  Table #{i}: {table.get('name', 'N/A')}")
            
            # Print columns
            if "columns" in table and table["columns"]:
                print("  📋 Columns:")
                for col in table["columns"]:
                    constraints = col.get("constraints", [])
                    constraints_str = ", ".join(constraints) if constraints else "no constraints"
                    print(f"    • {col.get('name', 'N/A')} ({col.get('type', 'N/A')}) - {constraints_str}")
            else:
                print("  📋 No columns defined")
    else:
        print("\n📊 No tables defined")
    
    # Print semantic notes
    if "semantic_notes" in schema and schema["semantic_notes"]:
        print(f"\n📝 FOUND {len(schema['semantic_notes'])} SEMANTIC NOTES:")
        for i, note in enumerate(schema["semantic_notes"], 1):
            # Show only first 100 characters for brevity
            preview = note[:100] + "..." if len(note) > 100 else note
            print(f"  {i}. {preview}")
    else:
        print("\n📝 No semantic notes")
    
    print("=" * 60)

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
def generate_schema_canonical(raw_schema_text: str, current_schema: dict | None = None) -> dict:
    """
    Uses an LLM model to generate or update the canonical schema.
    If a current schema exists, it passes it as context.
    """

    context_part = ""
    if current_schema:
        context_part = f"Current schema:\n{json.dumps(current_schema, indent=2, ensure_ascii=False)}\n\n"

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

{context_part}
SQL DDL to process:
\"\"\"{raw_schema_text}\"\"\"

Return ONLY the JSON object:
"""

    chain = ChatPromptTemplate.from_template(template) | model
    response = chain.invoke({
        "context_part": context_part,
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

    # Load existing schema (if present)
    if os.path.exists(SCHEMA_FILE):
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            current_schema = json.load(f)
        print("📂 Existing schema found and loaded.")
        # Classify update
        print("\n🔍 Analyzing update type...")
        update_type = classify_update(raw_text)
        print(f"📄 Type detected: {update_type}")
        # Update based on type
        if update_type == "semantic":
            print("🧠 Semantic update: adding description.")
            if current_schema is None:
                current_schema = {"tables": [], "semantic_notes": []}
            current_schema.setdefault("semantic_notes", []).append(raw_text)
            schema = current_schema

        elif update_type == "structural":
            print("🏗️ Structural update: regenerating canonical schema via LLM...")
            schema = generate_schema_canonical(raw_text, current_schema)
        else:
            print("⚠️ Type not recognized, no modification applied.")
            schema = current_schema or {"tables": [], "semantic_notes": []}
    else:
        current_schema = None
        print("🆕 No previous schema, a new one will be created.")
        schema = generate_schema_canonical(raw_text, current_schema)

    # Save to file
    with open(SCHEMA_FILE, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    print("\n✅ Updated canonical schema saved in schema_canonico.json.")
    
    # Show schema preview
    print_schema_preview(schema)


def update_schema(raw_text: str) -> dict:
    """
    Reusable function: updates schema_canonico.json based on the provided text.
    """
    if not raw_text.strip():
        raise ValueError("No text provided for schema update.")

    if os.path.exists(SCHEMA_FILE):
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            current_schema = json.load(f)
    else:
        current_schema = None

    update_type = classify_update(raw_text)

    if update_type == "semantic":
        if current_schema is None:
            current_schema = {"tables": [], "semantic_notes": []}
        current_schema.setdefault("semantic_notes", []).append(raw_text)
        schema = current_schema

    elif update_type == "structural":
        schema = generate_schema_canonical(raw_text, current_schema)

    else:
        schema = current_schema or {"tables": [], "semantic_notes": []}

    with open(SCHEMA_FILE, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    # Show preview even when using the function
    print_schema_preview(schema)

    return schema