from abc import ABC, abstractmethod

class BaseLLM(ABC):
    response: str
    
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
        return str(self.response).strip()