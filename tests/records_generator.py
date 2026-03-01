import argparse
import glob, sys, os, random, uuid, re
# Add parent directory to Python path for development
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from faker import Faker
from config import INPUT_DIR
from mysql.connector import Error
from src.classes.clients.mysql_client import MySQLClient
from src.classes.logger import LoggerManager


# Configuration
DDL_DIR = INPUT_DIR / 'existing_ddl'
DEFAULT_ROWS_PER_TABLE = 100  # How many fake rows to generate per table

fake = Faker()
LoggerManager.setup_project_logger()
logger = LoggerManager.get_logger(__name__)


def get_mysql_client(database: str | None = None):
    """Create a MySQL connection through the shared MySQLClient wrapper."""
    mysql_client = MySQLClient(database)
    return mysql_client


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


def get_foreign_key_map(cursor, table_name):
    """Return mapping of column name -> (referenced_table, referenced_column)."""
    cursor.execute(
        """
        SELECT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND REFERENCED_TABLE_NAME IS NOT NULL
        """,
        (table_name,)
    )
    return {row[0]: (row[1], row[2]) for row in cursor.fetchall()}


def get_primary_key_columns(cursor, table_name):
    """Return list of primary key columns for a table."""
    cursor.execute(
        """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND CONSTRAINT_NAME = 'PRIMARY'
        ORDER BY ORDINAL_POSITION
        """,
        (table_name,)
    )
    return [row[0] for row in cursor.fetchall()]


def get_table_dependencies(cursor, tables):
    """Return dependency mapping of table -> referenced tables."""
    dependencies = {table: set() for table in tables}
    for table in tables:
        cursor.execute(
            """
            SELECT REFERENCED_TABLE_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
              AND REFERENCED_TABLE_NAME IS NOT NULL
            """,
            (table,)
        )
        dependencies[table] = {row[0] for row in cursor.fetchall() if row[0] in tables}
    return dependencies


def order_tables_by_dependency(cursor, tables):
    """Order tables based on FK dependencies (parents before children)."""
    dependencies = get_table_dependencies(cursor, tables)
    remaining = {table: set(deps) for table, deps in dependencies.items()}
    ordered = []
    while remaining:
        ready = [table for table, deps in remaining.items() if not deps]
        if not ready:
            ordered.extend(sorted(remaining.keys()))
            break
        for table in sorted(ready):
            ordered.append(table)
            remaining.pop(table)
        for deps in remaining.values():
            deps.difference_update(ready)
    return ordered


def get_existing_values(cursor, table_name, column_name, cache):
    """Return cached list of existing values for a referenced column."""
    cache_key = (table_name, column_name)
    if cache_key not in cache:
        cursor.execute(
            f"SELECT {quote_identifier(column_name)} FROM {quote_identifier(table_name)} "
            f"WHERE {quote_identifier(column_name)} IS NOT NULL"
        )
        cache[cache_key] = [row[0] for row in cursor.fetchall()]
    return cache[cache_key]


def get_existing_pk_tuples(cursor, table_name, pk_columns, cache):
    """Return cached set of existing PK tuples for a table."""
    cache_key = (table_name, tuple(pk_columns))
    if cache_key not in cache:
        cols = ", ".join(quote_identifier(col) for col in pk_columns)
        cursor.execute(f"SELECT {cols} FROM {quote_identifier(table_name)}")
        cache[cache_key] = {tuple(row) for row in cursor.fetchall()}
    return cache[cache_key]


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
    if 'datetime' in col_type or 'timestamp' in col_type:
        return fake.date_time_between(start_date='-2y', end_date='now').strftime('%Y-%m-%d %H:%M:%S')
    if col_type.startswith('date'):
        return fake.date_between(start_date='-2y', end_date='today').strftime('%Y-%m-%d')
    if col_type.startswith('time'):
        return fake.time(pattern='%H:%M:%S')
    if 'decimal' in col_type or 'float' in col_type or 'double' in col_type:
        return round(random.uniform(10.0, 500.0), 2)

    # Fallback
    return "test"


