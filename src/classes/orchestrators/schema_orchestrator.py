import json
from typing import Optional
from classes.llm_clients import BaseLLM, OpenWebUILLM
from classes.orchestrators.base_orchestrator import BaseOrchestrator
from classes.RAG_service.schema_store import SchemaStore
from classes.domain_states.schema import Schema
from classes.database_client import DatabaseClient
from src.config import SCHEMA_MODELS
from src.logging_utils import setup_logger

logger = setup_logger(__name__)


class SchemaOrchestrator(BaseOrchestrator):
    """
    Orchestrator responsible for schema acquisition and updates.
    Handles both initial schema extraction and iterative improvements.
    """
    
    def __init__(
        self, 
        database_name: str, 
        source: str = "text",  # "mysql" or "text"
        llm_model: Optional[str] = None,
    ):
        super().__init__(database_name, llm_model)
        
        self.source = source
        self.schema_store = SchemaStore()
        self.schema: Schema = Schema(
            database_name=self.database_name,
            schema_source=self.source
        )
        
    def _initialize_llm(self, choice: str | None) -> BaseLLM | None:
        if choice is None:
            return None
        return OpenWebUILLM(model=SCHEMA_MODELS[choice]["id"])
    
    def acquire_schema(self, user_text: Optional[str] = None) -> Schema:
        """
        Main method to acquire schema from source.
        Returns the schema object after processing.
        """
        if self.schema and self.schema.json_ready:
            logger.info(f"Schema already exists and is valid for {self.database_name}")
            return self.schema
            
        if self.source == "mysql":
            # Extract schema from MySQL database
            self._extract_from_mysql()
        elif user_text:
            self._acquire_schema_with_llm(user_text)

            
        # Store in vector database
        if self.schema.json_ready:
            self.schema_store.add_schema(self.schema)
            logger.info(f"Schema for {self.database_name} acquired and stored successfully")
        else:
            logger.warning(f"Failed to acquire schema for {self.database_name}")
        
        return self.schema
    
    def _extract_from_mysql(self):
        """
        Extract schema from MySQL database.
        This would need implementation based on your MySQL connector.
        """
        self.database_client = DatabaseClient(self.database_name)
        schema_from_db = self.database_client.extract_schema()
        self.schema.parse_response(schema_from_db)
        
    
    def _prompt_for_schema_text(self) -> str:
        """Prompt user to input schema text if not provided"""
        print(f"Please provide the schema text for database '{self.database_name}':")
        print("(Enter multiple lines, end with Ctrl+D or an empty line)")
        lines = []
        while True:
            try:
                line = input()
                if not line:
                    break
                lines.append(line)
            except EOFError:
                break
        return "\n".join(lines)
    
    def _acquire_schema_with_llm(self, user_text: str):
        if self.llm is None:
            raise ValueError("LLM is None cannot generate or update the schema")
        
        if self.schema.json_ready:
            logger.info(f"Schema already exists and is valid for {self.database_name}")
            self._update_current_schema(user_text)
            return
        else:
            self._acquire_new_schema(user_text)
    
        
        """Process raw schema through LLM"""
        if not user_text:
            raise ValueError("User text is required when source is 'text'")
        prompt = self.prompt_builder.schema_generation_prompt()

        schema_raw = self.llm.generate(prompt)
        self.schema.parse_response(schema_raw)
        
    def _update_current_schema(self, user_text: str):
        update_type = self.schema.classify_update(user_text)
        if update_type == "semantic":
            self.schema.add_semantic_note(user_text)
            return
        elif update_type == "unknown":
            logger.info("Unknown update type, asking llm detect update type")
            prompt = self.prompt_builder.update_classification_prompt(user_text)
            update_type = self.llm.generate(prompt) # pyright: ignore[reportOptionalMemberAccess]
        
        if update_type == "structural":
            prompt = self.prompt_builder.schema_update_prompt(user_text, self.schema.to_string())
            schema_raw = self.llm.generate(prompt) # pyright: ignore[reportOptionalMemberAccess]
            self.schema.parse_response(schema_raw)
        else:
            self.schema.add_semantic_note(user_text)
            
    def _acquire_new_schema(self, user_text: str):
        prompt = self.prompt_builder.schema_generation_prompt()
        schema_from_llm = self.llm.generate(prompt.format(raw_schema_text=user_text)) # pyright: ignore[reportOptionalMemberAccess]
        self.schema.parse_response(schema_from_llm)