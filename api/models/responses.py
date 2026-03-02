from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime


class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str
    error_type: Optional[str] = None


class QueryStatusResponse(BaseModel):
    """Query status information"""
    attempt: int
    status: str
    error_type: Optional[str] = None
    knowledge_scope: Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for query generation"""
    user_request: str
    sql_code: Optional[str] = None
    status: str
    error_type: Optional[str] = None
    knowledge_scope: Optional[str] = None
    execution_result: Optional[Union[str, List[Dict[str, Any]]]] = None
    rows_fetched: Optional[int] = None
    attempts: int
    execution_time: Optional[float] = None
    feedback: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_request": "Show me all users",
                "sql_code": "SELECT * FROM users;",
                "status": "SUCCESS",
                "error_type": None,
                "knowledge_scope": "SCHEMA_SPECIFIC",
                "rows_fetched": 10,
                "attempts": 1
            }
        }


class SchemaResponse(BaseModel):
    """Response model for schema acquisition"""
    database_name: str
    source: str
    tables: List[Dict[str, Any]]
    semantic_notes: List[str]
    schema_id: Optional[str] = None
    table_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "database_name": "test_db",
                "source": "text",
                "tables": [
                    {
                        "name": "users",
                        "columns": [
                            {"name": "id", "type": "INT", "constraints": ["PRIMARY KEY"]}
                        ]
                    }
                ],
                "semantic_notes": [],
                "table_count": 1
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str