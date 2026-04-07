
from abc import ABC, abstractmethod
from src.classes.domain_states.query import QuerySession



class BaseClient(ABC):
    
    @abstractmethod
    def open_connection(self):
        pass
    
    @abstractmethod
    def close_connection(self):
        pass
    
    @abstractmethod
    def execute_query(self, query: QuerySession) -> QuerySession:
        pass
    
    @abstractmethod
    def get_foreign_keys(self, table_names: list[str] | None = None) -> list[str]:
        pass