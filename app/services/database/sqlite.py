"""
SQLite Database Implementation
Persistent storage using SQLite
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional
from uuid import uuid4
from pathlib import Path

from app.models.schemas import SessionStatus, MessageRole
from .base import BaseDatabase


class SQLiteDatabase(BaseDatabase):
    """
    SQLite database implementation for persistent storage
    """

    def __init__(self, db_path: str = "data/app.db"):
        self.db_path = db_path

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database tables"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        # Create messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                create_time TEXT NOT NULL,
                metadata TEXT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        ''')

        # Create file_versions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_versions (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                version_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                editor TEXT NOT NULL,
                create_time TEXT NOT NULL,
                file_id TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        ''')

        # Create llm_calls table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS llm_calls (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                agent_name TEXT,
                model_name TEXT NOT NULL,
                messages TEXT NOT NULL,
                response TEXT,
                error TEXT,
                duration_ms INTEGER,
                input_tokens INTEGER,
                output_tokens INTEGER,
                metadata TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        ''')

        # Create indexes for common queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_versions_session ON file_versions(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_versions_file ON file_versions(session_id, file_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_llm_calls_session ON llm_calls(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_llm_calls_model ON llm_calls(model_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_llm_calls_agent ON llm_calls(agent_name)')

        conn.commit()
        conn.close()

    def _datetime_to_str(self, dt: datetime) -> str:
        """Convert datetime to ISO format string"""
        return dt.isoformat()

    def _str_to_datetime(self, s: str) -> datetime:
        """Convert ISO format string to datetime"""
        return datetime.fromisoformat(s)

    # ==================== Session Operations ====================

    def create_session(self, session_id: Optional[str] = None, status: str = SessionStatus.ACTIVE) -> dict:
        if session_id is None:
            session_id = str(uuid4())

        now = datetime.now()
        now_str = self._datetime_to_str(now)

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO sessions (id, status, created_at, updated_at) VALUES (?, ?, ?, ?)',
            (session_id, status, now_str, now_str)
        )
        conn.commit()
        conn.close()

        return {
            'id': session_id,
            'status': status,
            'created_at': now,
            'updated_at': now
        }

    def get_session(self, session_id: str) -> Optional[dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sessions WHERE id = ?', (session_id,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return {
            'id': row['id'],
            'status': row['status'],
            'created_at': self._str_to_datetime(row['created_at']),
            'updated_at': self._str_to_datetime(row['updated_at'])
        }

    def update_session_status(self, session_id: str, status: str) -> Optional[dict]:
        session = self.get_session(session_id)
        if session is None:
            return None

        now_str = self._datetime_to_str(datetime.now())

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE sessions SET status = ?, updated_at = ? WHERE id = ?',
            (status, now_str, session_id)
        )
        conn.commit()
        conn.close()

        return self.get_session(session_id)

    def list_sessions(self, status: Optional[str] = None) -> list[dict]:
        conn = self._get_connection()
        cursor = conn.cursor()

        if status:
            cursor.execute('SELECT * FROM sessions WHERE status = ?', (status,))
        else:
            cursor.execute('SELECT * FROM sessions')

        rows = cursor.fetchall()
        conn.close()

        return [{
            'id': row['id'],
            'status': row['status'],
            'created_at': self._str_to_datetime(row['created_at']),
            'updated_at': self._str_to_datetime(row['updated_at'])
        } for row in rows]

    def delete_session(self, session_id: str) -> bool:
        session = self.get_session(session_id)
        if session is None:
            return False

        conn = self._get_connection()
        cursor = conn.cursor()

        # Delete all messages in this session
        cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))

        # Delete all file versions in this session
        cursor.execute('DELETE FROM file_versions WHERE session_id = ?', (session_id,))

        # Delete session
        cursor.execute('DELETE FROM sessions WHERE id = ?', (session_id,))

        conn.commit()
        conn.close()
        return True

    # ==================== Message Operations ====================

    def create_message(
        self,
        session_id: str,
        content: str,
        role: str = MessageRole.USER,
        metadata: Optional[dict] = None
    ) -> Optional[dict]:
        # Verify session exists
        if self.get_session(session_id) is None:
            return None

        message_id = str(uuid4())
        now = datetime.now()
        now_str = self._datetime_to_str(now)
        metadata_json = json.dumps(metadata or {})

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO messages (id, session_id, create_time, metadata, role, content) VALUES (?, ?, ?, ?, ?, ?)',
            (message_id, session_id, now_str, metadata_json, role, content)
        )
        conn.commit()
        conn.close()

        return {
            'id': message_id,
            'session_id': session_id,
            'create_time': now,
            'metadata': metadata or {},
            'role': role,
            'content': content
        }

    def get_message(self, message_id: str) -> Optional[dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM messages WHERE id = ?', (message_id,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return {
            'id': row['id'],
            'session_id': row['session_id'],
            'create_time': self._str_to_datetime(row['create_time']),
            'metadata': json.loads(row['metadata']) if row['metadata'] else {},
            'role': row['role'],
            'content': row['content']
        }

    def get_session_messages(
        self,
        session_id: str,
        role: Optional[str] = None,
        start_from=None,
    ) -> list[dict]:
        conn = self._get_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM messages WHERE session_id = ?'
        params = [session_id]

        if role:
            query += ' AND role = ?'
            params.append(role)

        if start_from is not None:
            query += ' AND create_time > ?'
            params.append(self._datetime_to_str(start_from))

        query += ' ORDER BY create_time'

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [{
            'id': row['id'],
            'session_id': row['session_id'],
            'create_time': self._str_to_datetime(row['create_time']),
            'metadata': json.loads(row['metadata']) if row['metadata'] else {},
            'role': row['role'],
            'content': row['content']
        } for row in rows]

    def update_message(
        self,
        message_id: str,
        content: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Optional[dict]:
        message = self.get_message(message_id)
        if message is None:
            return None

        conn = self._get_connection()
        cursor = conn.cursor()

        if content is not None:
            cursor.execute('UPDATE messages SET content = ? WHERE id = ?', (content, message_id))

        if metadata is not None:
            current_metadata = message['metadata']
            current_metadata.update(metadata)
            cursor.execute('UPDATE messages SET metadata = ? WHERE id = ?', (json.dumps(current_metadata), message_id))

        conn.commit()
        conn.close()

        return self.get_message(message_id)

    def delete_message(self, message_id: str) -> bool:
        message = self.get_message(message_id)
        if message is None:
            return False

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM messages WHERE id = ?', (message_id,))
        conn.commit()
        conn.close()
        return True

    # ==================== File Version Operations ====================

    def create_file_version(
        self,
        session_id: str,
        file_id: str,
        content: str,
        editor: str,
        version_id: Optional[int] = None
    ) -> Optional[dict]:
        # Verify session exists
        if self.get_session(session_id) is None:
            return None

        # Auto-increment version_id if not provided
        if version_id is None:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT MAX(version_id) as max_ver FROM file_versions WHERE session_id = ? AND file_id = ?',
                (session_id, file_id)
            )
            row = cursor.fetchone()
            conn.close()

            if row['max_ver'] is not None:
                version_id = row['max_ver'] + 1
            else:
                version_id = 1

        file_version_id = str(uuid4())
        now = datetime.now()
        now_str = self._datetime_to_str(now)

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO file_versions (id, session_id, version_id, content, editor, create_time, file_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (file_version_id, session_id, version_id, content, editor, now_str, file_id)
        )
        conn.commit()
        conn.close()

        return {
            'id': file_version_id,
            'session_id': session_id,
            'version_id': version_id,
            'content': content,
            'editor': editor,
            'create_time': now,
            'file_id': file_id
        }

    def get_file_version(self, file_version_id: str) -> Optional[dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM file_versions WHERE id = ?', (file_version_id,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return {
            'id': row['id'],
            'session_id': row['session_id'],
            'version_id': row['version_id'],
            'content': row['content'],
            'editor': row['editor'],
            'create_time': self._str_to_datetime(row['create_time']),
            'file_id': row['file_id']
        }

    def get_file_versions(
        self,
        session_id: Optional[str] = None,
        file_id: Optional[str] = None,
        editor: Optional[str] = None,
        start_from=None,
    ) -> list[dict]:
        conn = self._get_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM file_versions WHERE 1=1'
        params = []

        if session_id:
            query += ' AND session_id = ?'
            params.append(session_id)

        if file_id:
            query += ' AND file_id = ?'
            params.append(file_id)

        if editor:
            query += ' AND editor = ?'
            params.append(editor)

        if start_from is not None:
            query += ' AND create_time > ?'
            params.append(self._datetime_to_str(start_from))

        query += ' ORDER BY create_time'

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [{
            'id': row['id'],
            'session_id': row['session_id'],
            'version_id': row['version_id'],
            'content': row['content'],
            'editor': row['editor'],
            'create_time': self._str_to_datetime(row['create_time']),
            'file_id': row['file_id']
        } for row in rows]

    def get_latest_file_version(
        self,
        session_id: str,
        file_id: str
    ) -> Optional[dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM file_versions WHERE session_id = ? AND file_id = ? ORDER BY version_id DESC LIMIT 1',
            (session_id, file_id)
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return {
            'id': row['id'],
            'session_id': row['session_id'],
            'version_id': row['version_id'],
            'content': row['content'],
            'editor': row['editor'],
            'create_time': self._str_to_datetime(row['create_time']),
            'file_id': row['file_id']
        }

    def delete_file_version(self, file_version_id: str) -> bool:
        version = self.get_file_version(file_version_id)
        if version is None:
            return False

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM file_versions WHERE id = ?', (file_version_id,))
        conn.commit()
        conn.close()
        return True

    # ==================== LLM Call Operations ====================

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
        call_id = str(uuid4())
        now = datetime.now()
        now_str = self._datetime_to_str(now)
        messages_json = json.dumps(messages)
        metadata_json = json.dumps(metadata) if metadata else None

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO llm_calls
               (id, session_id, agent_name, model_name, messages, response, error,
                duration_ms, input_tokens, output_tokens, metadata, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (call_id, session_id, agent_name, model_name, messages_json, response, error,
             duration_ms, input_tokens, output_tokens, metadata_json, now_str)
        )
        conn.commit()
        conn.close()

        return {
            'id': call_id,
            'session_id': session_id,
            'agent_name': agent_name,
            'model_name': model_name,
            'messages': messages,
            'response': response,
            'error': error,
            'duration_ms': duration_ms,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'metadata': metadata,
            'created_at': now
        }

    def get_llm_call(self, call_id: str) -> Optional[dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM llm_calls WHERE id = ?', (call_id,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        return {
            'id': row['id'],
            'session_id': row['session_id'],
            'agent_name': row['agent_name'],
            'model_name': row['model_name'],
            'messages': json.loads(row['messages']) if row['messages'] else [],
            'response': row['response'],
            'error': row['error'],
            'duration_ms': row['duration_ms'],
            'input_tokens': row['input_tokens'],
            'output_tokens': row['output_tokens'],
            'metadata': json.loads(row['metadata']) if row['metadata'] else None,
            'created_at': self._str_to_datetime(row['created_at'])
        }

    def get_llm_calls(
        self,
        session_id: Optional[str] = None,
        model_name: Optional[str] = None,
        agent_name: Optional[str] = None,
        start_from=None,
        limit: Optional[int] = None
    ) -> list[dict]:
        conn = self._get_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM llm_calls WHERE 1=1'
        params = []

        if session_id:
            query += ' AND session_id = ?'
            params.append(session_id)

        if model_name:
            query += ' AND model_name = ?'
            params.append(model_name)

        if agent_name:
            query += ' AND agent_name = ?'
            params.append(agent_name)

        if start_from is not None:
            query += ' AND created_at > ?'
            params.append(self._datetime_to_str(start_from))

        query += ' ORDER BY created_at DESC'

        if limit:
            query += ' LIMIT ?'
            params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [{
            'id': row['id'],
            'session_id': row['session_id'],
            'agent_name': row['agent_name'],
            'model_name': row['model_name'],
            'messages': json.loads(row['messages']) if row['messages'] else [],
            'response': row['response'],
            'error': row['error'],
            'duration_ms': row['duration_ms'],
            'input_tokens': row['input_tokens'],
            'output_tokens': row['output_tokens'],
            'metadata': json.loads(row['metadata']) if row['metadata'] else None,
            'created_at': self._str_to_datetime(row['created_at'])
        } for row in rows]

    def update_llm_call(
        self,
        call_id: str,
        response: Optional[str] = None,
        error: Optional[str] = None,
        duration_ms: Optional[int] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None
    ) -> Optional[dict]:
        call = self.get_llm_call(call_id)
        if call is None:
            return None

        conn = self._get_connection()
        cursor = conn.cursor()

        updates = []
        params = []

        if response is not None:
            updates.append('response = ?')
            params.append(response)

        if error is not None:
            updates.append('error = ?')
            params.append(error)

        if duration_ms is not None:
            updates.append('duration_ms = ?')
            params.append(duration_ms)

        if input_tokens is not None:
            updates.append('input_tokens = ?')
            params.append(input_tokens)

        if output_tokens is not None:
            updates.append('output_tokens = ?')
            params.append(output_tokens)

        if updates:
            query = f'UPDATE llm_calls SET {", ".join(updates)} WHERE id = ?'
            params.append(call_id)
            cursor.execute(query, params)
            conn.commit()

        conn.close()
        return self.get_llm_call(call_id)

    # ==================== Utility Operations ====================

    def clear_all(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM messages')
        cursor.execute('DELETE FROM file_versions')
        cursor.execute('DELETE FROM llm_calls')
        cursor.execute('DELETE FROM sessions')
        conn.commit()
        conn.close()

    def get_stats(self) -> dict:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) as count FROM sessions')
        total_sessions = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM messages')
        total_messages = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM file_versions')
        total_file_versions = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM llm_calls')
        total_llm_calls = cursor.fetchone()['count']

        cursor.execute('SELECT status, COUNT(*) as count FROM sessions GROUP BY status')
        rows = cursor.fetchall()
        sessions_by_status = {row['status']: row['count'] for row in rows}

        cursor.execute('SELECT model_name, COUNT(*) as count FROM llm_calls GROUP BY model_name')
        rows = cursor.fetchall()
        llm_calls_by_model = {row['model_name']: row['count'] for row in rows}

        conn.close()

        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "total_file_versions": total_file_versions,
            "total_llm_calls": total_llm_calls,
            "sessions_by_status": sessions_by_status,
            "llm_calls_by_model": llm_calls_by_model
        }
