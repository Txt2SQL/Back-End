import copy
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pathlib import Path
from typing import Optional, List

from src.classes.orchestrators.base_orchestrator import BaseOrchestrator
from src.classes.clients import BaseLLM
from src.classes.domain_states import QuerySession, QueryStatus
from src.classes.RAG_service.schema_store import SchemaStore
from src.classes.RAG_service.query_store import QueryStore
from src.classes.RAG_service.schema_store import Document
from src.classes.clients.mysql_client import MySQLClient
from src.classes.llm_factory import LLMFactory
from src.classes.logger import LoggerManager

from config import DATA_DIR, QUERY_MODELS


class QueryOrchestrator(BaseOrchestrator):
    """
    Orchestrator responsible for SQL query generation and refinement.
    Handles query creation, execution, and learning from failures.
    """

    def __init__(
        self,
        database_name: str,
        schema_store: SchemaStore,
        model_name: str,
        database_client: Optional[MySQLClient] = None,
        query_store: Optional[QueryStore] = None, # query_store should not be created if source = "text"
        max_attempts: int = 4,
        instance_path: Path = DATA_DIR,
    ):
        super().__init__(database_name, instance_path)

        self.llm = LLMFactory.create(QUERY_MODELS[model_name])
        self.schema_store = schema_store
        self.max_attempts = max_attempts

        self.database_client = database_client
        self.query_store = query_store

        self.current_query: Optional[QuerySession] = None
        self.schema_context: Optional[str] = None

        self.join_hints: Optional[List[str]] = None
        self.failed_queries: Optional[List[Document]] = None
        self.evaluator: Optional[BaseLLM] = None
            
    @property
    def logger(self):
        return LoggerManager.get_logger(__name__)

    # --------------------------------------------------
    # MAIN GENERATION LOOP
    # --------------------------------------------------

    def generation(self, user_request: str) -> QuerySession:
        
        self.current_query = QuerySession(user_request)
        
        self.logger.info("📝 Getting inside the query generation...")

        self._init_generation_context(user_request)

        consecutive_runtime_errors = 0
        pre_execution_attempts = 0
        evaluation_attempts = 0
        runtime_error_limit = 10
        evaluation_attempts_limit = 5
        has_executable_query = False

        while True:
            
            self.logger.info("📝 Attempt: %s", self.current_query.attempt)

            # --------------------------------------------------
            # 1️⃣ GENERATE SQL
            # --------------------------------------------------

            self._generate_sql_attempt(user_request)

            if self.current_query.valid_syntax is False:
                self.logger.info("📝 Syntax validation failed")
                pre_execution_attempts += 1

                if pre_execution_attempts >= runtime_error_limit:
                    self.logger.warning(
                        "⚠️ Runtime error limit reached (%d). Stopping generation.",
                        runtime_error_limit,
                    )
                    break
            else:
                self.logger.info("📝 Syntax validation passed")

                if self.database_client is not None:
                    self.evaluation(self.current_query, consecutive_runtime_errors)

                    if self.current_query.status in [QueryStatus.RUNTIME_ERROR, QueryStatus.TIMEOUT_ERROR]:
                        consecutive_runtime_errors += 1
                    else:
                        consecutive_runtime_errors = 0

                    if self.current_query.execution_status is QueryStatus.SUCCESS:
                        has_executable_query = True
                        evaluation_attempts += 1
                    else:
                        pre_execution_attempts += 1
                        if pre_execution_attempts >= runtime_error_limit:
                            self.logger.warning(
                                "⚠️ Runtime error limit reached (%d). Stopping generation.",
                                runtime_error_limit,
                            )
                            break

                    if self.current_query.status is QueryStatus.SUCCESS:
                        break

                    if has_executable_query and evaluation_attempts >= evaluation_attempts_limit:
                        self.logger.warning(
                            "⚠️ Evaluation attempt limit reached (%d). Stopping generation.",
                            evaluation_attempts_limit,
                        )
                        break
                else:
                    break
                
            self.current_query.attempt += 1
            
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

        if self.database_client is not None:
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
        if self.current_query is None:
            raise Exception("Current query not found")
        
        self.logger.info("📝 Generating SQL...")
        
        previous_fail = None
        if self.current_query.status not in [QueryStatus.SUCCESS, QueryStatus.PENDING]:
            self.logger.info("📝 Using previous failures from previous attempt")
            previous_fail = copy.deepcopy(self.current_query)
            self.current_query.reset_for_new_attempt()
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
    
    def evaluation(self, query: QuerySession, consecutive_runtime_errors: int) -> QuerySession:
        if self.database_client is None:
            raise Exception("Database client not found")
        
        self.logger.info("📝 Detected MySQL source, starting execution...")
        
        # --- Execute query ---
        self.logger.info("📝 Executing query...")
        
        self.current_query = self.database_client.execute_query(
            query
        )

        self.current_query.evaluate()
        
        self.evaluator = LLMFactory(QUERY_MODELS["gpt-4o"])
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
                response = self.evaluator.generate(prompt)
                self.logger.info("📝 Explanation: \n%s", response)
                if self.current_query.llm_feedback is None:
                    self.logger.info("📝 Create LLMFeedback object!")
                    raise Exception("LLMFeedback object not found")
                self.current_query.set_explanation_feedback(response)
        else:            
            consecutive_runtime_errors = 0
            
            self.logger.info("📝 Query executed successfully")

            self.current_query.initialize_llm_feedback()
            prompt = self._build_feedback_prompt("evaluation")
            response = self.evaluator.generate(prompt)
            self.logger.info("📝 Evaluation response: \n%s", response)
            self.current_query.apply_llm_feedback(response)
            self.current_query.evaluate()
        
        return self.current_query 

    # --------------------------------------------------
    # PROMPT BUILDERS
    # --------------------------------------------------

    def _build_feedback_prompt(self, prompt_type: str) -> str:
        if self.current_query is None:
            raise Exception("Current query not found")
        if self.schema_context is None:
            self.schema_context, _ = self.schema_store.get_context(self.current_query.user_request)
        
        self.logger.info("📝 Building %s prompt...", prompt_type)

        if prompt_type == "evaluation":
            return self.prompt_builder.evaluation_prompt(
                sql=self.current_query.sql_code,  # pyright: ignore[reportArgumentType]
                request=self.current_query.user_request,
                context=self.schema_context,
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
        if self.current_query is None:
            raise Exception("Current query not found")

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
