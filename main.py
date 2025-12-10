from fastapi import FastAPI
from api.schema_route import router as schema_router
from api.query_route import router as query_router

app = FastAPI(
    title="Canonical Schema + SQL Generator API",
    version="1.0.0",
)

app.include_router(schema_router, prefix="/schema", tags=["Schema"])
app.include_router(query_router, prefix="/query", tags=["SQL Query"])

@app.get("/")
def root():
    return {"message": "Server running"}
