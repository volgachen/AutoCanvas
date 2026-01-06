"""
Abstract Base Class for Database Implementations
Defines the interface that all database backends must implement
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseDatabase(ABC):
    """
    Abstract base class for database implementations.
    All database backends must implement these methods.
    """

    # ==================== Session Operations ====================

    @abstractmethod
    def create_session(self, session_id: Optional[str] = None, status: str = "active") -> dict:
        """Create a new session"""
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session by ID"""
        pass

    @abstractmethod
    def update_session_status(self, session_id: str, status: str) -> Optional[dict]:
        """Update session status"""
        pass

    @abstractmethod
    def list_sessions(self, status: Optional[str] = None) -> list[dict]:
        """List all sessions, optionally filtered by status"""
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages"""
        pass

    # ==================== Message Operations ====================

    @abstractmethod
    def create_message(
        self,
        session_id: str,
        content: str,
        role: str = "user",
        metadata: Optional[dict] = None
    ) -> Optional[dict]:
        """Create a new message"""
        pass

    @abstractmethod
    def get_message(self, message_id: str) -> Optional[dict]:
        """Get message by ID"""
        pass

    @abstractmethod
    def get_session_messages(
        self,
        session_id: str,
        role: Optional[str] = None,
        start_from=None,
    ) -> list[dict]:
        """Get all messages for a session"""
        pass

    @abstractmethod
    def update_message(
        self,
        message_id: str,
        content: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Optional[dict]:
        """Update message content and/or metadata"""
        pass

    @abstractmethod
    def delete_message(self, message_id: str) -> bool:
        """Delete a message"""
        pass

    # ==================== File Version Operations ====================

    @abstractmethod
    def create_file_version(
        self,
        session_id: str,
        file_id: str,
        content: str,
        editor: str,
        version_id: Optional[int] = None
    ) -> Optional[dict]:
        """Create a new file version entry"""
        pass

    @abstractmethod
    def get_file_version(self, file_version_id: str) -> Optional[dict]:
        """Get a file version by ID"""
        pass

    @abstractmethod
    def get_file_versions(
        self,
        session_id: Optional[str] = None,
        file_id: Optional[str] = None,
        editor: Optional[str] = None,
        start_from=None,
    ) -> list[dict]:
        """Get file versions with optional filters"""
        pass

    @abstractmethod
    def get_latest_file_version(
        self,
        session_id: str,
        file_id: str
    ) -> Optional[dict]:
        """Get the latest version of a file in a session"""
        pass

    @abstractmethod
    def delete_file_version(self, file_version_id: str) -> bool:
        """Delete a file version"""
        pass

    # ==================== LLM Call Operations ====================

    @abstractmethod
    def create_llm_call(
        self,
        model_name: str,
        messages: list,
        response: Optional[str] = None,
        error: Optional[str] = None,
        duration_ms: Optional[int] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """Create a new LLM call record"""
        pass

    @abstractmethod
    def get_llm_call(self, call_id: str) -> Optional[dict]:
        """Get LLM call by ID"""
        pass

    @abstractmethod
    def get_llm_calls(
        self,
        session_id: Optional[str] = None,
        model_name: Optional[str] = None,
        agent_name: Optional[str] = None,
        start_from=None,
        limit: Optional[int] = None
    ) -> list[dict]:
        """Get LLM calls with optional filters"""
        pass

    @abstractmethod
    def update_llm_call(
        self,
        call_id: str,
        response: Optional[str] = None,
        error: Optional[str] = None,
        duration_ms: Optional[int] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None
    ) -> Optional[dict]:
        """Update LLM call with response data"""
        pass

    # ==================== Utility Operations ====================

    @abstractmethod
    def clear_all(self):
        """Clear all data"""
        pass

    @abstractmethod
    def get_stats(self) -> dict:
        """Get database statistics"""
        pass
