#!/usr/bin/env python
"""
Script to run the FastAPI application
"""
import uvicorn
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    # Load environment variables if needed
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get port from environment or use default
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    # Run the server
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=True,  # Set to False in production
        log_level="info"
    )