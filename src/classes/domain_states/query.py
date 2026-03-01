import sqlglot
import time
from typing import Any, List, Optional, Union

from .enums import (
    QueryStatus,
    ErrorType,
    KnowledgeScope,
    FeedbackStatus,
)
from src.classes.domain_states.feedback import LLMFeedback
from classes.logger_manager import LoggerManager

logger = LoggerManager.get_logger(__name__)


class QuerySession:

    def __init__(
        self,
        user_request: Optional[str] = None,
        sql_query: Optional[str] = None,
    ):

        if user_request is None and sql_query is None:
            raise ValueError("At least one input must be provided")

        self.user_request: str = user_request or ""
        self.sql_code: Optional[str] = sql_query

        self.rows_fetched: Optional[int] = None
        self.valid_syntax: Optional[bool] = None
        self.execution_status: Optional[str] = None
        self.execution_result: Union[str, List[Any], None] = None

        self.status: QueryStatus = QueryStatus.PENDING
        self.error_type: Optional[ErrorType] = None
        self.knowledge_scope: Optional[KnowledgeScope] = None

        self.llm_feedback: LLMFeedback = LLMFeedback()
        self.timestamp: float = time.time()

    # --------------------------------------------------
    # SQL CLEANING
    # --------------------------------------------------

    def clean_sql_from_llm(self, raw_llm_response: str) -> None:
        logger.debug("Cleaning LLM response")

        if not raw_llm_response:
            logger.warning("No LLM response to clean")
            return

        sql_query = raw_llm_response

        if "```" in sql_query:
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

        if ";" in sql_query:
            sql_query = sql_query[: sql_query.rfind(";") + 1].strip()

        if not sql_query:
            raise ValueError("LLM returned empty SQL")

        if not sql_query.endswith(";"):
            sql_query += ";"

        self.sql_code = sql_query
        self.validate_syntax()

    # --------------------------------------------------
    # SYNTAX VALIDATION
    # --------------------------------------------------

    def validate_syntax(self) -> None:
        if not self.sql_code:
            self.valid_syntax = False
            return

        try:
            sqlglot.parse_one(self.sql_code)
            self.valid_syntax = True
        except Exception as e:
            self.valid_syntax = False
            self.execution_result = str(e)

    # --------------------------------------------------
    # RUNTIME ERROR CLASSIFICATION
    # --------------------------------------------------

    def _classify_runtime_error(self) -> None:

        if isinstance(self.execution_result, str):
            msg = self.execution_result.lower()

            if "unknown column" in msg:
                self.error_type = ErrorType.UNKNOWN_COLUMN
            elif "unknown table" in msg:
                self.error_type = ErrorType.UNKNOWN_TABLE
            elif "ambiguous" in msg:
                self.error_type = ErrorType.AMBIGUOUS_COLUMN
            elif "join" in msg:
                self.error_type = ErrorType.BAD_JOIN
            else:
                self.error_type = ErrorType.GENERIC_RUNTIME_ERROR
            return

        if self.llm_feedback.error_category:
            self.error_type = self.llm_feedback.error_category

    # --------------------------------------------------
    # KNOWLEDGE SCOPE
    # --------------------------------------------------

    def _detect_knowledge_scope(self) -> None:
        if self.valid_syntax is False:
            self.knowledge_scope = KnowledgeScope.SYNTAX
            return

        if self._detect_structural_issue():
            self.knowledge_scope = KnowledgeScope.STRUCTURAL
            return

        self.knowledge_scope = KnowledgeScope.SCHEMA_SPECIFIC

    def _detect_structural_issue(self) -> bool:
        if not self.sql_code:
            return False

        sql_upper = self.sql_code.upper()

        return (
            "SELECT *" in sql_upper
            or ("JOIN" in sql_upper and " ON " not in sql_upper)
            or ("SUM(" in sql_upper and "GROUP BY" not in sql_upper)
        )

    # --------------------------------------------------
    # FULL EVALUATION
    # --------------------------------------------------

    def evaluate(self) -> None:

        self.validate_syntax()

        if self.valid_syntax is False:
            self.status = QueryStatus.SYNTAX_ERROR
            self.error_type = ErrorType.SYNTAX_ERROR
            self._detect_knowledge_scope()
            return

        if self.execution_status and self.execution_status != "SUCCESS":
            self.status = QueryStatus.RUNTIME_ERROR
            self._classify_runtime_error()
            self._detect_knowledge_scope()
            return

        if self.llm_feedback.feedback_status is FeedbackStatus.CORRECT:
            self.status = QueryStatus.SUCCESS
            self.error_type = None

        elif self.llm_feedback.feedback_status is FeedbackStatus.INCORRECT:
            self.status = QueryStatus.INCORRECT
            self.error_type = (
                self.llm_feedback.error_category
                or ErrorType.SEMANTIC_ERROR
            )

        else:
            self.status = QueryStatus.SUCCESS
            self.error_type = None

        self._detect_knowledge_scope()

    # --------------------------------------------------
    # APPLY FEEDBACK
    # --------------------------------------------------

    def apply_llm_feedback(self, raw_feedback: str) -> None:
        self.llm_feedback.parse_llm_feedback(raw_feedback)

    # --------------------------------------------------
    # OUTPUT
    # --------------------------------------------------

    def to_content_block(self) -> str:
        return f"""
User request:
{self.user_request}

Generated SQL:
{self.sql_code}

Status: {self.status}
Error type: {self.error_type}
Knowledge scope: {self.knowledge_scope}
""".strip()

    def to_document_metadata(self) -> dict:

        metadata = {
            "user_request": self.user_request,
            "sql_query": self.sql_code,
            "status": self.status.value,
            "error_type": self.error_type.value if self.error_type else None,
            "knowledge_scope": self.knowledge_scope.value if self.knowledge_scope else None,
            "outcome": self.execution_status,
            "attempt_count": self.llm_feedback.attempt,
            "feedback_status": self.llm_feedback.feedback_status if self.llm_feedback else None,
            "timestamp": self.timestamp,
        }

        return {
            k: (v if isinstance(v, (str, int, float, bool)) or v is None else str(v))
            for k, v in metadata.items()
        }
    
    def format_error_feedback(self):

        if self.status is QueryStatus.SYNTAX_ERROR:
            title = "The previous SQL query caused a syntax error."
        elif self.status is QueryStatus.RUNTIME_ERROR:
            title = "The previous SQL query failed at runtime."
        elif self.status is QueryStatus.INCORRECT:
            title = "The previous SQL query was semantically incorrect."
        else:
            title = "The previous SQL query was incorrect."

        details = ""

        if self.llm_feedback:
            details = self.llm_feedback.format_error_details()

        if not self.sql_code:
            return ""
        
        return f"""{title}

    SQL QUERY:

    {self.sql_code}

    {details}
    """