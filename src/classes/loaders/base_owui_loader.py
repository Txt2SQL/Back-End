import socket
import requests
from abc import abstractmethod
from urllib.parse import urlparse
from pathlib import Path
from typing import Type
from .exceptions import ConnectionTestError
from src.classes.loaders.base_loader import BaseLoader




class BaseOWUILoader(BaseLoader):

    def __init__(self, values: dict[str, Type]):
        super().__init__(".openwebui.env", values)
        
    def _test_connection(self):
        self.config = self.set_default_names()
        server_url = self.config["api_base"]

        # -------------------------------------------------
        # 1️⃣ DNS CHECK
        # -------------------------------------------------
        try:
            parsed = urlparse(server_url)
            hostname = parsed.hostname

            if not hostname:
                raise ConnectionTestError(
                    "Invalid SERVER_ADDRESS: cannot extract hostname."
                )

            socket.gethostbyname(hostname)

        except socket.gaierror:
            raise ConnectionTestError(
                f"DNS resolution failed for host '{server_url}'."
            )
        except Exception as e:
            raise ConnectionTestError(
                f"Unexpected DNS error: {e}"
            )

        # -------------------------------------------------
        # 2️⃣ HTTP CHECK
        # -------------------------------------------------
        try:
            response = requests.get(
                server_url,
                timeout=5
            )

            if response.status_code >= 400:
                raise ConnectionTestError(
                    f"HTTP check failed (status code {response.status_code})."
                )

        except requests.exceptions.RequestException as e:
            raise ConnectionTestError(
                f"HTTP connection error: {e}"
            )
    
    @abstractmethod
    def set_default_names(self) -> dict[str, str]:
        pass