"""Project-wide settings constants."""

AVAILABLE_MODELS = {
    0: "without_llm",
    1: "codellama:13b",
    2: "codestral:22b",
    3: "sqlcoder:15b",
    4: "deepseek-coder-v2:16b",
    5: "gpt-4o",
    6: "gpt-5-mini",
}

REQUIRED_CREDENTIAL_VARS = [
    "DB_HOST",
    "DB_PORT",
    "DB_USER",
    "DB_PASSWORD",
]