"""MySQL database utilities for connection, query execution, and schema extraction."""

import mysql.connector, os, sqlglot
from typing import Tuple, Any, Optional
from collections import defaultdict
from getpass import getpass

from src.logging_utils import setup_logger
from src.config import (
    ENV_DIR,
    REQUIRED_CREDENTIAL_VARS,
    load_mysql_config
)

# === LOGGING SETUP ===
logger = setup_logger(__name__)

# Constants
ENV_MYSQL_FILE = ENV_DIR / ".mysql.env"

# === SQL SYNTAX VALIDATION ===

def validate_sql_syntax(sql_query: str | None) -> str:
    """
    Checks if SQL compiles syntactically.
    
    Returns:
        - "OK" if it compiles
        - "SYNTAX_ERROR" if it fails
        - "" if query is None
    """
    logger.debug("Validating SQL syntax for query: %s", sql_query)
    
    if sql_query is None:
        logger.warning("Received None SQL query")
        return ""
    
    try:
        # Parse only, no DB execution
        sqlglot.parse_one(sql_query)
        logger.debug("SQL syntax validation passed")
        return "OK"
    except Exception as e:
        logger.error(f"Syntax validation failed: {e}")
        return "SYNTAX_ERROR"


# === ENVIRONMENT CONFIGURATION ===

def mysql_env_is_valid() -> bool:
    """Check if MySQL environment file exists and contains required variables."""
    if not ENV_MYSQL_FILE.exists():
        logger.debug(f"MySQL env file not found at {ENV_MYSQL_FILE}")
        return False
    
    try:
        load_mysql_config()
        # Check if all required variables are present and non-empty
        return True
    except Exception as e:
        logger.error(f"Error loading MySQL config: {e}")
        return False


def prompt_mysql_credentials() -> dict:
    """Prompt user for MySQL credentials interactively."""
    logger.info("🔐 MySQL configuration required")
    
    print("\n=== MySQL Configuration ===\n")
    
    creds = {
        "DB_HOST": input("DB_HOST (e.g. localhost): ").strip(),
        "DB_PORT": input("DB_PORT [3306]: ").strip() or "3306",
        "DB_USER": input("DB_USER: ").strip(),
        "DB_PASSWORD": getpass("DB_PASSWORD: "),
    }
    return creds


