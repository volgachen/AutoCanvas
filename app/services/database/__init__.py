"""
Database Factory
Selects the appropriate database implementation based on configuration
"""

from typing import Optional
from app.config import config
from .base import BaseDatabase


def get_database() -> BaseDatabase:
    """
    Factory function to get the configured database instance.

    Reads DATABASE_TYPE from environment/config:
    - "memory" or "pandas": In-memory pandas DataFrame storage (default)
    - "sqlite": SQLite persistent storage

    Returns:
        BaseDatabase: The configured database instance
    """
    db_type = getattr(config, 'database_type', 'memory').lower()

    if db_type in ('memory', 'pandas'):
        from .memory import MemoryDatabase
        return MemoryDatabase()

    elif db_type == 'sqlite':
        from .sqlite import SQLiteDatabase
        db_path = getattr(config, 'database_path', 'data/app.db')
        return SQLiteDatabase(db_path=db_path)

    else:
        raise ValueError(f"Unknown database type: {db_type}. Supported: memory, pandas, sqlite")


# Global database instance (singleton pattern)
_db_instance: Optional[BaseDatabase] = None


def get_db() -> BaseDatabase:
    """
    Get the global database instance (singleton).
    Creates the instance on first call based on configuration.
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = get_database()
    return _db_instance


# For backwards compatibility - create instance on import
db = get_db()


__all__ = ['BaseDatabase', 'get_database', 'get_db', 'db']
