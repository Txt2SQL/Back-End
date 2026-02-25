import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from abc import ABC, abstractmethod
from pathlib import Path
from dotenv import dotenv_values
from typing import Any, Type
from src.logging_utils import setup_logger
from src.config import ENV_DIR
from classes.loaders.exceptions import (
    MissingVariableError,
    UninitializedVariableError,
    InvalidTypeError,
)

logger = setup_logger(__name__)

class BaseLoader(ABC):
    """
    Abstract configuration loader.
    """

    values: dict[str, Type]
    config: dict[str, Any]
    env_path: Path

    def __init__(self, env_name: str, values: dict[str, Type]):
        self.env_path = ENV_DIR /  env_name
        self.values = values
        self.config = {}

        self._load_or_prompt()
        self._validate_mandatory_variables()
        self._validate_initialization()
        self._validate_types()
        self._test_connection()
    
    def _load_or_prompt(self):
        if not self.env_path.exists():
            print(f"\n⚙️  Configuration file not found at {self.env_path}\n")
            self._prompt_and_save()

        raw_config = dotenv_values(self.env_path)
        
        logger.info(f"📂 Loaded configuration from {self.env_path}"
                    f" with values: {raw_config}")
        self.config = dict(raw_config)

    def _prompt_and_save(self):
        print(f"\n⚙️  Creating configuration file at {self.env_path}\n")

        self.env_path.parent.mkdir(parents=True, exist_ok=True)

        data = {}

        for key, expected_type in self.values.items():
            value = input(f"{key}: ").strip()
            data[key] = value

        with open(self.env_path, "w", encoding="utf-8") as f:
            for k, v in data.items():
                f.write(f"{k}={v}\n")

    def _validate_mandatory_variables(self):
        missing = [k for k in self.values if k not in self.config]
        if missing:
            raise MissingVariableError(
                f"Missing mandatory variables: {missing}"
            )

    def _validate_initialization(self):
        uninitialized = [
            k for k, v in self.config.items()
            if v is None or v == ""
        ]

        if uninitialized:
            raise UninitializedVariableError(
                f"Uninitialized variables: {uninitialized}"
            )

    def _validate_types(self):
        for key, expected_type in self.values.items():
            raw_value = self.config[key]

            try:
                casted_value = expected_type(raw_value)
                self.config[key] = casted_value
            except Exception:
                raise InvalidTypeError(
                    f"Variable '{key}' must be {expected_type.__name__}"
                )

    @abstractmethod
    def _test_connection(self):
        """
        Each subclass must implement its own connection test.
        """
        pass