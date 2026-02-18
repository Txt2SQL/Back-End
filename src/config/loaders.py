import os
from dotenv import load_dotenv
from .paths import ENV_DIR

def load_azure_config():
    env_path = ENV_DIR / "azure.env"
    load_dotenv(env_path)

    return {
        "api_key": os.getenv("AZURE_API_KEY"),
        "endpoint": os.getenv("AZURE_ENDPOINT"),
        "api_version": os.getenv("AZURE_API_VERSION"),
    }


def load_openwebui_config():
    env_path = ENV_DIR / "openwebui.env"
    load_dotenv(env_path)

    return {
        "base_url": os.getenv("SERVER_ADDRESS"),
        "api_key": os.getenv("API_KEY"),
    }
    
def load_mysql_config():
    """Load MySQL configuration from mysql.env file."""
    env_path = ENV_DIR / "mysql.env"
    
    if not env_path.exists():
        raise ValueError(f"MySQL environment file not found at {env_path}")
    
    load_dotenv(env_path)
    
    config = {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }
    
    # Validate required configuration
    missing_vars = [key for key, value in config.items() if value is None]
    if missing_vars:
        raise ValueError(f"Missing required MySQL environment variables: {missing_vars}")
    
    return config