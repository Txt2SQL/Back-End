import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from abc import ABC, abstractmethod
from pathlib import Path
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

class VectorStore(ABC):
    embedding_function: OllamaEmbeddings
    collection_name: str
    persist_directory: str
    _store: Chroma
    
    def __init__(self, path: Path, collection_name: str):
        self.embedding_function = OllamaEmbeddings(model="mxbai-embed-large")
        self.collection_name = collection_name
        persist_path = path / "vector_stores" / collection_name
        persist_path.mkdir(parents=True, exist_ok=True)
        self.persist_directory = str(persist_path)
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