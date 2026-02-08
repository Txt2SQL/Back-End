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
        is_nullable = row[2]
        extra = row[5]  # auto_increment

        columns.append({
            'name': col_name,
            'type': col_type,
            'is_auto_increment': 'auto_increment' in extra.lower(),
            'is_nullable': is_nullable.upper() == 'YES'
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


def get_foreign_keys(cursor, db_name):
    """Return foreign key mappings for tables in the database."""
    cursor.execute(
        """
        SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL
        """,
        (db_name,)
    )
    foreign_keys = {}
    for table_name, column_name, ref_table, ref_column in cursor.fetchall():
        foreign_keys.setdefault(table_name, []).append({
            'column': column_name,
            'ref_table': ref_table,
            'ref_column': ref_column
        })
    return foreign_keys


def order_tables_by_dependencies(tables, foreign_keys):
    """Topologically sort tables based on foreign key dependencies."""
    dependencies = {table: set() for table in tables}
    for table, fks in foreign_keys.items():
        for fk in fks:
            if fk['ref_table'] in dependencies:
                dependencies[table].add(fk['ref_table'])

    ordered = []
    remaining = set(tables)

    while remaining:
        ready = [table for table in remaining if not dependencies[table]]
        if not ready:
            return tables
        for table in ready:
            remaining.remove(table)
            ordered.append(table)
            for other_table in remaining:
                dependencies[other_table].discard(table)

    return ordered


def fetch_fk_values(cursor, table_name, column_name):
    """Fetch existing values for a referenced column."""
    cursor.execute(
        f"SELECT {quote_identifier(column_name)} FROM {quote_identifier(table_name)}"
    )
    return [row[0] for row in cursor.fetchall()]


def populate_table(cursor, table_name, rows_per_table, foreign_keys, fk_value_cache):
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

    fk_map = {fk['column']: fk for fk in foreign_keys.get(table_name, [])}

    data_batch = []
    for _ in range(rows_per_table):
        row_data = []
        for col in insert_cols:
            fk = fk_map.get(col['name'])
            if fk:
                cache_key = (fk['ref_table'], fk['ref_column'])
                if cache_key not in fk_value_cache:
                    fk_value_cache[cache_key] = fetch_fk_values(
                        cursor,
                        fk['ref_table'],
                        fk['ref_column']
                    )
                fk_values = fk_value_cache[cache_key]
                if fk_values:
                    val = random.choice(fk_values)
                elif col['is_nullable']:
                    val = None
                else:
                    val = generate_fake_value(col['type'], col['name'])
            else:
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


def select_tables(tables, action_label):
    if not tables:
        print("Nessuna tabella trovata nel database selezionato.")
        logger.info("No tables found while selecting tables for %s.", action_label)
        return []

    table_choice = None
    while table_choice not in {"1", "2"}:
        print(f"\nVuoi {action_label} in tutte le tabelle o in una specifica?")
        print("1) tutte le tabelle")
        print("2) una tabella specifica")
        table_choice = input("Seleziona un'opzione (1/2): ").strip()

    if table_choice == "1":
        return tables

    print("\nTabelle disponibili:")
    for idx, table_name in enumerate(sorted(tables), start=1):
        print(f"{idx}) {table_name}")

    selected_table = None
    sorted_tables = sorted(tables)
    while selected_table is None:
        choice = input("Scegli la tabella (nome o numero): ").strip()
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(sorted_tables):
                selected_table = sorted_tables[index]
                break
        if choice in tables:
            selected_table = choice

        if selected_table is None:
            print("Selezione non valida. Riprova.")

    return [selected_table]


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
    while action not in {"1", "2", "3"}:
        print("\nCosa vuoi fare?")
        print("1) crea nuovo database")
        print("2) aggiungi nuovi record a database esistenti")
        print("3) empty database (svuota database)")
        action = input("Seleziona un'opzione (1/2/3): ").strip()

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
            print(f"[-] Database '{db_name}' does not exist.")
            logger.info("Database '%s' does not exist.", db_name)
            return

        cursor.execute(f"USE {quote_identifier(db_name)}")

    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]

    foreign_keys = get_foreign_keys(cursor, db_name)
    ordered_tables = order_tables_by_dependencies(tables, foreign_keys)
    fk_value_cache = {}

    for table in ordered_tables:
        populate_table(cursor, table, rows_per_table, foreign_keys, fk_value_cache)

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