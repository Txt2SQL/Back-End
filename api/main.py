import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.routers import query, schema
from api.utils.exception_handlers import add_exception_handlers
from src.classes.logger import LoggerManager

# Setup logging
logger = LoggerManager.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for startup and shutdown
    """
    logger.info("🚀 Starting SQL Query Generator API...")
    yield
    logger.info("🛑 Shutting down SQL Query Generator API...")

# Create FastAPI app
app = FastAPI(
    title="SQL Query Generator API",
    description="API for generating and refining SQL queries from natural language",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(query.router, prefix="/api/v1/query", tags=["queries"])
app.include_router(schema.router, prefix="/api/v1/schema", tags=["schemas"])

# Add exception handlers
add_exception_handlers(app)

@app.get("/")
async def root():
    return {
        "message": "SQL Query Generator API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}