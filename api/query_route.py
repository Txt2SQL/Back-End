from fastapi import APIRouter
from pydantic import BaseModel
from services.query_service import generate_sql

router = APIRouter()

class QueryRequest(BaseModel):
    request: str
    model_name: str = "sqlcoder:7b"

@router.post("/")
def generate_query_endpoint(body: QueryRequest):
    sql = generate_sql(body.request, body.model_name)
    return {"sql": sql}
