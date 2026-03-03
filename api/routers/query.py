from fastapi import APIRouter, HTTPException
from src.classes.orchestrators.query_orchestrator import QueryOrchestrator
from src.classes.domain_states import Records
from api.models import QueryRequest, QueryResponse
from api.dependencies import get_schema_store, get_query_store, get_mysql_client, get_llm
from src.classes.domain_states import QueryStatus

router = APIRouter(prefix="/queries", tags=["Queries"])

@router.post("/mysql", response_model=QueryResponse)
def generate_query_mysql(payload: QueryRequest):
    """Generate and Execute SQL on the real database."""
    try:
        # 1. Init Dependencies
        llm = get_llm(payload.model_id, "query")
        schema_store = get_schema_store()
        query_store = get_query_store()
        db_client = get_mysql_client(payload.database_name)

        # 2. Init Orchestrator
        orchestrator = QueryOrchestrator(
            database_name=payload.database_name,
            schema_store=schema_store,
            llm=llm,
            database_client=db_client,
            query_store=query_store
        )

        # 3. Run Generation
        query_session = orchestrator.generation(payload.question)

        # 4. Format Response
        # Convert Records object to list of dicts if success
        results = None
        error = None
        if query_session.execution_result and query_session.status == QueryStatus.SUCCESS:
             # Assuming Records class has .to_dict() or is iterable
            if isinstance(query_session.execution_result, Records):
                results = query_session.execution_result.to_dict()     
        elif isinstance(query_session.execution_result, str):
             # Handing error strings stored in execution_result
            error = query_session.execution_result

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
def generate_query_text(payload: QueryRequest):
    """Generate SQL only (No execution). Suitable for testing or offline mode."""
    try:
        # 1. Init Dependencies (No DB Client)
        llm = get_llm(payload.model_id, "query")
        schema_store = get_schema_store()
        
        # QueryStore is optional in text mode according to your Orchestrator logic
        # or we can pass it if we want to use previous failures (rag)
        query_store = get_query_store()

        # 2. Init Orchestrator (database_client=None)
        orchestrator = QueryOrchestrator(
            database_name=payload.database_name,
            schema_store=schema_store,
            llm=llm,
            database_client=None, 
            query_store=query_store,
            testing=False # Set True if you want the logic to simulate execution
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