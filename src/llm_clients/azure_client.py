from openai import AzureOpenAI
from src.config import load_azure_config
from .base import BaseLLM


class AzureLLM(BaseLLM):
    def __init__(self, model: str):
        cfg = load_azure_config()
        
        self.client = AzureOpenAI(
            api_key=cfg["api_key"],
            azure_endpoint=cfg["endpoint"], # pyright: ignore[reportArgumentType]
            api_version=cfg["api_version"],
        )
        self.model = model

    def generate(self, prompt: str, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content