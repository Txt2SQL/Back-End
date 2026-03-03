import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure the root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

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