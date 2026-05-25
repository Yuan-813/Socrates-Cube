"""
数据库 ORM 模型定义
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from src.loopse.db.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, nullable=False, unique=True)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    profile_json = Column(Text, nullable=False, default="{}")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    messages = Column(Text, default="[]")
    create_time = Column(DateTime, default=datetime.now)


class AgentLog(Base):
    __tablename__ = "agent_logs"

    log_id = Column(String, primary_key=True, index=True)
    session_id = Column(String, index=True)
    agent_name = Column(String, nullable=False)
    action = Column(String, nullable=False)
    state = Column(Text, default="{}")
    timestamp = Column(DateTime, default=datetime.now)
    result = Column(Text, default="{}")
