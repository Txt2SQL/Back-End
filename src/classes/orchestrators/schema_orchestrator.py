import json, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import Optional, Any
from pathlib import Path
from src.classes.clients import BaseLLM, OpenWebUILLM, AzureLLM
from src.classes.orchestrators.base_orchestrator import BaseOrchestrator
from src.classes.RAG_service.schema_store import SchemaStore
from src.classes.domain_states.schema import Schema
from src.classes.clients.mysql_client import MySQLClient
from src.classes.domain_states import SchemaSource
from src.classes.logger import LoggerManager
from config import SCHEMA_MODELS, DATA_DIR


class SchemaOrchestrator(BaseOrchestrator):
    """
    Orchestrator responsible for schema acquisition and updates.
    Handles both initial schema extraction and iterative improvements.
    """
    
    def __init__(
        self, 
        database_name: str, 
        schema_store: SchemaStore,
        llm: Optional[BaseLLM] = None, 
        database_client: Optional[MySQLClient] = None,
        instance_path: Path = DATA_DIR
    ):
        if database_client is None and llm is None:
            raise ValueError("Either database_client or llm_model must be provided")
        
        super().__init__(database_name, instance_path, llm)
        
        self.database_client = database_client
        self.schema_store = schema_store
        self.schema: Schema = Schema(
            database_name=self.database_name,
            schema_source=SchemaSource.MYSQL if database_client else SchemaSource.TEXT,
            path=self.instance_path / "schema"
        )
    
    @property
    def logger(self):
        return LoggerManager.get_logger(__name__)
        
    def _initialize_llm(self, choice: str) -> BaseLLM:
        if choice is None:
            return None
        elif SCHEMA_MODELS[choice]["provider"] == "openwebui":
            return OpenWebUILLM(model_config=SCHEMA_MODELS[choice])
        else:
            return AzureLLM(model=SCHEMA_MODELS[choice]["id"])
        
    def update_current_schema(self, user_text: str):
        if not self.schema.json_ready:
            raise ValueError("Schema is not valid")
        
        update_type = self.schema.classify_update(user_text)
        if update_type == "unknown":
            self.logger.info("Unknown update type, asking llm detect update type")
            prompt = self.prompt_builder.update_classification_prompt(user_text)
            update_type = self.llm.generate(prompt) # pyright: ignore[reportOptionalMemberAccess]
        
        if update_type == "structural":
            prompt = self.prompt_builder.schema_update_prompt(user_text, self.schema.to_string())
            schema_raw = self.llm.generate(prompt) # pyright: ignore[reportOptionalMemberAccess]
            self._process_response(schema_raw)
        else:
            self.schema.add_semantic_note(user_text)
        
        return self.schema
            
    def acquire_new_schema(self, user_text: str | None = None):
        if self.schema.json_ready:
            raise ValueError("Schema is already valid")
        
        if self.database_client is not None:
            response = self.database_client.extract_schema()
        elif self.llm is not None and user_text is not None:
            prompt = self.prompt_builder.schema_generation_prompt()
            response = self.llm.generate(prompt.format(raw_schema_text=user_text)) # pyright: ignore[reportOptionalMemberAccess]
        else:
            raise Exception("Either database_client or llm_model must be provided")
        
        self._process_response(response)
        
        return self.schema

    def _process_response(self, response: Any):
        self.logger.info(f"LLM response: {response}")
        # Parse response
        self.schema.parse_response(response)
        # Store in vector database
        if self.schema.json_ready:
            self.schema_store.add_schema(self.schema)
            self.logger.info(f"Schema for {self.database_name} acquired and stored successfully")
        else:
            self.logger.warning(f"Failed to acquire schema for {self.database_name}")