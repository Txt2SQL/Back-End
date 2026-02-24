import json
from pathlib import Path
from typing import Optional, List

from classes.orchestrators.base_orchestrator import BaseOrchestrator
from classes.llm_clients import BaseLLM, OpenWebUILLM, AzureLLM
from classes.domain_states.schema import Schema
from classes.domain_states import QuerySession
from classes.RAG_service.schema_store import SchemaStore
from classes.RAG_service.query_store import QueryStore
from classes.database_client import DatabaseClient
from src.config import QUERY_GENERATION_MODELS
from src.logging_utils import setup_logger, truncate_request

logger = setup_logger(__name__)

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
        self.current_query: Optional[QuerySession] = None
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
        schema_path = Path("data/schema") / f"{self.database_name}_schema.json"

        if not schema_path.exists():
            logger.warning("Schema file not found for database '%s': %s", self.database_name, schema_path)
            self.schema = None
            return

        with schema_path.open("r", encoding="utf-8") as schema_file:
            schema_data = json.load(schema_file)

        schema = Schema.__new__(Schema)
        schema.database_name = schema_data.get("database_name", self.database_name)
        schema.source = schema_data.get("source", "text")
        schema.save_path = schema_path.parent
        schema.file_path = schema_path
        schema.tables = schema_data
        schema.json_ready = True
        schema.schema_id = schema_data.get("schema_id")

        self.schema = schema
    
    def generation(
        self, 
        user_request: str,
    ) -> QuerySession:
        """
        Generate SQL query based on user request.
        Handles the complete query lifecycle from generation to execution.
        """
        logger.info(f"Generating SQL for request: {truncate_request(user_request)}")

        if self.llm is None:
            raise ValueError("An LLM model is required for query generation")
        
        # Get relevant schema context
        self.schema_context, table_names = self.schema_store.get_context(user_request)
        
        if self.schema is None:
            raise Exception("Schema not found for database")
        
        previous_failures = None
        if self.schema.source == "mysql":
            # Get similar failed queries for learning
            failed_queries = self.query_store.retrieve_failed_queries(user_request)
            if failed_queries:
                previous_failures = "\n\n".join(doc.page_content for doc in failed_queries)
            
            self.join_hints = self.database_client.get_foreign_keys(table_names)

        attempt = 1
        while attempt <= self.max_attempts:

            # Build generation prompt
            prompt = self.prompt_builder.query_generation_prompt(
                user_request=user_request,
                schema_context=self.schema_context,
                previous_fail=(self.current_query.format_error_feedback() if self.current_query else None) or previous_failures,
                join_hints=self.join_hints
            )
            
            # Generate SQL
            response = self.llm.generate(prompt)
            
            # Create query session
            self.current_query = QuerySession(
                user_request=user_request,
                raw_llm_response=response
            )
            
            self.current_query = self.database_client.execute_query(self.current_query)
            
            # Evaluate the query (validate syntax, execute, etc.)
            self.current_query.evaluate()

            if self.current_query.status == "SUCCESS":
                if self.schema.source == "mysql":
                    self._ask_feedback(attempt)
                break

            if attempt >= self.max_attempts:
                break

            self._ask_feedback(attempt)
            attempt += 1
            
        
        # Store the result
        self.query_store.store_query(self.current_query)
        
        # Log generation result
        if self.current_query.status == "SUCCESS":
            logger.info(f"Query generated successfully: {self.current_query.current_query}")
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
        if self.current_query.status == "SYNTAX_ERROR":
            return
        if self.llm is None:
            return
        elif self.current_query.status == "SUCCESS":
            prompt = self.prompt_builder.evaluation_prompt(
                sql=self.current_query.sql_code,
                request=self.request,
                context=self.schema_context,
                execution_output=self.current_query.execution_result
            )
        elif self.current_query.status == "RUNTIME_ERROR":
            prompt = self.prompt_builder.explanation_prompt(
                sql=self.current_query.sql_code,
                context=json.dumps(self.schema.tables, ensure_ascii=False, indent=2),
                execution_output=self.current_query.execution_result
            )
        else:
            return
            
        response = self.llm.generate(prompt)
        
        self.current_query.apply_llm_feedback(response)
