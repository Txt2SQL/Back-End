import socket
import requests
from urllib.parse import urlparse
from pathlib import Path
from .exceptions import ConnectionTestError
from loaders.base_loader import Loader




class OWUILoader(Loader):

    def __init__(self, env_dir: Path):
        values = {
            "SERVER_ADDRESS": str,
            "API_KEY": str,
        }

        super().__init__(env_dir / ".openwebui.env", values)

    def _test_connection(self):
        server_url = self.config["SERVER_ADDRESS"]

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