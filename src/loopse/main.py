import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Socrates-Cube",
    version="1.0.0",
    description="苏格拉底方块——多智能体自适应《计算机网络》学习系统（软件杯A3）",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _on_startup():
    """应用启动时初始化数据库"""
    try:
        from .db.connection import init_db
        init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error("数据库初始化失败（非致命）: %s", e)


# 注册所有路由
from .api.chat import router as chat_router
from .api.profile import router as profile_router
from .api.logs import router as logs_router
from .api.resources import router as resources_router
from .api.path import router as path_router

app.include_router(chat_router)
app.include_router(profile_router)
app.include_router(logs_router)
app.include_router(resources_router)
app.include_router(path_router)


@app.get("/health", tags=["系统"])
async def health_check():
    return {"status": "ok", "version": "1.0.0", "service": "Socrates-Cube"}
