import mysql.connector
from typing import Tuple, Any

def get_db_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="Vittorio.1931",
        database="supermarket",
        port=3306
    )

def execute_sql_query(sql_query: str) -> Tuple[str, Any]:
    """
    Executes a SQL query against the real database.

    Returns:
        status: "OK" | "RUNTIME_ERROR"
        result: fetched rows or error message
    """
    try:
        print("🔌 Connecting to MySQL database...")
        conn = get_db_connection()
        if conn.is_connected():
            print("✅ Connection established")
        cursor = conn.cursor()

        cursor.execute(sql_query)

        # Try fetching results (SELECT)
        try:
            result = cursor.fetchall()
        except Exception:
            result = None

        conn.commit()
        cursor.close()
        conn.close()

        return "OK", result

    except Exception as e:
        return "RUNTIME_ERROR", str(e)
