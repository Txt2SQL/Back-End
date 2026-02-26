import os
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional
from config import MAX_OUTPUT_LENGTH


class LoggerManager:
    """
    Thread-safe centralized logging manager.

    Architecture:
    - Root logger → Project-wide log file (INFO level)
    - Per-thread/model loggers → Fully isolated DEBUG logs
    - Thread-local active logger automatically returned when present

    Guarantees:
    - Thread safety
    - Thread isolation
    - No handler mutation after creation
    - No global reconfiguration side effects
    """

    _configured: bool = False
    _project_log_file: Optional[str] = None

    # registry of created dedicated loggers
    _thread_loggers: dict[str, logging.Logger] = {}

    # thread-local storage
    _thread_local = threading.local()

    # synchronization
    _lock = threading.RLock()

    MAIN_LOG_LEVEL = logging.INFO
    THREAD_LOG_LEVEL = logging.DEBUG

    # ==========================================================
    # PROJECT LOGGER
    # ==========================================================

    @classmethod
    def _get_project_log_file(cls) -> str:
        if cls._project_log_file is None:

            current_dir = os.path.dirname(os.path.abspath(__file__))
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

        with cls._lock:

            if cls._configured:
                return logging.getLogger()

            env_level = os.getenv("LOG_LEVEL")
            if env_level:
                cls.MAIN_LOG_LEVEL = getattr(
                    logging,
                    env_level.upper(),
                    cls.MAIN_LOG_LEVEL
                )

            log_file = cls._get_project_log_file()

            root_logger = logging.getLogger()
            root_logger.setLevel(cls.MAIN_LOG_LEVEL)

            # clear once during initial setup ONLY
            root_logger.handlers.clear()

            file_handler = logging.FileHandler(
                log_file,
                encoding="utf-8"
            )

            file_handler.setLevel(cls.MAIN_LOG_LEVEL)

            formatter = logging.Formatter(
                "%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"
            )

            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

            # prevent propagation to default handlers
            root_logger.propagate = False

            cls._configured = True

            root_logger.info("=== Project logging started ===")
            root_logger.info(f"Log file: {log_file}")
            root_logger.info(
                f"Main log level: {logging.getLevelName(cls.MAIN_LOG_LEVEL)}"
            )
            root_logger.info(
                f"Thread log level: {logging.getLevelName(cls.THREAD_LOG_LEVEL)}"
            )

            return root_logger

    # ==========================================================
    # THREAD LOCAL LOGGER CONTROL
    # ==========================================================

    @classmethod
    def set_thread_logger(cls, logger: logging.Logger) -> None:
        """
        Assign active logger to current thread.
        Completely isolated from other threads.
        """
        cls._thread_local.active_logger = logger

    @classmethod
    def clear_thread_logger(cls) -> None:
        """
        Remove active logger from current thread.
        """
        if hasattr(cls._thread_local, "active_logger"):
            del cls._thread_local.active_logger

    @classmethod
    def _get_thread_logger(cls) -> Optional[logging.Logger]:
        """
        Internal: fetch thread-local logger safely.
        """
        return getattr(cls._thread_local, "active_logger", None)

    # ==========================================================
    # LOGGER ACCESS
    # ==========================================================

    @classmethod
    def get_logger(
        cls,
        name: str,
        log_file: Optional[Path] = None
    ) -> logging.Logger:
        """
        Get logger instance.

        Priority order:

        1. Thread-local active logger (if set)
        2. Dedicated logger (if log_file provided)
        3. Project logger child

        Guarantees:
        - Thread isolation
        - No handler mutation
        - Deterministic reuse
        """

        if not cls._configured:
            cls.setup_project_logger()

        # ======================================================
        # THREAD LOCAL LOGGER (HIGHEST PRIORITY)
        # ======================================================

        active_logger = cls._get_thread_logger()

        if active_logger is not None:
            return active_logger

        # ======================================================
        # PROJECT LOGGER CHILD
        # ======================================================

        if log_file is None:
            return logging.getLogger(name)

        # ======================================================
        # DEDICATED ISOLATED LOGGER
        # ======================================================

        log_file_str = str(log_file.resolve())

        logger_key = f"{name}|{log_file_str}"

        with cls._lock:

            existing = cls._thread_loggers.get(logger_key)

            if existing is not None:
                return existing

            # Create isolated logger
            logger = logging.getLogger(name)

            logger.setLevel(cls.THREAD_LOG_LEVEL)

            # critical: prevent propagation
            logger.propagate = False

            # ensure clean handler state (only once at creation)
            logger.handlers.clear()

            fh = logging.FileHandler(
                log_file_str,
                encoding="utf-8"
            )

            fh.setLevel(cls.THREAD_LOG_LEVEL)

            formatter = logging.Formatter(
                "%(asctime)s - "
                "[%(name)s:%(funcName)s:%(lineno)d] - "
                "%(levelname)s - %(message)s"
            )

            fh.setFormatter(formatter)

            logger.addHandler(fh)

            cls._thread_loggers[logger_key] = logger

            logging.getLogger().info(
                f"Created model logger '{name}' → {log_file_str}"
            )

            return logger

    # ==========================================================
    # DYNAMIC LEVEL CONTROL
    # ==========================================================

    @classmethod
    def set_main_log_level(cls, level: int) -> None:

        with cls._lock:

            cls.MAIN_LOG_LEVEL = level

            root_logger = logging.getLogger()
            root_logger.setLevel(level)

            for handler in root_logger.handlers:
                handler.setLevel(level)

            root_logger.info(
                f"Main log level changed to: "
                f"{logging.getLevelName(level)}"
            )

    @classmethod
    def set_thread_log_level(cls, level: int) -> None:

        with cls._lock:

            cls.THREAD_LOG_LEVEL = level

            for logger in cls._thread_loggers.values():

                logger.setLevel(level)

                for handler in logger.handlers:
                    handler.setLevel(level)

            logging.getLogger().info(
                f"Thread log level changed to: "
                f"{logging.getLevelName(level)}"
            )

    # ==========================================================
    # UTILITIES
    # ==========================================================

    @staticmethod
    def truncate_request(
        request: str,
        max_length: int = MAX_OUTPUT_LENGTH
    ) -> str:

        if len(request) <= max_length:
            return request

        return request[:max_length] + "..."