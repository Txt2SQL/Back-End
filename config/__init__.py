"""Configuration package for the project.

This package contains all project-wide configuration settings,
including model definitions, error categories, and filesystem paths.
"""
import os
from dotenv import load_dotenv

from .settings import (
    SCHEMA_MODELS,
    PLANNER_MODELS,
    EVALUATION_MODELS,
    QUERY_MODELS,
    REQUIRED_CREDENTIAL_VARS,
    ERROR_CATEGORIES,
    LOGGER_LEVEL,
    LOGINFO_SEPARATOR,
    MAX_OUTPUT_LENGTH,
    TIMEOUT_PER_REQUEST,
    API_HOST,
    API_PORT,
    API_DEBUG,
    CORS_ORIGINS,
)

from .paths import (
    PROJECT_ROOT,
    SRC_DIR,
    API_DIR,
    DATA_DIR,
    TESTS_DIR,
    SAMPLE_QUERY_PATH,
    VECTOR_STORE_DIR,
    SCHEMA_DIR,
    INPUT_DIR,
    OUTPUT_DIR,
    ENV_DIR,
)

__all__ = [
    # Settings exports
    "SCHEMA_MODELS",
    "PLANNER_MODELS",
    "EVALUATION_MODELS",
    "QUERY_MODELS",
    "REQUIRED_CREDENTIAL_VARS",
    "ERROR_CATEGORIES",
    "LOGGER_LEVEL",
    "LOGINFO_SEPARATOR",
    "MAX_OUTPUT_LENGTH",
    "TIMEOUT_PER_REQUEST",
    "API_HOST",
    "API_PORT",
    "API_DEBUG",
    "CORS_ORIGINS",
    
    # Paths exports
    "PROJECT_ROOT",
    "SRC_DIR",
    "API_DIR",
    "DATA_DIR",
    "TESTS_DIR",
    "SAMPLE_QUERY_PATH",
    "VECTOR_STORE_DIR",
    "SCHEMA_DIR",
    "INPUT_DIR",
    "OUTPUT_DIR",
    "ENV_DIR",
]