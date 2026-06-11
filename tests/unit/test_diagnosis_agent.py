"""诊断 Agent 单元测试 - 三层诊断逻辑验证"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #
@pytest.fixture()
def mock_llm_response():
    """模拟 LLM 同步回复"""
    return (
        '{"is_correct": false, "confidence": 0.9, '
        '"surface_error": "混淆了 TCP 握手次数", '
        '"error_type": "factual", '
        '"root_causes": ["协议流程记忆不准确"], '
        '"missing_prerequisites": ["kn_008"], '
        '"intervention_suggestion": "重新学习 TCP 三次握手动画"}'
    )


@pytest.fixture()
def diagnosis_agent(mock_llm_response):
    """返回打了桩的 DiagnosisAgent 实例"""
    from loopse.agents.diagnosis import DiagnosisAgent

    agent = DiagnosisAgent.__new__(DiagnosisAgent)
    agent.llm = MagicMock()
    agent.llm.chat = MagicMock(return_value=mock_llm_response)
    agent.retriever = MagicMock()
    agent.retriever.search_all = AsyncMock(return_value={
        "docs": [], "protocols": [], "misconceptions": [], "graph_nodes": []
    })
    return agent


# ------------------------------------------------------------------ #
# 第一层：表面错误检测
# ------------------------------------------------------------------ #
class TestSurfaceErrorDetection:

    def test_detect_wrong_handshake_count(self, diagnosis_agent):
        """TCP 握手次数写错应被标记为错误"""
        result = diagnosis_agent._detect_surface_error(
            student_answer="TCP 需要两次握手才能建立连接",
            knowledge_point="TCP 三次握手"
        )
        assert result["has_error"] is True

    def test_correct_answer_passes(self, diagnosis_agent):
        """正确答案不应触发表面错误"""
        result = diagnosis_agent._detect_surface_error(
            student_answer="TCP 通过三次握手建立连接，确保双方收发能力正常",
            knowledge_point="TCP 三次握手"
        )
        assert result["has_error"] is False


# ------------------------------------------------------------------ #
# 第二层：根因分析
# ------------------------------------------------------------------ #
class TestRootCauseAnalysis:

    def test_returns_missing_prerequisites(self, diagnosis_agent):
        result = diagnosis_agent._analyze_root_cause(
            surface_error={"has_error": True, "error_type": "factual", "description": "握手次数错误"},
            knowledge_point="TCP 三次握手",
            context=""
        )
        assert "missing_prerequisites" in result
        assert isinstance(result["missing_prerequisites"], list)


# ------------------------------------------------------------------ #
# 第三层：误解模式匹配
# ------------------------------------------------------------------ #
class TestMisconceptionPatternMatch:

    def test_match_known_pattern(self, diagnosis_agent):
        result = diagnosis_agent._match_pattern(
            error_type="factual",
            root_causes=["协议流程记忆不准确"],
            knowledge_point="TCP 三次握手"
        )
        # 应返回一个字符串 pattern 名称或 None
        assert result is None or isinstance(result, str)


# ------------------------------------------------------------------ #
# 集成：完整 diagnose() 调用链
# ------------------------------------------------------------------ #
@pytest.mark.asyncio
async def test_full_diagnose_pipeline(diagnosis_agent):
    result = await diagnosis_agent.diagnose(
        student_answer="TCP 两次握手就够了",
        knowledge_point="TCP 三次握手",
        user_id="test_user",
        session_id="test_session"
    )
    assert "is_correct" in result
    assert "confidence" in result
    assert "surface_error" in result
    assert isinstance(result["root_causes"], list)
