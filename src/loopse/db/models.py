"""ORM 模型定义，与 init_db.py 的4张表对齐"""

from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.sql import func
from src.loopse.db.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, nullable=False)
    create_time = Column(DateTime, server_default=func.now())
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now())


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    user_id = Column(String, primary_key=True)
    profile_json = Column(Text, nullable=False)
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True)
    messages = Column(Text, default="[]")
    create_time = Column(DateTime, server_default=func.now())


class AgentLog(Base):
    __tablename__ = "agent_logs"

    log_id = Column(String, primary_key=True)
    session_id = Column(String, nullable=True)
    agent_name = Column(String, nullable=True)
    action = Column(String, nullable=True)
    state = Column(Text, nullable=True)
    timestamp = Column(DateTime, server_default=func.now())
    result = Column(Text, nullable=True)
