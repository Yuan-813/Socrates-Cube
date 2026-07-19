"""Challenger Agent 单元测试。"""
from __future__ import annotations

import pytest

from loopse.agent.challenger import ChallengerAgent


@pytest.fixture
def agent() -> ChallengerAgent:
    return ChallengerAgent()


@pytest.fixture
def sample_diagnosis() -> dict:
    return {
        "is_correct": False,
        "surface_error": "把 TCP 三次握手误认为两次握手",
        "error_type": "flow_omission",
        "pattern": "流程遗漏型",
        "intervention_suggestion": "用失效连接请求反例说明第三次 ACK 的必要性",
    }


class TestChallengerAgent:
    def test_should_challenge_on_wrong_answer(self, agent: ChallengerAgent, sample_diagnosis: dict):
        assert agent.should_challenge(sample_diagnosis, learning_turns=0) is True

    def test_should_challenge_after_five_learning_turns(self, agent: ChallengerAgent):
        correct_diag = {"is_correct": True}
        assert agent.should_challenge(correct_diag, learning_turns=5) is True
        assert agent.should_challenge(correct_diag, learning_turns=3) is False

    def test_start_session_returns_question(self, agent: ChallengerAgent, sample_diagnosis: dict):
        payload = agent.start_session("sess-001", sample_diagnosis, {"cognitive_style": "visual"})
        assert payload["status"] == "active"
        assert payload["round"] == 1
        assert payload["question"]
        assert payload["max_rounds"] == ChallengerAgent.MAX_ROUNDS

    def test_evaluate_answer_continue_then_complete(self, agent: ChallengerAgent, sample_diagnosis: dict):
        agent.start_session("sess-002", sample_diagnosis, {})
        r1 = agent.evaluate_answer("sess-002", "第三次 ACK 防止历史连接请求导致半开连接")
        assert r1["status"] in {"continue", "completed"}
        assert "feedback" in r1

        r2 = agent.evaluate_answer("sess-002", "服务端重传 SYN+ACK，客户端仍处于 SYN_SENT")
        assert r2["status"] in {"continue", "completed"}

    def test_evaluate_inactive_session(self, agent: ChallengerAgent):
        result = agent.evaluate_answer("missing-session", "任意回答")
        assert result["status"] == "inactive"
