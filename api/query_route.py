from fastapi import APIRouter
from pydantic import BaseModel
from services.query_service import generate_sql, execute_sql

router = APIRouter()

class QueryRequest(BaseModel):
    request: str
    model_name: str

class QueryCode:
    code: str

@router.post("/generate")
def generate_query_endpoint(body: QueryRequest):
    sql = generate_sql(body.request, body.model_name)
    return {"sql": sql}

@router.post("/execute")
def execute_query_endpoint(sql: QueryCode):
    outcome = execute_sql(sql.code)
    return {"outcome": outcome}