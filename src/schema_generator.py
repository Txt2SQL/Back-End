import hashlib, json, os, re, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings
from src.llm_clients.openwebui_client import OpenWebUILLM
from langchain_chroma import Chroma
from src.config.settings import LOGINFO_SEPARATOR, SCHEMA_MODELS
from src.retriver_utils import build_vector_store
from src.config.paths import VECTOR_STORE_DIR, SCHEMA_FILE
from src.prompt_factory import (
    schema_generation_prompt,
    schema_update_prompt,
    update_classification_prompt
)
from src.mysql_linker import (
    extract_schema,
    list_databases,
    mysql_env_is_valid,
    prompt_mysql_credentials,
    write_mysql_env,
    ENV_MYSQL_FILE
)
from src.logging_utils import (
    setup_logger,
    print_vector_store
)

# === CONFIG ===
DB_DIR = str(VECTOR_STORE_DIR / "schema")
COLLECTION_NAME = "schema_canonical"
MODEL_NAME = "gemma3:12b"

# === LOGGING SETUP ===
logger = setup_logger(__name__)

def choose_schema_model() -> OpenWebUILLM:
    """Allow users to choose one of the configured schema generation models."""
    # Display numbered list of models
    models = list(SCHEMA_MODELS.keys())
    for idx, model_name in enumerate(models, 1):
        print(f"   {idx}. {model_name}")
    
    while True:
        try:
            choice = int(input("\n👉 Select a model (1-{}): ".format(len(models))).strip())
            
            if 1 <= choice <= len(models):
                selected = models[choice - 1]
                print(f"✅ Selected model: {selected}\n")
                return OpenWebUILLM(model=SCHEMA_MODELS[selected]["id"])
            else:
                print(f"❌ Invalid choice. Please enter 1-{len(models)}.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")

def compute_schema_id(full_schema: dict) -> str:
    """
    Compute a unique identifier for the schema.
    """
    logger.debug("Computing schema ID")
    normalized = json.dumps(full_schema, sort_keys=True)
    schema_id = hashlib.sha256(normalized.encode()).hexdigest()[:16]
    logger.debug("Schema ID computed: %s", schema_id)
    return schema_id

def acquire_schema_from_text(raw_text: str):
    model = choose_schema_model()

    schema_exists = os.path.exists(SCHEMA_FILE) and os.path.getsize(SCHEMA_FILE) > 0
    vector_store_exists = os.path.exists(DB_DIR) and os.path.isdir(DB_DIR)

    if schema_exists and vector_store_exists:
        logger.info("Existing schema and vector store detected!")
        logger.info(f"Found: {SCHEMA_FILE}")
        logger.info(f"Found: {DB_DIR}")

        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            current_schema = json.load(f)

        return update_schema(model,raw_text, current_schema)

    logger.info("No existing schema found. Generating from scratch...")
    database_name = input("DB_NAME for this schema: ").strip()
    if not database_name:
        logger.error("DB_NAME is required to generate the schema.")
        return {}
    schema = generate_schema_canonical(model, raw_text)
    schema["database"] = database_name
    schema["source"] = "text"
    logger.info("New schema generated.")

    return schema

def acquire_schema_from_mysql():
    # Ensure MySQL credentials exist
    if not mysql_env_is_valid():
        creds = prompt_mysql_credentials()
        write_mysql_env(creds)

    # Load the env after creation/update
    load_dotenv(ENV_MYSQL_FILE, override=True)

    databases = list_databases()
    if not databases:
        logger.error("No databases available for the provided MySQL credentials.")
        return {}

    print("\nAvailable databases:")
    for i, db_name in enumerate(databases, 1):
        print(f"{i}. {db_name}")

    selected_db = ""
    while not selected_db:
        choice = input("\n👉 Select a database (name or number): ").strip()
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(databases):
                selected_db = databases[index]
            else:
                logger.error("Invalid database selection. Try again.")
        elif choice in databases:
            selected_db = choice
        else:
            logger.error("Invalid database selection. Try again.")

    write_mysql_env({"DB_NAME": selected_db})
    load_dotenv(ENV_MYSQL_FILE, override=True)

    logger.info("Connecting to MySQL database to retrieve schema...")
    schema = extract_schema(selected_db)
    schema["source"] = "mysql"
    schema["database"] = selected_db
    logger.info("Generating schema from database schema...")
    logger.info("New schema generated.")

    return schema

def generate_schema_canonical(model: OpenWebUILLM, raw_schema_text: str) -> dict:

    logger.info("Raw schema text being sent to LLM:")
    logger.info(f"{raw_schema_text}")
    logger.info("="*60)

    template = schema_generation_prompt()

    response = model.generate(template.format(raw_schema_text=raw_schema_text))

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

