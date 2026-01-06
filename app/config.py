"""
Application Configuration
Loads settings from environment variables
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Config(BaseSettings):
    """Application configuration"""

    # App metadata
    app_title: str = "AI Canvas Backend"
    app_description: str = "Backend API for AI Canvas application"

    # Server config
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # SSL/TLS Configuration
    ssl_enabled: bool = False
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None

    # CORS
    allowed_origins: list[str] = ["*"]

    # WebSocket
    ws_heartbeat_interval: int = 30
    ws_heartbeat_timeout: int = 60

    # Session
    session_timeout: int = 3600

    # Logging
    log_level: str = "INFO"

    # Database
    database_type: str = "sqlite"  # Options: memory, pandas, sqlite
    database_path: str = "data/app.db"  # SQLite database file path

    class Config:
        env_file = ".env"
        case_sensitive = False
        env_file_encoding = 'utf-8'


# Global config instance
config = Config()
