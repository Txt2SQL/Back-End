from getpass import getpass

import mysql.connector
from src.classes.domain_states.query import QuerySession
from src.classes.domain_states.enums import QueryStatus
from collections import defaultdict
from src.classes.loaders.mysql_loader import MySQLLoader
from src.classes.logger import LoggerManager

class MySQLClient:
    
    def __init__(self, database: str | None = None):
        self.config = MySQLLoader().config
        self.database = database
        
        self.set_connection()
    
    @property
    def logger(self):
        return LoggerManager.get_logger(__name__)
    
    def set_connection(self):
        try:
            self.logger.info("🔌 Establishing database connection with config: %s", {k: v for k, v in self.config.items() if k != "password"})
            connection_params = {
                "host": self.config["DB_HOST"],
                "port": int(self.config["DB_PORT"]),
                "user": self.config["DB_USER"],
                "password": self.config["DB_PASSWORD"],
                "connection_timeout": 10,   # seconds to establish connection
                "read_timeout": 30,         # seconds waiting for server response
                "write_timeout": 30,        # seconds sending query
            }
            if self.database is not None:
                self.logger.debug(f"📂 Setting database to: {self.database}")
                connection_params["database"] = self.database
                
            self.connection = mysql.connector.connect(**connection_params)
            self.logger.debug("✅ Database connection established successfully")
        except mysql.connector.Error as err:
            self.logger.error(f"Error connecting to the database: {err}")
            raise
    
    def execute_query(self, query: QuerySession):
        self.logger.info(f"📌 Received SQL query:\n{query.sql_code}")

        try:
            self.set_connection()

            if not self.connection.is_connected():
                raise ConnectionError("Failed to establish a connection to the database")

            cursor = self.connection.cursor(dictionary=True)

            # 🔒 Set max execution time (30 seconds)
            try:
                cursor.execute("SET SESSION MAX_EXECUTION_TIME = 30000")
                self.logger.debug("⏳ MAX_EXECUTION_TIME set to 30 seconds")
            except Exception as timeout_err:
                self.logger.warning(f"Could not set MAX_EXECUTION_TIME: {timeout_err}")

            if query.sql_code is None:
                raise ValueError("SQL query is None, cannot execute")

            self.logger.info("📝 Executing SQL query...")
            cursor.execute(query.sql_code)

            try:
                self.logger.info("📥 Attempting to fetch results...")
                query.execution_result = cursor.fetchall()
                if query.execution_result is not None:
                    self.logger.info(f"📥 Rows fetched: {len(query.execution_result)}")
            except Exception as fetch_err:
                query.execution_result = None
                raise fetch_err

            query.execution_status = QueryStatus.SUCCESS

            self.connection.commit()
            cursor.close()
            self.connection.close()
            self.logger.info("🔒 Connection closed")

        except mysql.connector.errors.DatabaseError as e:
            # ⬇️ Catch timeout specifically
            if "maximum statement execution time exceeded" in str(e).lower():
                self.logger.error("⏰ Query execution timed out")
                query.execution_status = QueryStatus.TIMEOUT_ERROR
                query.execution_result = "Query execution exceeded time limit (30s)"
            else:
                self.logger.error(f"🔥 RUNTIME ERROR during SQL execution: {e}")
                query.execution_status = QueryStatus.RUNTIME_ERROR
                query.execution_result = str(e)

        except Exception as e:
            self.logger.error(f"🔥 RUNTIME ERROR during SQL execution: {e}")
            query.execution_status = QueryStatus.RUNTIME_ERROR
            query.execution_result = str(e)

        return query
    
    def extract_schema(self) -> dict:
        if self.database is None:
            raise ValueError("Database name must be provided or set in DB_NAME environment variable")
        
        self.logger.info(f"📚 Extracting schema for database: {self.database}")
        
        
        schema_query = f"""
            SELECT
                c.TABLE_NAME,
                c.COLUMN_NAME,
                c.DATA_TYPE,
                c.IS_NULLABLE,
                c.COLUMN_KEY,
                c.EXTRA
            FROM information_schema.COLUMNS c
            WHERE c.TABLE_SCHEMA = {self.database!r}
            ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION
        """
        
        query = self.execute_query(QuerySession(sql_query=schema_query))

        if query.execution_status != QueryStatus.SUCCESS:
            self.logger.error(f"Failed to extract schema: {query.execution_result}")
            raise RuntimeError(f"Schema extraction failed: {query.execution_result}")
        if not query.execution_result:
            self.logger.warning("No columns found in the database schema")
            raise RuntimeError("Schema extraction returned no results")
        rows = query.execution_result
        tables = defaultdict(list)

        for row in rows:  # type: ignore[union-attr]
            table_name = row["TABLE_NAME"] # pyright: ignore[reportArgumentType, reportCallIssue]
            column_name = row["COLUMN_NAME"] # pyright: ignore[reportArgumentType, reportCallIssue]
            data_type = row["DATA_TYPE"] # pyright: ignore[reportArgumentType, reportCallIssue]
            is_nullable = row["IS_NULLABLE"] # pyright: ignore[reportArgumentType, reportCallIssue]
            column_key = row["COLUMN_KEY"] # pyright: ignore[reportArgumentType, reportCallIssue]
            extra = row["EXTRA"] or "" # pyright: ignore[reportArgumentType, reportCallIssue]
            
            self.logger.debug(f"➡️ Processing column: {table_name}.{column_name}")
            
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

        self.logger.info("🧱 Building schema structure...")
        for table_name, columns in tables.items():
            self.logger.info(f"📦 Adding table: {table_name} ({len(columns)} columns)")
            schema["tables"].append({
                "name": table_name,
                "columns": columns
            })

        self.logger.info("🏁 Schema extraction completed")

        return schema
    
    def get_foreign_keys(self, table_names: list[str] | None = None) -> list[str]:
        """
        Fetch join relationships directly from MySQL foreign key metadata.
        Returns human-readable join hints.
        
        Args:
            table_names: Optional list of table names to filter foreign keys.
                        If provided, only returns relationships where both tables
                        are in the list.
        """
        self.logger.info("🔍 Fetching relationship metadata from MySQL...")
        if not self.database:
            self.logger.warning("⚠️  DB_NAME is not set; cannot load foreign keys from MySQL")
            return []

        fk_query = f"""
            SELECT
                kcu.TABLE_NAME,
                kcu.COLUMN_NAME,
                kcu.REFERENCED_TABLE_NAME,
                kcu.REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE kcu
            WHERE kcu.TABLE_SCHEMA = '{self.database}'
            AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
            ORDER BY kcu.TABLE_NAME, kcu.COLUMN_NAME
        """

        self.logger.debug("Executing foreign key query for database: %s", self.database)
        query = self.execute_query(QuerySession(sql_query=fk_query))
        
        if query.execution_status != QueryStatus.SUCCESS:
            self.logger.warning("⚠️  Failed to query foreign key metadata: %s", query.execution_result)
            return []

        rows = query.execution_result
        if not rows:
            self.logger.info("📭 No foreign key relationships found in MySQL metadata")
            return []

        self.logger.info("Found %s foreign key relationship(s)", len(rows))
        relationships = []
        
        for row in rows:
            table_name = row["TABLE_NAME"] # pyright: ignore[reportArgumentType, reportCallIssue]
            column_name = row["COLUMN_NAME"] # pyright: ignore[reportArgumentType, reportCallIssue]
            referenced_table = row["REFERENCED_TABLE_NAME"] # pyright: ignore[reportArgumentType, reportCallIssue]
            referenced_column = row["REFERENCED_COLUMN_NAME"] # pyright: ignore[reportArgumentType, reportCallIssue]
            
            # Filter by table_names if provided
            if table_names is not None:
                if table_name not in table_names or referenced_table not in table_names:
                    continue
            
            relationship = (
                f"{table_name}.{column_name} → {referenced_table}.{referenced_column}"
            )
            relationships.append(relationship)

        unique_relationships = sorted(set(relationships))
        
        if table_names:
            self.logger.info("📊 Summary (filtered for tables: %s):", ", ".join(table_names))
        else:
            self.logger.info("📊 Summary (all relationships):")
        
        self.logger.info("  Foreign key relationships: %s", len(unique_relationships))
        return unique_relationships
    
    def list_databases(self) -> list[str]:
        cursor = self.connection.cursor()
        cursor.execute("SHOW DATABASES")
        rows = cursor.fetchall()
        cursor.close()
        return [row[0] for row in rows] # pyright: ignore[reportReturnType, reportArgumentType]
    
    def close_connection(self):
        if self.connection.is_connected():
            self.connection.close()
            self.logger.info("🔒 Database connection closed")
