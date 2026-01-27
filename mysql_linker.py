import mysql.connector, os
from typing import Tuple, Any
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    print("\n🔧 Creating DB connection object...")
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    print("\n🔧 DB connection object created")
    return conn


def execute_sql_query(sql_query: str) -> Tuple[str, Any]:
    """
    Executes a SQL query against the real database.

    Returns:
        status: "OK" | "RUNTIME_ERROR"
        result: fetched rows or error message
    """
    print(f"\n📌 Received SQL query:\n{sql_query}")

    try:
        print("\n🔌 Connecting to MySQL database...")
        conn = get_db_connection()

        if conn.is_connected():
            print("\n✅ Connection established")
        else:
            print("\n❌ Connection failed (conn.is_connected() returned False)")

        cursor = conn.cursor()
        print("\n📝 Executing SQL query...")

        cursor.execute(sql_query)
        print("\n📝 Query executed successfully")

        # Try fetching results (SELECT)
        try:
            print("\n📥 Attempting to fetch results...")
            result = cursor.fetchall()
            print(f"📥 Rows fetched: {len(result)}")
        except Exception as fetch_err:
            print(f"⚠️ No fetchable results (likely non-SELECT). Error: {fetch_err}")
            result = None

        print("\n💾 Committing transaction...")
        conn.commit()

        cursor.close()
        conn.close()
        print("\n🔒 Connection closed")

        return "OK", result

    except Exception as e:
        print(f"🔥 RUNTIME ERROR during SQL execution: {e}")
        return "RUNTIME_ERROR", str(e)


def extract_schema(database_name: str | None = None) -> dict:
    if database_name is None:
        database_name = os.getenv("DB_NAME", "")
    print(f"📚 Extracting schema for database: {database_name}")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    print("\n🔍 Querying information_schema.COLUMNS...")
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
    print(f"📊 Retrieved {len(rows)} column definitions")

    tables = defaultdict(list)

    for r in rows:
        print(f"➡️ Processing column: {r['TABLE_NAME']}.{r['COLUMN_NAME']}") # pyright: ignore[reportCallIssue, reportArgumentType]
        constraints = []

        if r["COLUMN_KEY"] == "PRI": # pyright: ignore[reportCallIssue, reportArgumentType]
            constraints.append("PRIMARY KEY")
        if r["IS_NULLABLE"] == "NO": # pyright: ignore[reportCallIssue, reportArgumentType]
            constraints.append("NOT NULL")
        if "auto_increment" in (r["EXTRA"] or ""): # pyright: ignore[reportOperatorIssue, reportArgumentType, reportCallIssue]
            constraints.append("AUTO_INCREMENT")

        tables[r["TABLE_NAME"]].append({ # pyright: ignore[reportCallIssue, reportArgumentType]
            "name": r["COLUMN_NAME"], # pyright: ignore[reportCallIssue, reportArgumentType]
            "type": r["DATA_TYPE"].upper(), # type: ignore
            "constraints": constraints
        })

    schema = {
        "tables": [],
        "semantic_notes": []
    }

    print("\n🧱 Building schema structure...")
    for table_name, columns in tables.items():
        print(f"📦 Adding table: {table_name} ({len(columns)} columns)")
        schema["tables"].append({
            "name": table_name,
            "columns": columns
        })

    cursor.close()
    conn.close()
    print("\n🏁 Schema extraction completed")

    return schema
