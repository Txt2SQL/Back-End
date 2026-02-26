from datetime import datetime
from abc import ABC, abstractmethod
from typing import Optional, Any
from pathlib import Path

from src.classes.clients import BaseLLM, OpenWebUILLM, AzureLLM
from src.classes.prompt_builder import PromptBuilder
from src.classes.logger import LoggerManager

logger = LoggerManager.get_logger(__name__)


class BaseOrchestrator(ABC):
    """Abstract base class for all orchestrators"""
    
    def __init__(self, database_name: str, instance_path: Path, model_name: Optional[str] = None):
        self.database_name = database_name
        self.instance_path = instance_path
        self.model_name = model_name
        self.llm: Optional[BaseLLM] = self._initialize_llm(model_name)
        self.prompt_builder = PromptBuilder()
    
    @abstractmethod
    def _initialize_llm(self, choice: str | None) -> BaseLLM | None:
        pass