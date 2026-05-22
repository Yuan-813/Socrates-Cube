"""
Orchestrator Agent — 总调度，基于规则+LLM的混合调度
Phase 2版本：规则优先，LLM做兜底判断
"""
import json
import time
from pathlib import Path
from typing import AsyncIterator, Optional

from src.loopse.agent.coordinator import AgentCoordinator, SessionPhase
from src.loopse.agent.profiler import profiler_agent
from src.loopse.agent.retriever import retriever_agent
from src.loopse.agent.diagnosis import diagnosis_agent
from src.loopse.core.llm_client import llm_client
from src.loopse.db.repositories import (
    ProfileRepository, SessionRepository, AgentLogRepository,
)

ROUTE_PROMPT = Path("config/prompts/orchestrator/route.txt").read_text(encoding="utf-8") \
    if Path("config/prompts/orchestrator/route.txt").exists() else ""

SIMULATION_KEYWORDS = ["步骤", "过程", "握手", "挥手", "流程", "怎么建立", "怎么断开"]
PLANNING_KEYWORDS = ["先学什么", "学习计划", "学习路径", "我该从", "建议我"]
RESOURCE_KEYWORDS = ["给我", "生成", "总结", "思维导图", "练习题", "代码示例"]


class OrchestratorAgent(AgentCoordinator):

    def _determine_phase(self, turn_count: int, profile_completeness: float,
                         user_message: str) -> SessionPhase:
        if turn_count < 3 or profile_completeness < 0.3:
            return SessionPhase.PROFILING
        if any(kw in user_message for kw in SIMULATION_KEYWORDS):
            return SessionPhase.SIMULATING
        if any(kw in user_message for kw in PLANNING_KEYWORDS):
            return SessionPhase.PLANNING
        return SessionPhase.LEARNING

    def _build_agent_chain(self, phase: SessionPhase, user_message: str) -> list:
        chains = {
            SessionPhase.PROFILING: ["profiler", "retriever"],
            SessionPhase.SIMULATING: ["retriever", "simulator"],
            SessionPhase.PLANNING: ["profiler", "planner"],
            SessionPhase.LEARNING: ["retriever"],
            SessionPhase.DIAGNOSING: ["retriever", "diagnosis", "profiler"],
        }
        return chains.get(phase, ["retriever"])

    def _calc_profile_completeness(self, profile: Optional[dict]) -> float:
        if not profile:
            return 0.0
        dims = [
            "network_layer_cognition", "protocol_flow_memory",
            "packet_format_understanding", "protocol_relationship",
            "fault_diagnosis_logic", "hands_on_ability",
            "cognitive_style", "misconception_patterns",
        ]
        filled = sum(1 for d in dims if profile.get(d) is not None)
        return filled / len(dims)

    async def process_message(
        self,
        session_id: str,
        user_id: str,
        user_message: str,
        turn_count: int = 0,
    ) -> AsyncIterator[str]:
        """核心处理入口，返回SSE事件流"""
        start = time.time()

        # 获取画像
        profile = ProfileRepository.get(user_id)
        completeness = self._calc_profile_completeness(profile)

        # 确定阶段
        phase = self._determine_phase(turn_count, completeness, user_message)
        agent_chain = self._build_agent_chain(phase, user_message)

        # 发送调度开始事件
        yield self._sse_event("agent_start", "Orchestrator", {
            "phase": phase,
            "agent_chain": agent_chain,
            "profile_completeness": completeness,
        })

        # 写调度日志
        await AgentLogRepository.write(
            session_id=session_id,
            agent_name="Orchestrator",
            action="route_message",
            input_state={"user_message": user_message, "turn_count": turn_count,
                         "phase": phase, "profile_completeness": completeness},
            output_state={"agent_chain": agent_chain},
            duration_ms=int((time.time() - start) * 1000),
        )

        # 执行Agent链
        context = {
            "user_message": user_message,
            "profile": profile or {},
            "retrieval_context": [],
            "diagnosis_result": None,
        }

        for agent_name in agent_chain:
            yield self._sse_event("agent_start", agent_name, {"status": "running"})
            agent_start = time.time()

            if agent_name == "profiler":
                updated_profile = profiler_agent.update_profile(
                    user_id, user_message, profile
                )
                context["profile"] = updated_profile
                profile = updated_profile
                yield self._sse_event("profile_update", "Profiler", updated_profile)

            elif agent_name == "retriever":
                results = retriever_agent.search_all(user_message)
                context["retrieval_context"] = results.get("knowledge", [])
                yield self._sse_event("tool_call", "Retriever", {
                    "retrieved_count": len(context["retrieval_context"]),
                    "sources": [r.get("metadata", {}).get("source", "未知")
                                for r in context["retrieval_context"][:3]],
                })

            elif agent_name == "diagnosis":
                ref_text = "\n".join([
                    r["content"] for r in context["retrieval_context"][:2]
                ])
                result = diagnosis_agent.diagnose(
                    user_message, ref_text, profile
                )
                context["diagnosis_result"] = result
                yield self._sse_event("diagnosis", "Diagnosis", result)

            elif agent_name == "simulator":
                yield self._sse_event("agent_end", "Simulator", {"status": "skipped_phase2"})

            elif agent_name == "planner":
                yield self._sse_event("agent_end", "Planner", {"status": "skipped_phase2"})

            await AgentLogRepository.write(
                session_id=session_id,
                agent_name=agent_name.capitalize(),
                action="execute",
                input_state={"input": context["user_message"]},
                output_state={"status": "done"},
                duration_ms=int((time.time() - agent_start) * 1000),
            )
            yield self._sse_event("agent_end", agent_name, {"status": "done"})

        # 生成最终回复（流式）
        system_prompt = self._build_system_prompt(context)
        yield self._sse_event("agent_start", "LLM", {"status": "streaming"})

        async for token in llm_client.async_stream_chat(
            user_message=user_message,
            system_prompt=system_prompt,
        ):
            yield self._sse_event("token", "Orchestrator", token)

        yield self._sse_event("agent_end", "Orchestrator", {"status": "done"})
        yield self._sse_event("done", "Orchestrator", {})

    def _build_system_prompt(self, context: dict) -> str:
        refs = "\n".join([
            f"[来源:{r.get('metadata', {}).get('source', '未知')}] {r['content']}"
            for r in context["retrieval_context"][:3]
        ])
        diagnosis_info = ""
        if context.get("diagnosis_result") and not context["diagnosis_result"].get("is_correct", True):
            d = context["diagnosis_result"]
            diagnosis_info = f"\n\n⚠️ 检测到认知错误：{d['surface_error'].get('error_description', '')}"

        return f"""你是计算机网络智能学习教练。
基于以下知识库内容回答，必须引用知识点来源：
{refs}
{diagnosis_info}
要求：回答清晰、结构化，适合本科生水平。如超出知识库范围，请说明"这超出了当前知识库范围"。"""

    @staticmethod
    def _sse_event(event: str, agent_name: str, data) -> str:
        from datetime import datetime
        payload = {
            "event": event,
            "agent_name": agent_name,
            "data": data if isinstance(data, str) else json.dumps(data, ensure_ascii=False),
            "timestamp": datetime.now().isoformat(),
        }
        return json.dumps(payload, ensure_ascii=False)


orchestrator = OrchestratorAgent()
