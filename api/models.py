from typing import Any

from pydantic import BaseModel, Field, model_validator

from src.classes.domain_states import QueryStatus

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

class QueryPayload(BaseModel):
    user_request: str | None = None
    sql_query: str | None = None

    @model_validator(mode="after")
    def validate_query_input(self) -> "QueryPayload":
        if self.user_request is None and self.sql_query is None:
            raise ValueError("At least one of 'user_request' or 'sql_query' must be provided")
        return self

class QueryEvaluationRequest(BaseModel):
    database_name: str
    query: QueryPayload
    model_id: str = "gpt-4o"

# --- Responses ---

class QueryResponse(BaseModel):
    sql: str | None
    status: QueryStatus
    results: list[dict[str, Any]] | None = None
    error: str | None = None
    reasoning: str | None = None


class DatabaseListResponse(BaseModel):
    databases: list[str]


class QueryModelListResponse(BaseModel):
    models: list[str]
