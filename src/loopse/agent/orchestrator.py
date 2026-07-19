"""多智能体编排器（Orchestrator Agent）。

本模块是 Socrates-Cube 的中央协调器，负责：

1. **意图路由**：调用 AgentCoordinator 识别用户意图（qa / resource /
   planning / simulation），决定本轮需要激活哪些下游 Agent。
2. **Agent 调度**：按状态机依次驱动 Retriever → Diagnosis → Profiler
   → ResourceGenerator → PathPlanner，各 Agent 执行结果通过 SSE
   事件实时推送到前端。
3. **流式回复**：以苏格拉底式追问风格流式输出回复文本，并附加
   参考来源标注和不确定性声明。
4. **状态机管理**：维护 idle / learning / consolidation 三态，
   学习阶段累计 5 轮后自动触发 Challenger 巩固检验。

SSE 事件类型：agent_start, agent_end, tool_call, token,
diagnosis, resource, path_update, state_change, done, error。
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator

from ..core.llm_client import llm_client, get_client_for_persona, get_persona_system_prompt
from ..core.trust_mechanism import trust_mechanism
from ..db.repositories import AgentLogRepository, LearningPathRepository, SessionRepository
from .cognitive_engine import CognitiveAgentMixin
from .challenger import ChallengerAgent
from .coordinator import AgentCoordinator
from .diagnosis import DiagnosisAgent
from .path_planner import PathPlannerAgent
from .profiler import ProfilerAgent
from .resource_generator import ResourceGeneratorAgent
from .retriever import RetrieverAgent
from ..kb.misconception_registry import misconception_registry
from .intervention_selector import intervention_selector
from ..kb.knowledge_graph import knowledge_graph as _kg

# 加载 AI 人格配置
_PERSONAS_PATH = Path("config/agent_personas.json")
_PERSONAS: dict[str, dict] = {}
try:
    _PERSONAS = json.loads(_PERSONAS_PATH.read_text(encoding="utf-8"))
except Exception:
    pass

# ── RL 方向2: HMARL 元控制器（软依赖）──
try:
    from ..rl.hmarl import hmarl_controller as _hmarl
    _RL_HMARL_AVAILABLE = True
except Exception:
    _RL_HMARL_AVAILABLE = False
    _hmarl = None

logger = logging.getLogger(__name__)


class OrchestratorAgent(CognitiveAgentMixin):
    """多智能体编排器。

    统一调度 7 个专业 Agent，管理对话状态机，并通过 SSE 流式推送
    各阶段事件。在 LLM 超时或 Agent 异常时自动降级，保证主流程
    不中断。
    """

    # State machine: conversation phases
    STATE_IDLE = "idle"
    STATE_LEARNING = "learning"
    STATE_CONSOLIDATION = "consolidation"  # Trigger Challenger after learning
    STATE_PLANNING = "planning"  # Trigger path after 3 knowledge points

    def __init__(self):
        self.coordinator = AgentCoordinator()
        self.retriever = RetrieverAgent()
        self.diagnosis = DiagnosisAgent()
        self.profiler = ProfilerAgent()
        self.resource_gen = ResourceGeneratorAgent()
        self.path_planner = PathPlannerAgent()
        self.challenger = ChallengerAgent()
        self._session_states: dict[str, dict[str, Any]] = {}
        self._completed_kp_count = 0  # Track completed knowledge points

    @staticmethod
    def _get_persona_prompt(persona_id: str) -> str:
        """Returns the persona prompt prefix for the given persona_id."""
        persona = _PERSONAS.get(persona_id, _PERSONAS.get("professor", {}))
        return persona.get("prompt_prefix", "")

    @staticmethod
    def _match_kg_nodes(text: str, max_hits: int = 6) -> list[str]:
        """Scan text and return matching KG node IDs (up to max_hits).

        Uses simple substring matching against node names — fast, no extra LLM call.
        """
        hits: list[str] = []
        text_lower = text.lower()
        for node in _kg.get_all_nodes():
            name_lower = node.name.lower()
            # Match if node name (or key alias) appears in text
            if name_lower in text_lower or node.id in text:
                hits.append(node.id)
                if len(hits) >= max_hits:
                    break
        return hits

    async def async_stream_reply(
        self,
        session_id: str,
        user_id: str,
        user_message: str,
        agent_persona: str = "professor",
    ) -> AsyncGenerator[str, None]:
        started = time.time()
        trace = self.make_trace(user_message)

        try:
            yield self._sse("agent_start", "Orchestrator", {"message": "开始理解问题与规划协作流程"})

            # 人格路由：根据 persona 选择不同 LLM 客户端
            _active_client = get_client_for_persona(agent_persona)
            _persona_sys_prompt = get_persona_system_prompt(agent_persona)
            yield self._sse("persona_set", "Orchestrator", {
                "persona": agent_persona,
                "model": getattr(_active_client, '_model', 'spark'),
            })

            scope = trust_mechanism.check_question_scope(user_message)
            if not scope.get("in_scope"):
                reject_msg = scope.get("reject_message") or (
                    "抱歉，我专注于计算机网络课程辅导。"
                    "你可以问我关于 TCP/IP、DNS、路由协议等计算机网络相关的问题。"
                )
                yield self._sse(
                    "scope_notice",
                    "TrustMechanism",
                    {"title": "超出服务范围", "description": reject_msg},
                )
                yield self._sse("token", "Orchestrator", {"token": reject_msg})
                yield self._sse("done", "Orchestrator", {"message": "scope_rejected"})
                self._log(session_id, "TrustMechanism", "scope_check", {"message": user_message}, scope)
                return

            history_text = self._get_history(session_id)

            # 获取长期记忆上下文（每个人格独立）
            try:
                from .memory_manager import memory_manager
                _memory_ctx = memory_manager.build_context_prompt(
                    user_id, persona=agent_persona, max_memories=5
                )
                if _memory_ctx:
                    _persona_sys_prompt = _persona_sys_prompt + "\n\n" + _memory_ctx
            except Exception:
                pass  # 记忆注入失败不影响主流程

            # 获取当前会话的 persona_id（从用户 profile 中读取）
            _profile_for_persona = self.profiler.get_profile(user_id)
            current_persona_id = _profile_for_persona.get("persona_id", "professor")


            # ── HMARL 方向2: 元控制器决策 (每轮对话开始时执行) ──
            _pre_profile = self.profiler.get_profile(user_id)  # 更新前快照
            _hmarl_state = None
            _hmarl_action = None
            _hmarl_difficulty = 3  # 默认难度
            _hmarl_challenger_threshold = 5  # 默认触发阈値
            _hmarl_force_resource = False
            if _RL_HMARL_AVAILABLE and _hmarl is not None:
                try:
                    sess_tmp = self._get_session_state(session_id)
                    _hmarl_state = _hmarl.extract_state(
                        _pre_profile, sess_tmp, user_id=user_id
                    )
                    _hmarl_action = _hmarl.select_action(_hmarl_state)
                    _hmarl_difficulty = max(1, min(5, 3 + _hmarl_action.difficulty_delta))
                    _hmarl_challenger_threshold = _hmarl_action.challenger_threshold
                    _hmarl_force_resource = _hmarl_action.force_resource
                    logger.debug(
                        "[HMARL] 元控制器决策 state=%d action=%s",
                        _hmarl_state, _hmarl_action.description,
                    )
                    yield self._sse("agent_start", "HMARL-MetaController", {
                        "message": f"HMARL元控制器决策: {_hmarl_action.description}",
                        "state_id": _hmarl_state,
                        "action": _hmarl_action.to_dict(),
                    })
                except Exception as _hmarl_exc:
                    logger.warning("[HMARL] 元控制器预处理失败: %s", _hmarl_exc)

            yield self._sse("agent_start", "Retriever", {"message": "检索知识库、协议片段和知识图谱"})
            yield self._sse("tool_call", "Retriever", {"tool_name": "hybrid_retrieval", "input": user_message[:120], "status": "calling"})
            retrieval = self.use_tool(trace, "hybrid_retrieval", self.retriever.search_all, user_message, history_text, session_id)
            yield self._sse("tool_call", "Retriever", {"tool_name": "hybrid_retrieval", "status": "completed", "result_count": len(retrieval.get("docs", []))})
            yield self._sse(
                "agent_end",
                "Retriever",
                {"message": f"检索完成，命中文档 {len(retrieval['docs'])} 条、图谱节点 {len(retrieval['graph_nodes'])} 个"},
            )
            self._log(session_id, "Retriever", "search_all", {"query": user_message}, retrieval)

            dispatch_plan = self.coordinator.dispatch(user_message, retrieval, persona_id=current_persona_id)
            intent = dispatch_plan.intent
            trace.add_step("intent", user_message[:120], intent, 0.82)

            yield self._sse("agent_start", "Diagnosis", {"message": "执行三层错误诊断"})
            yield self._sse("tool_call", "Diagnosis", {"tool_name": "three_layer_diagnosis", "input": user_message[:120], "status": "calling"})
            diag_result = self.use_tool(
                trace,
                "three_layer_diagnosis",
                self.diagnosis.diagnose,
                user_message,
                retrieval.get("docs", []) + retrieval.get("protocols", []),
                history_text,
            )
            yield self._sse("tool_call", "Diagnosis", {"tool_name": "three_layer_diagnosis", "status": "completed", "is_correct": diag_result.get("is_correct")})
            trace.add_step(
                "diagnosis_policy",
                str(diag_result.get("surface_error") or "no_surface_error"),
                "socratic_guidance" if diag_result.get("is_correct") else "repair_misconception_first",
                diag_result.get("confidence", 0.65),
            )
            yield self._sse("diagnosis", "Diagnosis", diag_result)
            yield self._sse("agent_end", "Diagnosis", {"message": "诊断完成", "is_correct": diag_result.get("is_correct")})
            self._log(session_id, "Diagnosis", "diagnose", {"message": user_message}, diag_result)

            # --- Intervention Layer: 干预策略推荐 ---
            if not diag_result.get("is_correct", True):
                try:
                    _mc = misconception_registry.get_by_id(diag_result.get("misconception_id", ""))
                    if not _mc:
                        _mc = misconception_registry.match_from_diagnosis(
                            diag_result.get("error_type", ""),
                            diag_result.get("surface_error", ""),
                        )
                    _interventions = intervention_selector.select(
                        misconception=_mc,
                        error_type=diag_result.get("error_type", "conceptual"),
                        profile={},
                        diagnosis_result=diag_result,
                    )
                    if _interventions:
                        yield self._sse("intervention_suggested", "InterventionSelector", {
                            "misconception_id": diag_result.get("misconception_id"),
                            "recommendations": [i.to_dict() for i in _interventions],
                        })
                except Exception as _exc:
                    logger.warning("[Orchestrator] intervention selection skipped: %s", _exc)

            yield self._sse("agent_start", "Orchestrator", {"message": "生成可追问的主回复"})
            prompt = self._build_reply_prompt(
                user_message, retrieval, diag_result, history_text, trace.to_dict(),
                persona_id=agent_persona,
            )
            full_reply = ""

            # 主流 LLM 流式生成，如果返回了错误提示则自动用 fallback
            # sentinel 匹配 llm_client.py 中 yield 的实际错误字符串
            _error_sentinel = "\u62b1\u6b49\uff0c\u6d41\u5f0f\u751f\u6210\u4e2d\u65ad"
            async for token in _active_client.async_stream_chat(
                prompt, system_prompt=_persona_sys_prompt
            ):
                full_reply += token
                yield self._sse("token", "Orchestrator", {"token": token})

            # 如果主力客户端返回了错误提示，尝试用 fallback 重新生成
            if _error_sentinel in full_reply or not full_reply.strip():
                from ..core.llm_client import openai_compat_client as _fb_client
                if _fb_client._available and _fb_client is not _active_client:
                    logger.warning(
                        "[Orchestrator] 主力 LLM 返回错误或空内容，自动降级到 OpenAI-compat (model=%s)",
                        _fb_client._model
                    )
                    yield self._sse("token", "Orchestrator", {"token": "", "fallback": True})
                    full_reply = ""
                    async for token in _fb_client.async_stream_chat(
                        prompt, system_prompt=_persona_sys_prompt
                    ):
                        full_reply += token
                        yield self._sse("token", "Orchestrator", {"token": token})

            # 可信机制：溯源标注 + 不确定性声明
            sources = retrieval.get("docs", []) + retrieval.get("protocols", [])
            confidence = diag_result.get("confidence", 0.7)
            trust_result = trust_mechanism.verify_response(full_reply, sources, confidence)
            if trust_result.get("has_sources") or trust_result.get("has_uncertainty"):
                full_reply = trust_result["content"]
                yield self._sse("token", "Orchestrator", {"token": "", "trust_applied": True})

            yield self._sse("agent_end", "Orchestrator", {"message": "主回复完成"})

            # ── KG 节点关联：从回答中提取关键概念，映射到知识图谱节点 ──
            try:
                kg_hits = self._match_kg_nodes(user_message + " " + full_reply)
                if kg_hits:
                    yield self._sse("kg_nodes", "Orchestrator", {"node_ids": kg_hits})
            except Exception as _kg_exc:
                logger.debug("[Orchestrator] KG node matching skipped: %s", _kg_exc)

            yield self._sse("agent_start", "Profiler", {"message": "更新学习画像"})
            try:
                profile = self.profiler.update_from_dialogue(user_id, user_message, full_reply, diag_result)
                self._log(session_id, "Profiler", "update_from_dialogue", {"user_message": user_message, "diagnosis": diag_result}, profile)
                yield self._sse(
                    "agent_end",
                    "Profiler",
                    {"message": "画像已更新", "weak_points": profile.get("weak_points", []), "turn_count": profile.get("turn_count")},
                )
            except Exception as exc:
                logger.warning("[Orchestrator] profile update skipped: %s", exc)
                profile = self.profiler.get_profile(user_id)
                self._log(session_id, "Profiler", "get_profile", {"user_id": user_id}, profile)
                yield self._sse("agent_end", "Profiler", {"message": "画像更新跳过"})

            # ── HMARL 方向2: 画像更新后计算全局奖励并更新Q表 ──
            if _RL_HMARL_AVAILABLE and _hmarl is not None and _hmarl_state is not None and _hmarl_action is not None:
                try:
                    _hmarl_reward = _hmarl.compute_global_reward(_pre_profile, profile, diag_result)
                    _hmarl_next_state = _hmarl.extract_state(profile, self._get_session_state(session_id), user_id=user_id)
                    _hmarl.step_update(_hmarl_state, _hmarl_action.action_id, _hmarl_reward, _hmarl_next_state)
                    # 记录诊断 Agent 局部奖励
                    _diag_local_r = _hmarl.compute_local_reward_diagnosis(diag_result)
                    _hmarl.record_local_reward("diagnosis", _diag_local_r)
                    # SSE 推送 HMARL 决策可视化数据
                    yield self._sse("rl_update", "HMARL-MetaController",
                                   _hmarl.to_sse_data(_hmarl_state, _hmarl_action, _hmarl_reward))
                except Exception as _rl_exc:
                    logger.warning("[HMARL] Q表更新失败: %s", _rl_exc)

            if intent in ("resource", "qa") or _hmarl_force_resource:
                has_error = not diag_result.get("is_correct", True)
                _difficulty = _hmarl_difficulty  # HMARL 调整后的难度
                if has_error and diag_result.get("misconception_id"):
                    # 诊断驱动：根据 ACU repair_strategies 选择针对性资源类型
                    yield self._sse("agent_start", "ResourceGenerator", {"message": "基于诊断结果生成针对性修复资源"})
                    resource_bundle = self.resource_gen.generate_from_diagnosis(
                        knowledge_point=dispatch_plan.knowledge_point,
                        diagnosis_result=diag_result,
                        profile=profile,
                        context_docs=retrieval.get("docs"),
                        difficulty=_difficulty,
                    )
                    self._log(session_id, "ResourceGenerator", "generate_from_diagnosis",
                              {"knowledge_point": dispatch_plan.knowledge_point, "misconception_id": diag_result.get("misconception_id"), "hmarl_difficulty": _difficulty},
                              resource_bundle)
                    generated_count = 0
                    for res_type, res in resource_bundle.get("resources", {}).items():
                        if res:
                            yield self._sse("resource", "ResourceGenerator", dict(res))
                            generated_count += 1
                    # LinUCB 本地奖励记录
                    if _RL_HMARL_AVAILABLE and _hmarl is not None:
                        try:
                            _res_local_r = _hmarl.compute_local_reward_resource(resource_bundle, profile)
                            _hmarl.record_local_reward("resource", _res_local_r)
                        except Exception:
                            pass
                    yield self._sse("agent_end", "ResourceGenerator", {
                        "message": f"诊断驱动资源生成完成，共 {generated_count} 份",
                        "strategy_reason": resource_bundle.get("strategy_reason", ""),
                        "diagnosis_driven": True,
                        "hmarl_difficulty": _difficulty,
                    })
                else:
                    # 无诊断错误时：生成全量五类资源
                    yield self._sse("agent_start", "ResourceGenerator", {"message": "生成并持久化五类学习资源（文档/练习/代码/思维导图/视频脚本）"})
                    resource_bundle = self.resource_gen.generate_all(
                        knowledge_point=dispatch_plan.knowledge_point,
                        context_docs=retrieval.get("docs"),
                        difficulty=_difficulty,
                    )
                    self._log(session_id, "ResourceGenerator", "generate_all", {"knowledge_point": dispatch_plan.knowledge_point, "hmarl_difficulty": _difficulty}, resource_bundle)
                    generated_count = 0
                    for res_type in ("doc", "exercise", "code", "mindmap", "script"):
                        res = resource_bundle.get(res_type)
                        if res:
                            yield self._sse("resource", "ResourceGenerator", dict(res))
                            generated_count += 1
                    yield self._sse("agent_end", "ResourceGenerator", {"message": f"五类资源生成完成，共 {generated_count} 份"})

            if intent == "planning":
                yield self._sse("agent_start", "PathPlanner", {"message": "基于诊断结果和知识图谱生成个性化路径"})
                # 将诊断识别的课程节点 ID 直接传入 Planner，实现诺断-图谱-路径闭环
                diag_kp_ids = diag_result.get("knowledge_node_ids", [])
                path = self.path_planner.plan(
                    user_id,
                    profile,
                    target_node_ids=diag_kp_ids if diag_kp_ids else None,
                )
                self._log(session_id, "PathPlanner", "plan",
                          {"user_id": user_id, "weak_points": profile.get("weak_points", []), "diag_kp_ids": diag_kp_ids},
                          path)
                try:
                    LearningPathRepository.save(path)
                except Exception as exc:
                    logger.warning("[Orchestrator] path persistence skipped: %s", exc)
                yield self._sse("path_update", "PathPlanner", path)
                yield self._sse("agent_end", "PathPlanner", {"message": f"路径规划完成，共 {len(path['nodes'])} 个节点"})

            # --- State machine + Challenger 自适应对抗 ---
            sess = self._get_session_state(session_id)
            prev_state = sess["state"]
            if not diag_result.get("is_correct", True):
                sess["state"] = self.STATE_CONSOLIDATION
            elif sess["state"] == self.STATE_IDLE:
                sess["state"] = self.STATE_LEARNING
                sess["learning_turns"] = 1
            elif sess["state"] == self.STATE_LEARNING:
                sess["learning_turns"] += 1
                # HMARL 方向2: Challenger触发阈値由元控制器动态调整
                _ch_threshold = _hmarl_challenger_threshold if _hmarl_action else 5
                if sess["learning_turns"] >= _ch_threshold:
                    sess["state"] = self.STATE_CONSOLIDATION

            if sess["state"] != prev_state:
                yield self._sse(
                    "state_change",
                    "Orchestrator",
                    {
                        "from": prev_state,
                        "to": sess["state"],
                        "message": self._state_change_message(sess["state"]),
                        "learning_turns": sess.get("learning_turns", 0),
                    },
                )

            if self.challenger.should_challenge(
                diag_result,
                learning_turns=sess.get("learning_turns", 0),
                force=(sess["state"] == self.STATE_CONSOLIDATION),
            ):
                yield self._sse("agent_start", "Challenger", {"message": "生成针对性误解检验题"})
                challenge = self.challenger.start_session(session_id, diag_result, profile)
                self._log(session_id, "Challenger", "start_session", {"diagnosis": diag_result}, challenge)
                yield self._sse("challenger", "Challenger", challenge)
                yield self._sse(
                    "agent_end",
                    "Challenger",
                    {"message": f"第 {challenge.get('round', 1)} 轮检验题已生成", "topic": challenge.get("topic")},
                )
                sess["challenger_active"] = True
                if sess["state"] == self.STATE_CONSOLIDATION:
                    sess["state"] = self.STATE_IDLE
                    sess["learning_turns"] = 0

            # --- State machine: path recommendation trigger ---
            strong_points = profile.get("strong_points", [])
            if len(strong_points) >= 3 and self._completed_kp_count < len(strong_points):
                self._completed_kp_count = len(strong_points)
                if self._completed_kp_count % 3 == 0:
                    sess["state"] = self.STATE_PLANNING
                    yield self._sse("agent_start", "PathPlanner", {"message": "已完成 3 个知识点，自动推荐下一步学习路径"})
                    auto_path = self.path_planner.plan(
                        user_id,
                        profile,
                        target_node_ids=diag_result.get("knowledge_node_ids") or None,
                    )
                    self._log(session_id, "PathPlanner", "auto_plan", {"completed": self._completed_kp_count}, auto_path)
                    yield self._sse("path_update", "PathPlanner", auto_path)
                    yield self._sse("agent_end", "PathPlanner", {"message": f"自动路径推荐完成，共 {len(auto_path['nodes'])} 个节点"})
                    sess["state"] = self.STATE_IDLE

            trace.add_step(
                "final_reflection",
                f"reply_len={len(full_reply)}, intent={intent}",
                "complete",
                0.9 if full_reply else 0.4,
            )
            SessionRepository.append_message(session_id, "user", user_message)
            SessionRepository.append_message(session_id, "assistant", full_reply)
            self._log(session_id, "Orchestrator", "agent_trace", {"message": user_message}, trace.to_dict())

            _elapsed = int((time.time() - started) * 1000)
            logger.info(
                "[Orchestrator] async_stream_reply 完成 | session=%s | 耗时=%dms | intent=%s | reply_len=%d",
                session_id, _elapsed, intent, len(full_reply),
            )
            yield self._sse(
                "done",
                "Orchestrator",
                {"session_id": session_id, "total_time_ms": _elapsed, "trace": trace.to_dict()},
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
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
        """异步写入 Agent 日志，不阻塞主流程。"""
        try:
            AgentLogRepository.write_async(session_id, agent_name, action, input_state, result)
        except Exception as exc:
            logger.debug("[Orchestrator] log skipped: %s", exc)

    def _get_session_state(self, session_id: str) -> dict[str, Any]:
        if session_id not in self._session_states:
            self._session_states[session_id] = {
                "state": self.STATE_IDLE,
                "learning_turns": 0,
                "challenger_active": False,
            }
        return self._session_states[session_id]

    @staticmethod
    def _state_change_message(state: str) -> str:
        messages = {
            OrchestratorAgent.STATE_LEARNING: "进入学习模式，开始积累对话轮次",
            OrchestratorAgent.STATE_CONSOLIDATION: "学习巩固：启动 Challenger 检验题确认理解深度",
            OrchestratorAgent.STATE_PLANNING: "进入路径推荐模式",
            OrchestratorAgent.STATE_IDLE: "回到空闲状态",
        }
        return messages.get(state, "状态切换")

    @staticmethod
    def _build_reply_prompt(
        user_message: str,
        retrieval: dict,
        diag: dict,
        history: str,
        trace: dict,
        persona_id: str = "professor",
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
        # 人格化系统提示词
        persona_prefix = ""
        persona = _PERSONAS.get(persona_id, {})
        if persona.get("prompt_prefix"):
            persona_prefix = persona["prompt_prefix"] + "\n\n"
        else:
            persona_prefix = "你是一个高级苏格拉底式计算机网络助教智能体。\n\n"
        return (
            persona_prefix
            + "你需要结合检索证据、错误论断、学习画像和自己的推理轨迹来回答。"
            "回答时先给学生可操作的理解框架，再用一到两个追问推动思考，避免只甩结论。\n\n"
            f"参考知识：\n{docs_text or '无'}\n"
            f"{diag_hint}\n"
            f"对话历史：\n{history or '无'}\n"
            f"智能体推理轨迹：{json.dumps(trace, ensure_ascii=False)[:1200]}\n\n"
            f"学生问题：{user_message}\n"
            "请用中文回答，结构清晰、语气友好。"
        )