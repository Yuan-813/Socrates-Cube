from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class CognitiveStyle(str, Enum):
    VISUAL = "visual"
    TEXTUAL = "textual"
    PRACTICAL = "practical"


class KnowledgeDimension(BaseModel):
    level: int = Field(ge=1, le=5, description="掌握程度1-5")
    desc: str = ""


class LearningProgress(BaseModel):
    completed_topics: List[str] = []
    current_topic: str = ""
    completion_rate: float = Field(ge=0.0, le=1.0, default=0.0)


class CommonMistakes(BaseModel):
    types: List[str] = []       # 如 ["概念混淆", "流程记忆错误"]
    frequency: dict = {}         # {"概念混淆": 3}


class StudentProfile(BaseModel):
    user_id: str
    updated_at: datetime = Field(default_factory=datetime.now)

    # 6个维度
    knowledge_base: KnowledgeDimension = Field(
        default_factory=lambda: KnowledgeDimension(level=1),
        description="知识储备维度：学生对计算机网络基础知识的整体掌握程度"
    )
    cognitive_style: CognitiveStyle = Field(
        default=CognitiveStyle.TEXTUAL,
        description="认知风格：visual=视觉型, textual=文本型, practical=实践型"
    )
    learning_progress: LearningProgress = Field(
        default_factory=LearningProgress,
        description="学习进度：已完成章节、当前章节、完成率"
    )
    protocol_understanding: KnowledgeDimension = Field(
        default_factory=lambda: KnowledgeDimension(level=1),
        description="协议理解维度：对TCP/IP、HTTP等网络协议的理解深度"
    )
    hands_on_ability: KnowledgeDimension = Field(
        default_factory=lambda: KnowledgeDimension(level=1),
        description="动手实践能力：抓包分析、Socket编程等实验能力"
    )
    common_mistakes: CommonMistakes = Field(
        default_factory=CommonMistakes,
        description="常见错误画像：高频错误类型及出现次数统计"
    )

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