def generate_primary_key_value(col_type, pk_counters):
    """Generate a PK-safe value based on column type."""
    col_type = col_type.lower()
    if 'int' in col_type or 'tinyint' in col_type:
        pk_counters['next'] += 1
        return pk_counters['next']
    if 'char' in col_type or 'text' in col_type or 'varchar' in col_type:
        max_len = None
        length_match = re.search(r"\((\d+)\)", col_type)
        if length_match:
            max_len = int(length_match.group(1))
        value = uuid.uuid4().hex
        return value[:max_len] if max_len else value
    return generate_fake_value(col_type, "id")


def populate_table(cursor, table_name, rows_per_table, fk_value_cache, pk_cache, pk_tuple_cache):
    """Generate and insert fake data with fallback when batch insert fails."""
    logger.info("Populating table: %s", table_name)
    columns = get_table_schema(cursor, table_name)
    fk_map = get_foreign_key_map(cursor, table_name)
    pk_columns = get_primary_key_columns(cursor, table_name)
    pk_column_set = set(pk_columns)
    pk_columns_non_auto = [col for col in pk_columns if not next(
        (c for c in columns if c['name'] == col and c['is_auto_increment']),
        None
    )]
    pk_counters = {}
    for col in pk_columns_non_auto:
        col_type = next(c['type'] for c in columns if c['name'] == col)
        if 'int' in col_type.lower() or 'tinyint' in col_type.lower():
            existing_values = get_existing_values(cursor, table_name, col, pk_cache)
            pk_counters[col] = {'next': max(existing_values, default=0)}

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
    existing_pk_tuples = None
    if pk_columns_non_auto:
        existing_pk_tuples = get_existing_pk_tuples(cursor, table_name, pk_columns_non_auto, pk_tuple_cache)
    missing_fk_logged = set()
    for _ in range(rows_per_table):
        row_data = []
        skip_row = False
        for col in insert_cols:
            fk_target = fk_map.get(col['name'])
            if fk_target:
                ref_table, ref_column = fk_target
                available_values = get_existing_values(
                    cursor,
                    ref_table,
                    ref_column,
                    fk_value_cache
                )
                if available_values:
                    val = random.choice(available_values)
                elif col['is_nullable']:
                    val = None
                else:
                    skip_row = True
                    missing_key = (table_name, col['name'])
                    if missing_key not in missing_fk_logged:
                        logger.warning(
                            "Missing referenced values for %s.%s -> %s.%s; skipping rows.",
                            table_name,
                            col['name'],
                            ref_table,
                            ref_column
                        )
                        missing_fk_logged.add(missing_key)
                    break
            else:
                if col['name'] in pk_column_set and col['name'] in pk_columns_non_auto:
                    col_type = col['type']
                    pk_counter = pk_counters.get(col['name'], {'next': 0})
                    val = generate_primary_key_value(col_type, pk_counter)
                    pk_counters[col['name']] = pk_counter
                else:
                    val = generate_fake_value(col['type'], col['name'])
            row_data.append(val)
        if skip_row:
            continue
        if pk_columns_non_auto:
            pk_values = []
            for pk_col in pk_columns_non_auto:
                pk_index = col_names.index(pk_col)
                pk_values.append(row_data[pk_index])
            pk_tuple = tuple(pk_values)
            if pk_tuple in existing_pk_tuples: # pyright: ignore[reportOperatorIssue]
                continue
            existing_pk_tuples.add(pk_tuple) # pyright: ignore[reportOptionalMemberAccess]
        data_batch.append(tuple(row_data))

    if not data_batch:
        print(f"    Skipping {table_name} (No valid rows to insert)")
        logger.info("Skipping %s (no valid rows to insert).", table_name)
        return

    inserted_rows = 0
    try:
        cursor.executemany(sql, data_batch)
        inserted_rows = len(data_batch)
        for row in data_batch:
            for col_idx, col_name in enumerate(col_names):
                fk_value_cache.setdefault((table_name, col_name), []).append(row[col_idx])
    except Error as batch_error:
        print(f"    Batch insert failed for {table_name}: {batch_error}")
        logger.warning("Batch insert failed for %s: %s", table_name, batch_error)
        # Fallback to per-row insert so one bad row does not drop all inserts
        for row in data_batch:
            try:
                cursor.execute(sql, row)
                inserted_rows += 1
                for col_idx, col_name in enumerate(col_names):
                    fk_value_cache.setdefault((table_name, col_name), []).append(row[col_idx])
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


