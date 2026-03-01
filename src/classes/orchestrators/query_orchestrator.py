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
from src.classes.domain_states import QueryStatus, FeedbackStatus, SchemaSource



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
        max_attempts: int = 3,
        instance_path: Path = DATA_DIR,
    ):
        super().__init__(schema.database_name, instance_path, model_name)

        self.schema = schema
        self.schema_store = schema_store
        self.query_store = query_store
        self.request = user_request
        self.max_attempts = max_attempts

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

        return OpenWebUILLM(model_name)

    # --------------------------------------------------
    # MAIN GENERATION LOOP
    # --------------------------------------------------

    def generation(self, user_request: str) -> QuerySession:
        
        self.logger.info("📝 Getting inside the query generation...")

        self._init_generation_context(user_request)

        consecutive_runtime_errors = 0

        while self.current_query.llm_feedback.attempt <= self.max_attempts:
            
            self.logger.info("📝 Attempt: %s", self.current_query.llm_feedback.attempt)

            # --------------------------------------------------
            # 1️⃣ GENERATE SQL
            # --------------------------------------------------

            self._generate_sql_attempt(user_request)

            # --------------------------------------------------
            # TEXT MODE
            # --------------------------------------------------
            if self.schema.source == SchemaSource.TEXT:

                self.current_query.evaluate()

                if self.current_query.status is QueryStatus.SUCCESS:
                    return self.current_query

                # Syntax error → feedback loop
                feedback = self.current_query.format_error_feedback()
                self.current_query.llm_feedback.explanation = feedback
                self.current_query.llm_feedback.attempt += 1
                continue

            # --------------------------------------------------
            # MYSQL MODE
            # --------------------------------------------------

            # --- Syntax validation first ---
            self.current_query.validate_syntax()

            if self.current_query.valid_syntax is False:
                
                self.logger.info("📝 Syntax validation failed")

                self.current_query.evaluate()
                feedback = self.current_query.format_error_feedback()
                self.current_query.llm_feedback.explanation = feedback
                self.current_query.llm_feedback.attempt += 1
                continue
            
            self.logger.info("📝 Syntax validation passed")

            self.logger.info("📝 Executing query...")

            # --- Execute query ---
            self._execute_and_evaluate_query()

            # --------------------------------------------------
            # Runtime error handling
            # --------------------------------------------------
            if self.current_query.status is not QueryStatus.SUCCESS:
                
                self.logger.info("📝 Runtime error occurred")

                consecutive_runtime_errors += 1

                # On second consecutive runtime error → ask explanation
                if consecutive_runtime_errors >= 2:
                    self.logger.info("📝 Asking for explanation...")
                    prompt = self._build_feedback_prompt("explanation")
                    response = self.llm.generate(prompt)
                    self.current_query.apply_llm_feedback(response)

                feedback = self.current_query.format_error_feedback()
                self.current_query.llm_feedback.explanation = feedback
                self.current_query.llm_feedback.attempt += 1
                continue

            else:
                consecutive_runtime_errors = 0

            # --------------------------------------------------
            # If execution success → ask correctness evaluation
            # --------------------------------------------------
            if self.current_query.status is QueryStatus.SUCCESS:
                
                self.logger.info("📝 Query executed successfully")

                prompt = self._build_feedback_prompt("evaluation")
                response = self.llm.generate(prompt)
                self.current_query.apply_llm_feedback(response)
                self.current_query.evaluate()

                if self.current_query.status is QueryStatus.SUCCESS:
                    self.logger.info("📝 Query evaluated successfully")
                    return self.current_query

                self.logger.info("📝 Query evaluation failed")
                # Incorrect query → feedback loop
                feedback = self.current_query.format_error_feedback()
                self.current_query.llm_feedback.explanation = feedback
                self.current_query.llm_feedback.attempt += 1
                continue
            
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
            self.evaluator = AzureLLM("gpt-4o")
            
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
        join_hints = None

        if self.schema.source == SchemaSource.MYSQL:
            previous_fail = self.current_query or self.failed_queries
            join_hints = self.join_hints

        prompt = self.prompt_builder.query_generation_prompt(
            user_request=user_request,
            schema_context=self.schema_context,
            previous_fail=previous_fail,
            join_hints=join_hints,
        )

        response = self.llm.generate(prompt) if self.llm else ""
        self.current_query.clean_sql_from_llm(response)

    # --------------------------------------------------
    # EXECUTION + EVALUATION
    # --------------------------------------------------

    def _execute_and_evaluate_query(self) -> None:
        if self.database_client is None:
            raise Exception("Database client not found")

        self.current_query.llm_feedback.feedback_status = FeedbackStatus.UNKNOWN
        self.current_query.llm_feedback.error_category = None
        
        self.current_query = self.database_client.execute_query(
            self.current_query
        )

        self.current_query.evaluate()
        self._request_feedback_if_needed()

    # --------------------------------------------------
    # FEEDBACK MANAGEMENT
    # --------------------------------------------------

    def _request_feedback_if_needed(self) -> None:
        
        self.logger.info("📝 Requesting feedback if needed...")

        prompt_type = self._should_request_feedback()

        if prompt_type and self.evaluator:
            prompt = self._build_feedback_prompt(prompt_type)
            response = self.evaluator.generate(prompt)
            self.logger.info("📝 Feedback response: %s", response)
            self.current_query.apply_llm_feedback(response)

    def _should_request_feedback(self) -> Optional[str]:

        self.logger.info("📝 Checking if feedback is needed...")

        query = self.current_query

        if not query.sql_code or not self.schema_context:
            return None

        # SUCCESS case with results
        if (
            query.status is QueryStatus.SUCCESS
            and isinstance(query.execution_result, list)
            and len(query.execution_result) > 0
        ):
            self.logger.info("📝 Feedback evaluation needed")

            return "evaluation"

        # RUNTIME ERROR case (after first attempt)
        if (
            query.status is QueryStatus.RUNTIME_ERROR
            and query.llm_feedback.attempt > 1
            and isinstance(query.execution_result, str)
            and query.execution_result
        ):
            self.logger.info("📝 Feedback explanation needed")

            return "explanation"

        return None

    # --------------------------------------------------
    # PROMPT BUILDERS
    # --------------------------------------------------

    def _build_feedback_prompt(self, prompt_type: str) -> str:
        
        self.logger.info("📝 Building feedback prompt...")

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