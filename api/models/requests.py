from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from src.classes.domain_states.enums import SchemaSource


class QueryGenerationRequest(BaseModel):
    """Request model for query generation"""
    database_name: str = Field(..., description="Name of the database")
    user_request: str = Field(..., description="Natural language request for SQL query")
    model_name: Optional[str] = Field("gpt-4", description="LLM model to use")
    max_attempts: Optional[int] = Field(4, description="Maximum generation attempts", ge=1, le=10)
    testing: Optional[bool] = Field(False, description="Enable testing mode")


class SchemaAcquisitionRequest(BaseModel):
    """Request model for schema acquisition"""
    database_name: str = Field(..., description="Name of the database")
    source: SchemaSource = Field(SchemaSource.TEXT, description="Schema source")
    user_text: Optional[str] = Field(None, description="Schema description text (required for TEXT source)")
    model_name: Optional[str] = Field("gpt-4", description="LLM model to use")


class SchemaUpdateRequest(BaseModel):
    """Request model for schema update"""
    database_name: str = Field(..., description="Name of the database")
    update_text: str = Field(..., description="Update description")
    model_name: Optional[str] = Field("gpt-4", description="LLM model to use")


class QueryExecutionRequest(BaseModel):
    """Request model for executing an existing query"""
    database_name: str = Field(..., description="Name of the database")
    sql_query: str = Field(..., description="SQL query to execute")