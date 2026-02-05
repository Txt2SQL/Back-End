import mysql.connector
import os
from typing import Tuple, Any
from collections import defaultdict
from dotenv import load_dotenv
from getpass import getpass
from logging_utils import setup_logger

ENV_MYSQL_FILE = ".env.mysql"

REQUIRED_VARS = [
    "DB_HOST",
    "DB_PORT",
    "DB_USER",
    "DB_PASSWORD",
    "DB_NAME",
]

# === LOGGING SETUP ===
logger = setup_logger(__name__)

def mysql_env_is_valid() -> bool:
    if not os.path.exists(ENV_MYSQL_FILE):
        return False

    load_dotenv(ENV_MYSQL_FILE, override=True)

    return all(os.getenv(v) for v in REQUIRED_VARS)

def prompt_mysql_credentials() -> dict:
    logger.info("🔐 MySQL configuration required")

    return {
        "DB_HOST": input("DB_HOST (e.g. localhost): ").strip(),
        "DB_PORT": input("DB_PORT [3306]: ").strip() or "3306",
        "DB_USER": input("DB_USER: ").strip(),
        "DB_PASSWORD": getpass("DB_PASSWORD: "),
        "DB_NAME": input("DB_NAME: ").strip(),
    }

def write_mysql_env(creds: dict) -> None:
    existing = {}

    if os.path.exists(ENV_MYSQL_FILE):
        with open(ENV_MYSQL_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    existing[k] = v

    existing.update(creds)

    with open(ENV_MYSQL_FILE, "w", encoding="utf-8") as f:
        for k, v in existing.items():
            f.write(f"{k}={v}\n")

    logger.info(f"✅ MySQL configuration saved to {ENV_MYSQL_FILE}")

def ensure_mysql_env():
    if mysql_env_is_valid():
        return

    creds = prompt_mysql_credentials()
    write_mysql_env(creds)
    load_dotenv(ENV_MYSQL_FILE, override=True)

def get_db_connection():
    ensure_mysql_env()

    logger.info("🔧 Creating DB connection object...")
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )
        logger.info("✅ DB connection object created")
        return conn
    except Exception as e:
        logger.error(f"❌ Failed to connect to MySQL: {e}")
        raise

def execute_sql_query(sql_query: str) -> Tuple[str, Any]:
    """
    Executes a SQL query against the real database.

    Returns:
        status: "OK" | "RUNTIME_ERROR"
        result: fetched rows or error message
    """
    logger.info(f"📌 Received SQL query:\n{sql_query}")

    try:
        logger.info("🔌 Connecting to MySQL database...")
        conn = get_db_connection()

        if conn.is_connected():
            logger.info("✅ Connection established")
        else:
            logger.error("❌ Connection failed (conn.is_connected() returned False)")

        cursor = conn.cursor()
        logger.info("📝 Executing SQL query...")

        cursor.execute(sql_query)
        logger.info("📝 Query executed successfully")

        # Try fetching results (SELECT)
        try:
            logger.info("📥 Attempting to fetch results...")
            result = cursor.fetchall()
            logger.info(f"📥 Rows fetched: {len(result)}")
        except Exception as fetch_err:
            logger.warning(f"⚠️ No fetchable results (likely non-SELECT). Error: {fetch_err}")
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

def extract_schema(database_name: str | None = None) -> dict:
    if database_name is None:
        database_name = os.getenv("DB_NAME", "")
    logger.info(f"📚 Extracting schema for database: {database_name}")

    conn = get_db_connection()
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

    for r in rows:
        logger.debug(f"➡️ Processing column: {r['TABLE_NAME']}.{r['COLUMN_NAME']}") # pyright: ignore[reportArgumentType, reportCallIssue]
        constraints = []

        if r["COLUMN_KEY"] == "PRI": # pyright: ignore[reportArgumentType, reportCallIssue]
            constraints.append("PRIMARY KEY")
        if r["IS_NULLABLE"] == "NO": # pyright: ignore[reportArgumentType, reportCallIssue]
            constraints.append("NOT NULL")
        if "auto_increment" in (r["EXTRA"] or ""): # pyright: ignore[reportOperatorIssue, reportArgumentType, reportCallIssue]
            constraints.append("AUTO_INCREMENT")

        tables[r["TABLE_NAME"]].append({ # type: ignore
            "name": r["COLUMN_NAME"], # type: ignore
            "type": r["DATA_TYPE"].upper(), # type: ignore
            "constraints": constraints
        })

    schema = {
        "tables": [],
        "semantic_notes": []
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