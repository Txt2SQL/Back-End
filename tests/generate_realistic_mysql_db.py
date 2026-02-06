import glob
import os
import random

import mysql.connector
from dotenv import load_dotenv
from faker import Faker
from mysql.connector import Error

# Load environment variables
load_dotenv()

# Configuration
SQL_DIR = './existing_ddl'
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASSWORD')
ROWS_PER_TABLE = 100  # How many fake rows to generate per table

fake = Faker()


def quote_identifier(identifier):
    """Safely quote MySQL identifiers such as db/table/column names."""
    return f"`{identifier.replace('`', '``')}`"


def get_db_connection(database=None):
    """Connect to MySQL Server."""
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=database
    )


def create_database(cursor, db_name):
    """Create the database only when it does not already exist."""
    try:
        cursor.execute(
            "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s",
            (db_name,)
        )
        db_exists = cursor.fetchone() is not None

        if db_exists:
            print(f"[=] Database '{db_name}' already exists. Skipping create/DDL and appending random rows.")
            return False

        cursor.execute(f"CREATE DATABASE {quote_identifier(db_name)}")
        print(f"[+] Database '{db_name}' created.")
        return True
    except Error as e:
        print(f"[-] Error creating database {db_name}: {e}")
        raise


def execute_sql_file(cursor, file_path):
    """Read SQL file and execute commands."""
    print(f"[*] Executing DDL from {file_path}...")
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


def populate_table(cursor, table_name):
    """Generate and insert fake data with fallback when batch insert fails."""
    columns = get_table_schema(cursor, table_name)

    # Filter out auto_increment columns (database handles them)
    insert_cols = [c for c in columns if not c['is_auto_increment']]

    if not insert_cols:
        print(f"    Skipping {table_name} (No columns to insert)")
        return

    col_names = [c['name'] for c in insert_cols]
    col_names_str = ", ".join(quote_identifier(name) for name in col_names)
    placeholders = ", ".join(["%s"] * len(col_names))

    sql = f"INSERT INTO {quote_identifier(table_name)} ({col_names_str}) VALUES ({placeholders})"

    data_batch = []
    for _ in range(ROWS_PER_TABLE):
        row_data = []
        for col in insert_cols:
            val = generate_fake_value(col['type'], col['name'])
            row_data.append(val)
        data_batch.append(tuple(row_data))

    inserted_rows = 0
    try:
        cursor.executemany(sql, data_batch)
        inserted_rows = ROWS_PER_TABLE
    except Error as batch_error:
        print(f"    Batch insert failed for {table_name}: {batch_error}")
        # Fallback to per-row insert so one bad row does not drop all inserts
        for row in data_batch:
            try:
                cursor.execute(sql, row)
                inserted_rows += 1
            except Error:
                continue

    print(f"    Inserted {inserted_rows}/{ROWS_PER_TABLE} rows into {table_name}")


def main():
    conn = None
    cursor = None

    # 1. Connect to MySQL Server (No specific DB yet)
    try:
        conn = get_db_connection()
        if conn.is_connected():
            print("Connected to MySQL Server.")
            cursor = conn.cursor()
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return

    # 2. Get list of .sql files
    sql_files = glob.glob(os.path.join(SQL_DIR, "*.sql"))

    if not sql_files:
        print("No .sql files found in directory.")
        return

    for file_path in sql_files:
        # Extract filename to use as database name (e.g., 'users.sql' -> 'users')
        base_name = os.path.basename(file_path)
        db_name = os.path.splitext(base_name)[0]

        print(f"\n--- Processing {db_name} ---")

        # Create database only when missing
        db_created = create_database(cursor, db_name)

        # Switch to the target database explicitly for this cursor/session
        cursor.execute(f"USE {quote_identifier(db_name)}")

        # Execute DDL only for a newly created database
        if db_created:
            execute_sql_file(cursor, file_path)
            conn.commit()

        # Disable FK checks to allow random insertion order
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        # Get list of tables in active database
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]

        # Populate each table
        for table in tables:
            populate_table(cursor, table)

        # Re-enable FK checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()

    if cursor is not None:
        cursor.close()
    if conn is not None and conn.is_connected():
        conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
