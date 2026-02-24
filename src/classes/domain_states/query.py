import sqlglot
import time
import re
from typing import Any, List, Optional, Union
from src.logging_utils import setup_logger
from src.classes.domain_states.feedback import LLMFeedback

logger = setup_logger(__name__)


class QuerySession:

    def __init__(
        self,
        user_request: Optional[str] = None,
        sql_query: Optional[str] = None,
    ):

        if user_request is None and sql_query is None:
            raise ValueError("At least one input must be provided")

        self.user_request = user_request or ""
        self.rows_fetched: Optional[int] = None

        self.sql_code: Optional[str] = sql_query

        self.valid_syntax: Optional[bool] = None
        self.execution_status: Optional[str] = None
        self.execution_result: Union[str, List[Any], None] = None

        self.status: str = "PENDING"
        self.error_type: Optional[str] = None
        self.knowledge_scope: Optional[str] = None
        self.llm_feedback: LLMFeedback = LLMFeedback()

        self.timestamp = time.time()

    # --------------------------------------------------
    # 1️⃣ SQL CLEANING
    # --------------------------------------------------

    def clean_sql_from_llm(self, raw_llm_response: str):
        logger.debug("Cleaning LLM response")
        
        if raw_llm_response is None:
            logger.warning("No LLM response to clean")
            return
        
        sql_query = raw_llm_response

        logger.debug("Original response length: %s characters", len(sql_query))

        # 2. Remove markdown fences safely
        if "```" in sql_query:
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            logger.debug("Removed markdown fences")

        # 4. Remove trailing junk after last semicolon IF present
        if ";" in sql_query:
            sql_query = sql_query[: sql_query.rfind(";") + 1].strip()

        # 5. Final validation
        if not sql_query:
            raise ValueError("LLM returned empty SQL")

        # 6. Ensure terminating semicolon (DO NOT FAIL)
        if not sql_query.endswith(";"):
            logger.warning("SQL query missing terminating semicolon, appending automatically")
            sql_query += ";"

        logger.debug("Cleaned SQL length: %s characters", len(sql_query))

        self.sql_code = sql_query

        logger.debug("Final SQL:\n%s", self.sql_code)
        
        self.validate_syntax()
        

    # --------------------------------------------------
    # 2️⃣ SYNTAX VALIDATION
    # --------------------------------------------------

    def validate_syntax(self):
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
    # 4️⃣ RUNTIME ERROR CLASSIFICATION
    # --------------------------------------------------

    def _classify_runtime_error(self):

        # Priorità al DB error
        if isinstance(self.execution_result, str):
            msg = self.execution_result.lower()

            if "unknown column" in msg:
                self.error_type = "UNKNOWN_COLUMN"
            elif "unknown table" in msg:
                self.error_type = "UNKNOWN_TABLE"
            elif "ambiguous" in msg:
                self.error_type = "AMBIGUOUS_COLUMN"
            elif "join" in msg:
                self.error_type = "BAD_JOIN"
            else:
                self.error_type = "GENERIC_RUNTIME_ERROR"
            return

        # fallback su LLM
        if self.llm_feedback and self.llm_feedback.error_category:
            self.error_type = self.llm_feedback.error_category

    # --------------------------------------------------
    # 5️⃣ KNOWLEDGE SCOPE
    # --------------------------------------------------

    def _detect_knowledge_scope(self):
        if self.valid_syntax is False:
            self.knowledge_scope = "SYNTAX"
            return

        if self._detect_structural_issue():
            self.knowledge_scope = "STRUCTURAL"
            return

        self.knowledge_scope = "SCHEMA_SPECIFIC"

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
    # 6️⃣ FULL EVALUATION
    # --------------------------------------------------

    def evaluate(self):

        self.validate_syntax()

        # 1️⃣ SYNTAX ERROR
        if self.valid_syntax is False:
            self.status = "SYNTAX_ERROR"
            self.error_type = "SYNTAX_ERROR"
            self._detect_knowledge_scope()
            return

        # 2️⃣ RUNTIME ERROR
        if self.execution_status and self.execution_status != "SUCCESS":
            self.status = "RUNTIME_ERROR"
            self._classify_runtime_error()
            self._detect_knowledge_scope()
            return

        # 3️⃣ LLM FEEDBACK (semantic evaluation)
        if self.llm_feedback and self.llm_feedback.feedback_status != "UNKNOWN":

            if self.llm_feedback.feedback_status == "CORRECT":
                self.status = "SUCCESS"
                self.error_type = None
            else:
                self.status = "SEMANTIC_ERROR"
                self.error_type = self.llm_feedback.error_category

            self._detect_knowledge_scope()
            return

        # 4️⃣ Default success
        self.status = "SUCCESS"
        self.error_type = None
        self._detect_knowledge_scope()
        
    def apply_llm_feedback(self, raw_feedback: str, attempt: int = 1):
        feedback = LLMFeedback()
        feedback.attempt = attempt
        feedback.parse_llm_feedback(raw_feedback)
        self.llm_feedback = feedback

    # --------------------------------------------------
    # 7️⃣ OUTPUT
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
            "status": self.status,
            "error_type": self.error_type,
            "knowledge_scope": self.knowledge_scope,
            "outcome": self.execution_status,
            "attempt_count": self.llm_feedback.attempt if self.llm_feedback else 1,
            "feedback_status": self.llm_feedback.feedback_status if self.llm_feedback else None,
            "timestamp": self.timestamp,
        }

        return {
            k: (v if isinstance(v, (str, int, float, bool)) or v is None else str(v))
            for k, v in metadata.items()
        }
    
    def format_error_feedback(self):

        if self.status == "SYNTAX_ERROR":
            title = "The previous SQL query caused a syntax error."
        elif self.status == "RUNTIME_ERROR":
            title = "The previous SQL query failed at runtime."
        elif self.status == "SEMANTIC_ERROR":
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