def write_mysql_env(creds: dict) -> None:
    """Write MySQL credentials to environment file."""
    # Load existing configuration if file exists
    existing = {}
    if ENV_MYSQL_FILE.exists():
        with open(ENV_MYSQL_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    existing[k] = v
    
    # Update with new credentials
    existing.update(creds)
    
    # Write back to file
    with open(ENV_MYSQL_FILE, "w", encoding="utf-8") as f:
        for k, v in existing.items():
            f.write(f"{k}={v}\n")
    
    logger.info(f"✅ MySQL configuration saved to {ENV_MYSQL_FILE}")


def ensure_mysql_env():
    """Ensure MySQL environment is properly configured."""
    if mysql_env_is_valid():
        logger.debug("MySQL environment is valid")
        return
    
    logger.info("MySQL environment not configured or invalid")
    creds = prompt_mysql_credentials()
    write_mysql_env(creds)


def get_mysql_config() -> dict:
    """Get MySQL configuration, ensuring environment is set up."""
    ensure_mysql_env()
    return load_mysql_config()


# === DATABASE CONNECTION ===

def get_db_connection(database_name: str | None = None):
    """
    Create and return a MySQL database connection.
    
    Args:
        database_name: Optional database name to connect to
        
    Returns:
        MySQL connection object
        
    Raises:
        Exception: If connection fails
    """
    config = get_mysql_config()
    
    logger.info("🔧 Creating DB connection object...")
    try:
        connection_params = {
            "host": config["host"],
            "port": int(config["port"]),
            "user": config["user"],
            "password": config["password"],
        }
        
        if database_name:
            connection_params["database"] = database_name
        
        return mysql.connector.connect(**connection_params)
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to MySQL: {e}")
        raise


# === QUERY EXECUTION ===

def execute_sql_query(sql_query: str, database_name: str | None = None) -> Tuple[str, Any]:
    """
    Executes a SQL query against the real database.

    Args:
        sql_query: SQL query to execute
        database_name: Optional database name to use

    Returns:
        Tuple containing:
        - status: "OK" | "RUNTIME_ERROR"
        - result: fetched rows or error message
    """
    logger.info(f"📌 Received SQL query:\n{sql_query}")

    try:
        logger.info("🔌 Connecting to MySQL database...")
        conn = get_db_connection(database_name=database_name)

        if conn.is_connected():
            logger.info("✅ Connection established")
        else:
            logger.error("❌ Connection failed (conn.is_connected() returned False)")
            return "RUNTIME_ERROR", "Connection failed"

        cursor = conn.cursor()
        logger.info("📝 Executing SQL query...")

        cursor.execute(sql_query)
        logger.info("📝 Query executed successfully")

        # Try fetching results (SELECT queries)
        try:
            logger.info("📥 Attempting to fetch results...")
            result = cursor.fetchall()
            logger.info(f"📥 Rows fetched: {len(result)}")
        except Exception as fetch_err:
            logger.info(f"ℹ️ No fetchable results (likely non-SELECT query)")
            result = None

        logger.info("💾 Committing transaction...")
        conn.commit()

        cursor.close()
        conn.close()
        logger.info("🔒 Connection closed")

        return "OK", result

    except Exception as e:
        logger.error(f"🔥 RUNTIME ERROR during SQL execution: {e}")
        return "RUNTIME_ERROR", str(e)


# === DATABASE METADATA ===

def list_databases() -> list[str]:
    """List all databases available in the MySQL server."""
    conn = get_db_connection(database_name=None)
    cursor = conn.cursor()
    
    cursor.execute("SHOW DATABASES")
    rows = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return [row[0] for row in rows] # pyright: ignore[reportReturnType, reportArgumentType]


def extract_schema(database_name: str | None = None) -> dict:
    """
    Extract database schema information.
    
    Args:
        database_name: Name of the database to extract schema from.
                      If None, uses DB_NAME from environment.
    
    Returns:
        Dictionary containing tables and columns information
    """
    if database_name is None:
        # Try to get from environment, but don't require it
        database_name = os.getenv("DB_NAME", "")
        if not database_name:
            raise ValueError("Database name must be provided or set in DB_NAME environment variable")
    
    logger.info(f"📚 Extracting schema for database: {database_name}")

    conn = get_db_connection(database_name=database_name)
    cursor = conn.cursor(dictionary=True)

    logger.info("🔍 Querying information_schema.COLUMNS...")
    cursor.execute("""
        SELECT
            c.TABLE_NAME,
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.IS_NULLABLE,
            c.COLUMN_KEY,
            c.EXTRA
        FROM information_schema.COLUMNS c
        WHERE c.TABLE_SCHEMA = %s
        ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION
    """, (database_name,))

    rows = cursor.fetchall()
    logger.info(f"📊 Retrieved {len(rows)} column definitions")

    tables = defaultdict(list)

    for row in rows:  # pyright: ignore[reportInvalidTypeForm] # type: dict[str, Any]
        table_name = row["TABLE_NAME"] # pyright: ignore[reportArgumentType, reportCallIssue]
        column_name = row["COLUMN_NAME"] # pyright: ignore[reportArgumentType, reportCallIssue]
        data_type = row["DATA_TYPE"] # pyright: ignore[reportArgumentType, reportCallIssue]
        is_nullable = row["IS_NULLABLE"] # pyright: ignore[reportArgumentType, reportCallIssue]
        column_key = row["COLUMN_KEY"] # pyright: ignore[reportArgumentType, reportCallIssue]
        extra = row["EXTRA"] or "" # pyright: ignore[reportArgumentType, reportCallIssue]
        
        logger.debug(f"➡️ Processing column: {table_name}.{column_name}")
        
        constraints = []
        if column_key == "PRI":
            constraints.append("PRIMARY KEY")
        if is_nullable == "NO":
            constraints.append("NOT NULL")
        if "auto_increment" in extra.lower(): # pyright: ignore[reportOperatorIssue, reportAttributeAccessIssue]
            constraints.append("AUTO_INCREMENT")

        tables[table_name].append({
            "name": column_name,
            "type": data_type.upper(), # type: ignore
            "constraints": constraints
        })

    schema = {
        "tables": [],
        "semantic_notes": []  # Placeholder for future semantic information
    }

    logger.info("🧱 Building schema structure...")
    for table_name, columns in tables.items():
        logger.info(f"📦 Adding table: {table_name} ({len(columns)} columns)")
        schema["tables"].append({
            "name": table_name,
            "columns": columns
        })

    cursor.close()
    conn.close()
    logger.info("🏁 Schema extraction completed")

    return schema