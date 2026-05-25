"""
数据库连接管理 —— SQLAlchemy + SQLite
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "edu_agent.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db():
    """创建所有数据表（如不存在）"""
    from src.loopse.db.models import User, StudentProfile, ChatSession, AgentLog  # noqa
    Base.metadata.create_all(bind=engine)
