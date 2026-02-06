from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

from src.schema.generation.query_generator import (
    generate_sql_query,
    validate_sql_syntax,
    compute_schema_id,
    get_schema_source,
    create_metadata
)
from src.retriver_utils import store_query_feedback
from src.mysql_linker import execute_sql_query

# =========================
# CONFIG
# =========================
SCHEMA_FILE = "../../schema_canonical.json"
SCHEMA_COLLECTION_NAME = "schema_canonical"
QUERY_COLLECTION_NAME = "query_feedback"
VSS_DIR = "../../vector_store/schema"
VSQ_DIR = "../../vector_store/queries"

router = APIRouter()

# =========================
# SHARED OBJECTS (created once)
# =========================
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

schema_vs = Chroma(
    collection_name=SCHEMA_COLLECTION_NAME,
    persist_directory=VSS_DIR,
    embedding_function=embeddings,
)

query_vs = Chroma(
    collection_name=QUERY_COLLECTION_NAME,
    persist_directory=VSQ_DIR,
    embedding_function=embeddings,
)

# =========================
# REQUEST / RESPONSE MODELS
# =========================
class QueryRequest(BaseModel):
    user_request: str
    model_name: str
    execute: bool


class QueryResponse(BaseModel):
    sql: str
    status: str
    rows_fetched: int | None = None
    error_message: str | None = None


# =========================
# ROUTE
# =========================
@router.post("/generate", response_model=QueryResponse)
def generate_query(req: QueryRequest):
    # -------------------------
    # Load schema
    # -------------------------
    try:
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            full_schema = json.load(f)
    except Exception:
        raise HTTPException(status_code=500, detail="Schema not found")


    source = get_schema_source(full_schema)
    schema_id = compute_schema_id(full_schema)

    # -------------------------
    # Generate SQL
    # -------------------------
    sql = generate_sql_query(
        user_request=req.user_request,
        source=source,
        full_schema=full_schema,
        model_name=req.model_name,
        query_vs=query_vs,
        schema_vs=schema_vs
    )

    # -------------------------
    # Validate syntax
    # -------------------------
    syntax_status = validate_sql_syntax(sql)

    execution_status = None
    execution_output = None

    # -------------------------
    # Optional execution
    # -------------------------
    if syntax_status == "OK" and req.execute and source == "mysql_extraction":
        execution_status, execution_output = execute_sql_query(sql)

    # -------------------------
    # Metadata + feedback
    # -------------------------
    metadata = create_metadata(
        sql_query=sql,
        syntax_status=syntax_status,
        schema_id=schema_id,
        user_request=req.user_request,
        model_name=req.model_name,
        execution_status=execution_status,
        execution_output=execution_output
    )

    store_query_feedback(
        store=query_vs,
        sql_query=sql,
        qm=metadata
    )

    # -------------------------
    # Response
    # -------------------------
    return QueryResponse(
        sql=sql,
        status=metadata.status,
        rows_fetched=metadata.rows_fetched,
        error_message=metadata.error_message
    )