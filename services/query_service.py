from query_generator import generate_sql_query, OllamaLLM, model as base_model

def generate_sql(request: str, model_name: str):
    # override model inside the query_generator file
    import query_generator
    query_generator.model = OllamaLLM(model=model_name)
    
    return generate_sql_query(request)
