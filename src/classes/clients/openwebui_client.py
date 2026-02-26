import requests
from .base_llm import BaseLLM
from src.classes.loaders.owui_loader import OWUILoader
from config import TIMEOUT_PER_REQUEST


class OpenWebUILLM(BaseLLM):
    def __init__(self, model: str):
        super().__init__()
        self.loader = OWUILoader()
        cfg = self.loader.config

        self.url = cfg["SERVER_ADDRESS"]
        self.api_key = cfg["API_KEY"]
        self.model = model

    def generate(self, prompt: str, **kwargs) -> str:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                **kwargs
            }

            # ADDED: pass timeout to requests.post
            response = requests.post(
                f"{self.url}/api/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            self.response = data["choices"][0]["message"]["content"]
            return self._extract_llm_text()
        except requests.exceptions.Timeout as e:
            raise TimeoutError("LLM request timed out")