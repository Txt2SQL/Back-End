import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.config import MAX_OUTPUT_LENGTH


class LoggerManager:
    """
    Centralized logging manager.
    """

    _configured: bool = False
    _project_log_file: Optional[str] = None

    # ✅ SINGLE PLACE TO CONTROL DEFAULT LEVEL
    LOG_LEVEL = logging.DEBUG

    # --------------------------------------------------
    # CONFIGURATION
    # --------------------------------------------------

    @classmethod
    def set_level(cls, level: int) -> None:
        """
        Change global logging level dynamically.
        Example:
            LoggerManager.set_level(logging.INFO)
        """
        cls.LOG_LEVEL = level

        if cls._configured:
            root = logging.getLogger()
            root.setLevel(level)
            for handler in root.handlers:
                handler.setLevel(level)

    @classmethod
    def _get_project_log_file(cls) -> str:
        if cls._project_log_file is None:
            project_root = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
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

        # ✅ Optional: allow env override
        env_level = os.getenv("LOG_LEVEL")
        if env_level:
            cls.LOG_LEVEL = getattr(logging, env_level.upper(), cls.LOG_LEVEL)

        log_file = cls._get_project_log_file()

        root_logger = logging.getLogger()
        root_logger.setLevel(cls.LOG_LEVEL)
        root_logger.handlers.clear()

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(cls.LOG_LEVEL)

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
        root_logger.info(f"Log level: {logging.getLevelName(cls.LOG_LEVEL)}")

        return root_logger

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        if not cls._configured:
            cls.setup_project_logger()

        logger = logging.getLogger(name)
        logger.setLevel(cls.LOG_LEVEL)
        logger.propagate = True

        return logger

    @staticmethod
    def truncate_request(request: str,
                         max_length: int = MAX_OUTPUT_LENGTH) -> str:
        if len(request) <= max_length:
            return request
        return request[:max_length] + "..."