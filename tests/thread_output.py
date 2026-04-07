import re

from dataclasses import dataclass
from typing import Optional

from src.classes.domain_states import QuerySession, Records, FeedbackStatus

@dataclass
class RequestResult:
    request_index: int
    model_name: str
    query_session: Optional[QuerySession]
    time_taken: float  # seconds
    success: bool  # whether completed without exception
    complexity: int = 0
    evaluation_method: Optional[str] = None
    evaluation_status: Optional[str] = None
    evaluation_verdict: Optional[str] = None
    evaluation_reason: Optional[str] = None
    
    def compute_query_complexity(self):
        sql = self.query_session.sql_code if self.query_session else None
        
        if not sql:
            return

        score = 0   

        # Count joins
        score += len(re.findall(r"\bJOIN\b", sql, re.IGNORECASE)) * 2

        # Aggregations
        score += len(re.findall(r"\b(SUM|AVG|MIN|MAX|COUNT)\s*\(", sql, re.IGNORECASE)) * 2

        # GROUP BY
        if re.search(r"\bGROUP\s+BY\b", sql, re.IGNORECASE):
            score += 2

        # HAVING
        if re.search(r"\bHAVING\b", sql, re.IGNORECASE):
            score += 2

        # Window functions
        score += len(re.findall(r"\bOVER\s*\(", sql, re.IGNORECASE)) * 3

        # Subqueries
        score += len(re.findall(r"\bSELECT\b", sql, re.IGNORECASE)) - 1  # nested SELECTs

        self.complexity = score

    def get_query_complexity(self) -> Optional[int]:
        sql = self.query_session.sql_code if self.query_session else None
        if not sql:
            return None

        if self.complexity == 0:
            self.compute_query_complexity()

        return self.complexity

    @staticmethod
    def complexity_level_from_score(score: float) -> str:
        if score <= 2:
            return "low"
        if score <= 5:
            return "medium"
        return "high"

    def get_complexity_level(self) -> Optional[str]:
        complexity = self.get_query_complexity()
        if complexity is None:
            return None

        return self.complexity_level_from_score(complexity)
    
    def format_output_content(self, index: int) -> str:
        query_session = self.query_session
        lines = []

        lines.append(f"{index}. 🤖[{self.model_name}]\n")
        lines.append(f"🧮 Query:\n\n{query_session.sql_code if query_session else 'N/A'}\n")
        # ----------------------------
        # Status + Outcome formatting
        # ----------------------------
        if self.evaluation_status == "success":
            status_label = "SUCCESS"
        elif self.evaluation_status == "incorrect":
            status_label = "INCORRECT"
        else:
            status_label = query_session.status.value if query_session and query_session.status else "RUNTIME_ERROR"

        execution_result = query_session.execution_result if query_session else None

        if status_label in ("SUCCESS", "INCORRECT"):
            rows_fetched = query_session.rows_fetched if query_session else None
            if rows_fetched is None and isinstance(execution_result, Records):
                rows_fetched = len(execution_result)

            if rows_fetched is not None:
                outcome = f"({rows_fetched} rows fetched)"
            else:
                outcome = "(Query executed successfully)" if status_label == "SUCCESS" else "(Query executed)"
            status_emoji = "🍾SUCCESS" if status_label == "SUCCESS" else "❌INCORRECT"
            lines.append(f"status and outcome: {status_emoji} {outcome}\n")
            if isinstance(execution_result, Records):
                lines.append(f"{execution_result.get_preview()}\n")
            else:
                lines.append(f"{execution_result}\n")
        else:
            error_msg = execution_result if isinstance(execution_result, str) else "Unknown error"
            lines.append(f"status and outcome: ⚠️RUNTIME_ERROR - {error_msg}\n")
        # ----------------------------
        # LLM Feedback formatting
        # ----------------------------
        feedback = query_session.llm_feedback if query_session else None
        if self.evaluation_verdict:
            reason = self.evaluation_reason or ""
            lines.append(f"LLM Feedback: {'👍CORRECT' if self.evaluation_verdict == 'correct' else '👎INCORRECT'}")
            if reason:
                lines.append(f"({reason})\n")
            else:
                lines.append("\n")
        elif status_label == "RUNTIME_ERROR":
            explanation = feedback.explanation if feedback else ""
            lines.append(f"LLM Feedback: {explanation}\n")
        elif feedback and feedback.feedback_status is FeedbackStatus.INCORRECT:
            explanation = feedback.explanation or ""
            category = feedback.error_category.value if feedback.error_category else "UNKNOWN_ERROR"
            lines.append(
                f"LLM Feedback: 👎INCORRECT ({category} - {explanation})\n"
            )
        elif feedback and feedback.feedback_status is FeedbackStatus.CORRECT:
            lines.append("LLM Feedback: 👍CORRECT\n")
        elif feedback is not None:
            lines.append("LLM Feedback: ⚠️UNKNOWN\n")

        # ----------------------------
        # Attempts + Time
        # ----------------------------
        attempts = query_session.attempt if query_session else 0
        lines.append(f"🏁Attempts: {attempts}")
        lines.append(f"⌚Request time: {self.time_taken:.2f}\n")

        return "\n".join(lines)
