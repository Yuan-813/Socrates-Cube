"""Multi-agent orchestrator with retrieval, diagnosis, planning and reflection."""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Any, AsyncGenerator

from ..core.llm_client import llm_client
from ..db.repositories import AgentLogRepository, LearningPathRepository, SessionRepository
from .cognitive_engine import CognitiveAgentMixin
from .diagnosis import DiagnosisAgent
from .path_planner import PathPlannerAgent
from .profiler import ProfilerAgent
from .resource_generator import ResourceGeneratorAgent
from .retriever import RetrieverAgent

logger = logging.getLogger(__name__)

_SIMULATION_KW = ["步骤", "过程", "握手", "挥手", "流程", "演示", "模拟"]
_PLANNING_KW = ["先学什么", "学习计划", "学习路径", "我该", "建议我", "学习顺序"]
_RESOURCE_KW = ["给我", "生成", "总结", "思维导图", "练习题", "代码示例", "代码", "例题"]


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(kw in text for kw in keywords)


class OrchestratorAgent(CognitiveAgentMixin):
    """Coordinates specialist agents and emits SSE events."""

    def __init__(self):
        self.retriever = RetrieverAgent()
        self.diagnosis = DiagnosisAgent()
        self.profiler = ProfilerAgent()
        self.resource_gen = ResourceGeneratorAgent()
        self.path_planner = PathPlannerAgent()

    async def async_stream_reply(
        self,
        session_id: str,
        user_id: str,
        user_message: str,
    ) -> AsyncGenerator[str, None]:
        started = time.time()
        trace = self.make_trace(user_message)

        try:
            yield self._sse("agent_start", "Orchestrator", {"message": "开始理解问题与规划协作流程"})
            history_text = self._get_history(session_id)
            intent = self._detect_intent(user_message)
            trace.add_step("intent", user_message[:120], intent, 0.82)

            yield self._sse("agent_start", "Retriever", {"message": "检索知识库、协议片段和知识图谱"})
            retrieval = self.use_tool(trace, "hybrid_retrieval", self.retriever.search_all, user_message, history_text, session_id)
            yield self._sse(
                "agent_end",
                "Retriever",
                {"message": f"检索完成，命中文档 {len(retrieval['docs'])} 条、图谱节点 {len(retrieval['graph_nodes'])} 个"},
            )
            self._log(session_id, "Retriever", "search_all", {"query": user_message}, retrieval)

            yield self._sse("agent_start", "Diagnosis", {"message": "执行三层错误诊断"})
            diag_result = self.use_tool(
                trace,
                "three_layer_diagnosis",
                self.diagnosis.diagnose,
                user_message,
                retrieval.get("docs", []) + retrieval.get("protocols", []),
                history_text,
            )
            trace.add_step(
                "diagnosis_policy",
                str(diag_result.get("surface_error") or "no_surface_error"),
                "socratic_guidance" if diag_result.get("is_correct") else "repair_misconception_first",
                diag_result.get("confidence", 0.65),
            )
            yield self._sse("diagnosis", "Diagnosis", diag_result)
            yield self._sse("agent_end", "Diagnosis", {"message": "诊断完成", "is_correct": diag_result.get("is_correct")})
            self._log(session_id, "Diagnosis", "diagnose", {"message": user_message}, diag_result)

            yield self._sse("agent_start", "Orchestrator", {"message": "生成可追问的主回复"})
            prompt = self._build_reply_prompt(user_message, retrieval, diag_result, history_text, trace.to_dict())
            full_reply = ""
            async for token in llm_client.async_stream_chat(prompt):
                full_reply += token
                yield self._sse("token", "Orchestrator", {"token": token})
            yield self._sse("agent_end", "Orchestrator", {"message": "主回复完成"})

            yield self._sse("agent_start", "Profiler", {"message": "更新学习画像"})
            try:
                profile = self.profiler.update_from_dialogue(user_id, user_message, full_reply, diag_result)
                yield self._sse(
                    "agent_end",
                    "Profiler",
                    {"message": "画像已更新", "weak_points": profile.get("weak_points", []), "turn_count": profile.get("turn_count")},
                )
            except Exception as exc:
                logger.warning("[Orchestrator] profile update skipped: %s", exc)
                profile = self.profiler.get_profile(user_id)
                yield self._sse("agent_end", "Profiler", {"message": "画像更新跳过"})

            if intent == "resource":
                yield self._sse("agent_start", "ResourceGenerator", {"message": "生成并持久化学习资源"})
                knowledge_point = self._extract_knowledge_point(user_message, retrieval)
                res_type = "code" if "代码" in user_message else "exercise" if "练习" in user_message or "例题" in user_message else "doc"
                resource = self.resource_gen.generate(res_type, knowledge_point, retrieval.get("docs"))
                yield self._sse("resource", "ResourceGenerator", resource)
                yield self._sse("agent_end", "ResourceGenerator", {"message": "资源生成完成"})

            if intent == "planning":
                yield self._sse("agent_start", "PathPlanner", {"message": "基于画像和图谱生成路径"})
                path = self.path_planner.plan(user_id, profile)
                try:
                    LearningPathRepository.save(path)
                except Exception as exc:
                    logger.warning("[Orchestrator] path persistence skipped: %s", exc)
                yield self._sse("path_update", "PathPlanner", path)
                yield self._sse("agent_end", "PathPlanner", {"message": f"路径规划完成，共 {len(path['nodes'])} 个节点"})

            trace.add_step(
                "final_reflection",
                f"reply_len={len(full_reply)}, intent={intent}",
                "complete",
                0.9 if full_reply else 0.4,
            )
            SessionRepository.append_message(session_id, "user", user_message)
            SessionRepository.append_message(session_id, "assistant", full_reply)
            self._log(session_id, "Orchestrator", "agent_trace", {"message": user_message}, trace.to_dict())

            yield self._sse(
                "done",
                "Orchestrator",
                {"session_id": session_id, "total_time_ms": int((time.time() - started) * 1000), "trace": trace.to_dict()},
            )

        except Exception as exc:
            logger.exception("[Orchestrator] fatal error: %s", exc)
            yield self._sse("error", "Orchestrator", {"error": str(exc)})

    @staticmethod
    def _sse(event: str, agent_name: str, data: Any) -> str:
        payload = {
            "event": event,
            "agent_name": agent_name,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        return f"data: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"

    @staticmethod
    def _get_history(session_id: str) -> str:
        try:
            session = SessionRepository.get_or_create(session_id=session_id)
            recent = session.get("messages", [])[-8:]
            return "\n".join(f"{m.get('role')}: {m.get('content', '')[:160]}" for m in recent)
        except Exception:
            return ""

    @staticmethod
    def _log(session_id: str, agent_name: str, action: str, input_state: Any, result: Any) -> None:
        try:
            AgentLogRepository.write(session_id, agent_name, action, input_state, result)
        except Exception as exc:
            logger.debug("[Orchestrator] log skipped: %s", exc)

    @staticmethod
    def _detect_intent(message: str) -> str:
        if _contains_any(message, _PLANNING_KW):
            return "planning"
        if _contains_any(message, _RESOURCE_KW):
            return "resource"
        if _contains_any(message, _SIMULATION_KW):
            return "simulation"
        return "qa"

    @staticmethod
    def _extract_knowledge_point(message: str, retrieval: dict) -> str:
        nodes = retrieval.get("graph_nodes", [])
        if nodes:
            return nodes[0].get("name", "TCP 三次握手")
        for token in ["TCP 三次握手", "TCP 四次挥手", "滑动窗口", "HTTP", "DNS", "子网划分"]:
            if token.lower() in message.lower():
                return token
        return "TCP 三次握手"

    @staticmethod
    def _build_reply_prompt(
        user_message: str,
        retrieval: dict,
        diag: dict,
        history: str,
        trace: dict,
    ) -> str:
        docs_text = "\n".join(
            d.get("document", d.get("content", d.get("text", "")))[:240]
            for d in (retrieval.get("docs", []) + retrieval.get("protocols", []))[:4]
        )
        diag_hint = ""
        if not diag.get("is_correct", True):
            diag_hint = (
                f"\n诊断提示：学生可能存在错误：{diag.get('surface_error', '')}。"
                f"干预建议：{diag.get('intervention_suggestion', '')}"
            )
        return (
            "你是一个高级苏格拉底式计算机网络助教智能体。"
            "你需要结合检索证据、错误诊断、学习画像和自己的推理轨迹来回答。"
            "回答时先给学生可操作的理解框架，再用一到两个追问推动思考，避免只甩结论。\n\n"
            f"参考知识：\n{docs_text or '无'}\n"
            f"{diag_hint}\n"
            f"对话历史：\n{history or '无'}\n"
            f"智能体推理轨迹：{json.dumps(trace, ensure_ascii=False)[:1200]}\n\n"
            f"学生问题：{user_message}\n"
            "请用中文回答，结构清晰、语气友好。"
        )
