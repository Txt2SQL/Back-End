import mysql.connector, os
from datetime import datetime
from typing import Tuple, Any
from collections import defaultdict
from dotenv import load_dotenv
from logging_utils import setup_logger

load_dotenv()

# === LOGGING SETUP ===
logger = setup_logger(__name__)

def get_db_connection():
    logger.info("🔧 Creating DB connection object...")
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    logger.info("🔧 DB connection object created")
    return conn

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