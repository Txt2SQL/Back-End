import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from src.classes.orchestrators.query_orchestrator import QueryOrchestrator
from src.classes.domain_states import QuerySession, Schema, Records
from src.classes.RAG_service import SchemaStore, QueryStore
from src.classes.logger import LoggerManager
from src.classes.domain_states.enums import SchemaSource
from api.models.responses import QueryResponse
from config import QUERY_GENERATION_MODELS

logger = LoggerManager.get_logger(__name__)


class QueryService:
    """Service layer for query operations"""
    
    def __init__(
        self,
        database_name: str,
        schema_store: SchemaStore,
        query_store: Optional[QueryStore],
        data_dir: Path
    ):
        self.database_name = database_name
        self.schema_store = schema_store
        self.query_store = query_store
        self.data_dir = data_dir
    
    async def generate_query(
        self,
        user_request: str,
        model_name: Optional[str] = None,
        max_attempts: int = 4,
        testing: bool = False
    ) -> QueryResponse:
        """
        Generate SQL query from natural language
        """
        logger.info(f"Generating query for request: {user_request[:50]}...")
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        
        # Get schema
        schema = await self._get_schema()
        if not schema:
            raise ValueError(f"Schema not found for database: {self.database_name}")
        
        # Select model
        model = model_name or list(QUERY_GENERATION_MODELS.keys())[0]
        
        # Create orchestrator
        orchestrator = QueryOrchestrator(
            schema=schema,
            schema_store=self.schema_store,
            model_name=model,
            user_request=user_request,
            query_store=self.query_store,
            max_attempts=max_attempts,
            instance_path=self.data_dir,
            testing=testing
        )
        
        # Run generation
        result: QuerySession = await loop.run_in_executor(
            None,
            orchestrator.generation,
            user_request
        )
        
        # Convert to response model
        return self._session_to_response(result)
    
    async def store_successful_query(self, query_response: QueryResponse):
        """
        Store successful query in background
        """
        if not self.query_store:
            logger.warning("Query store not available, skipping storage")
            return
        
        try:
            # Convert response back to session
            from src.classes.domain_states.enums import QueryStatus, ErrorType, KnowledgeScope
            
            session = QuerySession(
                user_request=query_response.user_request,
                sql_query=query_response.sql_code
            )
            session.status = QueryStatus(query_response.status)
            session.error_type = ErrorType(query_response.error_type) if query_response.error_type else None
            session.knowledge_scope = KnowledgeScope(query_response.knowledge_scope) if query_response.knowledge_scope else None
            
            self.query_store.store_query(session)
            logger.info("Successfully stored query in vector store")
        except Exception as e:
            logger.error(f"Failed to store query: {str(e)}")
    
    async def _get_schema(self) -> Optional[Schema]:
        """Get schema from store or create new one"""
        if not self.schema_store:
            return None
        
        # Try to get existing schema
        schema = Schema.from_json_file(self.data_dir / "schema" / f"{self.database_name}.json")
        
        if not schema:
            # Create minimal schema for MySQL source
            from src.classes.clients.mysql_client import MySQLClient
            
            try:
                client = MySQLClient(self.database_name)
                schema_data = client.extract_schema()
                
                schema = Schema(
                    database_name=self.database_name,
                    schema_source=SchemaSource.MYSQL,
                    path=self.data_dir / "schema"
                )
                schema.parse_response(schema_data)
            except Exception as e:
                logger.error(f"Failed to extract schema from MySQL: {str(e)}")
                return None
        
        return schema
    
    def _session_to_response(self, session: QuerySession) -> QueryResponse:
        """Convert QuerySession to response model"""
        execution_result = None
        rows_fetched = None
        
        if session.execution_result:
            if isinstance(session.execution_result, Records):
                execution_result = session.execution_result.to_dict()
                rows_fetched = len(session.execution_result) if session.execution_result else 0
            else:
                execution_result = str(session.execution_result)
        
        return QueryResponse(
            user_request=session.user_request,
            sql_code=session.sql_code,
            status=session.status.value if session.status else "UNKNOWN",
            error_type=session.error_type.value if session.error_type else None,
            knowledge_scope=session.knowledge_scope.value if session.knowledge_scope else None,
            execution_result=execution_result,
            rows_fetched=rows_fetched,
            attempts=session.attempt,
            execution_time=None,  # You might want to track this
            feedback=session.llm_feedback.explanation if session.llm_feedback else None
        )