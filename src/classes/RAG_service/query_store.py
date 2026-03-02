import time, math, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import List
from pathlib import Path
from langchain_core.documents import Document
from src.classes.RAG_service.base_vector_store import VectorStore
from src.classes.domain_states.query import QuerySession
from config import VECTOR_STORE_DIR
from src.classes.logger import LoggerManager

class QueryStore(VectorStore):

    def __init__(self, path: Path = VECTOR_STORE_DIR):
        self.half_life_days = 7
        super().__init__(path, "query_store")

    @property
    def logger(self):
        return LoggerManager.get_logger(__name__)

    # =====================================================
    # STORE QUERY
    # =====================================================

    def store_query(self, query: QuerySession):
        """
        Store a query in the vector DB if:
        - it does not already exist
        - it represents a failed attempt
        """

        if self._query_exists(query):
            return

        document = Document(
            page_content=query.to_content_block(),
            metadata=query.to_document_metadata(),
        )

        self._store.add_documents(
            documents=[document],
            ids=[self._build_query_id(query)],
        )

    # =====================================================
    # RETRIEVE FAILED QUERIES
    # =====================================================

    def retrieve_failed_queries(
        self,
        user_request: str,
        k: int = 3
    ) -> List[Document]:
        """
        Retrieves failed queries from the store, preferring recently-seen failures and
        diverse failure causes when possible.

        Parameters:
            user_request (str): The user's request.
            store (Chroma): The store to retrieve from.
            k (int): The number of failed queries to retrieve.
            half_life_days (int): The half-life of failures in days.

        Returns:
            list[Document]: A list of k failed queries.
        """
        self.logger.info(f"🔍 Retrieving failed queries for request: '{user_request}'")

        retrieval_pool = max(10, k * 6)

        syntax_errors = self._store.similarity_search(
            user_request,
            k=retrieval_pool,
            filter={
                "$and": [
                    {"status": "SYNTAX_ERROR"},
                    {"knowledge_scope": "SYNTAX"}
                ]
            } # pyright: ignore[reportArgumentType]
        )
        self.logger.info(f"ℹ️ Found {len(syntax_errors)} syntax error queries.")

        structural_errors = self._store.similarity_search(
            user_request,
            k=retrieval_pool,
            filter={
                "$and": [
                    {"status": {"$ne": "SUCCESS"}},
                    {"knowledge_scope": "STRUCTURAL"}
                ]
            } # pyright: ignore[reportArgumentType]
        )
        self.logger.info(f"ℹ️ Found {len(structural_errors)} structural error queries.")

        schema_specific_errors = self._store.similarity_search(
            user_request,
            k=retrieval_pool,
            filter={
                "$and": [
                    {"status": "RUNTIME_ERROR"},
                    {"knowledge_scope": "SCHEMA_SPECIFIC"}
                ]
            } # pyright: ignore[reportArgumentType]
        )
        self.logger.info(f"ℹ️ Found {len(schema_specific_errors)} schema-specific runtime errors.")

        candidates = syntax_errors + structural_errors + schema_specific_errors
        self.logger.info(f"ℹ️ Total failed query candidates before dedupe: {len(candidates)}")

        # Deduplicate by SQL metadata fallback to raw page content.
        unique_docs = []
        seen = set()
        for doc in candidates:
            metadata = doc.metadata or {}
            key = metadata.get("sql_query") or doc.page_content
            if key in seen:
                continue
            seen.add(key)
            unique_docs.append(doc)

        self.logger.info(f"ℹ️ Unique failed queries after dedupe: {len(unique_docs)}")

        # Prefer recently-seen failures.
        decayed = self._apply_time_decay(unique_docs)
        self.logger.info(f"⏳ Applied time decay with half-life {self.half_life_days} days.")

        # Keep diversity of failure causes when possible.
        selected = []
        used_error_types = set()
        for doc in decayed:
            error_type = (doc.metadata or {}).get("error_type")
            if error_type and error_type in used_error_types and len(decayed) > k:
                continue
            selected.append(doc)
            if error_type:
                used_error_types.add(error_type)
            if len(selected) == k:
                break

        # Fallback fill if diversity filtering was too restrictive.
        if len(selected) < k:
            selected_keys = {(d.metadata or {}).get("sql_query") or d.page_content for d in selected}
            for doc in decayed:
                key = (doc.metadata or {}).get("sql_query") or doc.page_content
                if key in selected_keys:
                    continue
                selected.append(doc)
                selected_keys.add(key)
                if len(selected) == k:
                    break

        self.logger.info(f"✅ Returning {len(selected)} failed queries (requested k={k}).")

        return selected

    # =====================================================
    # CHECK EXISTENCE
    # =====================================================

    def _query_exists(self, query: QuerySession) -> bool:
        """
        Check if same SQL query already stored.
        """

        data = self._store.get(include=["metadatas"])

        if not data or not data.get("metadatas"):
            self.logger.info("ℹ️ No metadata found in store.")
            return False

        for metadata in data["metadatas"]:
            if metadata.get("sql_query") == query.sql_code:
                self.logger.info("✅ Query already exists in store.")
                return True

        self.logger.info("❌ Query does not exist in store.")
        return False

    # =====================================================
    # TIME DECAY
    # =====================================================

    def _apply_time_decay(self, docs: List[Document]) -> List[Document]:
        """
        Re-rank documents based on:
        - similarity already applied by Chroma
        - recency boost
        """

        now = time.time()
        half_life_seconds = self.half_life_days * 86400

        scored_docs = []

        self.logger.info(f"Applying time decay to {len(docs)} documents with half-life of {self.half_life_days} days.")
        for doc in docs:
            timestamp = doc.metadata.get("timestamp", now)
            age = now - timestamp

            # exponential decay (half-life = 7 days)
            decay = math.exp(-age / half_life_seconds)

            # combine similarity score implicitly preserved by order
            scored_docs.append((decay, doc))

        # sort by decay descending
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        return [doc for _, doc in scored_docs]

    # =====================================================
    # BUILD QUERY ID
    # =====================================================

    def _build_query_id(self, query: QuerySession) -> str:
        base = f"{query.user_request}|{query.sql_code}|{query.timestamp}"
        return str(abs(hash(base)))
    
    def print_collection(self) -> str:
        """
        Returns a string of the 15 most recent documents stored in the query feedback vector store.
        Useful for debugging and inspection.
        """
        output = ["\n📦 QUERY FEEDBACK VECTOR STORE CONTENT (15 Most Recent)\n"]

        # Recupera TUTTI i documenti
        data = self._store.get()

        if not data or not data.get("documents"):
            return "\n⚠️ Query vector store is empty."

        # Crea lista di tuple (doc, metadata) e ordina per timestamp decrescente
        docs_with_metadata = list(zip(data["documents"], data["metadatas"])) # type: ignore
        docs_with_metadata.sort(
            key=lambda x: x[1].get("timestamp", 0),
            reverse=True
        )
        
        # Prendi solo i 15 più recenti
        recent_docs = docs_with_metadata[:15]

        for idx, (doc, metadata) in enumerate(recent_docs, start=1):
            output.append(f"--- Entry #{idx} ------------------------------")
            output.append(str(doc))
            output.append("\nMetadata:")
            for k, v in metadata.items():
                if k != "sql_query":
                    output.append(f"  {k}: {v}")
            output.append("---------------------------------------------\n")

        return "\n".join(output)
    
    def get_recent_queries(self, database_name, limit=10):
        if limit <= 0:
            return []

        metadata_keys = ("database_name", "database", "db_name")
        data = None

        # Try common metadata keys without scanning the whole collection first.
        for key in metadata_keys:
            candidate = self._store.get(
                where={key: database_name},
                include=["documents", "metadatas"],
            )
            if candidate and candidate.get("documents"):
                data = candidate
                break

        if not data or not data.get("documents"):
            return []

        docs_with_metadata = list(zip(data["documents"], data["metadatas"]))
        docs_with_metadata.sort(key=lambda x: x[1].get("timestamp", 0), reverse=True)

        return [
            Document(page_content=doc, metadata=metadata)
            for doc, metadata in docs_with_metadata[:limit]
        ]
