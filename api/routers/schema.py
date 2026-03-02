from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List

from api.models.requests import SchemaAcquisitionRequest, SchemaUpdateRequest
from api.models.responses import SchemaResponse, ErrorResponse
from api.services.schema_service import SchemaService
from api.dependencies import get_schema_store, get_data_dir
from src.classes.RAG_service.schema_store import SchemaStore
from pathlib import Path
from src.classes.logger import LoggerManager

router = APIRouter()
logger = LoggerManager.get_logger(__name__)


@router.post("/acquire", 
             response_model=SchemaResponse,
             responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def acquire_schema(
    request: SchemaAcquisitionRequest,
    background_tasks: BackgroundTasks,
    schema_store: SchemaStore = Depends(get_schema_store),
    data_dir: Path = Depends(get_data_dir)
):
    """
    Acquire database schema from source
    
    - **database_name**: Name of the database
    - **source**: Source type ("mysql" or "text")
    - **user_text**: Schema description (required for TEXT source)
    - **model_name**: Optional LLM model selection
    """
    logger.info(f"Received schema acquisition request for database: {request.database_name}")
    
    # Validate text source requires user_text
    if request.source == "text" and not request.user_text:
        raise HTTPException(
            status_code=400, 
            detail="user_text is required when source is 'text'"
        )
    
    try:
        service = SchemaService(
            database_name=request.database_name,
            schema_store=schema_store,
            data_dir=data_dir
        )
        
        result = await service.acquire_schema(
            source=request.source,
            user_text=request.user_text,
            model_name=request.model_name
        )
        
        return result
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/update",
            response_model=SchemaResponse,
            responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def update_schema(
    request: SchemaUpdateRequest,
    schema_store: SchemaStore = Depends(get_schema_store),
    data_dir: Path = Depends(get_data_dir)
):
    """
    Update existing schema with new information
    
    - **database_name**: Name of the database
    - **update_text**: Description of schema update
    - **model_name**: Optional LLM model selection
    """
    logger.info(f"Received schema update request for database: {request.database_name}")
    
    try:
        service = SchemaService(
            database_name=request.database_name,
            schema_store=schema_store,
            data_dir=data_dir
        )
        
        result = await service.update_schema(
            update_text=request.update_text,
            model_name=request.model_name
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{database_name}",
            response_model=SchemaResponse,
            responses={404: {"model": ErrorResponse}})
async def get_schema(
    database_name: str,
    schema_store: SchemaStore = Depends(get_schema_store)
):
    """
    Get schema information for a database
    """
    logger.info(f"Fetching schema for database: {database_name}")
    
    try:
        schema = schema_store.print_collection()
        if not schema:
            raise HTTPException(
                status_code=404,
                detail=f"Schema not found for database: {database_name}"
            )
        return schema
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching schema: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))