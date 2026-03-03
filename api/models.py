from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from src.classes.domain_states.enums import QueryStatus

# --- Schema Requests ---

class SchemaExtractMySQLRequest(BaseModel):
    database_name: str = Field(..., description="Name of the database to extract from")

class SchemaGenerateTextRequest(BaseModel):
    database_name: str
    raw_text: str = Field(..., description="DDL or description of the schema")
    model_id: str = "gpt-4o"

class SchemaUpdateRequest(BaseModel):
    database_name: str
    update_text: str = Field(..., description="Natural language description of the update")
    model_id: str = "gpt-4o"

# --- Query Requests ---

class QueryRequest(BaseModel):
    database_name: str
    question: str
    model_id: str = "gpt-4o"

# --- Responses ---

class QueryResponse(BaseModel):
    sql: Optional[str]
    status: QueryStatus
    results: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    reasoning: Optional[str] = None