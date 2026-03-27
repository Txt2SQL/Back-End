import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from bootstrap import bootstrap_project

bootstrap_project(PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import schema, query

app = FastAPI(title="Text-to-SQL API", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(schema.router)
app.include_router(query.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

# To run: uvicorn src.api.main:app --reload
