"""Project-wide settings constants."""

OLLAMA_MODELS = {
    1: "codellama:13b",
    2: "codestral:22b",
    3: "sqlcoder:15b",
    4: "deepseek-coder-v2:16b",
    7: "mxbai-embed-13b",    
}

AZURE_MODELS = {
    5: "gpt-4o",
    6: "gpt-5-mini",
}

AVAILABLE_MODELS = {
    0: "without_llm",
    **OLLAMA_MODELS,
    **AZURE_MODELS
}

REQUIRED_CREDENTIAL_VARS = [
    "DB_HOST",
    "DB_PORT",
    "DB_USER",
    "DB_PASSWORD",
]

ERROR_CATEGORIES = {
    "SCHEMA_ERROR": [
        "unknown column",
        "unknown table",
        "does not exist",
        "invalid column",
    ],
    "JOIN_ERROR": [
        "missing join",
        "wrong join",
        "incorrect join",
        "cartesian",
        "not joined",
    ],
    "AGGREGATION_ERROR": [
        "group by",
        "aggregation",
        "aggregate",
        "sum",
        "count",
        "average",
        "avg",
        "total",
    ],
    "FILTER_ERROR": [
        "missing filter",
        "wrong filter",
        "incorrect where",
        "extra filter",
        "should filter",
    ],
    "PROJECTION_ERROR": [
        "wrong column",
        "missing column",
        "extra column",
        "incorrect select",
    ],
    "SEMANTIC_ERROR": [
        "does not answer",
        "incorrect result",
        "wrong result",
        "not what was asked",
    ],
}