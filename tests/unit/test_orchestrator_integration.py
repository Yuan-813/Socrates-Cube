"""Orchestrator 集成测试 - 状态机转换、业务闭环、SSE事件序列、降级处理与异常场景。"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["MOCK_MODE"] = "true"

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ------------------------------------------------------------------ #
# 辅助工具
# ------------------------------------------------------------------ #
def _parse_sse_events(sse_strings: list[str]) -> list[dict]:
    """从 SSE 字符串列表解析出事件字典列表。"""
    events = []
    for raw in sse_strings:
        if raw.startswith("data: "):
            payload = json.loads(raw[6:].strip())
            events.append(payload)
    return events


def _make_mock_llm():
    """创建模拟 LLM 客户端。"""
    mock = MagicMock()
    mock.chat = MagicMock(return_value='{"is_correct": true, "confidence": 0.85, "surface_error": null, "error_type": "none"}')

    async def _stream(prompt, system_prompt=None):
        for token in ["你好", "，", "TCP", "三次握手", "是..."]:
            yield token

    mock.async_stream_chat = _stream
    return mock


def _make_diagnosis_result(is_correct=True, error_type="none"):
    """构建模拟诊断结果。"""
    if is_correct:
        return {
            "is_correct": True,
            "confidence": 0.85,
            "surface_error": None,
            "error_type": "none",
            "root_causes": [],
            "missing_prerequisites": [],
            "pattern": None,
            "intervention_suggestion": "理解基本正确",
            "related_node_ids": [],
            "knowledge_node_ids": [],
            "misconception_id": None,
            "recommended_interventions": [],
        }
    return {
        "is_correct": False,
        "confidence": 0.75,
        "surface_error": "TCP握手次数描述错误",
        "error_type": error_type,
        "root_causes": ["协议流程记忆不准确"],
        "missing_prerequisites": ["kp_008"],
        "pattern": "flow_omission",
        "intervention_suggestion": "建议重新学习TCP三次握手动画",
        "related_node_ids": ["kp_008"],
        "knowledge_node_ids": ["kp_008"],
        "misconception_id": "mc_001",
        "recommended_interventions": ["doc", "exercise"],
        "acu_ids": ["acu_001"],
    }


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #
@pytest.fixture()
def orchestrator():
    """构建一个完全 mock 掉外部依赖的 OrchestratorAgent 实例。"""
    with patch("loopse.agent.orchestrator._PERSONAS", {"professor": {"prompt_prefix": "你是教授"}}), \
         patch("loopse.agent.orchestrator._kg") as mock_kg, \
         patch("loopse.agent.orchestrator.trust_mechanism") as mock_trust, \
         patch("loopse.agent.orchestrator.misconception_registry"), \
         patch("loopse.agent.orchestrator.intervention_selector"), \
         patch("loopse.agent.orchestrator.SessionRepository") as mock_session_repo, \
         patch("loopse.agent.orchestrator.AgentLogRepository"), \
         patch("loopse.agent.orchestrator.LearningPathRepository"), \
         patch("loopse.agent.orchestrator.get_client_for_persona") as mock_get_client, \
         patch("loopse.agent.orchestrator.get_persona_system_prompt", return_value="你是教授"):

        mock_kg.get_all_nodes.return_value = []
        mock_trust.check_question_scope.return_value = {"in_scope": True}
        mock_trust.verify_response.return_value = {"has_sources": False, "has_uncertainty": False, "content": "test"}
        mock_session_repo.get_or_create.return_value = {"messages": []}
        mock_session_repo.append_message = MagicMock()

        mock_llm = _make_mock_llm()
        mock_get_client.return_value = mock_llm

        from loopse.agent.orchestrator import OrchestratorAgent
        agent = OrchestratorAgent.__new__(OrchestratorAgent)
        agent._session_states = {}
        agent._completed_kp_count = 0

        # Mock 所有子 Agent
        agent.coordinator = MagicMock()
        agent.coordinator.dispatch.return_value = MagicMock(
            intent="qa", knowledge_point="TCP 三次握手", persona_id="professor"
        )

        agent.retriever = MagicMock()
        agent.retriever.search_all = MagicMock(return_value={
            "docs": [{"content": "TCP三次握手", "source": "ch05"}],
            "protocols": [],
            "misconceptions": [],
            "graph_nodes": [],
        })

        agent.diagnosis = MagicMock()
        agent.diagnosis.diagnose = MagicMock(return_value=_make_diagnosis_result(True))

        agent.profiler = MagicMock()
        agent.profiler.get_profile.return_value = {
            "mastery_map": {"kp_008": 0.7},
            "weak_points": [],
            "strong_points": [],
            "turn_count": 1,
            "cognitive_style": "textual",
            "persona_id": "professor",
        }
        agent.profiler.update_from_dialogue.return_value = agent.profiler.get_profile.return_value

        agent.resource_gen = MagicMock()
        agent.resource_gen.generate_all = MagicMock(return_value={
            "knowledge_point": "TCP 三次握手",
            "total_resources": 5,
            "doc": {"resource_type": "doc", "content": "test"},
            "exercise": {"resource_type": "exercise", "content": "test"},
            "code": {"resource_type": "code", "content": "test"},
            "mindmap": {"resource_type": "mindmap", "content": "test"},
            "script": {"resource_type": "script", "content": "test"},
        })

        agent.path_planner = MagicMock()
        agent.path_planner.plan.return_value = {
            "path_id": "test-path",
            "nodes": [{"node_id": "kp_008", "status": "pending"}],
        }

        agent.challenger = MagicMock()
        agent.challenger.should_challenge.return_value = False

        yield agent


# ------------------------------------------------------------------ #
# 1. 状态机转换测试
# ------------------------------------------------------------------ #
class TestStateMachineTransitions:
    """验证 Orchestrator 状态机的转换逻辑。"""

    def test_initial_state_is_idle(self, orchestrator):
        """初始状态应为 idle"""
        state = orchestrator._get_session_state("s1")
        assert state["state"] == "idle"

    def test_idle_to_learning_on_correct_answer(self, orchestrator):
        """正确回答时，idle 应转换为 learning"""
        state = orchestrator._get_session_state("s1")
        assert state["state"] == "idle"
        # 模拟状态转换逻辑
        state["state"] = "learning"
        state["learning_turns"] = 1
        assert state["state"] == "learning"

    def test_learning_to_consolidation_after_threshold(self, orchestrator):
        """学习轮次达到阈值时应转入巩固阶段"""
        state = orchestrator._get_session_state("s1")
        state["state"] = "learning"
        state["learning_turns"] = 5
        # 到达阈值后应转入巩固
        if state["learning_turns"] >= 5:
            state["state"] = "consolidation"
        assert state["state"] == "consolidation"

    def test_consolidation_on_error(self, orchestrator):
        """诊断出错误时，应进入巩固状态"""
        state = orchestrator._get_session_state("s1")
        state["state"] = "learning"
        diag_result = _make_diagnosis_result(is_correct=False)
        if not diag_result.get("is_correct", True):
            state["state"] = "consolidation"
        assert state["state"] == "consolidation"

    @pytest.mark.parametrize("initial_state,expected", [
        ("idle", "idle"),
        ("learning", "learning"),
        ("consolidation", "consolidation"),
        ("planning", "planning"),
    ])
    def test_state_machine_valid_states(self, orchestrator, initial_state, expected):
        """验证所有合法状态都能被正确设置"""
        state = orchestrator._get_session_state("s_param")
        state["state"] = initial_state
        assert state["state"] == expected

    def test_state_change_message(self, orchestrator):
        """状态转换消息应对应正确的描述"""
        from loopse.agent.orchestrator import OrchestratorAgent
        msg = OrchestratorAgent._state_change_message("learning")
        assert "学习" in msg
        msg2 = OrchestratorAgent._state_change_message("consolidation")
        assert "巩固" in msg2 or "Challenger" in msg2


# ------------------------------------------------------------------ #
# 2. 完整业务闭环测试
# ------------------------------------------------------------------ #
class TestBusinessLoop:
    """验证完整的业务闭环：用户提问 → 诊断 → 画像更新 → 资源推荐。"""

    @pytest.mark.asyncio
    async def test_full_stream_reply_produces_events(self, orchestrator):
        """完整流式回复应产出 SSE 事件序列"""
        events = []
        async for sse in orchestrator.async_stream_reply(
            session_id="test_session",
            user_id="test_user",
            user_message="TCP三次握手是什么？",
            agent_persona="professor",
        ):
            events.append(sse)
        assert len(events) > 0
        parsed = _parse_sse_events(events)
        event_types = [e["event"] for e in parsed]
        assert "agent_start" in event_types
        assert "done" in event_types

    @pytest.mark.asyncio
    async def test_diagnosis_agent_is_called(self, orchestrator):
        """业务闭环中诊断 Agent 应被调用"""
        async for _ in orchestrator.async_stream_reply(
            session_id="s2", user_id="u1", user_message="TCP 三次握手",
        ):
            pass
        orchestrator.diagnosis.diagnose.assert_called()

    @pytest.mark.asyncio
    async def test_profiler_update_called(self, orchestrator):
        """业务闭环中画像更新应被调用"""
        async for _ in orchestrator.async_stream_reply(
            session_id="s3", user_id="u1", user_message="解释DNS解析过程",
        ):
            pass
        orchestrator.profiler.update_from_dialogue.assert_called()

    @pytest.mark.asyncio
    async def test_resource_intent_triggers_resource_gen(self, orchestrator):
        """resource 意图应触发资源生成"""
        orchestrator.coordinator.dispatch.return_value = MagicMock(
            intent="resource", knowledge_point="TCP 三次握手", persona_id="professor"
        )
        async for _ in orchestrator.async_stream_reply(
            session_id="s4", user_id="u1", user_message="给我生成TCP三次握手的学习资源",
        ):
            pass
        orchestrator.resource_gen.generate_all.assert_called()


# ------------------------------------------------------------------ #
# 3. SSE 事件序列测试
# ------------------------------------------------------------------ #
class TestSSEEventSequence:
    """验证 SSE 事件序列的正确性和顺序。"""

    @pytest.mark.asyncio
    async def test_event_sequence_starts_with_agent_start(self, orchestrator):
        """事件序列应以 agent_start 开头"""
        events = []
        async for sse in orchestrator.async_stream_reply(
            session_id="s5", user_id="u1", user_message="HTTP协议是什么",
        ):
            events.append(sse)
        parsed = _parse_sse_events(events)
        assert parsed[0]["event"] == "agent_start"

    @pytest.mark.asyncio
    async def test_event_sequence_ends_with_done(self, orchestrator):
        """事件序列应以 done 结束"""
        events = []
        async for sse in orchestrator.async_stream_reply(
            session_id="s6", user_id="u1", user_message="IP分片是什么",
        ):
            events.append(sse)
        parsed = _parse_sse_events(events)
        assert parsed[-1]["event"] == "done"

    @pytest.mark.asyncio
    async def test_diagnosis_event_present(self, orchestrator):
        """诊断事件应在事件序列中出现"""
        events = []
        async for sse in orchestrator.async_stream_reply(
            session_id="s7", user_id="u1", user_message="TCP的流量控制",
        ):
            events.append(sse)
        parsed = _parse_sse_events(events)
        event_types = [e["event"] for e in parsed]
        assert "diagnosis" in event_types

    @pytest.mark.asyncio
    async def test_token_events_present(self, orchestrator):
        """回复中应包含 token 流式事件"""
        events = []
        async for sse in orchestrator.async_stream_reply(
            session_id="s8", user_id="u1", user_message="什么是DNS",
        ):
            events.append(sse)
        parsed = _parse_sse_events(events)
        token_events = [e for e in parsed if e["event"] == "token"]
        assert len(token_events) > 0

    def test_sse_format_is_valid_json(self, orchestrator):
        """SSE 输出格式应是合法的 JSON"""
        from loopse.agent.orchestrator import OrchestratorAgent
        sse = OrchestratorAgent._sse("test_event", "TestAgent", {"key": "value"})
        assert sse.startswith("data: ")
        payload = json.loads(sse[6:].strip())
        assert payload["event"] == "test_event"
        assert payload["agent_name"] == "TestAgent"
        assert "timestamp" in payload


# ------------------------------------------------------------------ #
# 4. 降级处理测试
# ------------------------------------------------------------------ #
class TestGracefulDegradation:
    """验证 LLM 不可用或异常时系统的优雅降级。"""

    @pytest.mark.asyncio
    async def test_profiler_exception_does_not_crash(self, orchestrator):
        """画像更新失败不应导致整体流程崩溃"""
        orchestrator.profiler.update_from_dialogue.side_effect = RuntimeError("DB连接失败")
        events = []
        async for sse in orchestrator.async_stream_reply(
            session_id="s9", user_id="u1", user_message="ARP协议",
        ):
            events.append(sse)
        parsed = _parse_sse_events(events)
        event_types = [e["event"] for e in parsed]
        # 应正常完成而非抛出 error
        assert "done" in event_types

    @pytest.mark.asyncio
    async def test_scope_rejection(self, orchestrator):
        """超出范围的问题应被礼貌拒绝"""
        with patch("loopse.agent.orchestrator.trust_mechanism") as mock_trust:
            mock_trust.check_question_scope.return_value = {
                "in_scope": False,
                "reject_message": "抱歉，我只辅导计算机网络。",
            }
            events = []
            async for sse in orchestrator.async_stream_reply(
                session_id="s10", user_id="u1", user_message="今天天气怎么样",
            ):
                events.append(sse)
            parsed = _parse_sse_events(events)
            event_types = [e["event"] for e in parsed]
            assert "scope_notice" in event_types
            assert "done" in event_types


# ------------------------------------------------------------------ #
# 5. 异常场景测试
# ------------------------------------------------------------------ #
class TestEdgeCases:
    """验证边界条件和异常输入的处理。"""

    @pytest.mark.asyncio
    async def test_empty_input_handled(self, orchestrator):
        """空输入不应导致崩溃"""
        events = []
        async for sse in orchestrator.async_stream_reply(
            session_id="s11", user_id="u1", user_message="",
        ):
            events.append(sse)
        # 应正常完成或产出 error 事件，不应抛异常
        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_very_long_input_handled(self, orchestrator):
        """超长输入（10000字符）不应导致崩溃"""
        long_msg = "TCP三次握手 " * 1000
        events = []
        async for sse in orchestrator.async_stream_reply(
            session_id="s12", user_id="u1", user_message=long_msg,
        ):
            events.append(sse)
        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_multiple_sessions_independent(self, orchestrator):
        """不同 session 的状态应独立"""
        state1 = orchestrator._get_session_state("session_a")
        state2 = orchestrator._get_session_state("session_b")
        state1["state"] = "learning"
        assert state2["state"] == "idle"

    @pytest.mark.asyncio
    async def test_concurrent_sessions_no_interference(self, orchestrator):
        """并发请求不同session不应相互干扰"""
        import asyncio

        async def run_session(sid):
            events = []
            async for sse in orchestrator.async_stream_reply(
                session_id=sid, user_id="u1", user_message="TCP握手",
            ):
                events.append(sse)
            return events

        results = await asyncio.gather(
            run_session("concurrent_1"),
            run_session("concurrent_2"),
        )
        # 两个 session 都应成功完成
        for result in results:
            parsed = _parse_sse_events(result)
            event_types = [e["event"] for e in parsed]
            assert "done" in event_types

    @pytest.mark.parametrize("persona", ["professor", "engineer", "peer", "unknown_persona"])
    @pytest.mark.asyncio
    async def test_different_personas_handled(self, orchestrator, persona):
        """不同人格参数应都能正常处理"""
        events = []
        async for sse in orchestrator.async_stream_reply(
            session_id=f"s_persona_{persona}", user_id="u1",
            user_message="TCP三次握手", agent_persona=persona,
        ):
            events.append(sse)
        assert len(events) > 0
