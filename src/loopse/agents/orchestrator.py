"""
OrchestratorAgent：主调度代理
负责：意图识别 → 调度各子代理 → SSE 流式事件输出
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from ..core.llm_client import llm_client
from ..db.repositories import AgentLogRepository, SessionRepository
from .diagnosis import DiagnosisAgent
from .path_planner import PathPlannerAgent
from .profiler import ProfilerAgent
from .resource_generator import ResourceGeneratorAgent
from .retriever import RetrieverAgent

logger = logging.getLogger(__name__)

# 意图识别关键词
_SIMULATION_KW = ["步骤", "过程", "握手", "挥手", "流程", "演示", "模拟"]
_PLANNING_KW = ["先学什么", "学习计划", "学习路径", "我该从", "建议我", "学习顺序"]
_RESOURCE_KW = ["给我", "生成", "总结", "思维导图", "练习题", "代码示例", "代码", "例题"]


def _contains_any(text: str, keywords: List[str]) -> bool:
    return any(kw in text for kw in keywords)


class OrchestratorAgent:
    """
    主调度代理：
    - 解析用户意图
    - 按需调用子代理（Retriever → Diagnosis → Profiler → Resource/PathPlanner）
    - 通过 async_stream_reply 输出 SSE 事件流
    """

    def __init__(self):
        self.retriever = RetrieverAgent()
        self.diagnosis = DiagnosisAgent()
        self.profiler = ProfilerAgent()
        self.resource_gen = ResourceGeneratorAgent()
        self.path_planner = PathPlannerAgent()

    # ------------------------------------------------------------------
    # 主入口：异步 SSE 生成器
    # ------------------------------------------------------------------

    async def async_stream_reply(
        self,
        session_id: str,
        user_id: str,
        user_message: str,
    ) -> AsyncGenerator[str, None]:
        """
        异步生成器，产出 SSE 格式字符串（data: {...}\n\n）。

        事件类型：
        - agent_start / agent_end
        - tool_call
        - token
        - diagnosis
        - resource
        - path_update
        - done / error
        """
        start_ts = datetime.utcnow().isoformat()

        try:
            # --- Orchestrator 启动 ---
            yield self._sse("agent_start", "Orchestrator", {"message": "开始分析您的问题..."})

            # --- 获取历史对话 ---
            history_text = self._get_history(session_id)

            # --- Retriever ---
            yield self._sse("agent_start", "Retriever", {"message": "正在检索相关知识..."})
            yield self._sse("tool_call", "Retriever", {"tool": "vector_search", "query": user_message[:40]})
            retrieval = self.retriever.search_all(user_message, history_text, session_id)
            yield self._sse("agent_end", "Retriever", {
                "message": f"检索完成，找到 {len(retrieval['docs'])} 条相关文档"
            })
            self._log(session_id, "Retriever", "search_all", retrieval)

            # --- Diagnosis ---
            yield self._sse("agent_start", "Diagnosis", {"message": "正在分析您的理解情况..."})
            diag_result = self.diagnosis.diagnose(
                user_message,
                retrieval.get("docs", []) + retrieval.get("protocols", []),
                history_text,
            )
            yield self._sse("diagnosis", "Diagnosis", diag_result)
            yield self._sse("agent_end", "Diagnosis", {
                "is_correct": diag_result["is_correct"],
                "message": "诊断完成" if diag_result["is_correct"] else f"发现问题：{diag_result.get('surface_error', '')}"
            })
            self._log(session_id, "Diagnosis", "diagnose", diag_result)

            # --- 生成主回复（流式 token）---
            yield self._sse("agent_start", "Orchestrator", {"message": "正在生成回复..."})
            reply_prompt = self._build_reply_prompt(user_message, retrieval, diag_result, history_text)
            full_reply = ""
            async for token in llm_client.async_stream_chat(reply_prompt):
                full_reply += token
                yield self._sse("token", "Orchestrator", {"token": token})

            yield self._sse("agent_end", "Orchestrator", {"message": "回复生成完毕"})

            # --- Profiler（后台更新画像，不阻塞）---
            yield self._sse("agent_start", "Profiler", {"message": "更新学习画像..."})
            try:
                updated_profile = self.profiler.update_from_dialogue(
                    user_id, user_message, full_reply, diag_result
                )
                yield self._sse("agent_end", "Profiler", {
                    "message": "画像已更新",
                    "profile_summary": {k: updated_profile.get(k) for k in ["weak_points", "turn_count"]}
                })
            except Exception as pe:
                logger.warning("[Orchestrator] Profiler 更新失败: %s", pe)
                yield self._sse("agent_end", "Profiler", {"message": "画像更新跳过"})

            # --- 按意图触发额外代理 ---
            intent = self._detect_intent(user_message)

            if intent == "resource":
                yield self._sse("agent_start", "ResourceGenerator", {"message": "正在生成学习资源..."})
                knowledge_point = self._extract_knowledge_point(user_message, retrieval)
                res_type = "code" if "代码" in user_message else "exercise" if "练习" in user_message else "doc"
                try:
                    resource = self.resource_gen.generate(res_type, knowledge_point, retrieval.get("docs"))
                    yield self._sse("resource", "ResourceGenerator", resource)
                    yield self._sse("agent_end", "ResourceGenerator", {"message": "资源生成完毕"})
                except Exception as re_err:
                    logger.warning("[Orchestrator] 资源生成失败: %s", re_err)
                    yield self._sse("agent_end", "ResourceGenerator", {"message": "资源生成失败"})

            elif intent == "planning":
                yield self._sse("agent_start", "PathPlanner", {"message": "正在规划学习路径..."})
                try:
                    profile = self.profiler.get_profile(user_id)
                    path = self.path_planner.plan(user_id, profile)
                    yield self._sse("path_update", "PathPlanner", path)
                    yield self._sse("agent_end", "PathPlanner", {
                        "message": f"路径规划完毕，共 {len(path['nodes'])} 个节点"
                    })
                except Exception as pp_err:
                    logger.warning("[Orchestrator] 路径规划失败: %s", pp_err)
                    yield self._sse("agent_end", "PathPlanner", {"message": "路径规划失败"})

            # --- 保存对话 ---
            SessionRepository.append_message(session_id, {
                "role": "user",
                "content": user_message,
                "timestamp": start_ts,
            })
            SessionRepository.append_message(session_id, {
                "role": "assistant",
                "content": full_reply,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # --- 完成 ---
            yield self._sse("done", "Orchestrator", {
                "session_id": session_id,
                "total_time_ms": int((time.time() * 1000) - _ts_to_ms(start_ts)),
            })

        except Exception as e:
            logger.exception("[Orchestrator] 严重错误: %s", e)
            yield self._sse("error", "Orchestrator", {"error": str(e)})

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------

    @staticmethod
    def _sse(event: str, agent_name: str, data: Any) -> str:
        payload = {
            "event": event,
            "agent_name": agent_name,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    @staticmethod
    def _get_history(session_id: str) -> str:
        try:
            from ..db.repositories import SessionRepository
            session = SessionRepository.get_or_create(session_id)
            if session and session.get("messages"):
                msgs = session["messages"]
                recent = msgs[-6:] if len(msgs) > 6 else msgs
                return "\n".join(f"{m['role']}: {m['content'][:100]}" for m in recent)
        except Exception:
            pass
        return ""

    @staticmethod
    def _log(session_id: str, agent_name: str, action: str, result: Any) -> None:
        try:
            AgentLogRepository.write(session_id, agent_name, action, "completed",
                                     json.dumps(result, ensure_ascii=False)[:500])
        except Exception:
            pass

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
    def _extract_knowledge_point(message: str, retrieval: Dict) -> str:
        """从检索结果中提取最相关的知识点名称"""
        nodes = retrieval.get("graph_nodes", [])
        if nodes:
            return nodes[0].get("name", "TCP协议")
        return "TCP协议"

    @staticmethod
    def _build_reply_prompt(
        user_message: str,
        retrieval: Dict,
        diag: Dict,
        history: str,
    ) -> str:
        docs_text = "\n".join(
            d.get("document", "")[:200]
            for d in (retrieval.get("docs", []) + retrieval.get("protocols", []))[:3]
        )
        diag_hint = ""
        if not diag.get("is_correct"):
            diag_hint = (
                f"\n【诊断提示】学生存在错误：{diag.get('surface_error', '')}。"
                f"建议：{diag.get('intervention_suggestion', '')}"
            )

        return (
            f"你是苏格拉底AI助教，专注于《计算机网络》课程辅导（谢希仁第8版）。"
            f"请用启发式提问引导学生思考，而非直接给出答案。\n\n"
            f"参考知识：\n{docs_text or '（无）'}\n"
            f"{diag_hint}\n"
            f"对话历史：\n{history or '（无）'}\n\n"
            f"学生问题：{user_message}\n\n"
            "请用中文回答，语气友好，适当运用苏格拉底提问法。"
        )


def _ts_to_ms(iso_str: str) -> int:
    try:
        from datetime import timezone
        dt = datetime.fromisoformat(iso_str).replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except Exception:
        return int(time.time() * 1000)
