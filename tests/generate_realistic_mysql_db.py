import glob, sys, os, random
# Add parent directory to Python path for development
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from faker import Faker
from mysql.connector import Error
from src.mysql_linker import get_db_connection
from src.logging_utils import setup_single_project_logger, setup_logger


# Configuration
BASE_DIR = os.path.dirname(__file__)
SQL_DIR = os.path.join(BASE_DIR, 'input', 'existing_ddl')
DEFAULT_ROWS_PER_TABLE = 100  # How many fake rows to generate per table

fake = Faker()
setup_single_project_logger()
logger = setup_logger(__name__)


def quote_identifier(identifier):
    """Safely quote MySQL identifiers such as db/table/column names."""
    return f"`{identifier.replace('`', '``')}`"


def create_database(cursor, db_name):
    """Create the database only when it does not already exist."""
    try:
        logger.info("Checking if database exists: %s", db_name)
        cursor.execute(
            "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s",
            (db_name,)
        )
        db_exists = cursor.fetchone() is not None

        if db_exists:
            print(f"[=] Database '{db_name}' already exists. Skipping create/DDL and appending random rows.")
            logger.info("Database '%s' already exists; skipping create/DDL and appending rows.", db_name)
            return False

        cursor.execute(f"CREATE DATABASE {quote_identifier(db_name)}")
        print(f"[+] Database '{db_name}' created.")
        logger.info("Database '%s' created.", db_name)
        return True
    except Error as e:
        print(f"[-] Error creating database {db_name}: {e}")
        logger.exception("Error creating database %s", db_name)
        raise


def database_exists(cursor, db_name):
    """Check if database exists."""
    cursor.execute(
        "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s",
        (db_name,)
    )
    return cursor.fetchone() is not None


