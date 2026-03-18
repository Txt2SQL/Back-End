from typing import List
from pathlib import Path
from src.classes.RAG_service.base_vector_store import VectorStore
from langchain_core.documents import Document
from src.classes.domain_states.schema import Schema
from config import VECTOR_STORE_DIR
from src.classes.logger import LoggerManager

class SchemaStore(VectorStore):

    def __init__(self, path: Path = VECTOR_STORE_DIR):
        super().__init__(path, "schema_store")

    @property
    def logger(self):
        return LoggerManager.get_logger(__name__)

    # =====================================================
    # STORE SCHEMA
    # =====================================================

    def add_schema(self, schema: Schema):
        if not schema.json_ready:
            raise ValueError("Schema is not ready.")

        docs_data = schema.to_documents()

        if not docs_data:
            raise ValueError("Schema produced no documents.")
        
        self.empty_database_schema(schema.database_name)

        documents = [
            Document(
                page_content=doc_data["content"],
                metadata=doc_data["metadata"],
            )
            for doc_data in docs_data
        ]
        ids = [doc_data["id"] for doc_data in docs_data]
        
        self._store.add_documents(
            documents=documents,
            ids=ids,
        )

        self.logger.info(f"Stored {len(documents)} schema table documents in vector DB.")

    def empty_database_schema(self, database_name: str):
        """Delete all schema documents for a specific database."""
        existing_docs = self._store.get(where={"database_name": database_name}, include=[])
        ids = existing_docs.get("ids", [])

        if not ids:
            self.logger.info("No existing schema documents found for database '%s'.", database_name)
            return

        self._store.delete(ids=ids)
        self.logger.info("Deleted %s existing schema documents for database '%s'.", len(ids), database_name)

    # =====================================================
    # RETRIEVE CONTEXT
    # =====================================================

    def get_context(self, user_request: str) -> tuple[str, list[str]]:
        """
        Retrieve relevant schema fragments for the user request.
        Uses light query-intent heuristics to tune retrieval depth,
        removes duplicate chunks, and groups output by table.
        """
        self.logger.info("Retrieving schema context for request: '%s'", LoggerManager.truncate_request(user_request))

        # ------------------------------------------------------------------
        # SCHEMA RETRIEVAL (RAG)
        # ------------------------------------------------------------------

        request_lower = user_request.lower()
        request_tokens = set(request_lower.replace(",", " ").replace(".", " ").split())

        aggregate_terms = {
            "avg",
            "average",
            "count",
            "group",
            "having",
            "sum",
            "total",
            "min",
            "max",
        }
        join_terms = {"join", "across", "between", "related", "each"}

        has_aggregation = bool(request_tokens.intersection(aggregate_terms))
        
        join_indicators = {
            "per", "each", "for each",
            "with", "without",
            "have", "has", "had",
            "included", "not in", "never",
            "exists", "missing"
        }
        
        has_join_intent = (
            bool(request_tokens.intersection(join_terms | join_indicators))
            or " by " in f" {request_lower} "
        )
        # Start with a conservative context size and increase only when complexity suggests it.
        k = 3
        if has_aggregation:
            k += 2
            self.logger.debug("Request contains aggregation terms, increasing k to %s", k)
        if has_join_intent:
            k += 2
            self.logger.debug("Request contains join intent, increasing k to %s", k)
        
        self.logger.info("Retrieval parameters - has_aggregation: %s, has_join_intent: %s, k: %s", 
                    has_aggregation, has_join_intent, k)

        retriever = self._store.as_retriever(search_kwargs={"k": k})
        relevant_docs = retriever.invoke(user_request)
        self.logger.debug("Retrieved %s relevant documents", len(relevant_docs))

        seen_chunks = set()
        grouped_chunks = {}

        for doc in relevant_docs:
            table_name = (doc.metadata or {}).get("table") or "unknown_table"
            content = (doc.page_content or "").strip()
            self.logger.debug("Processing document for table '%s'", table_name)
            self.logger.debug("Content: \n%s", content) 
            

            if not content:
                self.logger.debug("Skipping empty document")
                continue

            dedup_key = (table_name, content)
            if dedup_key in seen_chunks:
                self.logger.debug("Duplicate chunk found for table '%s'", table_name)
                continue

            seen_chunks.add(dedup_key)
            grouped_chunks.setdefault(table_name, []).append(content)

        sections = []
        for table_name, chunks in grouped_chunks.items():
            sections.append(f"Table: {table_name}\n" + "\n".join(chunks[:2]))

        table_names = list(grouped_chunks.keys())
        schema_context = "\n\n".join(sections)

        self.logger.info(
            "Schema context retrieval complete: k=%s, docs=%s, unique_tables=%s, context_chars=%s",
            k,
            len(relevant_docs),
            len(grouped_chunks),
            len(schema_context),
        )

        if not schema_context:
            self.logger.warning("No schema context retrieved for request: %s", request_lower)

        return schema_context, table_names
    
    def print_collection(self) -> str:
        output = ["\n🔎 Current content of the vector store:"]
        all_docs = self._store.get(include=["metadatas", "documents"])

        if not all_docs or not all_docs.get("documents"):
            return "\n⚠️ Schema vector store is empty."

        for i, (doc_text, meta) in enumerate(zip(all_docs["documents"], all_docs["metadatas"])):  # type: ignore
            output.append(f"\n🧱 Document #{i+1}")
            output.append(f"📘 Table: {meta.get('table', 'N/A')}")
            output.append("📄 Content:")
            output.append(str(doc_text))
            output.append("-" * 50)
            
            if not doc_text:
                output.append(f"⚠️ Document #{i+1} is empty.")

        return "\n".join(output)