from datetime import datetime
from abc import ABC, abstractmethod
from typing import Optional, Any

from classes.llm_clients import BaseLLM, OpenWebUILLM, AzureLLM
from classes.prompt_builder import PromptBuilder
from src.logging_utils import setup_logger, truncate_request

logger = setup_logger(__name__)


class BaseOrchestrator(ABC):
    """Abstract base class for all orchestrators"""
    
    def __init__(self, database_name: str):
        self.database_name = database_name
        self.prompt_builder = PromptBuilder()
    
    @abstractmethod
    def initialize_llm(self, model_name: str | None) -> BaseLLM | None:
        pass