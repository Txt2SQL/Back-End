from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from schema_generator import update_schema
from query_generator import generate_query

app = FastAPI(title="Mini RAG SQL Service", version="1.0")

class SchemaUpdateRequest(BaseModel):
    text: str

class QueryRequest(BaseModel):
    request: str


@app.post("/update_schema")
def update_schema_endpoint(data: SchemaUpdateRequest):
    """
    Aggiorna lo schema canonico (JSON) e il vector store RAG.
    """
    try:
        schema = update_schema(data.text)
        return {"message": "✅ Schema aggiornato con successo", "schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query")
def query_endpoint(data: QueryRequest):
    """
    Genera una query SQL a partire da testo naturale.
    """
    try:
        sql = generate_query(data.request)
        return {"sql": sql}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def root():
    return {"service": "RAG SQL Generator", "status": "running"}