def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate fake records for MySQL tables.")
    parser.add_argument(
        "--create",
        action="store_true",
        default=False,
        help="Create a new database from a local schema before inserting records."
    )
    return parser.parse_args()


def select_database_by_index_or_name(options, prompt):
    selected_option = None
    sorted_options = sorted(options)
    while selected_option is None:
        choice = input(prompt).strip()
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(sorted_options):
                selected_option = sorted_options[index]
                break
        if choice in options:
            selected_option = choice

        if selected_option is None:
            print("Selezione non valida. Riprova.")
    return selected_option


def main():
    args = parse_arguments()
    create = args.create

    db_client = None
    conn = None
    cursor = None

    try:
        db_client = get_mysql_client()
        if not db_client.connection.is_connected():
            print("Error connecting to MySQL.")
            logger.error("Connection object returned but not connected.")
            return

        print("Connected to MySQL Server.")
        logger.info("Connected to MySQL Server.")
        cursor = db_client.connection.cursor()

        db_name = None
        if create:
            sql_files = glob.glob(os.path.join(DDL_DIR, "*.sql"))
            if not sql_files:
                print("No .sql files found in directory.")
                logger.warning("No .sql files found in directory: %s", DDL_DIR)
                return

            available_schemas = {}
            for file_path in sql_files:
                base_name = os.path.basename(file_path)
                schema_name = os.path.splitext(base_name)[0]
                available_schemas[schema_name] = file_path

            print("\nSchema disponibili (da input/existing_ddl):")
            for idx, schema_name in enumerate(sorted(available_schemas.keys()), start=1):
                print(f"{idx}) {schema_name}")

            db_name = select_database_by_index_or_name(
                available_schemas.keys(),
                "Scegli lo schema/database da creare (nome o numero): "
            )
            file_path = available_schemas[db_name]

            print(f"\n--- Creating and processing {db_name} ---")
            logger.info("Creating and processing database: %s", db_name)

            if database_exists(cursor, db_name):
                print(f"[-] Database '{db_name}' already exists.")
                logger.info("Database '%s' already exists, cannot create.", db_name)
                return

            create_database(cursor, db_name)
            cursor.execute(f"USE {quote_identifier(db_name)}") # pyright: ignore[reportOptionalMemberAccess]
            execute_sql_file(cursor, file_path)
            db_client.connection.commit()
            logger.info("DDL executed and committed for %s.", db_name)
        else:
            available_dbs = [
                db for db in db_client.list_databases()
                if db not in {"information_schema", "mysql", "performance_schema", "sys"}
            ]

            if not available_dbs:
                print("No user databases found in the connected server.")
                logger.warning("No user databases available on server.")
                return

            print("\nDatabase disponibili sul server:")
            for idx, available_db in enumerate(sorted(available_dbs), start=1):
                print(f"{idx}) {available_db}")

            db_name = select_database_by_index_or_name(
                available_dbs,
                "Scegli il database esistente (nome o numero): "
            )

            print(f"\n--- Processing {db_name} ---")
            logger.info("Processing existing database: %s", db_name)
            cursor.execute(f"USE {quote_identifier(db_name)}") # pyright: ignore[reportOptionalMemberAccess]

        cursor.execute("SHOW TABLES") # pyright: ignore[reportOptionalMemberAccess]
        tables = [table[0] for table in cursor.fetchall()] # pyright: ignore[reportArgumentType, reportOptionalMemberAccess]

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

        selected_tables = select_tables(tables, "inserire record")
        if not selected_tables:
            return

        cursor.execute("SET FOREIGN_KEY_CHECKS = 0") # pyright: ignore[reportOptionalMemberAccess]
        fk_value_cache = {}
        pk_value_cache = {}
        pk_tuple_cache = {}
        ordered_tables = order_tables_by_dependency(cursor, selected_tables)
        for table in ordered_tables:
            populate_table(cursor, table, rows_per_table, fk_value_cache, pk_value_cache, pk_tuple_cache)
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1") # pyright: ignore[reportOptionalMemberAccess]
        db_client.connection.commit()

    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        logger.exception("Error in MySQL workflow.")
        return
    finally:
        if cursor is not None:
            cursor.close()
        if db_client is not None:
            db_client.close_connection()

    print("\nDone.")
    logger.info("Done.")


if __name__ == "__main__":
    main()
