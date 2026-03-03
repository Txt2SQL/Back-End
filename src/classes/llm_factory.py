from typing import Dict, Any, Union
from src.classes.clients import AzureLLM, OpenWebUILLM
from src.classes.clients.base_llm import BaseLLM

class LLMFactory:
    """
    Factory to dynamically instantiate LLM clients based on provider configuration.
    """
    
    @staticmethod
    def create(model_config: dict[str, str]) -> "BaseLLM":
        """
        Instantiates an LLM based on the model_key found in the config_dict.
        """
        model_key = model_config["id"]
        provider = model_config.get("provider", "").lower()

        if provider == "azure":
            # AzureLLM only needs the model ID from the config
            return AzureLLM(model=model_config["id"])

        elif provider == "openwebui":
            # OpenWebUILLM takes the whole sub-dictionary for its config
            return OpenWebUILLM(model_config=model_config)

        else:
            raise ValueError(f"Unsupported provider '{provider}' for model '{model_key}'")

    # Optional: Allow calling LLMFactory(config_dict, key) directly
    def __new__(cls, model_config: dict[str, str]) -> "BaseLLM":
        return cls.create(model_config)