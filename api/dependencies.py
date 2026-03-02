from functools import lru_cache
from pathlib import Path
from typing import Optional

from src.classes.RAG_service.query_store import QueryStore
from src.classes.RAG_service.schema_store import SchemaStore
from src.classes.logger import LoggerManager
from config import DATA_DIR, VECTOR_STORE_DIR

logger = LoggerManager.get_logger(__name__)

@lru_cache()
def get_schema_store() -> SchemaStore:
    """Get or create schema store singleton"""
    logger.info("Initializing SchemaStore...")
    return SchemaStore(VECTOR_STORE_DIR)

@lru_cache()
def get_query_store() -> QueryStore:
    """Get or create query store singleton"""
    logger.info("Initializing QueryStore...")
    return QueryStore(VECTOR_STORE_DIR)

def get_data_dir() -> Path:
    """Get data directory"""
    return DATA_DIR