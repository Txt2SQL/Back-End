import json
from pathlib import Path
import sys
import types

import pytest

if "dotenv" not in sys.modules:
    dotenv_stub = types.ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = dotenv_stub

if "sqlglot" not in sys.modules:
    sqlglot_stub = types.ModuleType("sqlglot")

    def _parse_one(sql: str):
        normalized = " ".join((sql or "").strip().lower().split())
        if normalized in {"", "select from;", "select from"}:
            raise ValueError("Invalid SQL")
        return object()

    sqlglot_stub.parse_one = _parse_one
    sys.modules["sqlglot"] = sqlglot_stub

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
for path in (ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


from src.classes.domain_states import (
    ErrorType,
    FeedbackStatus,
    QuerySession,
    QueryStatus,
    Schema,
    SchemaSource,
)


@pytest.fixture
def schema_tmp_dir(tmp_path, monkeypatch):
    """Redirect schema persistence to a temporary directory for isolated tests."""
    from src.classes.domain_states import schema as schema_module

    monkeypatch.setattr(schema_module, "SCHEMA_DIR", tmp_path)
    return tmp_path


def test_query_session_requires_input():
    with pytest.raises(ValueError, match="At least one input"):
        QuerySession()


def test_query_session_cleans_fenced_sql_and_validates():
    session = QuerySession(user_request="List users")

    session.clean_sql_from_llm("```sql\nSELECT id, name FROM users\n```")

    assert session.sql_code == "SELECT id, name FROM users;"
    assert session.valid_syntax is True


def test_query_session_marks_syntax_error():
    session = QuerySession(user_request="Broken syntax")
    session.sql_code = "SELECT FROM;"

    session.evaluate()

    assert session.status is QueryStatus.SYNTAX_ERROR
    assert session.error_type is ErrorType.SYNTAX_ERROR


def test_query_session_classifies_runtime_error_from_db_message():
    session = QuerySession(user_request="Unknown column error", sql_query="SELECT foo FROM users;")
    session.execution_status = "ERROR"
    session.execution_result = "Unknown column 'foo' in 'field list'"

    session.evaluate()

    assert session.status is QueryStatus.RUNTIME_ERROR
    assert session.error_type is ErrorType.UNKNOWN_COLUMN


def test_query_session_applies_llm_feedback_incorrect_semantic_error():
    session = QuerySession(user_request="Get top customers", sql_query="SELECT * FROM orders;")

    session.apply_llm_feedback("INCORRECT: this does not answer the user request")
    session.evaluate()

    assert session.llm_feedback.feedback_status is FeedbackStatus.INCORRECT
    assert session.status is QueryStatus.INCORRECT
    assert session.error_type is ErrorType.SEMANTIC_ERROR


def test_feedback_retry_instruction_after_multiple_attempts():
    session = QuerySession(user_request="Need better SQL", sql_query="SELECT * FROM t;")
    session.apply_llm_feedback("INCORRECT: references invalid columns for this schema")
    session.llm_feedback.attempt = 3

    formatted = session.format_error_feedback()

    assert "DETAILS:" in formatted
    assert "invalid columns" in formatted.lower()
    assert session.llm_feedback.retry_instruction is not None


def test_schema_parse_response_and_to_documents(schema_tmp_dir):
    schema = Schema(database_name="demo", schema_source=SchemaSource.TEXT)
    payload = {
        "tables": [
            {
                "name": "users",
                "columns": [
                    {"name": "id", "type": "INT", "constraints": ["PRIMARY KEY"]},
                    {"name": "name", "type": "VARCHAR", "constraints": []},
                ],
            }
        ],
        "semantic_notes": ["A user may place multiple orders"],
    }

    schema.parse_response(payload)
    documents = schema.to_documents()

    assert schema.json_ready is True
    assert schema.schema_id
    assert len(documents) == 1
    assert documents[0]["metadata"]["table"] == "users"
    assert Path(schema_tmp_dir / "demo_schema.json").exists()


def test_schema_loads_existing_saved_schema(schema_tmp_dir):
    schema_path = schema_tmp_dir / "sample_schema.json"
    existing = {
        "database_name": "sample",
        "source": "text",
        "tables": [],
        "semantic_notes": [],
        "schema_id": "abc123",
    }
    schema_path.write_text(json.dumps(existing), encoding="utf-8")

    loaded = Schema(database_name="sample", schema_source=SchemaSource.TEXT)

    assert loaded.tables == existing
    assert loaded.schema_id == "abc123"
    assert loaded.json_ready is True
