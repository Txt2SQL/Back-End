from typing import Optional
from config import ERROR_CATEGORIES
from .enums import FeedbackStatus, ErrorType
from src.classes.logger import LoggerManager
from config import QUERY_MODELS


class LLMFeedback:

    def __init__(self):
        self.feedback_status: FeedbackStatus = FeedbackStatus.UNKNOWN
        self.error_category: Optional[ErrorType] = None
        self.explanation: Optional[str] = None
        self.retry_instruction: Optional[str] = None
    
    @property
    def logger(self):
        return LoggerManager.get_logger(__name__)

    # --------------------------------------------------
    # PARSING
    # --------------------------------------------------

    def parse_llm_feedback(self, text: str) -> None:

        if text.upper().startswith("CORRECT"):
            self.logger.info("Feedback starts with 'CORRECT'")
            self.feedback_status = FeedbackStatus.CORRECT
            self.explanation = None
            self.error_category = None
            return

        if text.upper().startswith("INCORRECT"):
            self.logger.info("Feedback starts with 'INCORRECT'")
            self.feedback_status = FeedbackStatus.INCORRECT

            parts = text.split(":", 1)
            self.explanation = parts[1].strip() if len(parts) == 2 else text

            self._classify_error_category()

    # --------------------------------------------------
    # ERROR CLASSIFICATION
    # --------------------------------------------------

    def _classify_error_category(self) -> None:
        self.logger.info("Classifying error category...")

        if not self.explanation:
            self.logger.info("Explanation is empty")
            self.error_category = ErrorType.UNKNOWN_ERROR
            return

        lower = self.explanation.lower()

        for category, keywords in ERROR_CATEGORIES.items():
            for kw in keywords:
                if kw.lower() in lower:
                    self.logger.info("Found error category: %s", category)
                    try:
                        self.logger.info("Assigning error category: %s", category)
                        self.error_category = ErrorType(category)
                    except ValueError:
                        self.logger.error("Invalid error category: %s", category)
                        self.error_category = ErrorType.UNKNOWN_ERROR
                    return

        self.error_category = ErrorType.UNKNOWN_ERROR

    # --------------------------------------------------
    # RETRY INSTRUCTION
    # --------------------------------------------------

    def _build_targeted_retry_instruction(self) -> None:
        self.logger.info(
            "Building retry instruction for error category: %s",
            self.error_category,
        )

        instructions = {
            ErrorType.SEMANTIC_ERROR: (
                "The query does not answer the user's request correctly."
            ),
            ErrorType.SCHEMA_ERROR: (
                "The query references invalid tables or columns."
            ),
            ErrorType.UNKNOWN_ERROR: (
                "Re-evaluate the query carefully to match the request."
            ),
        }

        self.retry_instruction = instructions.get(
            self.error_category or ErrorType.UNKNOWN_ERROR,
            instructions[ErrorType.UNKNOWN_ERROR],
        )

    # --------------------------------------------------
    # OUTPUT
    # --------------------------------------------------

    def format_error_details(self, attempt: int) -> str:

        if attempt >= 2:
            self._build_targeted_retry_instruction()

        return f"""DETAILS: {self.error_category.value if self.error_category else None}

{self.explanation}

""".strip()