import os
import logging
from datetime import datetime
from pathlib import Path
from src.config import MAX_OUTPUT_LENGTH, LOGINFO_SEPARATOR
from langchain_chroma import Chroma

# Global variable to track if the single log file has been configured
_single_log_file_configured = False
_PROJECT_LOG_FILE = None

def get_project_root():
    """Get the absolute path to the project root directory."""
    # Assuming this file is in the project root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_project_log_file():
    """Get or create the single project log file path."""
    global _PROJECT_LOG_FILE
    
    if _PROJECT_LOG_FILE is None:
        project_root = get_project_root()
        logs_dir = os.path.join(project_root, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        _PROJECT_LOG_FILE = os.path.join(logs_dir, f"project_{timestamp}.log")
    
    return _PROJECT_LOG_FILE

def setup_single_project_logger():
    """
    Setup a single logger for the entire project that ONLY writes to file.
    Call this once at the start of your main script.
    
    Returns:
        The root logger instance
    """
    global _single_log_file_configured

    if _single_log_file_configured:
        return logging.getLogger()

    log_file = get_project_log_file()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # REMOVE ALL existing handlers
    root_logger.handlers.clear()

    # ADD FILE HANDLER ONLY
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)

    root_logger.propagate = False

    _single_log_file_configured = True

    root_logger.info("=== Project logging started ===")
    root_logger.info(f"Log file: {log_file}")

    return root_logger

def setup_logger(name: str) -> logging.Logger:
    """
    Setup a logger that inherits from the single project logger.
    Use this in each module. NEVER logs to console.
    
    Args:
        name: Name of the logger (usually __name__)
    
    Returns:
        Configured logger instance that ONLY writes to file
    """
    # Ensure the single project logger is set up
    if not _single_log_file_configured:
        setup_single_project_logger()
    
    # Create logger with the module name
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Ensure this logger doesn't add any console handlers
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.StreamHandler):
            logger.removeHandler(handler)
    
    # Propagate to root logger (which has the file handler)
    logger.propagate = True
    
    return logger

def get_project_logger() -> logging.Logger:
    """
    Get the main project logger.
    Use this for high-level application logging.
    """
    if not _single_log_file_configured:
        setup_single_project_logger()
    
    return logging.getLogger("project")

def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module (convenience function)."""
    return setup_logger(name)

def add_request_log_handler(log_file: Path) -> logging.FileHandler:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - [%(name)s:%(funcName)s:%(lineno)d] - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
    return handler


def remove_request_log_handler(handler: logging.FileHandler) -> None:
    root_logger = logging.getLogger()
    root_logger.removeHandler(handler)
    handler.close()

logger = setup_logger(__name__)

def truncate_request(request: str, max_length: int = MAX_OUTPUT_LENGTH) -> str:
    """Truncate long requests for cleaner output."""
    logger.debug("Truncating request. Original length: %s, Max length: %s", len(request), max_length)
    if len(request) <= max_length:
        return request
    truncated = request[:max_length] + "..."
    logger.debug("Request truncated to: %s", truncated)
    return truncated

def print_query_vector_store(store: Chroma):
    """
    Prints the 15 most recent documents stored in the query feedback vector store.
    Useful for debugging and inspection.
    """
    print("\n📦 QUERY FEEDBACK VECTOR STORE CONTENT (15 Most Recent)\n")

    # Recupera TUTTI i documenti
    data = store.get()

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

def print_llm_prompt(prompt_text: str) -> None:
    """
    Logs the final prompt that will be sent to the LLM.
    Useful for debugging and understanding what context the model receives.
    """
    logger.info(LOGINFO_SEPARATOR + "\n\n")
    logger.info("📋 FINAL PROMPT SENT TO LLM\n\n")
    logger.info(LOGINFO_SEPARATOR + "\n")
    logger.info(prompt_text + "\n")
    logger.info(LOGINFO_SEPARATOR)
    
def print_schema_context(schema_context: str):
    """Prints the schema context in a readable format."""
    logger.info("====================  SCHEMA CONTEXT ====================")
    if schema_context.strip():
        logger.info(schema_context)
    else:
        logger.error("(No schema context found — retriever returned empty results)")
    logger.info("===========================================================\n")

def print_vector_store(vector_store: Chroma):
    print("\n🔎 Current content of the vector store:")
    all_docs = vector_store.get(include=["metadatas", "documents"])

    for i, (doc_text, meta) in enumerate(zip(all_docs["documents"], all_docs["metadatas"])):  # type: ignore
        print(f"\n🧱 Document #{i+1}")
        print("📘 Table:%s", meta.get("table", "N/A"))
        print("📄 Content:")
        print(doc_text)
        print("-" * 50)
        
        if not doc_text:
            print(f"⚠️ Document #{i+1} is empty.")