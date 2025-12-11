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

    # CORS
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:5174"]

    # WebSocket
    ws_heartbeat_interval: int = 30
    ws_heartbeat_timeout: int = 60

    # Session
    session_timeout: int = 3600

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False
        env_file_encoding = 'utf-8'


# Global config instance
config = Config()
