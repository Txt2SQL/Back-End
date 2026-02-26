import hashlib, json, os, re, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.classes.orchestrators.query_orchestrator import QueryOrchestrator
from src.classes.RAG_service.query_store import QueryStore
from src.classes.RAG_service.schema_store import SchemaStore
from config import QUERY_GENERATION_MODELS
from src.classes.logger import LoggerManager

logger = LoggerManager.get_logger(__name__)


def select_model() -> str | None:
    """
    Prompts user to select a model from available options.
    Returns None for without_llm mode.
    """
    print("\n🤖 Available models:")
    print("   0. without_llm (no LLM)")

    models = list(QUERY_GENERATION_MODELS.keys())
    for idx, model_name in enumerate(models, 1):
        print(f"   {idx}. {model_name}")

    while True:
        try:
            choice = int(input(f"\n👉 Select a model (0-{len(models)}): ").strip())

            if choice == 0:
                print("✅ Selected mode: without_llm\n")
                return None
            elif 1 <= choice <= len(models):
                selected = models[choice - 1]
                print(f"✅ Selected model: {selected}\n")
                return selected
            else:
                print(f"❌ Invalid choice. Please enter 0-{len(models)}.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")


def list_schema_databases() -> list[str]:
    """
    Returns database names discovered from data/schema/<database_name>_schema.json files.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    schema_dir = os.path.join(project_root, "data", "schema")

    if not os.path.isdir(schema_dir):
        logger.warning("Schema directory not found: %s", schema_dir)
        return []

    database_names = []
    for file_name in os.listdir(schema_dir):
        file_path = os.path.join(schema_dir, file_name)
        if os.path.isfile(file_path) and file_name.endswith("_schema.json"):
            database_names.append(file_name[: -len("_schema.json")])

    return sorted(database_names)


def select_database_name() -> str | None:
    """Prompt user to select a database from schema files."""
    database_names = list_schema_databases()

    if not database_names:
        print("❌ No schema files found in data/schema.")
        return None

    print("\n🗂️  Available databases:")
    for idx, database_name in enumerate(database_names, 1):
        print(f"   {idx}. {database_name}")

    while True:
        choice = input("\n👉 Select a database by number or name: ").strip()

        if choice.isdigit():
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(database_names):
                selected_database_name = database_names[choice_index]
                print(f"✅ Selected database: {selected_database_name}\n")
                return selected_database_name
        elif choice in database_names:
            print(f"✅ Selected database: {choice}\n")
            return choice

        print("❌ Invalid choice. Please select a valid database.")


def main():
    print("🤖 SQL query generator (orchestrator version)\n")

    query_store = QueryStore()
    schema_store = SchemaStore()

    while True:
        print("\nChoose an option:")
        print("1️⃣  Generate SQL query")
        print("2️⃣  Show query feedback vector store")
        print("3️⃣  Empty query feedback vector store")
        print("0️⃣  Exit")

        choice = input("\n👉 Your choice: ").strip()

        if choice == "0":
            print("👋 Bye!")
            break

        # ------------------------------------------------------
        # PRINT QUERY VECTOR STORE
        # ------------------------------------------------------

        elif choice == "2":
            query_store.print_collection()

        # ------------------------------------------------------
        # CLEAR QUERY VECTOR STORE
        # ------------------------------------------------------

        elif choice == "3":
            confirm = input(
                "⚠️  Are you sure you want to empty the query feedback vector store? (y/n): "
            ).strip().lower()

            if confirm == "y":
                query_store.empty_collection()
                print("✅ Query feedback vector store emptied.")
            else:
                print("❌ Operation cancelled.")

        # ------------------------------------------------------
        # GENERATE QUERY
        # ------------------------------------------------------

        elif choice == "1":

            # Select model
            model_name = select_model()

            # Select database from schema files
            database_name = select_database_name()
            if database_name is None:
                continue

            # User request
            user_request = input("\n👉 Enter a request in natural language: ").strip()

            print("\n🔍 Generating query...\n")

            orchestrator = QueryOrchestrator(
                database_name=database_name,
                query_store=query_store,
                schema_store=schema_store,
                user_request=user_request,
                model_name=model_name,
            )

            query_session = orchestrator.generation(user_request)

            print("\n💡 Generated SQL:\n")
            print(query_session.sql_code)
            print("\n---------------------------------------------")

            if query_session.execution_status == "SUCCESS":
                if query_session.execution_result:
                    print("\n📊 Execution Preview:\n")
                    for row in query_session.execution_result[:5]:
                        print(row)
                else:
                    print("\nℹ️ Query executed but returned no rows.")
            else:
                print(f"\n❌ Execution failed: {query_session.execution_result}")

        else:
            print("❌ Invalid option. Try again.")
            
if __name__ == "__main__":
    main()
