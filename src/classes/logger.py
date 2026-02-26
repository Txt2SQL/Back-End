import os
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from config import MAX_OUTPUT_LENGTH

# Thread-local storage for log context
_thread_local = threading.local()
# Global lock for logger dictionary operations
_logger_dict_lock = threading.RLock()

class ThreadLogContext:
    """Context manager to set thread-specific log file for all loggers"""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.old_handlers = {}
        self.temp_loggers = set()
        self.modified_loggers = set()
    
    def __enter__(self):
        with _logger_dict_lock:
            # Make a copy of logger keys to avoid modification during iteration
            logger_names = list(logging.root.manager.loggerDict.keys())
            
            for logger_name in logger_names:
                logger = logging.getLogger(logger_name)
                # Skip root logger and thread loggers
                if logger != logging.getLogger() and not logger_name.startswith('thread_'):
                    # Store original handlers
                    self.old_handlers[logger_name] = logger.handlers.copy()
                    
                    # Clear existing handlers
                    logger.handlers.clear()
                    
                    # Add file handler for this thread
                    fh = logging.FileHandler(self.log_file, encoding='utf-8')
                    fh.setLevel(logging.DEBUG)
                    formatter = logging.Formatter('%(asctime)s - [%(name)s] - %(message)s')
                    fh.setFormatter(formatter)
                    logger.addHandler(fh)
                    logger.propagate = False
                    self.modified_loggers.add(logger_name)
            
            # Set thread-local variable
            _thread_local.log_file = self.log_file
            return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        with _logger_dict_lock:
            # Restore original handlers for modified loggers
            for logger_name in self.modified_loggers:
                if logger_name in logging.root.manager.loggerDict:
                    logger = logging.getLogger(logger_name)
                    if logger_name in self.old_handlers:
                        logger.handlers = self.old_handlers[logger_name]
                        logger.propagate = True
            
            # Clean up thread-local
            if hasattr(_thread_local, 'log_file'):
                delattr(_thread_local, 'log_file')


