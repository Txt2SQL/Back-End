from typing import Optional

from dataclasses import dataclass

@dataclass
class SQLiteExecutionReport:
    sql: str
    rows: Optional[list[tuple]]
    error: Optional[str]
    
    def format_execution_result(self, row_limit: int = 20) -> str:
        parts = [f"SQL: {self.sql}"]
        if self.error is not None:
            parts.append(f"Error: {self.error}")
            return "\n".join(parts)

        rows = self.rows or []
        parts.append(f"Row count: {len(rows)}")
        preview = rows[:row_limit]
        parts.append(f"Rows preview ({len(preview)} shown): {preview}")
        if len(rows) > row_limit:
            parts.append(f"Additional rows omitted: {len(rows) - row_limit}")
        return "\n".join(parts)