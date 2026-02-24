from typing import List
from classes.RAG_service.base_vector_store import VectorStore
from langchain_core.documents import Document
from classes.domain_states.schema import Schema
from src.logging_utils import setup_logger, truncate_request

logger = setup_logger(__name__)

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

    def get_context(self, user_request: str) -> tuple[str, list[str]]:
        """
        Retrieve relevant schema fragments for the user request.
        Uses light query-intent heuristics to tune retrieval depth,
        removes duplicate chunks, and groups output by table.
        """
        logger.info("Retrieving schema context for request: '%s'", truncate_request(user_request))

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
        has_join_intent = bool(request_tokens.intersection(join_terms)) or " by " in f" {request_lower} "

        # Start with a conservative context size and increase only when complexity suggests it.
        k = 3
        if has_aggregation:
            k += 1
            logger.debug("Request contains aggregation terms, increasing k to %s", k)
        if has_join_intent:
            k += 1
            logger.debug("Request contains join intent, increasing k to %s", k)
        
        logger.info("Retrieval parameters - has_aggregation: %s, has_join_intent: %s, k: %s", 
                    has_aggregation, has_join_intent, k)

        retriever = self._store.as_retriever(search_kwargs={"k": k})
        relevant_docs = retriever.invoke(user_request)
        logger.debug("Retrieved %s relevant documents", len(relevant_docs))

        seen_chunks = set()
        grouped_chunks = {}

        for doc in relevant_docs:
            table_name = (doc.metadata or {}).get("table") or "unknown_table"
            content = (doc.page_content or "").strip()

            if not content:
                logger.debug("Skipping empty document")
                continue

            dedup_key = (table_name, content)
            if dedup_key in seen_chunks:
                logger.debug("Duplicate chunk found for table '%s'", table_name)
                continue

            seen_chunks.add(dedup_key)
            grouped_chunks.setdefault(table_name, []).append(content)

        sections = []
        for table_name, chunks in grouped_chunks.items():
            sections.append(f"Table: {table_name}\n" + "\n".join(chunks[:2]))

        table_names = list(grouped_chunks.keys())
        schema_context = "\n\n".join(sections)

        logger.info(
            "Schema context retrieval complete: k=%s, docs=%s, unique_tables=%s, context_chars=%s",
            k,
            len(relevant_docs),
            len(grouped_chunks),
            len(schema_context),
        )

        if not schema_context:
            logger.warning("No schema context retrieved for request: %s", truncate_request(user_request))

        return schema_context, table_names