"""
Logging utilities for the application
"""

import logging
import sys
from typing import Optional


class LoggerManager:
    """Singleton logger manager"""

    _instance: Optional['LoggerManager'] = None
    _loggers: dict[str, logging.Logger] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_logger(self, name: str, level: str = "INFO") -> logging.Logger:
        """Get or create a logger with the given name"""
        if name in self._loggers:
            return self._loggers[name]

        logger = logging.getLogger(name)

        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(getattr(logging, level.upper(), logging.INFO))
            logger.propagate = False

        self._loggers[name] = logger
        return logger


# Global logger manager instance
logger_manager = LoggerManager()


def setup_logging(level: str = "INFO"):
    """
    Setup application-wide logging configuration

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=getattr(logging, level.upper(), logging.INFO),
        stream=sys.stdout,
        force=True
    )

    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
