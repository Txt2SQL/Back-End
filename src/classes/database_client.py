from getpass import getpass

import mysql.connector
from src.classes.query import QuerySession
from collections import defaultdict
from mysql.connector.pooling import PooledMySQLConnection
from mysql.connector.abstracts import MySQLConnectionAbstract
from src.logging_utils import setup_logger
from src.classes.loaders.mysql_loader import MySQLLoader
from pathlib import Path

logger = setup_logger(__name__)

class DatabaseClient:
    database: str | None = None
    connection: PooledMySQLConnection | MySQLConnectionAbstract
    
    def __post_init__(self):
        self.config = MySQLLoader().config
        
        self.set_connection()
    
    def set_connection(self):
        try:
            logger.info("🔌 Establishing database connection with config: %s", {k: v for k, v in self.config.items() if k != "password"})
            connection_params = {
                "host": self.config["host"],
                "port": int(self.config["port"]),
                "user": self.config["user"],
                "password": self.config["password"],
            }
            
            if self.database is not None:
                logger.debug(f"📂 Setting database to: {self.database}")
                connection_params["database"] = self.database
                
            self.connection = mysql.connector.connect(**connection_params)
            logger.debug("✅ Database connection established successfully")
        except mysql.connector.Error as err:
            logger.error(f"Error connecting to the database: {err}")
            raise
    
    def execute_query(self, query: QuerySession) -> QuerySession:
        logger.info(f"📌 Received SQL query:\n{query}")

        try:
            logger.info("🔌 Connecting to MySQL database...")
            self.set_connection()

            if self.connection.is_connected():
                logger.info("✅ Connection established")
            else:
                logger.error("❌ Connection failed (self.connection.is_connected() returned False)")
                raise ConnectionError("Failed to establish a connection to the database")

            # Execute the query

            cursor = self.connection.cursor(dictionary=True)
            logger.info("📝 Executing SQL query...")

            if query.current_query is None:
                logger.warning("No SQL query provided to execute")
                raise ValueError("SQL query is None, cannot execute")
            cursor.execute(query.current_query)
            logger.info("📝 Query executed successfully")

            # Try fetching results (SELECT queries)
            try:
                logger.info("📥 Attempting to fetch results...")
                query.execution_result = cursor.fetchall()
                logger.info(f"📥 Rows fetched: {len(query.execution_result)}") # pyright: ignore[reportArgumentType]
            except Exception as fetch_err:
                logger.info(f"ℹ️ No fetchable results (likely non-SELECT query): {fetch_err}")
                query.execution_result = None
                raise fetch_err

            # Commit the transaction

            query.execution_status = "SUCCESS"
            logger.info("💾 Committing transaction...")
            self.connection.commit()

            cursor.close()
            self.connection.close()
            logger.info("🔒 Connection closed")

        except Exception as e:
            logger.error(f"🔥 RUNTIME ERROR during SQL execution: {e}")
            query.execution_status = "RUNTIME_ERROR"
            query.execution_result = str(e)
        
        return query
    
    def extract_schema(self) -> dict:
        if self.database is None:
            raise ValueError("Database name must be provided or set in DB_NAME environment variable")
        
        logger.info(f"📚 Extracting schema for database: {self.database}")
        
        
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

        if query.execution_status != "SUCCESS":
            logger.error(f"Failed to extract schema: {query.execution_result}")
            raise RuntimeError(f"Schema extraction failed: {query.execution_result}")
        if not query.execution_result:
            logger.warning("No columns found in the database schema")
            raise RuntimeError("Schema extraction returned no results")
        rows = query.execution_result
        tables = defaultdict(list)

        for row in rows:
            table_name = row["TABLE_NAME"] # pyright: ignore[reportArgumentType, reportCallIssue]
            column_name = row["COLUMN_NAME"] # pyright: ignore[reportArgumentType, reportCallIssue]
            data_type = row["DATA_TYPE"] # pyright: ignore[reportArgumentType, reportCallIssue]
            is_nullable = row["IS_NULLABLE"] # pyright: ignore[reportArgumentType, reportCallIssue]
            column_key = row["COLUMN_KEY"] # pyright: ignore[reportArgumentType, reportCallIssue]
            extra = row["EXTRA"] or "" # pyright: ignore[reportArgumentType, reportCallIssue]
            
            logger.debug(f"➡️ Processing column: {table_name}.{column_name}")
            
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

        logger.info("🧱 Building schema structure...")
        for table_name, columns in tables.items():
            logger.info(f"📦 Adding table: {table_name} ({len(columns)} columns)")
            schema["tables"].append({
                "name": table_name,
                "columns": columns
            })

        logger.info("🏁 Schema extraction completed")

        return schema
    
    def get_foreign_keys(self) -> list[str]:
        """
        Fetch join relationships directly from MySQL foreign key metadata.
        Returns human-readable join hints.
        """
        logger.info("🔍 Fetching relationship metadata from MySQL...")
        if not self.database:
            logger.warning("⚠️  DB_NAME is not set; cannot load foreign keys from MySQL")
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

        logger.debug("Executing foreign key query for database: %s", self.database)
        query = self.execute_query(QuerySession(sql_query=fk_query))
        
        if query.execution_status != "OK":
            logger.warning("⚠️  Failed to query foreign key metadata: %s", query.execution_result)
            return []

        rows = query.execution_result
        if not rows:
            logger.info("📭 No foreign key relationships found in MySQL metadata")
            return []

        logger.info("Found %s foreign key relationship(s)", len(rows))
        relationships = []
        for table_name, column_name, referenced_table, referenced_column in rows:
            relationship = (
                f"{table_name}.{column_name} → {referenced_table}.{referenced_column}"
            )
            relationships.append(relationship)

        unique_relationships = sorted(set(relationships))
        logger.info("📊 Summary:")
        logger.info("  Foreign key relationships: %s", len(unique_relationships))
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
            logger.info("🔒 Database connection closed")