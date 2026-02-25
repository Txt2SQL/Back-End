import requests
from .base_llm import BaseLLM
from src.classes.loaders.owui_loader import OWUILoader


class OpenWebUILLM(BaseLLM):
    def __init__(self, model: str):
        self.loader = OWUILoader()
        cfg = self.loader.config
        
        self.url = cfg["base_url"]
        self.api_key = cfg["api_key"]
        self.model = model

    def generate(self, prompt: str, **kwargs) -> str:
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

        response = requests.post(f"{self.url}/api/chat/completions", headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()
        self.response = data["choices"][0]["message"]["content"]
        
        return self._extract_llm_text()