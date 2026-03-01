from src.classes.prompt_builder import PromptBuilder
from src.classes.domain_states.query import QuerySession
from src.classes.domain_states.enums import QueryStatus


def test_evaluation_prompt_formats_dict_rows_as_json_lines():
    builder = PromptBuilder()
    prompt = builder.evaluation_prompt(
        sql="SELECT id, name FROM users;",
        request="List users",
        context="users(id, name)",
        execution_output=[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
    )

    assert '--- QUERY RESULT (first 20 rows) ---' in prompt
    assert '{"id": 1, "name": "Alice"}' in prompt
    assert '{"id": 2, "name": "Bob"}' in prompt


def test_format_error_feedback_uses_enum_status_logic():
    session = QuerySession(user_request="x")
    session.status = QueryStatus.RUNTIME_ERROR
    session.sql_code = "SELECT * FROM missing;"

    feedback = session.format_error_feedback()

    assert "failed at runtime" in feedback
