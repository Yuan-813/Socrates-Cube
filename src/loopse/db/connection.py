"""数据库连接管理，使用 SQLAlchemy + aiosqlite"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./edu_agent.db")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    """创建所有表"""
    from src.loopse.db.models import User, StudentProfile, ChatSession, AgentLog  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("数据库表初始化完成 ✅")


async def get_session() -> AsyncSession:
    """获取异步数据库会话"""
    async with async_session() as session:
        yield session
