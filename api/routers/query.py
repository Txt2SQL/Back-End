from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List

from api.models.requests import QueryGenerationRequest, QueryExecutionRequest
from api.models.responses import QueryResponse, ErrorResponse
from api.services.query_service import QueryService
from api.dependencies import get_schema_store, get_query_store, get_data_dir
from src.classes.RAG_service.schema_store import SchemaStore
from src.classes.RAG_service.query_store import QueryStore
from pathlib import Path
from src.classes.logger import LoggerManager

router = APIRouter()
logger = LoggerManager.get_logger(__name__)


@router.post("/generate", 
             response_model=QueryResponse,
             responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def generate_query(
    request: QueryGenerationRequest,
    background_tasks: BackgroundTasks,
    schema_store: SchemaStore = Depends(get_schema_store),
    query_store: QueryStore = Depends(get_query_store),
    data_dir: Path = Depends(get_data_dir)
):
    """
    Generate SQL query from natural language request
    
    - **database_name**: Name of the target database
    - **user_request**: Natural language description of desired query
    - **model_name**: Optional LLM model selection
    - **max_attempts**: Maximum number of generation attempts
    """
    logger.info(f"Received query generation request for database: {request.database_name}")
    
    try:
        service = QueryService(
            database_name=request.database_name,
            schema_store=schema_store,
            query_store=query_store,
            data_dir=data_dir
        )
        
        result = await service.generate_query(
            user_request=request.user_request,
            model_name=request.model_name,
            max_attempts=request.max_attempts or 3,
            testing=request.testing or False
        )
        
        # Optionally store in background
        if result.status == "SUCCESS":
            background_tasks.add_task(
                service.store_successful_query,
                result
            )
        
        return result
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/history/{database_name}",
            response_model=List[QueryResponse])
async def get_query_history(
    database_name: str,
    limit: int = 10,
    query_store: QueryStore = Depends(get_query_store)
):
    """
    Get recent query history for a database
    """
    logger.info(f"Fetching query history for database: {database_name}")
    
    try:
        # You'll need to implement this method in QueryStore
        history = query_store.get_recent_queries(database_name, limit)
        return history
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))