def execute_sql_file(cursor, file_path):
    """Read SQL file and execute commands."""
    print(f"[*] Executing DDL from {file_path}...")
    logger.info("Executing DDL from %s", file_path)
    with open(file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Split commands by semicolon (basic parsing)
    commands = sql_content.split(';')

    for command in commands:
        if command.strip():
            try:
                cursor.execute(command)
            except Error as e:
                print(f"    Warning executing statement: {e}")
                logger.warning("Warning executing statement from %s: %s", file_path, e)


def get_table_schema(cursor, table_name):
    """Fetch column names and data types for a table."""
    cursor.execute(f"DESCRIBE {quote_identifier(table_name)}")
    columns = []
    for row in cursor.fetchall():
        col_name = row[0]
        col_type = row[1]
        extra = row[5]  # auto_increment

        columns.append({
            'name': col_name,
            'type': col_type,
            'is_auto_increment': 'auto_increment' in extra.lower()
        })
    return columns


def generate_fake_value(col_type, col_name):
    """Generate a fake value based on SQL type and column name."""
    col_type = col_type.lower()
    col_name = col_name.lower()

    # Heuristics based on column name
    if 'email' in col_name:
        return fake.email()
    if 'name' in col_name:
        return fake.name()
    if 'phone' in col_name:
        return fake.phone_number()
    if 'address' in col_name:
        return fake.address()

    # Heuristics based on data type
    if 'int' in col_type or 'tinyint' in col_type:
        return random.randint(1, 100)
    if 'varchar' in col_type or 'text' in col_type or 'char' in col_type:
        return fake.word() if 'varchar(10)' in col_type else fake.sentence()
    if 'date' in col_type or 'time' in col_type:
        return fake.date_time_between(start_date='-2y', end_date='now').strftime('%Y-%m-%d %H:%M:%S')
    if 'decimal' in col_type or 'float' in col_type or 'double' in col_type:
        return round(random.uniform(10.0, 500.0), 2)

    # Fallback
    return "test"


def populate_table(cursor, table_name, rows_per_table):
    """Generate and insert fake data with fallback when batch insert fails."""
    logger.info("Populating table: %s", table_name)
    columns = get_table_schema(cursor, table_name)

    # Filter out auto_increment columns (database handles them)
    insert_cols = [c for c in columns if not c['is_auto_increment']]

    if not insert_cols:
        print(f"    Skipping {table_name} (No columns to insert)")
        logger.info("Skipping %s (no insertable columns).", table_name)
        return

    col_names = [c['name'] for c in insert_cols]
    col_names_str = ", ".join(quote_identifier(name) for name in col_names)
    placeholders = ", ".join(["%s"] * len(col_names))

    sql = f"INSERT INTO {quote_identifier(table_name)} ({col_names_str}) VALUES ({placeholders})"

    data_batch = []
    for _ in range(rows_per_table):
        row_data = []
        for col in insert_cols:
            val = generate_fake_value(col['type'], col['name'])
            row_data.append(val)
        data_batch.append(tuple(row_data))

    inserted_rows = 0
    try:
        cursor.executemany(sql, data_batch)
        inserted_rows = rows_per_table
    except Error as batch_error:
        print(f"    Batch insert failed for {table_name}: {batch_error}")
        logger.warning("Batch insert failed for %s: %s", table_name, batch_error)
        # Fallback to per-row insert so one bad row does not drop all inserts
        for row in data_batch:
            try:
                cursor.execute(sql, row)
                inserted_rows += 1
            except Error:
                continue

    print(f"    Inserted {inserted_rows}/{rows_per_table} rows into {table_name}")
    logger.info("Inserted %s/%s rows into %s.", inserted_rows, rows_per_table, table_name)


def main():
    conn = None
    cursor = None

    # 1. Connect to MySQL Server (No specific DB yet)
    try:
        conn = get_db_connection()
        if conn.is_connected():
            print("Connected to MySQL Server.")
            logger.info("Connected to MySQL Server.")
            cursor = conn.cursor()
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        logger.exception("Error connecting to MySQL.")
        return

    # 2. Get list of .sql files
    sql_files = glob.glob(os.path.join(SQL_DIR, "*.sql"))

    if not sql_files:
        print("No .sql files found in directory.")
        logger.warning("No .sql files found in directory: %s", SQL_DIR)
        return

    action = None
    while action not in {"1", "2"}:
        print("\nCosa vuoi fare?")
        print("1) crea nuovo database")
        print("2) aggiungi nuovi record a database esistenti")
        action = input("Seleziona un'opzione (1/2): ").strip()

    rows_per_table = None
    while rows_per_table is None:
        rows_input = input(
            f"Quanti record inserire per tabella? (default {DEFAULT_ROWS_PER_TABLE}): "
        ).strip()
        if not rows_input:
            rows_per_table = DEFAULT_ROWS_PER_TABLE
            break
        if rows_input.isdigit() and int(rows_input) > 0:
            rows_per_table = int(rows_input)
            break
        print("Inserisci un numero valido maggiore di zero.")

    available_dbs = {}
    for file_path in sql_files:
        base_name = os.path.basename(file_path)
        db_name = os.path.splitext(base_name)[0]
        available_dbs[db_name] = file_path

    print("\nDatabase disponibili (da input/existing_ddl):")
    for idx, db_name in enumerate(sorted(available_dbs.keys()), start=1):
        print(f"{idx}) {db_name}")

    selected_db = None
    sorted_db_names = sorted(available_dbs.keys())
    while selected_db is None:
        choice = input("Scegli il database (nome o numero): ").strip()
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(sorted_db_names):
                selected_db = sorted_db_names[index]
                break
        if choice in available_dbs:
            selected_db = choice

        if selected_db is None:
            print("Selezione non valida. Riprova.")

    db_name = selected_db
    file_path = available_dbs[db_name]

    print(f"\n--- Processing {db_name} ---")
    logger.info("Processing database: %s", db_name)

    if action == "1":
        if database_exists(cursor, db_name):
            print(f"[=] Database '{db_name}' already exists. Skipping create/DDL.")
            logger.info("Database '%s' already exists; skipping create/DDL.", db_name)
            return

        create_database(cursor, db_name)
        cursor.execute(f"USE {quote_identifier(db_name)}")
        execute_sql_file(cursor, file_path)
        conn.commit()
        logger.info("DDL executed and committed for %s.", db_name)
    else:
        if not database_exists(cursor, db_name):
            print(f"[-] Database '{db_name}' does not exist. Cannot add records.")
            logger.info("Database '%s' does not exist; cannot add records.", db_name)
            return

        cursor.execute(f"USE {quote_identifier(db_name)}")

    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]

    for table in tables:
        populate_table(cursor, table, rows_per_table)

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()

    if cursor is not None:
        cursor.close()
    if conn is not None and conn.is_connected():
        conn.close()
    print("\nDone.")
    logger.info("Done.")


if __name__ == "__main__":
    main()
