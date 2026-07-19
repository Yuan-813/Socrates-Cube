"""干预推荐数据类型定义。"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class InterventionRecommendation:
    """单条干预推荐"""
    type: str            # "simulation" | "exercise" | "challenge" | "doc"
    id: Optional[str]    # 具体资源ID（如仿真场景名），无则 None
    label: str           # 展示标签（如 "协议仿真演示"）
    description: str     # 描述文本
    rationale: str       # 推荐理由（可解释性）
    priority: int = 1    # 优先级 1-5，越小越高

    def to_dict(self) -> dict:
        return asdict(self)
