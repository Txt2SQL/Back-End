"""Shared filesystem paths for the project."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

PROJECT_ROOT = BASE_DIR.parent

SRC_DIR = BASE_DIR / "src"
API_DIR = BASE_DIR / "api"
DATA_DIR = BASE_DIR / "data"
TESTS_DIR = BASE_DIR / "tests"

SAMPLE_QUERY_PATH = DATA_DIR / "sample_query.sql"
VECTOR_STORE_DIR = DATA_DIR / "vector_stores"
SCHEMA_DIR = DATA_DIR / "schema"

INPUT_DIR = TESTS_DIR / "input"
OUTPUT_DIR = TESTS_DIR / "output"
TMP_DIR = TESTS_DIR / "tmp"

SPIDER_DATA = PROJECT_ROOT / "spider_data"
SPIDER_REPO = PROJECT_ROOT / "spider_repo"

ENV_DIR = BASE_DIR / "config"