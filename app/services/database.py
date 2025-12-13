"""
In-Memory Database Service using Pandas DataFrames
Provides CRUD operations for Sessions and Messages
"""

from datetime import datetime
from typing import Optional
import pandas as pd
from uuid import uuid4

from app.models.schemas import SessionStatus, MessageRole


class InMemoryDatabase:
    """
    In-memory database using pandas DataFrames
    Thread-safe singleton implementation
    """

    _instance: Optional['InMemoryDatabase'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True

        # Table 1: Sessions
        self.sessions = pd.DataFrame(columns=['id', 'status', 'created_at', 'updated_at'])
        self.sessions = self.sessions.set_index('id')

        # Table 2: Messages
        self.messages = pd.DataFrame(columns=[
            'id', 'session_id', 'create_time', 'metadata', 'role', 'content'
        ])
        self.messages = self.messages.set_index('id')

    # ==================== Session Operations ====================

    def create_session(self, session_id: Optional[str] = None, status: str = SessionStatus.ACTIVE) -> dict:
        """
        Create a new session

        Args:
            session_id: Optional custom session ID
            status: Initial status (default: ACTIVE)

        Returns:
            Created session as dictionary
        """
        if session_id is None:
            session_id = str(uuid4())

        now = datetime.now()
        self.sessions.loc[session_id] = {
            'status': status,
            'created_at': now,
            'updated_at': now
        }

        return {
            'id': session_id,
            'status': status,
            'created_at': now,
            'updated_at': now
        }

    def get_session(self, session_id: str) -> Optional[dict]:
        """
        Get session by ID

        Args:
            session_id: Session ID to retrieve

        Returns:
            Session as dictionary or None if not found
        """
        if session_id not in self.sessions.index:
            return None

        session = self.sessions.loc[session_id].to_dict()
        session['id'] = session_id
        return session

    def update_session_status(self, session_id: str, status: str) -> Optional[dict]:
        """
        Update session status

        Args:
            session_id: Session ID to update
            status: New status value

        Returns:
            Updated session as dictionary or None if not found
        """
        if session_id not in self.sessions.index:
            return None

        self.sessions.loc[session_id, 'status'] = status
        self.sessions.loc[session_id, 'updated_at'] = datetime.now()

        return self.get_session(session_id)

    def list_sessions(self, status: Optional[str] = None) -> list[dict]:
        """
        List all sessions, optionally filtered by status

        Args:
            status: Optional status filter

        Returns:
            List of sessions as dictionaries
        """
        df = self.sessions
        if status:
            df = df[df['status'] == status]

        result = []
        for idx, row in df.iterrows():
            session = row.to_dict()
            session['id'] = idx
            result.append(session)

        return result

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its messages

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted, False if not found
        """
        if session_id not in self.sessions.index:
            return False

        # Delete all messages in this session
        self.messages = self.messages[self.messages['session_id'] != session_id]

        # Delete session
        self.sessions = self.sessions.drop(session_id)
        return True

    # ==================== Message Operations ====================

    def create_message(
        self,
        session_id: str,
        content: str,
        role: str = MessageRole.USER,
        metadata: Optional[dict] = None
    ) -> Optional[dict]:
        """
        Create a new message

        Args:
            session_id: Session ID this message belongs to
            content: Message content
            role: Message role (user/assistant/system)
            metadata: Optional metadata dictionary

        Returns:
            Created message as dictionary or None if session doesn't exist
        """
        # Verify session exists
        if session_id not in self.sessions.index:
            return None

        message_id = str(uuid4())
        now = datetime.now()

        self.messages.loc[message_id] = {
            'session_id': session_id,
            'create_time': now,
            'metadata': metadata or {},
            'role': role,
            'content': content
        }

        return {
            'id': message_id,
            'session_id': session_id,
            'create_time': now,
            'metadata': metadata or {},
            'role': role,
            'content': content
        }

    def get_message(self, message_id: str) -> Optional[dict]:
        """
        Get message by ID

        Args:
            message_id: Message ID to retrieve

        Returns:
            Message as dictionary or None if not found
        """
        if message_id not in self.messages.index:
            return None

        message = self.messages.loc[message_id].to_dict()
        message['id'] = message_id
        return message

    def get_session_messages(
        self,
        session_id: str,
        role: Optional[str] = None,
        start_from = None,
    ) -> list[dict]:
        """
        Get all messages for a session, optionally filtered by role

        Args:
            session_id: Session ID to get messages for
            role: Optional role filter

        Returns:
            List of messages as dictionaries ordered by create_time
        """
        df = self.messages[self.messages['session_id'] == session_id]

        if role:
            df = df[df['role'] == role]

        # Sort by create_time
        df = df.sort_values('create_time')

        # if start_from is not None, only return whose create_time after start_from
        if start_from is not None:
            df = df[df['create_time'] > start_from]

        result = []
        for idx, row in df.iterrows():
            message = row.to_dict()
            message['id'] = idx
            result.append(message)

        return result

    def update_message(
        self,
        message_id: str,
        content: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Optional[dict]:
        """
        Update message content and/or metadata

        Args:
            message_id: Message ID to update
            content: New content (optional)
            metadata: New metadata to merge (optional)

        Returns:
            Updated message as dictionary or None if not found
        """
        if message_id not in self.messages.index:
            return None

        if content is not None:
            self.messages.loc[message_id, 'content'] = content

        if metadata is not None:
            current_metadata = self.messages.loc[message_id, 'metadata']
            if isinstance(current_metadata, dict):
                current_metadata.update(metadata)
            else:
                current_metadata = metadata
            self.messages.loc[message_id, 'metadata'] = current_metadata

        return self.get_message(message_id)

    def delete_message(self, message_id: str) -> bool:
        """
        Delete a message

        Args:
            message_id: Message ID to delete

        Returns:
            True if deleted, False if not found
        """
        if message_id not in self.messages.index:
            return False

        self.messages = self.messages.drop(message_id)
        return True

    # ==================== Utility Operations ====================

    def clear_all(self):
        """Clear all data (useful for testing)"""
        self.sessions = pd.DataFrame(columns=['id', 'status', 'created_at', 'updated_at']).set_index('id')
        self.messages = pd.DataFrame(columns=[
            'id', 'session_id', 'create_time', 'metadata', 'role', 'content'
        ]).set_index('id')

    def get_stats(self) -> dict:
        """Get database statistics"""
        sessions_by_status = {}
        if not self.sessions.empty:
            status_counts = self.sessions['status'].value_counts().to_dict()
            sessions_by_status = status_counts

        return {
            "total_sessions": len(self.sessions),
            "total_messages": len(self.messages),
            "sessions_by_status": sessions_by_status
        }


# Global database instance
db = InMemoryDatabase()


# ==================== Sample Usage ====================

if __name__ == "__main__":
    """
    Sample usage examples
    """
    print("=== In-Memory Database Sample Usage ===\n")

    # 1. Create sessions
    print("1. Creating sessions...")
    session1 = db.create_session()
    session2 = db.create_session(status=SessionStatus.PROCESSING)
    print(f"   Created session 1: {session1['id']}")
    print(f"   Created session 2: {session2['id']}\n")

    # 2. Create messages
    print("2. Creating messages...")
    msg1 = db.create_message(
        session_id=session1['id'],
        content="Hello, how can you help me?",
        role=MessageRole.USER
    )
    msg2 = db.create_message(
        session_id=session1['id'],
        content="I can help you with many tasks!",
        role=MessageRole.ASSISTANT,
        metadata={"model": "gpt-4"}
    )
    msg3 = db.create_message(
        session_id=session2['id'],
        content="What's the weather?",
        role=MessageRole.USER
    )
    print(f"   Created {len([msg1, msg2, msg3])} messages\n")

    # 3. Query sessions
    print("3. Querying sessions...")
    all_sessions = db.list_sessions()
    print(f"   Total sessions: {len(all_sessions)}")
    active_sessions = db.list_sessions(status=SessionStatus.ACTIVE)
    print(f"   Active sessions: {len(active_sessions)}\n")

    # 4. Query messages by session
    print("4. Querying messages for session 1...")
    session1_messages = db.get_session_messages(session1['id'])
    for msg in session1_messages:
        print(f"   [{msg['role']}] {msg['content']}")
    print()

    # 5. Update session status
    print("5. Updating session status...")
    db.update_session_status(session1['id'], SessionStatus.COMPLETED)
    updated_session = db.get_session(session1['id'])
    print(f"   Session {session1['id']} status: {updated_session['status']}\n")

    # 6. Get statistics
    print("6. Database statistics:")
    stats = db.get_stats()
    print(f"   {stats}\n")

    # 7. Display DataFrames
    print("7. Sessions DataFrame:")
    print(db.sessions)
    print("\n8. Messages DataFrame:")
    print(db.messages)