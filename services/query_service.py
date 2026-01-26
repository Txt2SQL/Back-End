from query_generator import generate_sql_query, OllamaLLM
from mysql_executor import execute_sql_query
from query_feedback_store import store_query_feedback

def generate_sql(request: str, model_name: str):
    # override model inside the query_generator file
    import query_generator
    query_generator.model = OllamaLLM(model=model_name)
    
    return generate_sql_query(request)

def execute_sql(query: str):
    return execute_sql_query(query)

def build_query_store_internal(    
    user_request: str,
    sql_query: str,
    status: str,
    model_name: str,
    error_message: str | None = None,
    schema_id: str | None = None):
    return store_query_feedback(
        user_request,
        sql_query,
        status,
        model_name,
        error_message,
        schema_id
    )