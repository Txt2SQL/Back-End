import requests
from pathlib import Path
from .exceptions import ConnectionTestError
from loaders.base_loader import Loader


class AzureLoader(Loader):

    def __init__(self):
        values = {
            "AZURE_API_KEY": str,
            "AZURE_ENDPOINT": str,
            "AZURE_API_VERSION": str,
        }

        super().__init__(".azure.env", values)

    def _test_connection(self):
        try:
            response = requests.get(
                self.config["AZURE_ENDPOINT"],
                headers={"api-key": self.config["AZURE_API_KEY"]},
                timeout=5
            )

            if response.status_code >= 400:
                raise ConnectionTestError("Azure connection failed.")

        except Exception as e:
            raise ConnectionTestError(f"Azure connection error: {e}")