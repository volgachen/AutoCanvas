"""
Main application entry point
Initializes FastAPI app, WebSocket manager, and routes
"""

import asyncio
import logging

from app.server import AlphaEvolveApplication
from utils.log import setup_logging

# 配置 Uvicorn 日志格式（在 app 创建前设置）
# 注意：uvicorn.access 使用特殊的格式变量，需要保留 %(message)s
UVICORN_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"

# 清除默认 handler 并设置自定义格式
for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    logger = logging.getLogger(logger_name)
    logger.handlers = []
    logger.propagate = False  # 防止日志向上传播导致重复
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(UVICORN_LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)

alphaevolve_app = AlphaEvolveApplication()
app = alphaevolve_app.app

if __name__ == "__main__":
    setup_logging()
    asyncio.run(alphaevolve_app.run())