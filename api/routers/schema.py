from fastapi import APIRouter, HTTPException, Body
from src.classes.orchestrators.schema_orchestrator import SchemaOrchestrator
from api.models import (
    SchemaExtractMySQLRequest, 
    SchemaGenerateTextRequest, 
    SchemaUpdateRequest
)
from api.dependencies import get_schema_store, get_mysql_client, get_llm

router = APIRouter(prefix="/schema", tags=["Schema"])

@router.post("/mysql")
def extract_schema_mysql(payload: SchemaExtractMySQLRequest):
    """Extract schema directly from the connected MySQL database."""
    try:
        schema_store = get_schema_store()
        db_client = get_mysql_client(payload.database_name)
        
        # Initialize Orchestrator
        orchestrator = SchemaOrchestrator(
            database_name=payload.database_name,
            schema_store=schema_store,
            database_client=db_client,
            llm=None # LLM not needed for raw extraction
        )
        
        result_schema = orchestrator.acquire_new_schema()
        return {"message": "Schema extracted successfully", "schema": result_schema.tables}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/text")
def generate_schema_text(payload: SchemaGenerateTextRequest):
    """Generate schema from raw text/DDL using LLM."""
    try:
        schema_store = get_schema_store()
        llm = get_llm(payload.model_id, "schema")
        
        orchestrator = SchemaOrchestrator(
            database_name=payload.database_name,
            schema_store=schema_store,
            llm=llm
        )
        
        result_schema = orchestrator.acquire_new_schema(user_text=payload.raw_text)
        return {"message": "Schema generated successfully", "schema": result_schema.tables}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("")
def update_schema(payload: SchemaUpdateRequest):
    """Update existing schema with natural language."""
    try:
        schema_store = get_schema_store()
        llm = get_llm(payload.model_id, "schema")
        
        orchestrator = SchemaOrchestrator(
            database_name=payload.database_name,
            schema_store=schema_store,
            llm=llm
        )
        
        # Ensure json is ready (load from disk)
        if not orchestrator.schema.json_ready:
             raise HTTPException(status_code=404, detail="Schema not found. Create it first.")

        updated_schema = orchestrator.update_current_schema(user_text=payload.update_text)
        return {"message": "Schema updated successfully", "schema": updated_schema.tables}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
def get_schema(database_name: str):
    """Retrieve the current JSON schema."""
    try:
        # We can reuse the orchestrator to load the schema
        # or access the Store/Schema object directly.
        schema_store = get_schema_store()
        
        # Assuming SchemaStore has a method to get the dict, 
        # or we instantiate Schema object to load file.
        # Here we use the Orchestrator logic to load from file:
        orchestrator = SchemaOrchestrator(
             database_name=database_name,
             schema_store=schema_store,
             llm=None # Not needed for read-only
        )
        
        if orchestrator.schema.json_ready:
            return orchestrator.schema.tables
        else:
            raise HTTPException(status_code=404, detail="Schema not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))