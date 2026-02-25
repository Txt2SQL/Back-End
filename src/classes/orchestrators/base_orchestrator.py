from datetime import datetime
from abc import ABC, abstractmethod
from typing import Optional, Any

from classes.llm_clients import BaseLLM, OpenWebUILLM, AzureLLM
from classes.prompt_builder import PromptBuilder
from src.logging_utils import setup_logger, truncate_request

logger = setup_logger(__name__)


class BaseOrchestrator(ABC):
    """Abstract base class for all orchestrators"""
    
    def __init__(self, database_name: str, model_name: Optional[str] = None):
        self.database_name = database_name
        self.model_name = model_name
        self.llm: Optional[BaseLLM] = self._initialize_llm(model_name)
        self.prompt_builder = PromptBuilder()
    
    @abstractmethod
    def _initialize_llm(self, choice: str | None) -> BaseLLM | None:
        pass