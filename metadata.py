from dataclasses import dataclass, field
from typing import Optional
import time

@dataclass
class QueryMetadata:
    # --- Core identity ---
    schema_id: Optional[str]
    user_request: str
    model_name: str
    status: str  # OK | SYNTAX_ERROR | RUNTIME_ERROR

    # --- Execution info ---
    rows_fetched: int = 0
    error_message: Optional[str] = None
    
    # --- Derived / internal ---
    knowledge_scope: Optional[str] = None
    error_type: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    
    def to_document_metadata(self, sql_query: str) -> dict:
        base = {
            "schema_id": self.schema_id,
            "knowledge_scope": self.knowledge_scope,
            "status": self.status,
            "model": self.model_name,
            "timestamp": time.time(),
            "sql_query": sql_query,
        }

        if self.error_message:
            base["error_type"] = self.error_type
        else:
            base["rows_fetched"] = self.rows_fetched

        return base

    def to_page_content(self, sql_query: str) -> str:
        return f"""
User request:
{self.user_request}

Generated SQL query:
{sql_query}

Outcome: {self.status}
""".strip()