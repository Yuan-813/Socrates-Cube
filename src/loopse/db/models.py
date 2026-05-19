from sqlalchemy import Column, String, Text, DateTime, Float, Integer
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
import uuid

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), nullable=False, unique=True)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    user_id = Column(String, primary_key=True)
    profile_json = Column(Text, nullable=False)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    session_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    messages = Column(Text, default="[]")
    create_time = Column(DateTime, default=datetime.now)

class AgentLog(Base):
    __tablename__ = "agent_logs"
    log_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, nullable=False)
    agent_name = Column(String(50), nullable=False)
    action = Column(String(100))
    input_state = Column(Text)
    output_state = Column(Text)
    duration_ms = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.now)
    result = Column(Text)
