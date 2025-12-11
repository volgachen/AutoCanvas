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
        @self.app.get("/heartbeat")
        async def heartbeat():
            return JSONResponse(content={"message": "ok"})

        @self.app.post("/user_message")
        async def handle_user_message(request: Request):
            self.logger.info(f"user_message:")
            username = request.headers.get("webauth-username", "anonymous")
            payload = await request.json()
            self.logger.info(f"user_message: {payload}")
            if payload.get("id", None) is None:
                payload["created_by"] = username
            return JSONResponse(content={"message": "success"})

    async def run(self):
        if config.reload:
            uvicorn.run("app:app", host=config.host, port=config.port, reload=True)
        else:
            uvicorn.run(self.app, host=config.host, port=config.port)