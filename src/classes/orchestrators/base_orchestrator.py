from datetime import datetime
from abc import ABC, abstractmethod
from typing import Optional, Any
from src.config import QUERY_GENERATION_MODELS

from classes.llm_clients import BaseLLM, OpenWebUILLM, AzureLLM
from classes.prompt_builder import PromptBuilder
from src.logging_utils import setup_logger, truncate_request

logger = setup_logger(__name__)


class BaseOrchestrator(ABC):
    """Abstract base class for all orchestrators"""
    
    def __init__(self, database_name: str, model_name: str = "default"):
        self.database_name = database_name
        self.model_name = model_name
        self.llm: Optional[BaseLLM] = self._initialize_llm(model_name)
        self.prompt_builder = PromptBuilder()
        
    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Main execution method to be implemented by subclasses"""
        pass
    
    def _initialize_llm(self, choice: str) -> BaseLLM:
        """Initialize the appropriate LLM based on model name pattern"""
        logger.info("Getting LLM model for choice: %s", choice)
        if choice is None:
            logger.info("Selected 'none' model (no LLM)")
            return None
        elif QUERY_GENERATION_MODELS[choice]["provider"] == "azure":
            model_name = QUERY_GENERATION_MODELS[choice]["id"]
            logger.info("Selected Azure OpenAI model: %s", model_name)
            return AzureLLM(model_name)
        else:
            model_name = QUERY_GENERATION_MODELS[choice]["id"]
            logger.info("Selected OpenWebUI model: %s", model_name)
            return OpenWebUILLM(model_name)