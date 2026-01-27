from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_chroma import Chroma

MODEL_NAME = "gemma3:12b"
llm = OllamaLLM(model=MODEL_NAME)
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

def get_vector_store(collection_name: str, persist_dir: str):
    return Chroma(collection_name=collection_name, persist_directory=persist_dir, embedding_function=embeddings)
