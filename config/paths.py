"""Shared filesystem paths for the project."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2] / "Ollama"
SRC_DIR = PROJECT_ROOT / "src"
API_DIR = PROJECT_ROOT / "api"
DATA_DIR = PROJECT_ROOT / "data"
TESTS_DIR = PROJECT_ROOT / "tests"

SAMPLE_QUERY_PATH = DATA_DIR / "sample_query.sql"
VECTOR_STORE_DIR = DATA_DIR / "vector_stores"
SCHEMA_DIR = DATA_DIR / "schema"
INPUT_DIR = TESTS_DIR / "input"
OUTPUT_DIR = TESTS_DIR / "output"

TMP_DIR = TESTS_DIR / "tmp"

ENV_DIR = PROJECT_ROOT / "config"