from abc import ABC
from classes.domain_states.query import QuerySession
from classes.RAG_service.schema_store import SchemaStore
from classes.RAG_service.query_store import QueryStore
from classes.llm_clients.base import BaseLLM
from classes.database_client import DatabaseClient
from classes.prompt_builder import PromptBuilder
from src.logging_utils import setup_logger

logger = setup_logger(__name__)

class QueryOrchestrator(ABC):
    """
    Handles full SQL generation + evaluation lifecycle.
    """

    def __init__(
        self,
        llm_service: BaseLLM,
        schema_store: SchemaStore,
        query_store: QueryStore,
    ):
        self.llm = llm_service
        self.database_client = database_client
        self.schema_store = schema_store
        self.query_store = query_store
        self.prompt_builder = prompt_builder
        self.max_attempts = max_attempts

    def run(self, user_request: str) -> QuerySession:
        """
        Full SQL generation pipeline with retry loop.
        """

        # 1️⃣ Retrieve schema context
        schema_context = self.schema_store.get_context(user_request)

        # 2️⃣ Retrieve failed queries (negative guidance)
        failed_docs = self.query_store.retrieve_failed_queries(user_request)

        # 3️⃣ Build initial prompt
        prompt = self.prompt_builder.build_sql_prompt(
            user_request=user_request,
            schema_context=schema_context,
            failed_queries=failed_docs,
        )

        attempt = 1
        session = QuerySession(user_request=user_request)

        while attempt <= self.max_attempts:

            # 4️⃣ Generate SQL
            llm_response = self.llm.generate(prompt)
            session.raw_llm_response = llm_response
            session.clean_sql_from_llm()

            # 5️⃣ Execute query
            session = self.database_client.execute_query(session)

            # 6️⃣ Evaluate
            session.evaluate()

            if session.status == "SUCCESS":
                break

            # 7️⃣ Ask LLM for feedback
            feedback_prompt = self.prompt_builder.build_feedback_prompt(
                user_request=user_request,
                sql_query=session.current_query,
                execution_result=session.execution_result,
            )

            feedback_response = self.llm.generate(feedback_prompt)
            session.apply_llm_feedback(feedback_response, attempt=attempt)

            # 8️⃣ Build retry prompt
            prompt = self.prompt_builder.build_retry_prompt(
                original_request=user_request,
                previous_query=session.current_query,
                error_details=session.format_error_feedback(),
                schema_context=schema_context,
            )

            attempt += 1

        # 9️⃣ Store query session in RAG
        self.query_store.store_query(session)

        return session