def print_schema_preview(schema: dict):
    """Prints a readable preview of the canonical schema"""
    print("\n" +  LOGINFO_SEPARATOR)
    print("Canonical schema preview:")
    print(LOGINFO_SEPARATOR)
    
    # Print tables
    if "tables" in schema and schema["tables"]:
        print(f"\nFound {len(schema['tables'])} tables:")
        for i, table in enumerate(schema["tables"], 1):
            print(f"\n  Table #{i}: {table.get('name', 'N/A')}")
            
            # Print columns
            if "columns" in table and table["columns"]:
                print("  Columns:")
                for col in table["columns"]:
                    constraints = col.get("constraints", [])
                    constraints_str = ", ".join(constraints) if constraints else "no constraints"
                    print(f"    • {col.get('name', 'N/A')} ({col.get('type', 'N/A')}) - {constraints_str}")
            else:
                print("  No columns defined")
    else:
        print("\nNo tables defined")
    
    # Print semantic notes
    if "semantic_notes" in schema and schema["semantic_notes"]:
        print(f"\nFound {len(schema['semantic_notes'])} semantic notes:")
        for i, note in enumerate(schema["semantic_notes"], 1):
            # Show only first 100 characters for brevity
            preview = note[:100] + "..." if len(note) > 100 else note
            print(f"  {i}. {preview}")
    else:
        print("\nNo semantic notes")
    
    print(LOGINFO_SEPARATOR)

def classify_update(model: OpenWebUILLM,text: str) -> str:
    """Recognizes if the text describes a structural or semantic modification."""

    sql_keywords = ["CREATE TABLE", "ALTER TABLE", "ADD COLUMN", "DROP TABLE", "FOREIGN KEY", "REFERENCES"]
    desc_keywords = ["means", "can assume", "contains", "represents", "describes", "equivalent to"]

    if any(k.lower() in text.lower() for k in sql_keywords):
        return "structural"
    if any(k.lower() in text.lower() for k in desc_keywords):
        return "semantic"

    prompt = update_classification_prompt(text)
    response = model.generate(prompt.format(text=text)) # pyright: ignore[reportArgumentType]

    content = response if isinstance(response, str) else getattr(response, "content", str(response))
    content = content.strip().upper()

    if "A" in content:
        return "structural"
    elif "B" in content:
        return "semantic"
    return "unknown"

def update_schema_with_existing(model: OpenWebUILLM, raw_schema_text: str, current_schema: dict) -> dict:
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

    template = schema_update_prompt(raw_schema_text, current_schema_text)

    response = model.generate(template.format(current_schema_str=current_schema_text, new_text=raw_schema_text)) # pyright: ignore[reportArgumentType]

    if isinstance(response, str):
        content = response.strip()
    elif hasattr(response, "content"):
        content = response.content.strip()
    else:
        content = str(response).strip()

    logger.info(f"Raw LLM response: {content}")

    schema = extract_json_from_response(content)
    
    logger.info("Structural schema generated.")

    if current_schema and "database" in current_schema:
        schema["database"] = current_schema["database"]

    return schema

def update_schema(model: OpenWebUILLM, raw_text: str, current_schema: dict):

    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        current_schema = json.load(f)

    logger.info("Current schema:")
    print_schema_preview(current_schema)

    logger.info("Classifying the update...")
    update_type = classify_update(model, raw_text)
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
        
        return update_schema_with_existing(model, raw_text, current_schema)

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
    try:
        vs = build_vector_store(schema)
        logger.info("Vector store built successfully!")
        logger.info("Workflow completed successfully!")
        return vs
    except Exception as e:
        logger.error(f"Error building vector store: {e}")
        raise

def main():
    """Main function to handle the interactive workflow."""
    print("🤖 Interactive canonical schema management (phase 1)")
    
    vector_store_exists = os.path.exists(DB_DIR) and os.path.isdir(DB_DIR)

    print("\nChoose how to acquire the database schema:")
    print("1️⃣  via text input (DDL statements or descriptions)")
    print("2️⃣  via MySQL database connection")
    
    if vector_store_exists:
        print("3️⃣  Print current vector store")

    method = input("\n👉 Your choice: ").strip()

    valid_choices = {"1", "2"}
    if vector_store_exists:
        valid_choices.add("3")

    if method not in valid_choices:
        logger.error("Invalid method choice. Exiting.")
        exit(1)
    schema = []
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
        elif method == "2":
            schema = acquire_schema_from_mysql()
        elif method == "3":
            try:
                embeddings = OllamaEmbeddings(model="mxbai-embed-large")
                vector_store = Chroma(
                    collection_name=COLLECTION_NAME,
                    persist_directory=DB_DIR,
                    embedding_function=embeddings,
                )
                print_vector_store(vector_store)
            except FileNotFoundError:
                logger.error("Vector store does not exist. Please generate the schema first.")

        if schema:
            vector_store = save_validate_and_build(schema)
            print_vector_store(vector_store) # pyright: ignore[reportArgumentType]
            
        if method != "1":
            break

        print("\nChoose an option:")
        print("0️⃣  Exit")
        print("1️⃣  Provide more text to update the schema")
        print("3️⃣  Print current vector store")

        choice = input("\n👉 Your choice: ").strip()
        if choice == "0":
            print("👋 Exiting. Goodbye!")
            break
        else:
            method = choice

# === ENTRY POINT ===
if __name__ == "__main__":
    main()
