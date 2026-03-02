import sqlglot, re
import time
from typing import Any, List, Optional, Union

from .enums import (
    QueryStatus,
    ErrorType,
    KnowledgeScope,
    FeedbackStatus,
)
from src.classes.domain_states.feedback import LLMFeedback
from src.classes.domain_states.records import Records
from src.classes.logger import LoggerManager


class QuerySession:

    def __init__(
        self,
        user_request: Optional[str] = None,
        sql_query: Optional[str] = None,
    ):
        self.attempt: int = 1

        if user_request is None and sql_query is None:
            raise ValueError("At least one input must be provided")

        self.user_request: str = user_request or ""
        self.sql_code: Optional[str] = sql_query

        self.rows_fetched: Optional[int] = None
        self.valid_syntax: Optional[bool] = None
        self.execution_status: Optional[QueryStatus] = None
        self.execution_result: Union[str, Records, None] = None

        self.status: QueryStatus = QueryStatus.PENDING
        self.error_type: Optional[ErrorType] = None
        self.knowledge_scope: Optional[KnowledgeScope] = None

        self.llm_feedback: Optional[LLMFeedback] = None
        self.timestamp: float = time.time()
    
    @property
    def logger(self):
        return LoggerManager.get_logger(__name__)
    
    def initialize_llm_feedback(self):
        self.llm_feedback = LLMFeedback()

    # --------------------------------------------------
    # SQL CLEANING
    # --------------------------------------------------

    def clean_sql_from_llm(self, raw_llm_response: str) -> None:
        self.logger.debug("Cleaning LLM response")

        if not raw_llm_response:
            self.logger.warning("No LLM response to clean")
            return

        sql_query = raw_llm_response

        # 1. Remove specific artifacts found in raw model output (like <0x0A>)
        # These are often literal strings representing control characters
        artifacts = ["<0x0A>", "<0x0D>", "<s>", "</s>", "[SQL]", "[/SQL]"]
        for artifact in artifacts:
            self.logger.debug(f"Removing artifact: {artifact}")
            sql_query = sql_query.replace(artifact, " ")

        # 2. Extract from Markdown code blocks if present (regex is safer than simple replace)
        # Looks for ```sql ... ``` or just ``` ... ```
        code_block_pattern = r"```(?:sql)?\s*(.*?)```"
        match = re.search(code_block_pattern, sql_query, re.DOTALL | re.IGNORECASE)
        if match:
            self.logger.debug("Found code block in LLM response")
            sql_query = match.group(1)

        # 3. Locate the start of the actual SQL query
        # Models often chat before the query: "Here is the code: SELECT..."
        # We look for the first occurrence of common SQL starting keywords.
        keywords = ["SELECT", "WITH", "INSERT", "UPDATE", "DELETE", "SHOW", "DESCRIBE"]
        start_index = len(sql_query)
        found_keyword = False

        upper_query = sql_query.upper()
        for kw in keywords:
            idx = upper_query.find(kw)
            if idx != -1 and idx < start_index:
                self.logger.debug(f"Found keyword: {kw}")
                start_index = idx
                found_keyword = True
        
        if found_keyword:
            sql_query = sql_query[start_index:]

        # 4. Truncate after the last semicolon
        # This removes post-query explanations like "This query calculates..."
        if ";" in sql_query:
            self.logger.debug("Truncating after last semicolon")
            sql_query = sql_query[: sql_query.rfind(";") + 1]

        # 5. Final whitespace cleanup
        sql_query = sql_query.strip()

        # 6. Safety fallback: if the query became empty (e.g., weird parsing), 
        # try to recover the original stripped version
        if not sql_query and raw_llm_response.strip():
            self.logger.debug("Query became empty, trying to recover original")
            sql_query = raw_llm_response.replace("<0x0A>", " ").strip()

        # 7. Ensure it ends with a semicolon
        if sql_query and not sql_query.endswith(";"):
            self.logger.debug("Adding missing semicolon")
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
            self.logger.debug(f"Classifying runtime error: {msg}")
            
            if "unknown column" in msg:
                self.logger.debug("Unknown column error")
                self.error_type = ErrorType.UNKNOWN_COLUMN
            elif "unknown table" in msg:
                self.logger.debug("Unknown table error")
                self.error_type = ErrorType.UNKNOWN_TABLE
            elif "ambiguous" in msg:
                self.logger.debug("Ambiguous column error")
                self.error_type = ErrorType.AMBIGUOUS_COLUMN
            elif "join" in msg:
                self.logger.debug("Bad join error")
                self.error_type = ErrorType.BAD_JOIN
            else:
                self.logger.debug("Generic runtime error")
                self.error_type = ErrorType.GENERIC_RUNTIME_ERROR
            return

        if self.llm_feedback is not None and self.llm_feedback.error_category:
            self.error_type = self.llm_feedback.error_category

    # --------------------------------------------------
    # KNOWLEDGE SCOPE
    # --------------------------------------------------

    def _detect_knowledge_scope(self) -> None:
        self.logger.debug("Detecting knowledge scope")

        if self.valid_syntax is False:
            self.logger.debug("Syntax error detected")
            self.knowledge_scope = KnowledgeScope.SYNTAX
            return

        if self._detect_structural_issue():
            self.logger.debug("Structural issue detected")
            self.knowledge_scope = KnowledgeScope.STRUCTURAL
            return

        self.logger.debug("Schema-specific issue detected")
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
            self.logger.debug("Syntax error detected")
            self.status = QueryStatus.SYNTAX_ERROR
            self.error_type = ErrorType.SYNTAX_ERROR
            self._detect_knowledge_scope()
            return

        if self.execution_status and self.execution_status is not QueryStatus.SUCCESS:
            self.logger.debug("Runtime error detected")
            if self.execution_status is QueryStatus.TIMEOUT_ERROR:
                self.logger.debug("Timeout error detected")
                self.status = QueryStatus.TIMEOUT_ERROR
            else:
                self.status = QueryStatus.RUNTIME_ERROR
            self._classify_runtime_error()
            self._detect_knowledge_scope()
            return

        if self.llm_feedback is not None and self.llm_feedback.feedback_status is FeedbackStatus.CORRECT:
            self.logger.debug("Correct feedback detected")
            self.status = QueryStatus.SUCCESS
            self.error_type = None

        elif self.llm_feedback is not None and self.llm_feedback.feedback_status is FeedbackStatus.INCORRECT:
            self.logger.debug("Incorrect feedback detected")
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
        if self.llm_feedback is not None:
            self.llm_feedback.parse_llm_feedback(raw_feedback)
    
    def ask_for_feedback(self, prompt: str) -> str:
        if self.llm_feedback is not None:
            return self.llm_feedback.evaluator.generate(prompt)
        else:
            raise ValueError("No LLM feedback available")
            

    # --------------------------------------------------
    # OUTPUT
    # --------------------------------------------------

    def to_content_block(self) -> str:
        return f"""
User request:
{self.user_request}

Generated SQL:
{self.sql_code}

Status: {self.status.value}
Error type: {self.error_type.value if self.error_type else None}
Knowledge scope: {self.knowledge_scope.value if self.knowledge_scope else None}
""".strip()

    def to_document_metadata(self) -> dict:

        metadata = {
            "user_request": self.user_request,
            "sql_query": self.sql_code,
            "status": self.status.value,
            "error_type": self.error_type.value if self.error_type else None,
            "knowledge_scope": self.knowledge_scope.value if self.knowledge_scope else None,
            "outcome": self.execution_status,
            "attempt_count": self.attempt,
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
        elif self.status is QueryStatus.TIMEOUT_ERROR:
            title = "The previous SQL query timed out during execution."
        elif self.status is QueryStatus.RUNTIME_ERROR:
            title = "The previous SQL query failed at runtime."
        elif self.status is QueryStatus.INCORRECT:
            title = "The previous SQL query was semantically incorrect."
        else:
            title = "The previous SQL query was incorrect."

        details = ""

        if self.llm_feedback and self.status is not QueryStatus.SYNTAX_ERROR:
            details = self.llm_feedback.format_error_details(self.attempt)

        if not self.sql_code:
            return ""
        
        return f"""{title}

    SQL QUERY:

    {self.sql_code}

    {details}
    """