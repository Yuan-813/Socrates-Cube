"""
单元测试：StudentProfile Pydantic 模型
验证模型可以正常实例化、字段校验生效、序列化为 JSON 正常工作。
"""

import json
import pytest
from datetime import datetime

# 调整 sys.path，使测试可以在项目根目录直接运行
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.loopse.schema.student_profile_schema import (
    StudentProfile,
    KnowledgeDimension,
    LearningProgress,
    CommonMistakes,
    CognitiveStyle,
)


class TestKnowledgeDimension:
    def test_default_instantiation(self):
        dim = KnowledgeDimension(level=3)
        assert dim.level == 3
        assert dim.desc == ""

    def test_level_boundary_valid(self):
        assert KnowledgeDimension(level=1).level == 1
        assert KnowledgeDimension(level=5).level == 5

    def test_level_boundary_invalid_low(self):
        with pytest.raises(Exception):
            KnowledgeDimension(level=0)

    def test_level_boundary_invalid_high(self):
        with pytest.raises(Exception):
            KnowledgeDimension(level=6)


class TestLearningProgress:
    def test_default_instantiation(self):
        lp = LearningProgress()
        assert lp.completed_topics == []
        assert lp.current_topic == ""
        assert lp.completion_rate == 0.0

    def test_with_data(self):
        lp = LearningProgress(
            completed_topics=["TCP/IP基础", "三次握手"],
            current_topic="UDP协议",
            completion_rate=0.4,
        )
        assert len(lp.completed_topics) == 2
        assert lp.completion_rate == 0.4

    def test_completion_rate_boundary_invalid(self):
        with pytest.raises(Exception):
            LearningProgress(completion_rate=1.5)


class TestCommonMistakes:
    def test_default_instantiation(self):
        cm = CommonMistakes()
        assert cm.types == []
        assert cm.frequency == {}

    def test_with_data(self):
        cm = CommonMistakes(
            types=["概念混淆", "流程记忆错误"],
            frequency={"概念混淆": 3, "流程记忆错误": 1},
        )
        assert "概念混淆" in cm.types
        assert cm.frequency["概念混淆"] == 3


class TestStudentProfile:
    def test_minimal_instantiation(self):
        """只提供必填字段 user_id 即可实例化"""
        profile = StudentProfile(user_id="user_001")
        assert profile.user_id == "user_001"
        assert isinstance(profile.updated_at, datetime)

    def test_default_dimensions(self):
        """6 个维度应有合理默认值"""
        profile = StudentProfile(user_id="user_002")
        assert profile.knowledge_base.level == 1
        assert profile.protocol_understanding.level == 1
        assert profile.hands_on_ability.level == 1
        assert profile.learning_progress.completion_rate == 0.0
        assert profile.common_mistakes.types == []

    def test_cognitive_style_default(self):
        profile = StudentProfile(user_id="user_003")
        # use_enum_values=True 时值为字符串
        assert profile.cognitive_style == "textual"

    def test_cognitive_style_enum_values(self):
        for style in ["visual", "textual", "practical"]:
            profile = StudentProfile(user_id="u", cognitive_style=style)
            assert profile.cognitive_style == style

    def test_cognitive_style_invalid(self):
        with pytest.raises(Exception):
            StudentProfile(user_id="u", cognitive_style="unknown_style")

    def test_full_profile_instantiation(self):
        """完整字段实例化"""
        profile = StudentProfile(
            user_id="user_full",
            knowledge_base=KnowledgeDimension(level=3, desc="掌握基础概念"),
            cognitive_style=CognitiveStyle.VISUAL,
            learning_progress=LearningProgress(
                completed_topics=["第1章", "第3章"],
                current_topic="第4章",
                completion_rate=0.4,
            ),
            protocol_understanding=KnowledgeDimension(level=2, desc="TCP理解较弱"),
            hands_on_ability=KnowledgeDimension(level=4, desc="抓包熟练"),
            common_mistakes=CommonMistakes(
                types=["概念混淆"],
                frequency={"概念混淆": 5},
            ),
        )
        assert profile.knowledge_base.level == 3
        assert profile.learning_progress.completion_rate == 0.4
        assert profile.common_mistakes.frequency["概念混淆"] == 5

    def test_json_serialization(self):
        """模型可序列化为合法 JSON"""
        profile = StudentProfile(
            user_id="user_json",
            knowledge_base=KnowledgeDimension(level=2, desc="初步了解"),
        )
        json_str = profile.model_dump_json()
        data = json.loads(json_str)
        assert data["user_id"] == "user_json"
        assert data["knowledge_base"]["level"] == 2
        assert "updated_at" in data

    def test_dict_serialization(self):
        """model_dump 返回字典结构完整"""
        profile = StudentProfile(user_id="user_dict")
        d = profile.model_dump()
        expected_keys = {
            "user_id", "updated_at", "knowledge_base", "cognitive_style",
            "learning_progress", "protocol_understanding",
            "hands_on_ability", "common_mistakes",
        }
        assert expected_keys.issubset(d.keys())
