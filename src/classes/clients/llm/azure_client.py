from src.classes.loaders.azure_loader import AzureLoader
from openai import AzureOpenAI
from .base_llm import BaseLLM
from config import TIMEOUT_PER_REQUEST


class AzureLLM(BaseLLM):
    def __init__(self, model: str):
        super().__init__()
        self.loader = AzureLoader()
        cfg = self.loader.config

        self.client = AzureOpenAI(
            api_key=cfg["AZURE_API_KEY"],
            azure_endpoint=cfg["AZURE_ENDPOINT"],  # pyright: ignore[reportArgumentType]
            api_version=cfg["AZURE_API_VERSION"],
            timeout=self.timeout,
        )
        self.model = model

    def generate(self, prompt: str, **kwargs) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            self.response = response.choices[0].message.content
            return self._extract_llm_text()
        except TimeoutError as e:
            raise TimeoutError("LLM request timed out")