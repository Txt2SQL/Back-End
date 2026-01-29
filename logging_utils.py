import os
import logging
from datetime import datetime

from langchain_chroma import Chroma

# Global variable to track if the single log file has been configured
_single_log_file_configured = False
_PROJECT_LOG_FILE = None

def get_project_root():
    """Get the absolute path to the project root directory."""
    # Assuming this file is in the project root
    return os.path.dirname(os.path.abspath(__file__))

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
    root_logger.setLevel(logging.INFO)

    # REMOVE ALL existing handlers
    root_logger.handlers.clear()

    # ADD FILE HANDLER ONLY
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)

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
    logger.setLevel(logging.INFO)
    
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

logger = setup_logger(__name__)

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
    logger.info("\n" + "=" * 80)
    logger.info("📋 FINAL PROMPT SENT TO LLM")
    logger.info("=" * 80)
    logger.info(prompt_text)
    logger.info("=" * 80 + "\n")
    
def print_schema_preview(schema: dict):
    """Prints a readable preview of the canonical schema"""
    logger.info("\n" + "=" * 60)
    logger.info("Canonical schema preview:")
    logger.info("=" * 60)
    
    # Print tables
    if "tables" in schema and schema["tables"]:
        logger.info(f"\nFound {len(schema['tables'])} tables:")
        for i, table in enumerate(schema["tables"], 1):
            logger.info(f"\n  Table #{i}: {table.get('name', 'N/A')}")
            
            # Print columns
            if "columns" in table and table["columns"]:
                logger.info("  Columns:")
                for col in table["columns"]:
                    constraints = col.get("constraints", [])
                    constraints_str = ", ".join(constraints) if constraints else "no constraints"
                    logger.info(f"    • {col.get('name', 'N/A')} ({col.get('type', 'N/A')}) - {constraints_str}")
            else:
                logger.error("  No columns defined")
    else:
        logger.error("\nNo tables defined")
    
    # Print semantic notes
    if "semantic_notes" in schema and schema["semantic_notes"]:
        logger.info(f"\nFound {len(schema['semantic_notes'])} semantic notes:")
        for i, note in enumerate(schema["semantic_notes"], 1):
            # Show only first 100 characters for brevity
            preview = note[:100] + "..." if len(note) > 100 else note
            logger.info(f"  {i}. {preview}")
    else:
        logger.error("\nNo semantic notes")
    
    logger.info("=" * 60)
    
def print_schema_context(schema_context: str):
    """Prints the schema context in a readable format."""
    logger.info("\n====================  SCHEMA CONTEXT ====================")
    if schema_context.strip():
        logger.info(schema_context)
    else:
        logger.error("(No schema context found — retriever returned empty results)")
    logger.info("===========================================================\n")

def print_vector_store(vector_store: Chroma):
    logger.info("\n🔎 Current content of the vector store:")
    all_docs = vector_store.get(include=["metadatas", "documents"])

    for i, (doc_text, meta) in enumerate(zip(all_docs["documents"], all_docs["metadatas"])):  # type: ignore
        logger.info(f"\n🧱 Document #{i+1}")
        logger.info("📘 Table:", meta.get("table", "N/A"))
        logger.info("📄 Content:")
        logger.info(doc_text)
        logger.info("-" * 50)
        
        if not doc_text:
            logger.error(f"⚠️ Document #{i+1} is empty.")