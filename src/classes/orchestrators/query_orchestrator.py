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

logger = LoggerManager.get_logger(__name__)


class QueryOrchestrator(BaseOrchestrator):
    """
    Orchestrator responsible for SQL query generation and refinement.
    Handles query creation, execution, and learning from failures.
    """

    def __init__(
        self,
        database_name: str,
        schema_store: SchemaStore,
        user_request: str,
        query_store: Optional[QueryStore] = None, # query_store should not be created if source = "text"
        model_name: Optional[str] = None,
        max_attempts: int = 3,
        instance_path: Path = DATA_DIR,
    ):
        super().__init__(database_name, instance_path, model_name)

        self.max_attempts = max_attempts
        self.schema_store = schema_store
        self.query_store = query_store
        self.database_client: Optional[MySQLClient] = None
        self.request = user_request

        self.current_query: QuerySession = QuerySession(user_request=user_request)
        self.schema_context: Optional[str] = None

        self.join_hints: Optional[List[str]] = None
        self.failed_queries: Optional[List[Document]] = None

        self._load_schema()

    # --------------------------------------------------
    # LLM INITIALIZATION
    # --------------------------------------------------

    def _initialize_llm(self, choice: str | None) -> BaseLLM | None:
        logger.info("Getting LLM model for choice: %s", choice)

        if choice is None:
            return None

        model_config = QUERY_GENERATION_MODELS[choice]
        model_name = model_config["id"]

        if model_config["provider"] == "azure":
            return AzureLLM(model_name)

        return OpenWebUILLM(model_name)

    # --------------------------------------------------
    # SCHEMA LOADING
    # --------------------------------------------------

    def _load_schema(self) -> None:
        schema_path = self.instance_path / "schema" / f"{self.database_name}_schema.json"

        if not schema_path.exists():
            logger.warning("Schema file not found: %s", schema_path)
            self.schema = None
            return

        with schema_path.open("r", encoding="utf-8") as schema_file:
            schema_data = json.load(schema_file)

        if not schema_data:
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

        self.schema = schema

    # --------------------------------------------------
    # MAIN GENERATION LOOP
    # --------------------------------------------------

    def generation(self, user_request: str) -> QuerySession:

        logger.info(
            "Generating SQL for request: %s",
            LoggerManager.truncate_request(user_request),
        )

        if self.schema is None:
            raise Exception("Schema not found for database")

        self._init_generation_context(user_request)

        while self.current_query.llm_feedback.attempt <= self.max_attempts:

            logger.info("Attempt #%s", self.current_query.llm_feedback.attempt)

            self._generate_sql_attempt(user_request)

            # TEXT MODE → Only syntax validation
            if self.schema.source == SchemaSource.TEXT:
                if self.current_query.valid_syntax:
                    break
                self.current_query.llm_feedback.attempt += 1
                continue

            # MYSQL MODE
            self._execute_and_evaluate_query()

            if (
                self.current_query.llm_feedback.feedback_status
                is FeedbackStatus.CORRECT
            ):
                break

            self.current_query.llm_feedback.attempt += 1

        if self.schema.source == SchemaSource.MYSQL:
            if self.query_store is None:
                raise Exception("QueryStore not found")
            self.query_store.store_query(self.current_query)
        self._log_generation_result()

        return self.current_query

    # --------------------------------------------------
    # CONTEXT INITIALIZATION
    # --------------------------------------------------

    def _init_generation_context(self, user_request: str) -> None:

        self.schema_context, table_names = self.schema_store.get_context(
            user_request
        )

        if self.schema is None:
            raise Exception("Schema not found")
        if self.query_store is None:
            raise Exception("QueryStore not found")

        if self.schema.source == SchemaSource.MYSQL:
            self.database_client = MySQLClient(self.database_name)
            self.failed_queries = self.query_store.retrieve_failed_queries(
                user_request
            )
            self.join_hints = self.database_client.get_foreign_keys(
                table_names
            )
        else:
            self.failed_queries = None
            self.join_hints = None

    # --------------------------------------------------
    # SQL GENERATION ATTEMPT
    # --------------------------------------------------

    def _generate_sql_attempt(self, user_request: str) -> None:

        if self.schema_context is None:
            raise Exception("Schema context not found")

        error_feedback = self.current_query.llm_feedback.explanation

        prompt = self.prompt_builder.query_generation_prompt(
            user_request=user_request,
            schema_context=self.schema_context,
            previous_fail=self.failed_queries if not error_feedback else None,
            join_hints=self.join_hints,
        )

        response = self.llm.generate(prompt) if self.llm else ""
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
        self._request_feedback_if_needed()

    # --------------------------------------------------
    # FEEDBACK MANAGEMENT
    # --------------------------------------------------

    def _request_feedback_if_needed(self) -> None:

        prompt_type = self._should_request_feedback()

        if prompt_type and self.llm:
            prompt = self._build_feedback_prompt(prompt_type)
            response = self.llm.generate(prompt)
            self.current_query.apply_llm_feedback(response)

    def _should_request_feedback(self) -> Optional[str]:

        query = self.current_query

        if not query.sql_code or not self.schema_context:
            return None

        # SUCCESS case with results
        if (
            query.status is QueryStatus.SUCCESS
            and isinstance(query.execution_result, list)
            and len(query.execution_result) > 0
        ):
            return "evaluation"

        # RUNTIME ERROR case (after first attempt)
        if (
            query.status is QueryStatus.RUNTIME_ERROR
            and query.llm_feedback.attempt > 1
            and isinstance(query.execution_result, str)
            and query.execution_result
        ):
            return "explanation"

        return None

    # --------------------------------------------------
    # PROMPT BUILDERS
    # --------------------------------------------------

    def _build_feedback_prompt(self, prompt_type: str) -> str:

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
            logger.info(
                "✅ Query generated successfully: %s",
                self.current_query.sql_code,
            )
        else:
            logger.warning(
                "⚠️ Query generation issue: %s",
                self.current_query.status.value,
            )