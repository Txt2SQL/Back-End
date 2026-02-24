from typing import Optional
from abc import ABC
from classes.domain_states.schema import Schema
from src.logging_utils import setup_logger

logger = setup_logger(__name__)


class SchemaOrchestrator(ABC):
    """
    Handles full schema generation lifecycle:
    - Extract raw schema
    - Ask LLM to normalize it
    - Validate and persist
    - Store inside SchemaStore
    """

    def __init__(
        self,
        llm_service,
        database_client,
        schema_store,
        prompt_builder,
    ):
        self.llm = llm_service
        self.database_client = database_client
        self.schema_store = schema_store
        self.prompt_builder = prompt_builder

    def run(
        self,
        database_name: str,
        schema_source: str = "mysql",
        raw_text_schema: Optional[str] = None,
    ) -> Schema:
        """
        Main execution method.
        """

        # 1️⃣ Create Schema object
        schema = Schema(database_name=database_name, schema_source=schema_source)

        # If already parsed and saved, reuse
        if schema.json_ready:
            return schema

        # 2️⃣ Extract raw schema
        if schema_source == "mysql":
            raw_schema = self.database_client.extract_schema()
        elif schema_source == "text":
            if not raw_text_schema:
                raise ValueError("raw_text_schema required when schema_source='text'")
            raw_schema = raw_text_schema
        else:
            raise ValueError("Invalid schema_source")

        # 3️⃣ Build LLM prompt
        prompt = self.prompt_builder.build_schema_prompt(raw_schema)

        # 4️⃣ Call LLM
        llm_response = self.llm.generate(prompt)

        # 5️⃣ Parse response
        schema.parse_llm_response(llm_response)

        # 6️⃣ Save schema
        schema._save_schema()

        # 7️⃣ Store in vector store
        self.schema_store.add_schema(schema)

        return schema