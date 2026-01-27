from fastapi import APIRouter
from schema_generator import acquire_schema_from_text, acquire_schema_from_mysql, save_validate_and_build

router = APIRouter()

@router.post("/text")
def create_schema_from_text(raw_text: str):
    schema = acquire_schema_from_text(raw_text)
    save_validate_and_build(schema)
    return {"status": "ok", "schema": schema}

@router.post("/mysql")
def create_schema_from_mysql():
    schema = acquire_schema_from_mysql()
    save_validate_and_build(schema)
    return {"status": "ok", "schema": schema}