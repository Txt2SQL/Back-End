
from typing import Optional
from src.logging_utils import setup_logger
from src.config import ERROR_CATEGORIES

logger = setup_logger(__name__)


class LLMFeedback:

    def __init__(self):
        self.attempt = 1
        self.feedback_status: str = "UNKNOWN"
        self.error_category: Optional[str] = None
        self.explanation: Optional[str] = None
        self.retry_instruction: Optional[str] = None

    def parse_llm_feedback(self, text: str):

        if text.upper().startswith("CORRECT"):
            self.feedback_status = "CORRECT"
            self.explanation = None
            return

        if text.upper().startswith("INCORRECT"):
            self.feedback_status = "INCORRECT"
            parts = text.split(":", 1)
            if len(parts) == 2:
                self.explanation = parts[1].strip()
            else:
                self.explanation = text
            self._classify_error_category()

    def _classify_error_category(self):
        if not self.explanation:
            return

        lower = self.explanation.lower()

        for category, keywords in ERROR_CATEGORIES.items():
            for kw in keywords:
                if kw.lower() in lower:
                    self.error_category = category
                    break

        if not self.error_category:
            self.error_category = "UNKNOWN_ERROR"

    def _build_targeted_retry_instruction(self):
        """
        Build targeted retry instruction based on error category.
        """
        logger.info("Building targeted retry instruction for error category: %s", self.error_category)
        
        instructions = {
            "AGGREGATION_ERROR": (
                "The query has incorrect aggregation logic. "
                "Re-check GROUP BY clauses and aggregated columns."
            ),
            "JOIN_ERROR": (
                "The query has incorrect or missing joins. "
                "Re-evaluate join paths using foreign keys."
            ),
            "FILTER_ERROR": (
                "The query applies incorrect filtering. "
                "Review WHERE conditions carefully."
            ),
            "PROJECTION_ERROR": (
                "The selected columns do not match the request."
            ),
            "SEMANTIC_ERROR": (
                "The query does not answer the user's request correctly."
            ),
            "SCHEMA_ERROR": (
                "The query references invalid tables or columns."
            ),
            "UNKNOWN_ERROR": (
                "Re-evaluate the query carefully to match the request."
            ),
        }

        instruction = instructions.get(self.error_category or "UNKNOWN_ERROR", instructions["UNKNOWN_ERROR"])
        logger.debug("Retry instruction: %s", instruction)
        self.retry_instruction = instruction
        
    def format_error_details(self):
        if self.attempt > 1:
            self._build_targeted_retry_instruction()
        return f"""DETAILS: {self.error_category}

{self.explanation}

{self.retry_instruction if self.retry_instruction else ""}
"""