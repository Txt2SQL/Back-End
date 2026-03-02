import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pathlib import Path
from typing import Optional, List

from src.classes.orchestrators.base_orchestrator import BaseOrchestrator
from src.classes.clients import BaseLLM, OpenWebUILLM, AzureLLM
from src.classes.domain_states.schema import Schema
from src.classes.domain_states import QuerySession
from src.classes.RAG_service.schema_store import SchemaStore
from src.classes.RAG_service.query_store import QueryStore
from src.classes.RAG_service.schema_store import Document
from src.classes.clients.mysql_client import MySQLClient
from src.classes.logger import LoggerManager

from config import QUERY_GENERATION_MODELS, DATA_DIR
from src.classes.domain_states import QueryStatus, FeedbackStatus, SchemaSource, ErrorType



class QueryOrchestrator(BaseOrchestrator):
    """
    Orchestrator responsible for SQL query generation and refinement.
    Handles query creation, execution, and learning from failures.
    """

    def __init__(
        self,
        schema: Schema,
        schema_store: SchemaStore,
        model_name: str,
        user_request: str,
        query_store: Optional[QueryStore] = None, # query_store should not be created if source = "text"
        max_attempts: int = 4,
        instance_path: Path = DATA_DIR,
        testing: bool = False
    ):
        super().__init__(schema.database_name, instance_path, model_name)

        self.schema = schema
        self.schema_store = schema_store
        self.query_store = query_store
        self.request = user_request
        self.max_attempts = max_attempts
        self.testing = testing

        self.current_query: QuerySession = QuerySession(user_request=user_request)
        self.schema_context: Optional[str] = None

        self.database_client: Optional[MySQLClient] = None
        self.join_hints: Optional[List[str]] = None
        self.failed_queries: Optional[List[Document]] = None
        self.evaluator: Optional[BaseLLM] = None
            
    @property
    def logger(self):
        return LoggerManager.get_logger(__name__)

    # --------------------------------------------------
    # LLM INITIALIZATION
    # --------------------------------------------------

    def _initialize_llm(self, choice: str | None) -> BaseLLM:
        self.logger.info("Getting LLM model for choice: %s", choice)

        if choice is None:
            raise Exception("No model choice provided")

        model_config = QUERY_GENERATION_MODELS[choice]
        model_name = model_config["id"]

        if model_config["provider"] == "azure":
            return AzureLLM(model_name)

        return OpenWebUILLM(model_config)

    # --------------------------------------------------
    # MAIN GENERATION LOOP
    # --------------------------------------------------

    def generation(self, user_request: str) -> QuerySession:
        
        self.logger.info("📝 Getting inside the query generation (mode: %s)...", self.schema.source.value)

        self._init_generation_context(user_request)

        consecutive_runtime_errors = 0

        while self.current_query.attempt <= self.max_attempts:
            
            self.logger.info("📝 Attempt: %s", self.current_query.attempt)

            # --------------------------------------------------
            # 1️⃣ GENERATE SQL
            # --------------------------------------------------

            self._generate_sql_attempt(user_request)

            if self.current_query.valid_syntax is False:
                
                self.logger.info("📝 Syntax validation failed")
            else:
                self.logger.info("📝 Syntax validation passed")

                if self.schema.source == SchemaSource.TEXT:
                    self.logger.info("📝 Skipping execution for text source")
                    break
            
            if self.schema.source == SchemaSource.MYSQL:
                self.logger.info("📝 Detected MySQL source, starting execution...")

                # --- Execute query ---
                self._execute_and_evaluate_query()

                # --------------------------------------------------
                # Handle non-success outcomes
                # --------------------------------------------------
                if self.current_query.status is not QueryStatus.SUCCESS:
                    
                    self.logger.info("📝 Query execution failed with status: %s", self.current_query.status.value)

                    consecutive_runtime_errors += 1

                    # On second consecutive runtime error → ask explanation
                    if consecutive_runtime_errors >= 2:
                        self.current_query.initialize_llm_feedback()
                        self.logger.info("📝 Asking for explanation...")
                        prompt = self._build_feedback_prompt("explanation")
                        response = self.current_query.ask_for_feedback(prompt)
                        self.logger.info("📝 Explanation: \n%s", response)
                        if self.current_query.llm_feedback is None:
                            self.logger.info("📝 Create LLMFeedback object!")
                            raise Exception("LLMFeedback object not found")
                        self.current_query.set_explanation_feedback(response)

                # --------------------------------------------------
                # SUCCESS case → ask correctness evaluation
                # --------------------------------------------------
                if self.current_query.status is QueryStatus.SUCCESS:
                    
                    consecutive_runtime_errors = 0
                    
                    self.logger.info("📝 Query executed successfully")

                    self.current_query.initialize_llm_feedback()
                    prompt = self._build_feedback_prompt("evaluation")
                    response = self.current_query.ask_for_feedback(prompt)
                    self.logger.info("📝 Evaluation response: \n%s", response)
                    self.current_query.apply_llm_feedback(response)
                    self.current_query.evaluate()

                    if self.current_query.status is QueryStatus.SUCCESS:
                        self.logger.info("📝 Query evaluated successfully")
                        break

                    self.logger.info("📝 Query evaluation failed - query was incorrect")
                    # Incorrect query → feedback loop

            self.current_query.attempt += 1
        
        if self.testing and self.schema.source == SchemaSource.TEXT:
            self.logger.info("Detected testing mode, asking evaluation even if source is text...")
            self.database_client = MySQLClient(self.database_name)
            self.current_query = self.database_client.execute_query(self.current_query)
            self.current_query.evaluate()
            if self.current_query.status is QueryStatus.SUCCESS:
                self.current_query.initialize_llm_feedback()
                prompt = self._build_feedback_prompt("evaluation")
                response = self.current_query.ask_for_feedback(prompt)
                self.logger.info("📝 Evaluation response: \n%s", response)
                self.current_query.apply_llm_feedback(response)
                self.current_query.evaluate()
            
        self._log_generation_result()

        return self.current_query

    # --------------------------------------------------
    # CONTEXT INITIALIZATION
    # --------------------------------------------------

    def _init_generation_context(self, user_request: str) -> None:
        
        self.logger.info("📝 Initializing generation context...")

        self.schema_context, table_names = self.schema_store.get_context(
            user_request
        )
        
        self.logger.info("📝 Schema context: \n%s", self.schema_context)
        self.logger.info("📝 Table names: %s", table_names)

        if self.query_store is None:
            raise Exception("QueryStore not found")

        if self.schema.source == SchemaSource.MYSQL:
            self.database_client = MySQLClient(self.database_name)
            self.logger.info("📝 Database client initialized")
            self.failed_queries = (
                self.query_store.retrieve_failed_queries(user_request)
                if self.query_store else None
            )
            self.logger.info("📝 Returned %d failed queries", len(self.failed_queries) if self.failed_queries is not None else 0)
            self.join_hints = self.database_client.get_foreign_keys(table_names)
            self.logger.info("📝 Returned %d join hints", len(self.join_hints))
            
        else:
            self.failed_queries = None
            self.join_hints = None

    # --------------------------------------------------
    # SQL GENERATION ATTEMPT
    # --------------------------------------------------

    def _generate_sql_attempt(self, user_request: str) -> None:

        if self.schema_context is None:
            raise Exception("Schema context not found")
        
        self.logger.info("📝 Generating SQL...")
        
        previous_fail = None
        if self.current_query.status not in [QueryStatus.SUCCESS, QueryStatus.PENDING]:
            self.logger.info("📝 Using previous failures from previous attempt")
            previous_fail = self.current_query
        elif self.failed_queries is not None:
            self.logger.info("📝 Using previous failure from query store")
            previous_fail = self.failed_queries

        prompt = self.prompt_builder.query_generation_prompt(
            user_request=user_request,
            schema_context=self.schema_context,
            previous_fail=previous_fail,
            join_hints=self.join_hints,
        )

        self.logger.info("Sending generation prompt to LLM...")
        response = self.llm.generate(prompt)
        
        self.logger.info("📝 Generation response: \n%s", response)
        
        self.current_query.clean_sql_from_llm(response)

    # --------------------------------------------------
    # EXECUTION + EVALUATION
    # --------------------------------------------------

    def _execute_and_evaluate_query(self) -> None:
        if self.database_client is None:
            raise Exception("Database client not found")
        
        self.current_query = self.database_client.execute_query(
            self.current_query
        )

        self.current_query.evaluate()

    # --------------------------------------------------
    # PROMPT BUILDERS
    # --------------------------------------------------

    def _build_feedback_prompt(self, prompt_type: str) -> str:
        
        self.logger.info("📝 Building %s prompt...", prompt_type)

        if prompt_type == "evaluation":
            return self.prompt_builder.evaluation_prompt(
                sql=self.current_query.sql_code, # pyright: ignore[reportArgumentType]
                request=self.request,
                context=self.schema_context, # pyright: ignore[reportArgumentType]
                execution_output=self.current_query.execution_result, # pyright: ignore[reportArgumentType]
            )

        return self.prompt_builder.explanation_prompt(
            sql=self.current_query.sql_code, # pyright: ignore[reportArgumentType]
            context=self.schema_context, # pyright: ignore[reportArgumentType]
            execution_output=self.current_query.execution_result, # pyright: ignore[reportArgumentType]
        )

    # --------------------------------------------------
    # LOGGING
    # --------------------------------------------------

    def _log_generation_result(self) -> None:

        if self.current_query.status is QueryStatus.SUCCESS:
            self.logger.info(
                "✅ Query generated successfully: %s",
                self.current_query.sql_code,
            )
        else:
            self.logger.warning(
                "⚠️ Query generation issue: %s",
                self.current_query.status.value,
            )