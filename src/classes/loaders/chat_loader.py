from src.classes.loaders.base_owui_loader import BaseOWUILoader

class ChatLoader(BaseOWUILoader):
    """
    Loader for OpenWebUI Chat API configuration.
    """
    def __init__(self):
        values = {
            "CHAT_ADDRESS": str,
            "CHAT_API_KEY": str
        }
        super().__init__(values)
    
    def set_default_names(self):
        return {
            "api_base": self.config["CHAT_ADDRESS"],
            "api_key": self.config["CHAT_API_KEY"]
        }