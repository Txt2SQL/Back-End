import json, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path
from typing import Optional, List, Dict
from classes.orchestrators.base_orchestrator import BaseOrchestrator
from classes.llm_clients import BaseLLM, OpenWebUILLM, AzureLLM
from classes.domain_states.schema import Schema
from classes.domain_states import QuerySession
from classes.RAG_service.schema_store import SchemaStore
from classes.RAG_service.query_store import QueryStore
from classes.llm_clients.database_client import DatabaseClient
from src.config import QUERY_GENERATION_MODELS, SCHEMA_DIR
from classes.logger_manager import LoggerManager

logger = LoggerManager.get_logger(__name__)

class QueryOrchestrator(BaseOrchestrator):
    """
    Orchestrator responsible for SQL query generation and refinement.
    Handles query creation, execution, and learning from failures.
    """
    
    def __init__(
        self,
        database_name: str,
        query_store: QueryStore,
        schema_store: SchemaStore,
        user_request: str,
        model_name: Optional[str] = None,
        max_attempts: int = 3
    ):
        super().__init__(database_name, model_name)
        
        self.max_attempts = max_attempts
        self.schema_store = schema_store
        self.query_store = query_store
        self.database_client = DatabaseClient(self.database_name)
        self.request = user_request
        
        # Current session data
        self.schema: Optional[Schema] = None
        self.current_query: QuerySession = QuerySession(user_request=user_request)
        self.schema_context: Optional[str] = None
        
        self.join_hints: Optional[List[str]] = None
        
        # Load schema for this database
        self._load_schema()
    
    def _initialize_llm(self, choice: str | None) -> BaseLLM | None:
        """Initialize the appropriate LLM based on model name pattern"""
        logger.info("Getting LLM model for choice: %s", choice)
        if choice is None:
            logger.info("Selected 'none' model (no LLM)")
            return None
        elif QUERY_GENERATION_MODELS[choice]["provider"] == "azure":
            model_name = QUERY_GENERATION_MODELS[choice]["id"]
            logger.info("Selected Azure OpenAI model: %s", model_name)
            return AzureLLM(model_name)
        else:
            model_name = QUERY_GENERATION_MODELS[choice]["id"]
            logger.info("Selected OpenWebUI model: %s", model_name)
            return OpenWebUILLM(model_name)
        
    def _load_schema(self) -> None:
        """Load the schema for this database from the json file"""
        schema_path = SCHEMA_DIR / f"{self.database_name}_schema.json"

        if not schema_path.exists():
            logger.warning("Schema file not found for database '%s': %s", self.database_name, schema_path)
            self.schema = None
            return

        logger.info("Loading schema for database '%s': %s", self.database_name, schema_path)
        with schema_path.open("r", encoding="utf-8") as schema_file:
            schema_data = json.load(schema_file)

        if schema_data is None:
            logger.warning("Schema data is empty for database '%s'", self.database_name)
            self.schema = None
            return
        
        schema = Schema.__new__(Schema)
        schema.database_name = schema_data.get("database_name", self.database_name)
        schema.source = schema_data.get("source", "text")
        schema.file_path = schema_path
        schema.tables = schema_data
        schema.json_ready = True
        schema.schema_id = schema_data.get("schema_id")

        logger.info("Loaded schema for database '%s'", self.database_name)
        #schema.print_schema_preview()
        self.schema = schema
    
    def generation(
        self, 
        user_request: str,
    ) -> QuerySession:
        """
        Generate SQL query based on user request.
        Handles the complete query lifecycle from generation to execution.
        """
        logger.info(f"Generating SQL for request: {LoggerManager.truncate_request(user_request)}")
        
        # Get relevant schema context
        self.schema_context, table_names = self.schema_store.get_context(user_request)
        
        if self.schema is None:
            raise Exception("Schema not found for database")
        
        failed_queries = None
        if self.schema.source == "mysql":
            logger.info("Getting similar failed queries for learning...")
            # Get similar failed queries for learning
            failed_queries = self.query_store.retrieve_failed_queries(user_request)
            
            logger.info("Getting join hints for learning...")
            self.join_hints = self.database_client.get_foreign_keys(table_names)
        
        while self.current_query.llm_feedback.attempt <= self.max_attempts:
            logger.info(f"Attempt #{self.current_query.llm_feedback.attempt} for request: {LoggerManager.truncate_request(user_request)}")
            # Build generation prompt
            error_feedback = self.current_query.format_error_feedback()
            prompt = self.prompt_builder.query_generation_prompt(
                user_request=user_request,
                schema_context=self.schema_context,
                previous_fail=failed_queries if error_feedback is None else None,
                join_hints=self.join_hints
            )
            
            if self.llm is None:
                # TODO: add choose of a random sample query
                response = ""
            else:
                logger.info("Sending prompt to LLM: %s", user_request)
                # Generate SQL
                response = self.llm.generate(prompt)
            
            logger.info("Received response from LLM: %s", response)
            # Create query session
            self.current_query.clean_sql_from_llm(response)
            
            if self.schema.source == "text": 
                if self.current_query.valid_syntax: break
            else:
                self.current_query = self.database_client.execute_query(self.current_query)
            
                # Evaluate the query (validate syntax, execute, etc.)
                self.current_query.evaluate()

                self._ask_feedback(self.current_query.llm_feedback.attempt)
                
                if self.current_query.llm_feedback.feedback_status == "CORRECT":
                    break
            
            self.current_query.llm_feedback.attempt += 1    
        
        # Store the result
        self.query_store.store_query(self.current_query)
        
        # Log generation result
        if self.current_query.status == "SUCCESS":
            logger.info(f"Query generated successfully: {self.current_query.sql_code}")
        else:
            logger.warning(f"Query generation issue: {self.current_query.status}")
        
        return self.current_query
    
    def _ask_feedback(
        self, 
        attempt: int = 1
    ):
        """
        Ask LLM for feedback on a failed query.
        Returns updated query session with feedback applied.
        """
        if self.current_query.sql_code is None:
            logger.info("Skipping feedback for empty query")
            return
        if self.schema_context is None:
            logger.info("Skipping feedback for empty schema context")
            return
        
        if self.current_query.status == "SUCCESS":
            if self.current_query.execution_result is None or not isinstance(self.current_query.execution_result, list) or len(self.current_query.execution_result) == 0:
                logger.info("Skipping feedback for empty execution result")
                return
            prompt = self.prompt_builder.evaluation_prompt(
                sql=self.current_query.sql_code,
                request=self.request,
                context=self.schema_context,
                execution_output=self.current_query.execution_result
            )
        elif self.current_query.status == "RUNTIME_ERROR" and attempt > 1:
            if self.current_query.execution_result is None or not isinstance(self.current_query.execution_result, str) or len(self.current_query.execution_result) == 0:
                logger.info("Skipping feedback for empty execution result")
                return
            prompt = self.prompt_builder.explanation_prompt(
                sql=self.current_query.sql_code,
                context=self.schema_context,
                execution_output=self.current_query.execution_result
            )
        else:
            logger.info("Skipping feedback for other type of query")
            return
            
        if self.llm is not None:
            response = self.llm.generate(prompt)

            self.current_query.apply_llm_feedback(response)