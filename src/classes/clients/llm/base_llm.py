from abc import ABC, abstractmethod
from src.classes.loaders.base_loader import BaseLoader
from config import TIMEOUT_PER_REQUEST

class BaseLLM(ABC):
    response: str
    loader: BaseLoader
    
    def __init__(self, timeout: int = TIMEOUT_PER_REQUEST):
        self.timeout = timeout
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        pass
    
    def _extract_llm_text(self) -> str:
        """
        Extracts text content from an LLM response.
        """
        if isinstance(self.response, str):
            return self.response.strip()
        if hasattr(self.response, "content"):
            return str(self.response.content).strip()
        if hasattr(self.response, "text"):
            return str(self.response.text).strip()
        return str(self.response).strip()