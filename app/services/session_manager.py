"""
Session Manager
Tracks active sessions and their metadata
"""
import asyncio

from app.models.schemas import SessionStatus, MessageRole
from app.services.database import db
from src.conversation import Conversation
from src.agent import BaselineReActAgent


class SessionManager:
    conversations = {}

    def get_or_create_conversation(self, session_id, logger):
        # Check if session exists or create new one
        if session_id is None or db.get_session(session_id) is None:
            # Create new session
            session = db.create_session()
            session_id = session["id"]
            logger.info(f"Created new session: {session_id}")
        else:
            logger.info(f"Using existing session: {session_id}")

        if session_id not in self.conversations:
            agent = BaselineReActAgent(model="gpt-4.1-mini")
            self.conversations[session_id] = Conversation(session_id=session_id, agents=[agent])
        return self.conversations[session_id], session_id

    def check_if_restart(self, session_id, logger):
        conversation = self.conversations[session_id]
        conversation.check_new_running_tasks()

        async def wrapped_main_loop():
            try:
                await conversation.main_loop()
            finally:
                db.update_session_status(session_id, status=SessionStatus.PAUSED)
                logger.info(f"Session {session_id} paused")

        asyncio.create_task(wrapped_main_loop())


sessionManager = SessionManager()
