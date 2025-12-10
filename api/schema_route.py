from fastapi import APIRouter
from pydantic import BaseModel
from services.schema_services import generate_schema, update_schema

router = APIRouter()

class SchemaUpdateRequest(BaseModel):
    text: str

@router.post("/generate")
def generate_schema_endpoint(body: SchemaUpdateRequest):
    schema = generate_schema(body.text)
    return {"schema": schema}

@router.post("/update")
def update_schema_endpoint(body: SchemaUpdateRequest):
    schema = update_schema(body.text)
    return {"schema": schema}
