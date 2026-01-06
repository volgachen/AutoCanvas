"""
In-Memory Database Implementation using Pandas DataFrames
"""

from datetime import datetime
from typing import Optional
import pandas as pd
from uuid import uuid4
import json

from app.models.schemas import SessionStatus, MessageRole
from .base import BaseDatabase


class MemoryDatabase(BaseDatabase):
    """
    In-memory database using pandas DataFrames
    """

    def __init__(self):
        # Table 1: Sessions
        self.sessions = pd.DataFrame(columns=['id', 'status', 'created_at', 'updated_at'])
        self.sessions = self.sessions.set_index('id')

        # Table 2: Messages
        self.messages = pd.DataFrame(columns=[
            'id', 'session_id', 'create_time', 'metadata', 'role', 'content'
        ])
        self.messages = self.messages.set_index('id')

        # Table 3: File Versions
        self.file_versions = pd.DataFrame(columns=[
            'id', 'session_id', 'version_id', 'content', 'editor', 'create_time', 'file_id'
        ])
        self.file_versions = self.file_versions.set_index('id')

        # Table 4: LLM Calls
        self.llm_calls = pd.DataFrame(columns=[
            'id', 'session_id', 'agent_name', 'model_name', 'messages', 'response',
            'error', 'duration_ms', 'input_tokens', 'output_tokens', 'metadata', 'created_at'
        ])
        self.llm_calls = self.llm_calls.set_index('id')

    # ==================== Session Operations ====================

    def create_session(self, session_id: Optional[str] = None, status: str = SessionStatus.ACTIVE) -> dict:
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
        if session_id not in self.sessions.index:
            return None

        session = self.sessions.loc[session_id].to_dict()
        session['id'] = session_id
        return session

    def update_session_status(self, session_id: str, status: str) -> Optional[dict]:
        if session_id not in self.sessions.index:
            return None

        self.sessions.loc[session_id, 'status'] = status
        self.sessions.loc[session_id, 'updated_at'] = datetime.now()

        return self.get_session(session_id)

    def list_sessions(self, status: Optional[str] = None) -> list[dict]:
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
        if session_id not in self.sessions.index:
            return False

        # Delete all messages in this session
        self.messages = self.messages[self.messages['session_id'] != session_id]

        # Delete all file versions in this session
        self.file_versions = self.file_versions[self.file_versions['session_id'] != session_id]

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
        if message_id not in self.messages.index:
            return None

        message = self.messages.loc[message_id].to_dict()
        message['id'] = message_id
        return message

    def get_session_messages(
        self,
        session_id: str,
        role: Optional[str] = None,
        start_from=None,
    ) -> list[dict]:
        df = self.messages[self.messages['session_id'] == session_id]

        if role:
            df = df[df['role'] == role]

        # Sort by create_time
        df = df.sort_values('create_time')

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
        if message_id not in self.messages.index:
            return False

        self.messages = self.messages.drop(message_id)
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
        if session_id not in self.sessions.index:
            return None

        # Auto-increment version_id if not provided
        if version_id is None:
            existing_versions = self.file_versions[
                (self.file_versions['session_id'] == session_id) &
                (self.file_versions['file_id'] == file_id)
            ]
            if not existing_versions.empty:
                version_id = existing_versions['version_id'].max() + 1
            else:
                version_id = 1

        file_version_id = str(uuid4())
        now = datetime.now()

        self.file_versions.loc[file_version_id] = {
            'session_id': session_id,
            'version_id': version_id,
            'content': content,
            'editor': editor,
            'create_time': now,
            'file_id': file_id
        }

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
        if file_version_id not in self.file_versions.index:
            return None

        version = self.file_versions.loc[file_version_id].to_dict()
        version['id'] = file_version_id
        return version

    def get_file_versions(
        self,
        session_id: Optional[str] = None,
        file_id: Optional[str] = None,
        editor: Optional[str] = None,
        start_from=None,
    ) -> list[dict]:
        df = self.file_versions

        if session_id:
            df = df[df['session_id'] == session_id]

        if file_id:
            df = df[df['file_id'] == file_id]

        if editor:
            df = df[df['editor'] == editor]

        # Sort by create_time
        df = df.sort_values('create_time')

        if start_from is not None:
            df = df[df['create_time'] > start_from]

        result = []
        for idx, row in df.iterrows():
            version = row.to_dict()
            version['id'] = idx
            result.append(version)

        return result

    def get_latest_file_version(
        self,
        session_id: str,
        file_id: str
    ) -> Optional[dict]:
        versions = self.get_file_versions(session_id=session_id, file_id=file_id)
        if not versions:
            return None

        return max(versions, key=lambda v: v['version_id'])

    def delete_file_version(self, file_version_id: str) -> bool:
        if file_version_id not in self.file_versions.index:
            return False

        self.file_versions = self.file_versions.drop(file_version_id)
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

        self.llm_calls.loc[call_id] = {
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
        if call_id not in self.llm_calls.index:
            return None

        call = self.llm_calls.loc[call_id].to_dict()
        call['id'] = call_id
        return call

    def get_llm_calls(
        self,
        session_id: Optional[str] = None,
        model_name: Optional[str] = None,
        agent_name: Optional[str] = None,
        start_from=None,
        limit: Optional[int] = None
    ) -> list[dict]:
        df = self.llm_calls

        if session_id:
            df = df[df['session_id'] == session_id]

        if model_name:
            df = df[df['model_name'] == model_name]

        if agent_name:
            df = df[df['agent_name'] == agent_name]

        if start_from is not None:
            df = df[df['created_at'] > start_from]

        # Sort by created_at descending
        df = df.sort_values('created_at', ascending=False)

        if limit:
            df = df.head(limit)

        result = []
        for idx, row in df.iterrows():
            call = row.to_dict()
            call['id'] = idx
            result.append(call)

        return result

    def update_llm_call(
        self,
        call_id: str,
        response: Optional[str] = None,
        error: Optional[str] = None,
        duration_ms: Optional[int] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None
    ) -> Optional[dict]:
        if call_id not in self.llm_calls.index:
            return None

        if response is not None:
            self.llm_calls.loc[call_id, 'response'] = response

        if error is not None:
            self.llm_calls.loc[call_id, 'error'] = error

        if duration_ms is not None:
            self.llm_calls.loc[call_id, 'duration_ms'] = duration_ms

        if input_tokens is not None:
            self.llm_calls.loc[call_id, 'input_tokens'] = input_tokens

        if output_tokens is not None:
            self.llm_calls.loc[call_id, 'output_tokens'] = output_tokens

        return self.get_llm_call(call_id)

    # ==================== Utility Operations ====================

    def clear_all(self):
        self.sessions = pd.DataFrame(columns=['id', 'status', 'created_at', 'updated_at']).set_index('id')
        self.messages = pd.DataFrame(columns=[
            'id', 'session_id', 'create_time', 'metadata', 'role', 'content'
        ]).set_index('id')
        self.file_versions = pd.DataFrame(columns=[
            'id', 'session_id', 'version_id', 'content', 'editor', 'create_time', 'file_id'
        ]).set_index('id')
        self.llm_calls = pd.DataFrame(columns=[
            'id', 'session_id', 'agent_name', 'model_name', 'messages', 'response',
            'error', 'duration_ms', 'input_tokens', 'output_tokens', 'metadata', 'created_at'
        ]).set_index('id')

    def get_stats(self) -> dict:
        sessions_by_status = {}
        if not self.sessions.empty:
            status_counts = self.sessions['status'].value_counts().to_dict()
            sessions_by_status = status_counts

        llm_calls_by_model = {}
        if not self.llm_calls.empty:
            model_counts = self.llm_calls['model_name'].value_counts().to_dict()
            llm_calls_by_model = model_counts

        return {
            "total_sessions": len(self.sessions),
            "total_messages": len(self.messages),
            "total_file_versions": len(self.file_versions),
            "total_llm_calls": len(self.llm_calls),
            "sessions_by_status": sessions_by_status,
            "llm_calls_by_model": llm_calls_by_model
        }
