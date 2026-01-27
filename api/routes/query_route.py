from fastapi import APIRouter
from query_generator import generate_sql_query, compute_schema_id, validate_sql_syntax
from mysql_linker import execute_sql_query

router = APIRouter()

@router.post("/generate")
def generate_query(request: dict):
    """
    request: {
        "user_request": str,
        "model_choice": str (optional),
        "source": "text_input" | "mysql_extraction"
    }
    """
    user_request = request.get("user_request")
    if not user_request:
        return {"error": "user_request is required"}
    
    source = request.get("source", "text_input")
    selected_model = request.get("model_choice", "1")

    schema_id = compute_schema_id()

    sql_query = generate_sql_query(user_request, schema_id, source, selected_model)
    syntax_status = validate_sql_syntax(sql_query)

    result = {"sql": sql_query, "syntax_status": syntax_status}

    # Optionally run query if mysql_extraction
    if syntax_status == "OK" and source == "mysql_extraction":
        status, output = execute_sql_query(sql_query)
        result.update({"execution_status": status, "output_preview": output[:5]})

    return result