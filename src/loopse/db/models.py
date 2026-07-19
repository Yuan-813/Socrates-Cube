"""Database ORM models for Socrates-Cube."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint

from src.loopse.db.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    username = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=True)   # nullable 支持社交登录
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(20), nullable=True, index=True)
    role_type = Column(String(50), nullable=False, default="student")  # student/professional/self_learner/job_seeker
    meta_json = Column(Text, default="{}")    # 年龄、背景、目标等自定义信息
    is_first_login = Column(Integer, default=1)  # 1=首次登录0=老用户
    onboarded = Column(Boolean, default=False, nullable=False)  # AI引导初始化是否完成
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    user_id = Column(String(64), ForeignKey("users.id"), primary_key=True)
    profile_json = Column(Text, nullable=False, default="{}")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=True)
    messages = Column(Text, default="[]")
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class AgentLog(Base):
    __tablename__ = "agent_logs"

    log_id = Column(String(64), primary_key=True, index=True)
    session_id = Column(String(64), index=True)
    agent_name = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    state = Column(Text, default="{}")
    timestamp = Column(DateTime, default=datetime.now)
    result = Column(Text, default="{}")


class KnowledgeNodeRecord(Base):
    __tablename__ = "knowledge_nodes"

    node_id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    chapter = Column(String(100), nullable=False, index=True)
    node_type = Column(String(50), nullable=False, default="concept")
    difficulty = Column(Integer, nullable=False, default=3)
    estimated_time = Column(Integer, nullable=False, default=30)
    keywords_json = Column(Text, nullable=False, default="[]")
    description = Column(Text, nullable=False, default="")
    prerequisite_ids_json = Column(Text, nullable=False, default="[]")
    create_time = Column(DateTime, default=datetime.now)


class LearningResource(Base):
    __tablename__ = "learning_resources"

    resource_id = Column(String(64), primary_key=True, index=True)
    knowledge_node_id = Column(String(64), index=True, nullable=True)
    knowledge_point = Column(String(255), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    difficulty = Column(Integer, nullable=False, default=3)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=False, default="{}")
    quality_score = Column(Float, nullable=False, default=0.75)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class LearningPath(Base):
    __tablename__ = "learning_paths"

    path_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False, default="")
    status = Column(String(50), nullable=False, default="active")
    total_estimated_time = Column(Integer, nullable=False, default=0)
    plan_json = Column(Text, nullable=False, default="{}")
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class LearningPathNode(Base):
    __tablename__ = "learning_path_nodes"

    id = Column(String(128), primary_key=True)
    path_id = Column(String(64), ForeignKey("learning_paths.path_id"), nullable=False, index=True)
    node_id = Column(String(64), nullable=False, index=True)
    sequence = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    current_mastery = Column(Float, nullable=False, default=0.0)
    recommendation_reason = Column(Text, nullable=False, default="")
    create_time = Column(DateTime, default=datetime.now)


class AssessmentRecord(Base):
    __tablename__ = "assessment_records"

    assessment_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    knowledge_node_id = Column(String(64), nullable=False, index=True)
    question_type = Column(String(50), nullable=False)
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

    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    knowledge_node_id = Column(String(64), nullable=False, index=True)
    pattern = Column(String(255), nullable=False, index=True)
    severity = Column(Float, nullable=False, default=0.5)
    evidence = Column(Text, nullable=False, default="")
    intervention = Column(Text, nullable=False, default="")
    last_seen = Column(DateTime, default=datetime.now)


class MemoryRecord(Base):
    """Agent 长期记忆存储（跨会话持久化，按人格隔离）。"""
    __tablename__ = "memory_records"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    persona = Column(String(50), nullable=False, default="general", index=True)
    memory_type = Column(String(50), nullable=False, default="long_term")  # long_term / session_summary / preference
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    archived_at = Column(DateTime, nullable=True)


class Bookmark(Base):
    """用户收藏的行业资料/外部链接。"""
    __tablename__ = "bookmarks"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    resource_url = Column(Text, nullable=True)
    resource_title = Column(String(255), nullable=False, default="")
    resource_type = Column(String(50), nullable=False, default="link")  # link / doc / video / paper
    source = Column(String(100), nullable=False, default="web")  # web / kb / generated
    created_at = Column(DateTime, default=datetime.now)
