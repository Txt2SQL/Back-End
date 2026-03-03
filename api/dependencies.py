from src.classes.RAG_service.schema_store import SchemaStore
from src.classes.RAG_service.query_store import QueryStore
from src.classes.llm_factory import LLMFactory
from src.classes.clients.mysql_client import MySQLClient
from config import DATA_DIR, SCHEMA_MODELS, QUERY_MODELS

# Singleton-like behavior for Stores if they are thread-safe, 
# otherwise instantiate per request.
# Assuming Stores load from disk, we can instantiate them lightly.

def get_schema_store() -> SchemaStore:
    # You might need to adjust SchemaStore init based on your actual implementation
    return SchemaStore()

def get_query_store() -> QueryStore:
    return QueryStore()

def get_llm(model_id: str, model_type: str = "schema"):
    """
    Factory to get the correct LLM instance.
    """
    config_source = SCHEMA_MODELS if model_type == "schema" else QUERY_MODELS
    
    # Simple lookup logic matching your config structure
    if model_id in config_source:
        config = config_source[model_id]
    else:
        # Fallback or error handling
        config = config_source.get("gpt-4o", next(iter(config_source.values())))
    
    return LLMFactory.create(config)

def get_mysql_client(database_name: str) -> MySQLClient:
    return MySQLClient(database=database_name)