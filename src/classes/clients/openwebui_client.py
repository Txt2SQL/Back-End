import requests
from requests import Response
from .base_llm import BaseLLM
from src.classes.loaders import ChatLoader, CompLoader
from src.classes.logger import LoggerManager

class OpenWebUILLM(BaseLLM):
    def __init__(self, model_config: dict):
        super().__init__()

        self.api_type = model_config["api_type"]
        
        if self.api_type == "completion":
            self.loader = CompLoader()
        elif self.api_type == "chat":
            self.loader = ChatLoader()

        cfg = self.loader.config
        
        self.model = model_config["id"]
        self.url = cfg["api_base"]
        self.api_key = cfg["api_key"]
        self.endpoint = model_config["api_endpoint"]
        
    @property
    def logger(self):
        return LoggerManager.get_logger(__name__)
        
    def generate(self, prompt: str, **kwargs) -> str:
        self.logger.info(f"Generating response from url: {self.url}{self.endpoint} and model: {self.model}...")
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                f"{self.url}{self.endpoint}",
                headers=headers,
                json=self._dynamic_payload(prompt, **kwargs),
                timeout=self.timeout
            )
            
            self.logger.info(f"Response status code: {response.status_code}")
            self.logger.info(f"Response content: {response.text}")

            self.response = self._dynamic_response(response)
            return self._extract_llm_text()

        except requests.exceptions.Timeout:
            raise TimeoutError("LLM request timed out")
        
    def _dynamic_payload(self, prompt: str, **kwargs) -> dict:
        if self.api_type == "completion":
            return {
                "model": self.model,
                "prompt": prompt,
                **kwargs
            }

        elif self.api_type == "chat":
            return {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                **kwargs
            }

        else:
            raise ValueError(f"Unsupported api_type: {self.api_type}")
    
    def _dynamic_response(self, response: Response) -> str:
        data = response.json()
        if self.api_type == "completion":
            return data["choices"][0]["text"]
        elif self.api_type == "chat":
            return data["choices"][0]["message"]["content"]
        else:
            raise ValueError(f"Unsupported api_type: {self.api_type}")