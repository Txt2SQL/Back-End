from datetime import datetime
from abc import ABC, abstractmethod
from typing import Optional, Any
from pathlib import Path

from src.classes.clients import BaseLLM, OpenWebUILLM, AzureLLM
from src.classes.prompt_builder import PromptBuilder


class BaseOrchestrator(ABC):
    """Abstract base class for all orchestrators"""
    
    def __init__(self, database_name: str, instance_path: Path, model_name: str):
        self.database_name = database_name
        self.instance_path = instance_path
        self.model_name = model_name
        self.llm: BaseLLM = self._initialize_llm(model_name)
        self.prompt_builder = PromptBuilder()
    
    @abstractmethod
    def _initialize_llm(self, choice: str) -> BaseLLM:
        pass