import os
from pathlib import Path
from classes.orchestrators.schema_orchestrator import SchemaOrchestrator
from src.logging_utils import setup_logger
from src.config import VECTOR_STORE_DIR, SCHEMA_MODELS
from classes.llm_clients import OpenWebUILLM
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings

logger = setup_logger(__name__)

COLLECTION_NAME = "%s_schema_store"
DB_DIR = str(VECTOR_STORE_DIR / "%s_schema")

def choose_schema_model() -> str:
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
                return selected
            else:
                print(f"❌ Invalid choice. Please enter 1-{len(models)}.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")

def main():
    """Main function to handle interactive schema workflow using SchemaOrchestrator."""
    
    print("🤖 Interactive canonical schema management (phase 2 - orchestrated)")


    print("\nChoose how to acquire the database schema:")
    print("1️⃣  via text input (DDL statements or descriptions)")
    print("2️⃣  via MySQL database connection")
    print("3️⃣  Print current vector store")

    method = input("\n👉 Your choice: ").strip()    

    database_name = input("\n📂 Enter database name: ").strip()

    file_path = Path("data/schema") / f"{database_name}_schema.json"

    if method == "1":
        source = "text"
    elif method == "2":
        source = "mysql"
    elif method == "3":
        if not file_path.exists():
            logger.error(f"Schema file not found: {file_path}")
            return
        else:
            source = "file"
    else:
        print("❌ Invalid choice.")
        return

    orchestrator = SchemaOrchestrator(
        database_name=database_name,
        source=source
    )
    # ------------------------
    # TEXT-BASED SCHEMA FLOW
    # ------------------------
    if method == "1":
        model_name = choose_schema_model()

        orchestrator.initialize_llm(model_name)

        while True:
            print("\n👉 Paste schema text (press ENTER twice to finish):\n")

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

            schema = orchestrator.acquire_schema(user_text=raw_text)

            if schema and schema.json_ready:
                print("✅ Schema processed successfully.")

            print("\nChoose an option:")
            print("0️⃣  Exit")
            print("1️⃣  Provide more text to update schema")
            print("3️⃣  Print current vector store")

            choice = input("\n👉 Your choice: ").strip()

            if choice == "0":
                print("👋 Exiting. Goodbye!")
                break
            elif choice == "3":
                orchestrator.schema_store.print_collection()
            else:
                continue

    # ------------------------
    # MYSQL SCHEMA FLOW
    # ------------------------
    elif method == "2":

        schema = orchestrator.acquire_schema()

        if schema and schema.json_ready:
            print("✅ Schema extracted from MySQL successfully.")
        else:
            logger.error("Schema extraction failed.")

    # ------------------------
    # PRINT VECTOR STORE
    # ------------------------
    elif method == "3":
        orchestrator.schema_store.print_collection()

if __name__ == "__main__":
    main()