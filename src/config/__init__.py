"""Configuration package for the project.

This package contains all project-wide configuration settings,
including model definitions, error categories, and filesystem paths.
"""
import os
from dotenv import load_dotenv

from .settings import (
    SCHEMA_MODELS,
    QUERY_GENERATION_MODELS,
    REQUIRED_CREDENTIAL_VARS,
    ERROR_CATEGORIES,
    LOGINFO_SEPARATOR,
    MAX_OUTPUT_LENGTH,
)

from .paths import (
    PROJECT_ROOT,
    SRC_DIR,
    API_DIR,
    DATA_DIR,
    TESTS_DIR,
    SAMPLE_QUERY_PATH,
    VECTOR_STORE_DIR,
    SCHEMA_FILE,
    ENV_DIR,
)

__all__ = [
    # Settings exports
    "SCHEMA_MODELS",
    "QUERY_GENERATION_MODELS",
    "REQUIRED_CREDENTIAL_VARS",
    "ERROR_CATEGORIES",
    "LOGINFO_SEPARATOR",
    "MAX_OUTPUT_LENGTH",
    
    # Paths exports
    "PROJECT_ROOT",
    "SRC_DIR",
    "API_DIR",
    "DATA_DIR",
    "TESTS_DIR",
    "SAMPLE_QUERY_PATH",
    "VECTOR_STORE_DIR",
    "SCHEMA_FILE",
    "ENV_DIR",
]