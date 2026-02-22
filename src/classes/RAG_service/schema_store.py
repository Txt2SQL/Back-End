from typing import List
from src.classes.RAG_service.vector_store import VectorStore
from src.classes.schema import Schema
from langchain_core.documents import Document

class SchemaStore(VectorStore):

    def __init__(self):
        super().__init__("schema_store")

    # =====================================================
    # STORE SCHEMA
    # =====================================================

    def add_schema(self, schema: Schema):
        if not schema.json_ready:
            raise ValueError("Schema is not ready.")

        doc_data = schema.to_document()

        document = Document(
            page_content=doc_data["content"],
            metadata=doc_data["metadata"],
        )

        self._store.add_documents(
            documents=[document],
            ids=[doc_data["id"]],
        )

        print(f"Schema {doc_data['id']} stored in vector DB.")

    # =====================================================
    # RETRIEVE CONTEXT
    # =====================================================

    def get_context(self, user_query: str, k: int = 3) -> str:
        results = self._store.similarity_search(
            user_query,
            k=k,
        )

        if not results:
            return ""

        context = "\n\n".join([doc.page_content for doc in results])
        return context