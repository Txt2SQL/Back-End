from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

from src.classes.domain_states import QuerySession, QueryStatus

# --- Schema Requests ---

class SchemaExtractMySQLRequest(BaseModel):
    database_name: str = Field(..., description="Name of the database to extract from")

class SchemaGenerateTextRequest(BaseModel):
    database_name: str
    raw_text: str = Field(..., description="DDL or description of the schema")
    model_id: str

class SchemaUpdateRequest(BaseModel):
    database_name: str
    update_text: str = Field(..., description="Natural language description of the update")
    model_id: str

# --- Query Requests ---

class QueryGenerationRequest(BaseModel):
    database_name: str
    question: str
    model_id: str


class QuerySessionPayload(BaseModel):
    user_request: Optional[str] = None
    sql_query: Optional[str] = None

    @model_validator(mode="after")
    def validate_payload(self) -> "QuerySessionPayload":
        if self.user_request is None and self.sql_query is None:
            raise ValueError("At least one of 'user_request' or 'sql_query' must be provided")
        return self

    def to_query_session(self) -> QuerySession:
        return QuerySession(
            user_request=self.user_request,
            sql_query=self.sql_query,
        )


class QueryEvaluationRequest(BaseModel):
    database_name: str
    query: QuerySessionPayload
    model_id: str = "gpt-4o"

# --- Responses ---

class QueryResponse(BaseModel):
    sql: str | None
    status: QueryStatus
    results: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    reasoning: Optional[str] = None


class DatabaseListResponse(BaseModel):
    databases: list[str]


class QueryModelListResponse(BaseModel):
    models: list[str]
