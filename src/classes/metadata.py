from dataclasses import dataclass, field
from typing import Optional
import time

@dataclass
class QueryMetadata:
    # --- Core identity ---
    schema_id: Optional[str]
    schema_source: str
    user_request: str
    model_name: str | None
    status: str  # OK | SYNTAX_ERROR | RUNTIME_ERROR

    # --- Execution info ---
    rows_fetched: int = 0
    error_message: Optional[str] = None
    
    # --- Derived / internal ---
    knowledge_scope: Optional[str] = None
    error_type: Optional[str] = None
    LLM_feedback: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    
    def to_document_metadata(self, sql_query: str) -> dict:
        raw = {
            "request": self.user_request,
            "schema_id": self.schema_id,
            "schema_source": self.schema_source,
            "knowledge_scope": self.knowledge_scope,
            "status": self.status,
            "model": self.model_name,
            "timestamp": time.time(),
            "sql_query": sql_query,
            "rows_fetched": self.rows_fetched,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "error_category": self.LLM_feedback
        }

        clean = {}
        for k, v in raw.items():
            if isinstance(v, (str, int, float, bool)) or v is None:
                clean[k] = v
            else:
                clean[k] = str(v)  # ← last-resort safety

        return clean

    def to_page_content(self, sql_query: str) -> str:
        return f"""
User request:
{self.user_request}

Generated SQL query:
{sql_query}

Outcome: {self.status}
""".strip()