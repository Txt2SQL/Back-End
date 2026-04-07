import sqlite3

from src.classes.domain_states.query import QuerySession, Records
from .base_client import BaseClient
from src.classes.logger import LoggerManager
from config import DATASET_DATA

class SQLiteClient(BaseClient):
    
    def __init__(self, database: str) -> None:
        super().__init__()
        self.database = database
        self.sqlite_file = DATASET_DATA / self.database / f"{self.database}.sqlite"
        self.connection: sqlite3.Connection | None = None

        self.open_connection()

    @property
    def logger(self):
        return LoggerManager.get_logger(__name__)

    def open_connection(self) -> None:
        if self.connection is not None:
            try:
                self.connection.execute("SELECT 1")
                return
            except sqlite3.Error:
                self.close_connection()

        self.logger.info("🔌 Opening SQLite connection to '%s'", self.sqlite_file)
        self.connection = sqlite3.connect(self.sqlite_file)
        self.logger.debug("✅ SQLite connection established successfully")

    def close_connection(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None
            self.logger.info("🔒 SQLite connection closed")

    def execute_query(self, query: QuerySession) -> QuerySession:
        """
        Executes the SQL code within the QuerySession against the SQLite database.
        Populates the session with Records on success, or an error string on failure.
        """
        if not query.sql_code:
            self.logger.warning("execute_query called but QuerySession has no sql_code.")
            query.valid_syntax = False
            query.execution_result = "No SQL code provided."
            query.rows_fetched = 0
            return query

        self.logger.debug(f"Executing query on '{self.database}': {query.sql_code}")

        cursor = None
        try:
            self.open_connection()
            if self.connection is None:
                raise ConnectionError("Failed to establish a connection to the SQLite database")

            cursor = self.connection.cursor()
            cursor.execute(query.sql_code)

            rows = cursor.fetchall()
            columns = [description[0] for description in (cursor.description or [])]

            query.execution_result = Records(rows, columns=columns)
            query.rows_fetched = len(rows)
            query.valid_syntax = True

            self.logger.debug(f"Query executed successfully. Rows fetched: {query.rows_fetched}")

        except sqlite3.Error as e:
            error_msg = str(e)
            self.logger.error(f"SQLite error on '{self.database}': {error_msg}")
            
            query.execution_result = error_msg
            query.valid_syntax = False
            query.rows_fetched = 0
        finally:
            if cursor is not None:
                cursor.close()

        return query

    def get_foreign_keys(self, table_names: list[str] | None = None) -> list[str]:
        """
        Fetch join relationships directly from SQLite foreign key metadata using PRAGMAs.
        Returns human-readable join hints matching the MySQL implementation.
        
        Args:
            table_names: Optional list of table names to filter foreign keys.
                        If provided, only returns relationships where both tables
                        are in the list.
        """
        self.logger.info("🔍 Fetching relationship metadata from SQLite...")
        
        if not self.database:
            self.logger.warning("⚠️  DB_NAME is not set; cannot load foreign keys from SQLite")
            return []

        relationships = []
        cursor = None
        
        try:
            self.open_connection()
            if self.connection is None:
                raise ConnectionError("Failed to establish a connection to the SQLite database")

            cursor = self.connection.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            all_tables = [row[0] for row in cursor.fetchall()]

            for table_name in all_tables:
                cursor.execute(f"PRAGMA foreign_key_list('{table_name}');")
                fk_list = cursor.fetchall()

                for fk in fk_list:
                    referenced_table = fk[2]
                    column_name = fk[3]
                    referenced_column = fk[4]
                    
                    if table_names is not None:
                        if table_name not in table_names or referenced_table not in table_names:
                            continue
                    
                    relationship = f"{table_name}.{column_name} → {referenced_table}.{referenced_column}"
                    relationships.append(relationship)

        except sqlite3.Error as e:
            self.logger.warning("⚠️  Failed to query foreign key metadata: %s", str(e))
            return []
        finally:
            if cursor is not None:
                cursor.close()

        if not relationships and not table_names:
            self.logger.info("📭 No foreign key relationships found in SQLite metadata")
            return []

        if relationships:
            self.logger.info("Found %s foreign key relationship(s)", len(relationships))

        # Sort and deduplicate exactly as the MySQL client does
        unique_relationships = sorted(set(relationships))
        
        if table_names:
            self.logger.info("📊 Summary (filtered for tables: %s):", ", ".join(table_names))
        else:
            self.logger.info("📊 Summary (all relationships):")
        
        self.logger.info("  Foreign key relationships: %s", len(unique_relationships))
        
        return unique_relationships
