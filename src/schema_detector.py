import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import VECTOR_STORE_DIR, SCHEMA_MODELS
from src.classes.orchestrators.schema_orchestrator import SchemaOrchestrator
from src.classes.RAG_service.schema_store import SchemaStore
from src.classes.domain_states import SchemaSource
from src.classes.logger import LoggerManager

LoggerManager.setup_project_logger()
logger = LoggerManager.get_logger(__name__)

DB_DIR = os.path.join(VECTOR_STORE_DIR, "schema")

def choose_schema_model() -> str:
    """Allow users to choose one of the configured schema generation models."""
    models = list(SCHEMA_MODELS.keys())

    print("\nAvailable schema models:")
    for idx, model_name in enumerate(models, 1):
        print(f"   {idx}. {model_name}")

    while True:
        try:
            choice = int(input(f"\n👉 Select a model (1-{len(models)}): ").strip())
            if 1 <= choice <= len(models):
                selected = models[choice - 1]
                print(f"✅ Selected model: {selected}\n")
                return selected
            else:
                print(f"❌ Invalid choice. Please enter 1-{len(models)}.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")


def main():
    print("🤖 Interactive canonical schema management (orchestrator version)")

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
        return

    database_name = input("\n👉 Enter database name: ").strip()
    # ------------------------------------------------------------------
    # PRINT EXISTING VECTOR STORE
    # ------------------------------------------------------------------

    if method == "3":
        schema_store = SchemaStore()
        schema_store.print_collection()
        return

    # ------------------------------------------------------------------
    # MYSQL FLOW
    # ------------------------------------------------------------------

    if method == "2":

        orchestrator = SchemaOrchestrator(
            database_name=database_name,
            source=SchemaSource.MYSQL,
        )

        schema = orchestrator.acquire_schema()

        if schema.json_ready:
            print(f"\n✅ Schema for '{database_name}' successfully extracted and stored.")
        else:
            print("\n❌ Failed to extract schema.")

        return

    # ------------------------------------------------------------------
    # TEXT + LLM FLOW
    # ------------------------------------------------------------------

    if method == "1":
        model_choice = choose_schema_model()

        orchestrator = SchemaOrchestrator(
            database_name=database_name,
            source=SchemaSource.TEXT,
            llm_model=model_choice,
        )

        while True:
            print("\n👉 Paste schema text (press ENTER twice to finish):")

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

            if schema.json_ready:
                print(f"\n✅ Schema for '{database_name}' processed and stored.")
            else:
                print("\n❌ Schema generation failed.")

            print("\nChoose an option:")
            print("0️⃣  Exit")
            print("1️⃣  Provide more text to update the schema")
            print("3️⃣  Print current vector store")

            choice = input("\n👉 Your choice: ").strip()

            if choice == "0":
                print("\n👋 Exiting. Goodbye!")
                break
            elif choice == "3":
                orchestrator.schema_store.print_collection()
            elif choice != "1":
                print("\nInvalid choice. Exiting.")
                break

if __name__ == "__main__":
    main()