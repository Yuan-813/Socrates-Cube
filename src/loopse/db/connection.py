"""SQLAlchemy database connection management.

支持三种模式（仅需修改 .env 文件）：
  - 本地 SQLite：不配置 DATABASE_URL，自动使用 edu_agent.db
  - 云端 MySQL（CloudBase/RDS）： DATABASE_URL=mysql+pymysql://...
  - 云端 PostgreSQL（Neon）：  DATABASE_URL=postgresql://...
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

# 优先读取 DATABASE_URL；未配置时回落到本地 SQLite
_db_url_env = os.getenv("DATABASE_URL", "")
if _db_url_env and not _db_url_env.startswith("sqlite"):
    # 云端数据库（MySQL / PostgreSQL 等）
    DATABASE_URL = _db_url_env
    connect_args: dict = {}
else:
    # 本地 SQLite（开发默认）
    DB_PATH = os.getenv("DB_PATH", "edu_agent.db")
    DATABASE_URL = _db_url_env if _db_url_env else f"sqlite:///{DB_PATH}"
    connect_args = {"check_same_thread": False}

# MySQL 需要额外参数来处理大文本字段
_extra_kwargs: dict = {}
if "mysql" in DATABASE_URL:
    _extra_kwargs["pool_size"] = 5
    _extra_kwargs["max_overflow"] = 10

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=os.getenv("SQL_ECHO", "0") == "1",
    pool_pre_ping=True,   # 自动重连（云端网络报萧必备）
    pool_recycle=1800,    # 30分钟内必被复用的连接重建
    **_extra_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Create all declared tables."""
    from src.loopse.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
