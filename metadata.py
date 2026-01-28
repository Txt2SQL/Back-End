from dataclasses import dataclass, field
from typing import Optional
import time

@dataclass
class UIMetadata:
    # --- Core identity ---
    schema_id: Optional[str]
    user_request: str
    model_name: str
    status: str  # OK | SYNTAX_ERROR | RUNTIME_ERROR | WRONG_RESULT

    # --- Execution info ---
    rows_fetched: int = 0
    error_message: Optional[str] = None