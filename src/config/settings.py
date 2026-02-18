"""Project-wide settings constants."""

SCHEMA_MODELS = {
    "starchat-alpha": {
        "provider": "openwebui",
        "id": "huggingfaceh4_-_starchat-alpha",
    },
    "Qwen2.5-Coder": {
        "provider": "openwebui",
        "id": "ollama@isarco02.MHKetbi/Qwen2.5-Coder-32B-Instruct:q4_K_S"
    }
}

QUERY_GENERATION_MODELS = {
    "gpt-4o": {
        "provider": "azure",
        "id": "gpt-4o",
    },
    "gpt-5-mini": {
        "provider": "azure",
        "id": "gpt-5-mini",
    },
    "codestral:22b": {
        "provider": "openwebui",
        "id": "ollama@isarco02.codestral:22b",
    },
    "codellama:34b": {
        "provider": "openwebui",
        "id": "ollama@isarco02.codellama:34b",
    },
    "sqlcoder:15b": {
        "provider": "openwebui",
        "id": "ollama@isarco02.sqlcoder:15b",
    },
    "Qwen3-Coder-Next": {
        "provider": "openwebui",
        "id": "Qwen3-Coder-Next-UD-Q4_K_XL.gguf",
    },
    "DeepSeek-V2.5": {
        "provider": "openwebui",
        "id": "DeepSeek-V2.5-Q6_K-00001-of-00005.gguf",
    }
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

LOGINFO_SEPARATOR = "//" *80
MAX_OUTPUT_LENGTH = 1000  # Truncate long requests in output