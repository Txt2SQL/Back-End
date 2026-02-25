import mysql.connector

from src.classes.loaders.base_loader import BaseLoader
from src.classes.loaders.exceptions import ConnectionTestError
from pathlib import Path




class MySQLLoader(BaseLoader):

    def __init__(self):
        values = {
            "DB_HOST": str,
            "DB_PORT": int,
            "DB_USER": str,
            "DB_PASSWORD": str,
        }

        super().__init__(".mysql.env", values)

    def _test_connection(self):
        try:
            conn = mysql.connector.connect(
                host=self.config["DB_HOST"],
                port=self.config["DB_PORT"],
                user=self.config["DB_USER"],
                password=self.config["DB_PASSWORD"],
            )

            if not conn.is_connected():
                raise ConnectionTestError("MySQL connection failed.")

            conn.close()

        except Exception as e:
            raise ConnectionTestError(f"MySQL connection error: {e}")