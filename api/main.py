from fastapi import FastAPI
from api.routes import schema_route, query_route

app = FastAPI(
    title="SQL RAG API",
    description="API for schema management and SQL query generation using LLM + RAG",
    version="1.0.0"
)

# Include routes
app.include_router(schema_route.router, prefix="/schema", tags=["Schema"])
app.include_router(query_route.router, prefix="/query", tags=["Query"])