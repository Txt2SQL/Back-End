import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from abc import ABC, abstractmethod
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

class VectorStore(ABC):
    embedding_function: OllamaEmbeddings
    collection_name: str
    persist_directory: str
    _store: Chroma
    
    def __init__(self, collection_name: str):
        self.embedding_function = OllamaEmbeddings(model="mxbai-embed-large")
        self.collection_name = collection_name
        self.persist_directory = f"data/vector_stores/{collection_name}" 
        self._store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_function,
            persist_directory=self.persist_directory
        )
    
    def empty_collection(self):
        self._store.delete_collection()
    
    @abstractmethod
    def print_collection(self):
        pass