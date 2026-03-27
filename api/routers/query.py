from fastapi import APIRouter, HTTPException

from config import QUERY_MODELS
from src.classes.orchestrators.query_orchestrator import QueryOrchestrator
from src.classes.domain_states import QuerySession, Records
from api.models import (
    QueryGenerationRequest,
    QueryEvaluationRequest,
    QueryResponse,
    DatabaseListResponse,
)
from api.dependencies import get_schema_store, get_query_store, get_mysql_client
from src.classes.domain_states import QueryStatus

router = APIRouter(prefix="/queries", tags=["Queries"])

def _serialize_execution_result(query_session) -> tuple[list[dict] | None, str | None]:
    results = None
    error = None

    if query_session.execution_result and query_session.status == QueryStatus.SUCCESS:
        if isinstance(query_session.execution_result, Records):
            results = query_session.execution_result.to_dict()
    elif isinstance(query_session.execution_result, str):
        error = query_session.execution_result

    return results, error

@router.get("/mysql/databases", response_model=DatabaseListResponse)
def list_mysql_databases():
    """Return all databases available on the current MySQL connection."""
    try:
        db_client = get_mysql_client()
        databases = db_client.list_databases()
        return DatabaseListResponse(databases=databases)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mysql", response_model=QueryResponse)
def generate_query_mysql(payload: QueryGenerationRequest):
    """Generate and Execute SQL on the real database."""
    try:
        # 1. Init Dependencies
        schema_store = get_schema_store()
        query_store = get_query_store()
        db_client = get_mysql_client(payload.database_name)

        # 2. Init Orchestrator
        orchestrator = QueryOrchestrator(
            database_name=payload.database_name,
            schema_store=schema_store,
            model_name=payload.model_id,
            database_client=db_client,
            query_store=query_store
        )

        # 3. Run Generation
        query_session = orchestrator.generation(payload.question)

        # 4. Format Response
        results, error = _serialize_execution_result(query_session)

        return QueryResponse(
            sql=query_session.sql_code,
            status=query_session.status,
            results=results,
            error=error
        )

    except Exception as e:
        # Log error here
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/text", response_model=QueryResponse)
def generate_query_text(payload: QueryGenerationRequest):
    """Generate SQL only (No execution). Suitable for testing or offline mode."""
    try:
        # 1. Init Dependencies (No DB Client)
        schema_store = get_schema_store()
        
        # QueryStore is optional in text mode according to your Orchestrator logic
        # or we can pass it if we want to use previous failures (rag)
        query_store = get_query_store()

        # 2. Init Orchestrator (database_client=None)
        orchestrator = QueryOrchestrator(
            database_name=payload.database_name,
            schema_store=schema_store,
            model_name=payload.model_id,
            database_client=None, 
            query_store=query_store,
        )

        # 3. Run Generation
        query_session = orchestrator.generation(payload.question)

        return QueryResponse(
            sql=query_session.sql_code,
            status=query_session.status,
            results=None, # No execution
            error=None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/evaluate", response_model=QueryResponse)
def evaluate_query(payload: QueryEvaluationRequest):
    try:
        # 1. Init Dependencies
        schema_store = get_schema_store()
        db_client = get_mysql_client(payload.database_name)

        # 2. Init Orchestrator
        orchestrator = QueryOrchestrator(
            database_name=payload.database_name,
            schema_store=schema_store,
            model_name=payload.model_id,
            database_client=db_client
        )

        # 3. Run Evaluation
        query_session = orchestrator.evaluation(payload.query.to_query_session(), 0)

        # 4. Format Response
        results, error = _serialize_execution_result(query_session)

        return QueryResponse(
            sql=query_session.sql_code,
            status=query_session.status,
            results=results,
            error=error
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
