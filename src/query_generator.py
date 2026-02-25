import hashlib, json, os, re, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from classes.orchestrators.query_orchestrator import QueryOrchestrator
from classes.RAG_service.query_store import QueryStore
from classes.RAG_service.schema_store import SchemaStore
from src.config import QUERY_GENERATION_MODELS
from src.logging_utils import setup_logger

logger = setup_logger(__name__)


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

            # Ask database name
            database_name = input("\n👉 Enter database name: ").strip()

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