class LoggerManager:
    """
    Centralized logging manager with thread-aware logging.
    """

    _configured: bool = False
    _project_log_file: Optional[str] = None
    _thread_loggers: dict = {}  # Store thread-specific loggers
    _thread_loggers_lock = threading.RLock()  # Lock for thread loggers dict

    # Different log levels for different purposes
    MAIN_LOG_LEVEL = logging.INFO  # Main project log - INFO level
    THREAD_LOG_LEVEL = logging.DEBUG  # Thread-specific logs - DEBUG level

    # --------------------------------------------------
    # CONFIGURATION
    # --------------------------------------------------

    @classmethod
    def set_level(cls, level: int, logger_type: str = "main") -> None:
        """
        Change logging level dynamically.
        
        Args:
            level: Logging level (e.g., logging.INFO, logging.DEBUG)
            logger_type: "main" for main project log, "thread" for thread logs
        """
        if logger_type == "main":
            cls.MAIN_LOG_LEVEL = level
        else:
            cls.THREAD_LOG_LEVEL = level

        if cls._configured:
            if logger_type == "main":
                root = logging.getLogger()
                root.setLevel(level)
                for handler in root.handlers:
                    handler.setLevel(level)
            else:
                # Update all thread loggers with lock
                with cls._thread_loggers_lock:
                    for logger in cls._thread_loggers.values():
                        logger.setLevel(level)
                        for handler in logger.handlers:
                            handler.setLevel(level)

    @classmethod
    def _get_project_log_file(cls) -> str:
        if cls._project_log_file is None:
            # Get the directory where this file is located (src/classes/)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Go up two levels to get to project root
            project_root = os.path.dirname(os.path.dirname(current_dir))
            
            logs_dir = os.path.join(project_root, "logs")
            os.makedirs(logs_dir, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            cls._project_log_file = os.path.join(
                logs_dir,
                f"project_{timestamp}.log"
            )

        return cls._project_log_file

    @classmethod
    def setup_project_logger(cls) -> logging.Logger:
        if cls._configured:
            return logging.getLogger()

        # Optional: allow env override
        env_level = os.getenv("LOG_LEVEL")
        if env_level:
            cls.MAIN_LOG_LEVEL = getattr(logging, env_level.upper(), cls.MAIN_LOG_LEVEL)

        log_file = cls._get_project_log_file()

        root_logger = logging.getLogger()
        root_logger.setLevel(cls.MAIN_LOG_LEVEL)
        root_logger.handlers.clear()

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(cls.MAIN_LOG_LEVEL)

        formatter = logging.Formatter(
            '%(asctime)s - [%(name)s:%(funcName)s:%(lineno)d] - '
            '%(levelname)s - %(message)s'
        )

        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        root_logger.propagate = False

        cls._configured = True

        root_logger.info("=== Project logging started ===")
        root_logger.info(f"Log file: {log_file}")
        root_logger.info(f"Main log level: {logging.getLevelName(cls.MAIN_LOG_LEVEL)}")
        root_logger.info(f"Thread log level: {logging.getLevelName(cls.THREAD_LOG_LEVEL)}")

        return root_logger

    @classmethod
    def get_logger(cls, name: str, log_file: Optional[Path] = None) -> logging.Logger:
        """
        Get a logger. If in a thread context with log_file, use thread's log file.
        
        Args:
            name: Logger name
            log_file: If provided, creates a thread-specific logger
        
        Returns:
            logging.Logger: Configured logger instance
        """
        if not cls._configured:
            cls.setup_project_logger()

        # Check if we're in a thread with a log file context
        if hasattr(_thread_local, 'log_file') and not log_file:
            log_file = _thread_local.log_file

        if log_file:
            # Create a unique key for this logger
            logger_key = f"{name}_{log_file}"
            
            with cls._thread_loggers_lock:
                if logger_key not in cls._thread_loggers:
                    logger = logging.getLogger(f"thread_{name}")
                    logger.setLevel(cls.THREAD_LOG_LEVEL)
                    logger.handlers.clear()
                    logger.propagate = False
                    
                    # Create file handler for this specific log file
                    fh = logging.FileHandler(log_file, encoding='utf-8')
                    fh.setLevel(cls.THREAD_LOG_LEVEL)
                    
                    # Include logger name in thread logs for better traceability
                    formatter = logging.Formatter('%(asctime)s - [%(name)s] - %(message)s')
                    fh.setFormatter(formatter)
                    logger.addHandler(fh)
                    
                    cls._thread_loggers[logger_key] = logger
                    
                    # Log the creation with the main logger
                    main_logger = logging.getLogger("main")
                    main_logger.info(f"Created thread logger for {name} at {log_file}")
                
                return cls._thread_loggers[logger_key]
        else:
            # Return project logger
            return logging.getLogger(name)

    @classmethod
    def set_thread_log_level(cls, level: int) -> None:
        """Set the log level for all thread loggers."""
        cls.THREAD_LOG_LEVEL = level
        with cls._thread_loggers_lock:
            for logger in cls._thread_loggers.values():
                logger.setLevel(level)
                for handler in logger.handlers:
                    handler.setLevel(level)
        
        main_logger = logging.getLogger("main")
        main_logger.info(f"Thread log level changed to: {logging.getLevelName(level)}")

    @classmethod
    def set_main_log_level(cls, level: int) -> None:
        """Set the log level for the main project logger."""
        cls.MAIN_LOG_LEVEL = level
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        for handler in root_logger.handlers:
            handler.setLevel(level)
        
        root_logger.info(f"Main log level changed to: {logging.getLevelName(level)}")

    @staticmethod
    def truncate_request(request: str,
                         max_length: int = MAX_OUTPUT_LENGTH) -> str:
        if len(request) <= max_length:
            return request
        return request[:max_length] + "..."