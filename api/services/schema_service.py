import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

from src.classes.orchestrators.schema_orchestrator import SchemaOrchestrator
from src.classes.domain_states.schema import Schema
from src.classes.RAG_service.schema_store import SchemaStore
from src.classes.domain_states.enums import SchemaSource
from src.classes.logger import LoggerManager
from api.models.responses import SchemaResponse
from config import SCHEMA_MODELS

logger = LoggerManager.get_logger(__name__)


class SchemaService:
    """Service layer for schema operations"""
    
    def __init__(
        self,
        database_name: str,
        schema_store: SchemaStore,
        data_dir: Path
    ):
        self.database_name = database_name
        self.schema_store = schema_store
        self.data_dir = data_dir
    
    async def acquire_schema(
        self,
        source: SchemaSource,
        user_text: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> SchemaResponse:
        """
        Acquire schema from source
        """
        logger.info(f"Acquiring schema for {self.database_name} from {source}")
        
        loop = asyncio.get_event_loop()
        
        # Select model
        model = model_name or list(SCHEMA_MODELS.keys())[0]
        
        # Create orchestrator
        orchestrator = SchemaOrchestrator(
            database_name=self.database_name,
            llm_model=model,
            source=source,
            instance_path=self.data_dir
        )
        
        # Run acquisition
        schema: Schema = await loop.run_in_executor(
            None,
            orchestrator.acquire_schema,
            user_text
        )
        
        # Convert to response
        return self._schema_to_response(schema)
    
    async def update_schema(
        self,
        update_text: str,
        model_name: Optional[str] = None
    ) -> SchemaResponse:
        """
        Update existing schema
        """
        logger.info(f"Updating schema for {self.database_name}")
        
        loop = asyncio.get_event_loop()
        
        # Get existing schema
        existing_schema = Schema.from_json_file(self.data_dir / "schema" / f"{self.database_name}.json")
        if not existing_schema:
            raise ValueError(f"No existing schema found for {self.database_name}")
        
        # Select model
        model = model_name or list(SCHEMA_MODELS.keys())[0]
        
        # Create orchestrator
        orchestrator = SchemaOrchestrator(
            database_name=self.database_name,
            llm_model=model,
            source=existing_schema.source,
            instance_path=self.data_dir
        )
        orchestrator.schema = existing_schema
        
        # Run update
        updated_schema: Schema = await loop.run_in_executor(
            None,
            orchestrator.,
            update_text
        )
        
        return self._schema_to_response(updated_schema)
    
    def _schema_to_response(self, schema: Schema) -> SchemaResponse:
        """Convert Schema object to response model"""
        if not schema.tables:
            return SchemaResponse(
                database_name=schema.database_name,
                source=schema.source.value if hasattr(schema.source, 'value') else str(schema.source),
                tables=[],
                semantic_notes=[],
                table_count=0
            )
        
        tables = schema.tables.get("tables", []) if isinstance(schema.tables, dict) else []
        semantic_notes = schema.tables.get("semantic_notes", []) if isinstance(schema.tables, dict) else schema.semantic_notes
        
        return SchemaResponse(
            database_name=schema.database_name,
            source=schema.source.value if hasattr(schema.source, 'value') else str(schema.source),
            tables=tables,
            semantic_notes=semantic_notes,
            schema_id=schema.schema_id,
            table_count=len(tables)
        )