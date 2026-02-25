import time, math, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import List
from langchain_core.documents import Document
from classes.RAG_service.base_vector_store import VectorStore
from classes.domain_states.query import QuerySession
from src.logging_utils import setup_logger

logger = setup_logger(__name__)


class QueryStore(VectorStore):

    def __init__(self, collection_name: str = "queries"):
        self.half_life_days = 7
        super().__init__(collection_name=collection_name)

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
        logger.info(f"🔍 Retrieving failed queries for request: '{user_request}'")

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
        logger.info(f"ℹ️ Found {len(syntax_errors)} syntax error queries.")

        structural_errors = self._store.similarity_search(
            user_request,
            k=retrieval_pool,
            filter={
                "$and": [
                    {"status": {"$ne": "OK"}},
                    {"knowledge_scope": "STRUCTURAL"}
                ]
            } # pyright: ignore[reportArgumentType]
        )
        logger.info(f"ℹ️ Found {len(structural_errors)} structural error queries.")

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
        logger.info(f"ℹ️ Found {len(schema_specific_errors)} schema-specific runtime errors.")

        candidates = syntax_errors + structural_errors + schema_specific_errors
        logger.info(f"ℹ️ Total failed query candidates before dedupe: {len(candidates)}")

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

        logger.info(f"ℹ️ Unique failed queries after dedupe: {len(unique_docs)}")

        # Prefer recently-seen failures.
        decayed = self._apply_time_decay(unique_docs)
        logger.info(f"⏳ Applied time decay with half-life {self.half_life_days} days.")

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

        logger.info(f"✅ Returning {len(selected)} failed queries (requested k={k}).")

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
            logger.info("ℹ️ No metadata found in store.")
            return False

        for metadata in data["metadatas"]:
            if metadata.get("sql_query") == query.sql_code:
                logger.info("✅ Query already exists in store.")
                return True

        logger.info("❌ Query does not exist in store.")
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

        logger.info(f"Applying time decay to {len(docs)} documents with half-life of {self.half_life_days} days.")
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
    
    def print_collection(self):
        """
        Prints the 15 most recent documents stored in the query feedback vector store.
        Useful for debugging and inspection.
        """
        print("\n📦 QUERY FEEDBACK VECTOR STORE CONTENT (15 Most Recent)\n")

        # Recupera TUTTI i documenti
        data = self._store.get()

        if not data or not data.get("documents"):
            print("\n⚠️ Query vector store is empty.")
            return

        # Crea lista di tuple (doc, metadata) e ordina per timestamp decrescente
        docs_with_metadata = list(zip(data["documents"], data["metadatas"]))
        docs_with_metadata.sort(
            key=lambda x: x[1].get("timestamp", 0),
            reverse=True
        )
        
        # Prendi solo i 15 più recenti
        docs_with_metadata = docs_with_metadata[:15]

        for idx, (doc, metadata) in enumerate(docs_with_metadata, start=1):
            print(f"--- Entry #{idx} ------------------------------")
            print(doc)
            print("\nMetadata:")
            for k, v in metadata.items():
                if k != "sql_query":
                    print(f"  {k}: {v}")
            print("---------------------------------------------\n")