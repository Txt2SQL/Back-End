"""Project-wide settings constants."""
import logging, os

SCHEMA_MODELS = {
    "gpt-5-mini": {
        "provider": "azure",
        "id": "gpt-5-mini",
    },
    "Qwen2.5-Coder": {
        "provider": "openwebui",
        "id": "ollama@isarco02.MHKetbi/Qwen2.5-Coder-32B-Instruct:q4_K_S",
        "api_type": "chat",      # 🔥 key addition
        "api_key": "CHAT_API_KEY",
        "api_base": "CHAT_ADDRESS",
        "api_endpoint": "/api/chat/completions",
    },
    "DeepSeek-V2.5": {
        "provider": "openwebui",
        "id": "DeepSeek-V2.5-Q6_K-00001-of-00005.gguf",
        "api_type": "chat",      # 🔥 key addition
        "api_key": "CHAT_API_KEY",
        "api_base": "CHAT_ADDRESS",
        "api_endpoint": "/api/chat/completions",
    }
}

QUERY_MODELS = {
    "gpt-4o": {
        "provider": "azure",
        "id": "gpt-4o",
        "log_file": "gpt-4o",
    },
    "gpt-5-mini": {
        "provider": "azure",
        "id": "gpt-5-mini",
        "log_file": "gpt-5-mini",
    },
    "codestral:22b": {
        "provider": "openwebui",
        "id": "ollama@isarco02.codestral:22b",
        "api_type": "chat",
        "api_endpoint": "/api/chat/completions",
        "log_file": "codestral",
    },
    "codellama:34b": {
        "provider": "openwebui",
        "id": "ollama@isarco02.codellama:34b",
        "api_type": "chat",
        "api_endpoint": "/api/chat/completions",
        "log_file": "codellama",
    },
    "sqlcoder:34b": {
        "provider": "openwebui",
        "id": "sqlcoder-34b-alpha",
        "api_type": "completion",
        "api_endpoint": "/completions",
        "log_file": "sqlcoder",
    },
    # "omnisql:7b": {
    #     "provider": "openwebui",
    #     "id": "omnisql-7b",
    #     "api_type": "completion",
    #     "api_endpoint": "/completions",
    #     "log_file": "omnisql",
    # },
    "Qwen3.5:35b": {
        "provider": "openwebui",
        "id": "qwen3.5-35b-a3b",
        "api_type": "chat",
        "api_endpoint": "/api/chat/completions",
        "log_file": "Qwen3.5",
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
    "BAD_JOIN": [
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

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_DEBUG = os.getenv("API_DEBUG", "False").lower() == "true"

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")