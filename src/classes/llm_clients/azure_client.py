from classes.loaders.azure_loader import AzureLoader
from openai import AzureOpenAI
from .base_llm import BaseLLM


class AzureLLM(BaseLLM):
    def __init__(self, model: str):
        self.loader = AzureLoader()
        cfg = self.loader.config
        
        self.client = AzureOpenAI(
            api_key=cfg["AZURE_API_KEY"],
            azure_endpoint=cfg["AZURE_ENDPOINT"], # pyright: ignore[reportArgumentType]
            api_version=cfg["AZURE_API_VERSION"],
        )
        self.model = model

    def generate(self, prompt: str, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        self.response = response.choices[0].message.content
        
        return self._extract_llm_text()