"""Project-wide settings constants."""
import logging

SCHEMA_MODELS = {
    "gpt-5-mini": {
        "provider": "azure",
        "id": "gpt-5-mini",
    },
    "Qwen2.5-Coder": {
        "provider": "openwebui",
        "id": "ollama@isarco02.MHKetbi/Qwen2.5-Coder-32B-Instruct:q4_K_S"
    },
    "DeepSeek-V2.5": {
        "provider": "openwebui",
        "id": "DeepSeek-V2.5-Q6_K-00001-of-00005.gguf",
    }
}

QUERY_GENERATION_MODELS = {
    "gpt-4o": {
        "provider": "azure",
        "id": "gpt-4o",
        "log_file": "gpt-4o.log",
    },
    "gpt-5-mini": {
        "provider": "azure",
        "id": "gpt-5-mini",
        "log_file": "gpt-5-mini.log",
    },
    "codestral:22b": {
        "provider": "openwebui",
        "id": "ollama@isarco02.codestral:22b",
        "log_file": "codestral.log",
    },
    "codellama:34b": {
        "provider": "openwebui",
        "id": "ollama@isarco02.codellama:34b",
        "log_file": "codellama.log",
    },
    # "sqlcoder:34b": {
    #     "provider": "openwebui",
    #     "id": "sqlcoder-34b-alpha",
    #     "log_file": "sqlcoder.log",
    # },
    "Qwen3-Coder-Next": {
        "provider": "openwebui",
        "id": "qwen3-coder-next",
        "log_file": "Qwen3-Coder-Next.log",
    },
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

LOGGER_LEVEL = logging.INFO
LOGINFO_SEPARATOR = "//" *80
MAX_OUTPUT_LENGTH = 1000  # Truncate long requests in output
TIMEOUT_PER_REQUEST = 600   # 10 minutes timeout per model per request