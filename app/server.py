import asyncio
import json
from contextlib import asynccontextmanager
from typing import Any, Optional, cast

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, Request, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import config
from app.services.database import db
from app.services.session_manager import sessionManager
from app.models.schemas import SessionStatus, MessageRole
from utils.log import logger_manager
from utils.errors import AppError


class AlphaEvolveApplication:
    def __init__(self):
        self.logger = logger_manager.get_logger(__name__)

        self.app = FastAPI(
            title=config.app_title,
            description=config.app_description,
            lifespan=self._lifespan,
        )

        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=config.allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self._register_routes()

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        """Application lifespan manager"""
        self.logger.info("Starting AI Canvas Backend...")
        # Startup logic here
        yield
        # Shutdown logic here
        self.logger.info("Shutting down AI Canvas Backend...")

    def _register_routes(self):
        @self.app.post("/heartbeat")
        async def heartbeat(request: Request):
            """
            Heartbeat endpoint - retrieves messages for a session
            Expects JSON body: {"session_id": "uuid-string"}
            Returns: {"status": "...", "messages": [...]}
            """
            try:
                payload = await request.json()
            except Exception:
                payload = {}

            session_id = payload.get("session_id", None)
            self.logger.info(f"Heartbeat for session {session_id}")

            if not session_id:
                return JSONResponse(
                    content={
                        "status": "error",
                        "error": "session_id is required",
                        "messages": []
                    },
                    status_code=400
                )

            # Check if session exists
            session = db.get_session(session_id)
            if not session:
                return JSONResponse(
                    content={
                        "status": "error",
                        "error": "session not found",
                        "messages": []
                    },
                    status_code=404
                )

            # Get all messages for this session
            messages = db.get_session_messages(session_id)

            # Format messages for response
            formatted_messages = [
                {
                    "id": msg["id"],
                    "role": msg["role"],
                    "content": msg["content"],
                    "create_time": msg["create_time"].isoformat(),
                    "metadata": msg["metadata"]
                }
                for msg in messages
            ]

            # Get newest file versions for this session
            conversation, _ = sessionManager.get_or_create_conversation(session_id, self.logger)
            file_versions = conversation.get_newest_file_versions()

            # Format file versions for response
            formatted_files = [
                {
                    "id": fv["id"],
                    "file_id": fv["file_id"],
                    "version_id": fv["version_id"],
                    "content": fv["content"],
                    "editor": fv["editor"],
                    "create_time": fv["create_time"].isoformat()
                }
                for fv in file_versions
            ]

            self.logger.info(f"Heartbeat for session {session_id} ({session['status']}): {len(formatted_messages)} messages, {len(formatted_files)} files")

            return JSONResponse(content={
                "status": session["status"],
                "session_id": session_id,
                "messages": formatted_messages,
                "files": formatted_files
            })

        @self.app.get("/debug/database")
        async def debug_database(request: Request):
            """Debug endpoint to inspect database state"""
            sessions = db.list_sessions()
            messages_by_session = {}

            for session in sessions:
                session_messages = db.get_session_messages(session['id'])
                messages_by_session[session['id']] = [
                    {
                        "id": msg["id"],
                        "role": msg["role"],
                        "content": msg["content"],
                        "create_time": msg["create_time"].isoformat(),
                        "metadata": msg["metadata"]
                    }
                    for msg in session_messages
                ]

            return JSONResponse(content={
                "stats": db.get_stats(),
                "sessions": [
                    {
                        "id": s["id"],
                        "status": s["status"],
                        "created_at": s["created_at"].isoformat(),
                        "updated_at": s["updated_at"].isoformat(),
                        "messages": messages_by_session.get(s["id"], [])
                    }
                    for s in sessions
                ]
            })

        @self.app.post("/user_message")
        async def handle_user_message(request: Request):
            username = request.headers.get("webauth-username", "anonymous")
            payload = await request.json()

            # Extract session_id and message content
            session_id = payload.get("session_id", None)
            message_content = payload.get("user_message", "")
            self.logger.info(f"Received user_message request: session {session_id}, content: {message_content}")

            conversation, session_id = sessionManager.get_or_create_conversation(session_id, self.logger)

            # Create message in database
            message = db.create_message(
                session_id=session_id,
                content=message_content,
                role=MessageRole.USER,
                metadata={
                    "username": username,
                    "source": "api"
                }
            )

            if message is None:
                self.logger.error(f"Failed to create message for session: {session_id}")
                return JSONResponse(
                    content={"error": "Failed to create message"},
                    status_code=500
                )

            self.logger.info(f"Created message {message['id']} in session {session_id}")

            # Update session status to processing
            sessionManager.check_if_restart(session_id, self.logger)
            db.update_session_status(session_id, SessionStatus.PROCESSING)

            return JSONResponse(content={
                "status": "processing",
                "session_id": session_id,
                "message_id": message["id"]
            })

        @self.app.post("/update_passage")
        async def update_passage(request: Request):
            """
            Update passage endpoint - save user-edited file version
            Expects JSON body: {"content": "...", "version_id": int, "session_id": "..."}
            """
            payload = await request.json()

            # Extract parameters
            content = payload.get("content", "")
            version_id = payload.get("version_id")
            session_id = payload.get("session_id")

            self.logger.info(f"Received update_passage request: session {session_id}, version {version_id}")

            if content is None or content == "":
                return JSONResponse(
                    content={"error": "content is required"},
                    status_code=400
                )

            conversation, session_id = sessionManager.get_or_create_conversation(session_id, self.logger)

            # Create file version with editor as "user"
            file_version = db.create_file_version(
                session_id=session_id,
                file_id="passage",  # Using "passage" as the file_id
                content=content,
                editor="user",
                version_id=version_id  # Use provided version_id or let it auto-increment
            )

            if file_version is None:
                self.logger.error(f"Failed to create file version for session: {session_id}")
                return JSONResponse(
                    content={"error": "Failed to create file version"},
                    status_code=500
                )

            self.logger.info(f"Created file version {file_version['id']} (v{file_version['version_id']}) in session {session_id}")

            return JSONResponse(content={
                "status": "success",
                "session_id": session_id,
                "version_id": file_version["version_id"],
                "file_version_id": file_version["id"],
                "create_time": file_version["create_time"].isoformat()
            })

    async def run(self):
        # Prepare uvicorn config
        uvicorn_config = {
            "host": config.host,
            "port": config.port,
        }

        # Add SSL configuration if enabled
        if config.ssl_enabled:
            if not config.ssl_certfile or not config.ssl_keyfile:
                raise ValueError("SSL is enabled but ssl_certfile or ssl_keyfile is not configured")

            uvicorn_config["ssl_certfile"] = config.ssl_certfile
            uvicorn_config["ssl_keyfile"] = config.ssl_keyfile
            self.logger.info(f"HTTPS enabled with cert: {config.ssl_certfile}")
        else:
            self.logger.info("Running in HTTP mode (SSL disabled)")

        if config.reload:
            uvicorn.run("main:app", reload=True, **uvicorn_config)
        else:
            uvicorn.run(self.app, **uvicorn_config)