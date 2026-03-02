from src.classes.loaders.base_owui_loader import BaseOWUILoader

class CompLoader(BaseOWUILoader):
    def __init__(self):
        values = {
            "COMP_ADDRESS": str,
            "COMP_API_KEY": str
        }
        super().__init__(values)
    
    def set_default_names(self):
        return {
            "api_base": self.config["COMP_ADDRESS"],
            "api_key": self.config["COMP_API_KEY"]
        }