"""
Student profile Pydantic models — aligned with api_schema.yaml.

Two sets of models are provided:
  1. **YAML-aligned** models (``StudentProfileModel``, ``ProfileData``, etc.)
     whose structure matches ``config/api_schema.yaml`` exactly (nested
     ``profile`` object, ``cognitive_style`` as ``{type, desc}``).
  2. **Legacy flat** models (``StudentProfile``, ``KnowledgeDimension``,
     ``CognitiveStyle``, etc.) re-exported from
     ``student_profile_schema.py`` for backward compatibility.

New code should prefer the YAML-aligned models.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ====================================================================== #
# YAML-aligned nested models  (match config/api_schema.yaml)
# ====================================================================== #

class CognitiveStyleType(str, Enum):
    VISUAL = "visual"
    TEXTUAL = "textual"
    PRACTICAL = "practical"


class KnowledgeBaseModel(BaseModel):
    level: int = Field(default=1, ge=1, le=5, description="掌握程度 1-5")
    desc: str = Field(default="", description="简要描述")


class CognitiveStyleModel(BaseModel):
    type: CognitiveStyleType = Field(
        default=CognitiveStyleType.TEXTUAL,
        description="visual=视觉型 | textual=文本型 | practical=实践型",
    )
    desc: str = Field(default="", description="认知风格补充描述")


class LearningProgressModel(BaseModel):
    completed_topics: List[str] = Field(default_factory=list, description="已完成章节列表")
    current_topic: str = Field(default="", description="当前学习章节")
    completion_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="整体完成率")


class ProtocolUnderstandingModel(BaseModel):
    level: int = Field(default=1, ge=1, le=5)
    weak_points: List[str] = Field(default_factory=list, description="薄弱知识点列表")


class HandsOnAbilityModel(BaseModel):
    level: int = Field(default=1, ge=1, le=5)
    desc: str = Field(default="")


class CommonMistakesModel(BaseModel):
    types: List[str] = Field(default_factory=list, description="错误类型列表")
    frequency: Dict[str, int] = Field(default_factory=dict, description="各类错误出现次数")


class ProfileData(BaseModel):
    """Nested profile object matching api_schema.yaml StudentProfile.profile."""

    knowledge_base: KnowledgeBaseModel = Field(default_factory=KnowledgeBaseModel)
    cognitive_style: CognitiveStyleModel = Field(default_factory=CognitiveStyleModel)
    learning_progress: LearningProgressModel = Field(default_factory=LearningProgressModel)
    protocol_understanding: ProtocolUnderstandingModel = Field(default_factory=ProtocolUnderstandingModel)
    hands_on_ability: HandsOnAbilityModel = Field(default_factory=HandsOnAbilityModel)
    common_mistakes: CommonMistakesModel = Field(default_factory=CommonMistakesModel)


class StudentProfileModel(BaseModel):
    """Top-level student profile matching api_schema.yaml structure."""

    user_id: str
    updated_at: datetime = Field(default_factory=datetime.now)
    profile: ProfileData = Field(default_factory=ProfileData)

    class Config:
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# ====================================================================== #
# Backward-compat re-exports  (from student_profile_schema.py)
# ====================================================================== #

from .student_profile_schema import (  # noqa: E402, F401
    CognitiveStyle,
    CommonMistakes,
    KnowledgeDimension,
    LearningProgress,
    StudentProfile,
)
