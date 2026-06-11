"""Database ORM models for Socrates-Cube."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint

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
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class AgentLog(Base):
    __tablename__ = "agent_logs"

    log_id = Column(String, primary_key=True, index=True)
    session_id = Column(String, index=True)
    agent_name = Column(String, nullable=False)
    action = Column(String, nullable=False)
    state = Column(Text, default="{}")
    timestamp = Column(DateTime, default=datetime.now)
    result = Column(Text, default="{}")


class KnowledgeNodeRecord(Base):
    __tablename__ = "knowledge_nodes"

    node_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    chapter = Column(String, nullable=False, index=True)
    node_type = Column(String, nullable=False, default="concept")
    difficulty = Column(Integer, nullable=False, default=3)
    estimated_time = Column(Integer, nullable=False, default=30)
    keywords_json = Column(Text, nullable=False, default="[]")
    description = Column(Text, nullable=False, default="")
    prerequisite_ids_json = Column(Text, nullable=False, default="[]")
    create_time = Column(DateTime, default=datetime.now)


class LearningResource(Base):
    __tablename__ = "learning_resources"

    resource_id = Column(String, primary_key=True, index=True)
    knowledge_node_id = Column(String, index=True, nullable=True)
    knowledge_point = Column(String, nullable=False, index=True)
    resource_type = Column(String, nullable=False, index=True)
    difficulty = Column(Integer, nullable=False, default=3)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=False, default="{}")
    quality_score = Column(Float, nullable=False, default=0.75)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class LearningPath(Base):
    __tablename__ = "learning_paths"

    path_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False, default="")
    status = Column(String, nullable=False, default="active")
    total_estimated_time = Column(Integer, nullable=False, default=0)
    plan_json = Column(Text, nullable=False, default="{}")
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class LearningPathNode(Base):
    __tablename__ = "learning_path_nodes"

    id = Column(String, primary_key=True)
    path_id = Column(String, ForeignKey("learning_paths.path_id"), nullable=False, index=True)
    node_id = Column(String, nullable=False, index=True)
    sequence = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="pending")
    current_mastery = Column(Float, nullable=False, default=0.0)
    recommendation_reason = Column(Text, nullable=False, default="")
    create_time = Column(DateTime, default=datetime.now)


class AssessmentRecord(Base):
    __tablename__ = "assessment_records"

    assessment_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    knowledge_node_id = Column(String, nullable=False, index=True)
    question_type = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    max_score = Column(Float, nullable=False, default=100.0)
    answer_json = Column(Text, nullable=False, default="{}")
    diagnosis_json = Column(Text, nullable=False, default="{}")
    create_time = Column(DateTime, default=datetime.now)


class MisconceptionRecord(Base):
    __tablename__ = "misconception_records"
    __table_args__ = (
        UniqueConstraint("user_id", "knowledge_node_id", "pattern", name="uq_user_node_pattern"),
    )

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    knowledge_node_id = Column(String, nullable=False, index=True)
    pattern = Column(String, nullable=False, index=True)
    severity = Column(Float, nullable=False, default=0.5)
    evidence = Column(Text, nullable=False, default="")
    intervention = Column(Text, nullable=False, default="")
    last_seen = Column(DateTime, default=datetime.now)
