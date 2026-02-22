import sqlglot, time
from typing import Any, List, Optional, TypeVar, Union
from langchain_core.documents import Document
from src.logging_utils import setup_logger

logger = setup_logger(__name__)


class Query:

    def __init__(self, 
                 user_request: Optional[str] = None,
                 sql_query: Optional[str] = None,
                 attempt_count: int = 1):
        """
        Instantiate a Query object.
        
        Args:
            user_request: the original user request in natural language (if available)
            sql_query: the generated SQL query (if available)
            attempt_count: number of attempts made to generate/execute the query
        """
        # Validation: at least one of user_request or sql_query must be provided
        if user_request is None and sql_query is None:
            raise ValueError("At least one of user_request or sql_query must be provided")
        
        self.user_request = user_request or ""
        self.current_query = sql_query
        
        # state fields
        self.status: Optional[str] = "PENDING"
        self.valid_syntax: Optional[bool] = None
        self.execution_status: Optional[str] = None
        self.execution_result: Union[str, List[Any], None] = None
        self.llm_feedback: Optional[str] = None
        self.attempt_count: int = attempt_count
        self.knowledge_scope: Optional[str] = None
        self.error_type: Optional[str] = None
        self.error_message: Optional[str] = None
        self.timestamp: float = time.time()
        
        # if provided with an initial SQL query, validate its syntax immediately
        if sql_query is not None:
            self.validate_syntax()
    
    @classmethod
    def from_user_request(cls, user_request: str, attempt_count: int = 1) -> 'Query':
        """
        Factory method for creating a Query from a user request in natural language.
        
        Args:
            user_request: the original user request in natural language
            attempt_count: number of attempts
            
        Returns:
            Query: new instance of Query
        """
        return cls(user_request=user_request, attempt_count=attempt_count)
    
    @classmethod
    def from_sql_query(cls, sql_query: str, attempt_count: int = 1) -> 'Query':
        """
        Factory method for creating a Query from an existing SQL query.
        
        Args:
            sql_query: The SQL query
            attempt_count: number of attempts
            
        Returns:
            Query: new instance of Query with validated syntax
        """
        return cls(sql_query=sql_query, attempt_count=attempt_count)
    
    def validate_syntax(self):
        """
        Checks if SQL compiles syntactically.
        
        Returns:
            - True if it compiles
            - False if it fails
            - None if query is None
        """
        logger.debug("Validating SQL syntax for query: %s", self.current_query)
        try:
            # Parse only, no DB execution
            sqlglot.parse_one(self.current_query) # pyright: ignore[reportArgumentType]
            logger.debug("SQL syntax validation passed")
            self.valid_syntax = True
        except Exception as e:
            logger.error(f"Syntax validation failed: {e}")
            self.valid_syntax = False
    
    def evaluate_status(self):
        """
        Evaluates the overall status of the query based on syntax and execution results.
        Sets self.status to one of: "SUCCESS", "SYNTAX_ERROR", "EXECUTION_ERROR", "PENDING", or "UNKNOWN".
        """
        if self.valid_syntax is True and self.execution_status == "SUCCESS":
            self.status = "SUCCESS"
        elif self.valid_syntax is False:
            self.status = "SYNTAX_ERROR"
        elif self.valid_syntax is True and self.execution_status != "SUCCESS":
            self.status = "EXECUTION_ERROR"
        elif self.valid_syntax is None or self.execution_status is None:
            self.status = "PENDING"
        else:
            self.status = "UNKNOWN"

    def to_content_block(self) -> str:
        return f"""
User request:
{self.user_request}

Generated SQL query:
{self.current_query}

Outcome: {self.status}
""".strip()

    def to_document_metadata(self) -> Document:
        raw = {
            "user_request": self.user_request,
            "sql_query": self.current_query,
            "status": self.status,
            "valid_syntax": self.valid_syntax,
            "execution_status": self.execution_status,
            "attempt_count": self.attempt_count,
            "timestamp": self.timestamp
        }

        metadata = {}
        for k, v in raw.items():
            if isinstance(v, (str, int, float, bool)) or v is None:
                metadata[k] = v
            else:
                metadata[k] = str(v)  # ← last-resort safety
        
        page_content = self.to_content_block()
        return Document(page_content=page_content, metadata=metadata)
    