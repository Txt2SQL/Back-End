from abc import ABC
from typing import Optional
from pathlib import Path

from src.classes.clients import BaseLLM
from src.classes.prompt_builder import PromptBuilder


class BaseOrchestrator(ABC):
    """Abstract base class for all orchestrators"""
    
    def __init__(self, database_name: str, instance_path: Path, llm: Optional[BaseLLM] = None):
        self.database_name = database_name
        self.instance_path = instance_path
        self.llm = llm
        self.prompt_builder = PromptBuilder()