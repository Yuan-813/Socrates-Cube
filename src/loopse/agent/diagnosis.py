"""三层认知诊断引擎 Agent。

本模块实现 Socrates-Cube 的核心创新——三层递进式误解诊断：

1. **表层错误识别** (surface_error)：判断学生回答是否正确，
   归类为流程遗漏 / 层级错位 / 概念混淆等 9 种错误类型：
   layer_misplacement / flow_omission / concept_confusion /
   field_misunderstanding / reasoning_breakdown / factual /
   security_misconception / performance_confusion / over_simplification
2. **根因溯源** (root_cause)：结合知识图谱上下文，分析错误的
   深层原因和缺失的前置知识，支持多根因排序。
3. **误区模式匹配** (pattern_match)：将错误映射到 9 种已知误区
   模式，并生成对应的干预建议（如仿真纠偏、对比题练习等）。

参考标准：RFC 9293(TCP)、RFC 8446(TLS)、RFC 4301(IPsec)、RFC 2544(基准测试)、
RFC 791(IPv4)、RFC 1034/1035(DNS)、RFC 9110(HTTP Semantics)。

异常处理：LLM 返回非法 JSON 时进行类型兜底，保证 pattern 始终
为 dict、root_causes 始终为 list，不向上层抛异常。
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Optional

from ..core.llm_client import llm_client
from ..kb.misconception_registry import misconception_registry
from .cognitive_engine import AwaitableDict, CognitiveAgentMixin

logger = logging.getLogger(__name__)
_PROMPT_DIR = Path("config/prompts/diagnosis")


def _load_prompt(name: str) -> str:
    path = _PROMPT_DIR / name
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


class DiagnosisAgent(CognitiveAgentMixin):
    """三层认知诊断 Agent。

    通过三次 LLM 调用依次完成表层错误识别、根因溯源和误区模式匹配，
    返回结构化诊断结果字典。每次调用均记录耗时日志，便于性能分析。
    """

    def __init__(self):
        self._surface_prompt = _load_prompt("surface_error.txt")
        self._root_cause_prompt = _load_prompt("root_cause.txt")
        self._pattern_prompt = _load_prompt("pattern_match.txt")

    def diagnose(
        self,
        user_message: str | None = None,
        context_docs: Optional[list[dict]] = None,
        session_history: Optional[str] = None,
        **legacy_kwargs: Any,
    ) -> dict[str, Any]:
        user_message = user_message or legacy_kwargs.get("student_answer", "")
        _t0 = time.time()
        logger.info("[Diagnosis] diagnose 入参 | msg=%s... | docs=%d", user_message[:60], len(context_docs or []))
        trace = self.make_trace(f"diagnose:{user_message[:80]}")
        surface = self._detect_surface_error(user_message, context_docs, session_history)
        trace.add_step("surface_error", user_message[:120], str(surface), surface.get("confidence", 0.6))

        if surface.get("is_correct", True):
            result = {
                "is_correct": True,
                "confidence": surface.get("confidence", 0.82),
                "surface_error": None,
                "error_type": "none",
                "root_causes": [],
                "missing_prerequisites": [],
                "pattern": None,
                "intervention_suggestion": "理解基本正确，可以继续通过变式题巩固。",
                "related_node_ids": surface.get("related_node_ids", []),
            }
            result["agent_trace"] = trace.to_dict()
            logger.info("[Diagnosis] diagnose 完成 | 耗时=%.0fms | 结果=correct", (time.time() - _t0) * 1000)
            return AwaitableDict(result)

        root = self._analyze_root_cause(user_message, surface.get("surface_error", ""), context_docs)
        trace.add_step("root_cause", surface.get("surface_error", ""), str(root), 0.72)
        pattern = self._match_pattern(surface.get("surface_error", ""), root.get("root_causes", []))
        trace.add_step("pattern_match", str(root.get("root_causes", [])), str(pattern), 0.7)

        # 确保 pattern 始终为 dict（_match_pattern 在某些遗留路径可能返回 str）
        if isinstance(pattern, str):
            pattern = {"pattern": pattern, "intervention_suggestion": "建议先用对比题澄清概念边界。"}
        if not isinstance(pattern, dict):
            pattern = {}
        # 确保 root_causes 始终为 list
        root_causes = root.get("root_causes", [])
        if not isinstance(root_causes, list):
            root_causes = [str(root_causes)] if root_causes else []
        missing_prereq = root.get("missing_prerequisites", [])
        if not isinstance(missing_prereq, list):
            missing_prereq = [str(missing_prereq)] if missing_prereq else []

        result = {
            "is_correct": False,
            "confidence": surface.get("confidence", 0.7),
            "surface_error": surface.get("surface_error"),
            "error_type": surface.get("error_type", "conceptual"),
            "root_causes": root_causes,
            "missing_prerequisites": missing_prereq,
            "pattern": pattern.get("pattern"),
            "intervention_suggestion": pattern.get("intervention_suggestion", "建议先用对比题澄清概念边界。"),
            "related_node_ids": surface.get("related_node_ids", []),
            "agent_trace": trace.to_dict(),
        }

        # 误解映射查询（P0: 显式映射层）
        try:
            matched_mc = misconception_registry.match_from_diagnosis(
                surface.get("error_type", "conceptual"),
                surface.get("knowledge_point", user_message[:60] if user_message else "")
            )
            result["misconception_id"] = matched_mc["id"] if matched_mc else None
            # kp_node_ids：课程节点 ID（kp_xxx），供 PathPlanner 使用
            result["knowledge_node_ids"] = (
                matched_mc.get("kp_node_ids") or matched_mc.get("weak_prerequisites", [])
            ) if matched_mc else surface.get("related_node_ids", [])
            # acu_ids：认知理解单元 ID（acu_xxx），供 ResourceGenerator 精准定位修复策略
            result["acu_ids"] = matched_mc.get("knowledge_node_ids", []) if matched_mc else []
            result["recommended_interventions"] = matched_mc.get("interventions", []) if matched_mc else []
        except Exception as _mc_exc:
            logger.warning("[Diagnosis] misconception mapping failed: %s", _mc_exc)
            result["misconception_id"] = None
            result["knowledge_node_ids"] = surface.get("related_node_ids", [])
            result["recommended_interventions"] = []

        logger.info(
            "[Diagnosis] diagnose 完成 | 耗时=%.0fms | 结果=error type=%s pattern=%s",
            (time.time() - _t0) * 1000,
            result.get("error_type", "unknown"),
            result.get("pattern", "none"),
        )
        return AwaitableDict(result)

    def _detect_surface_error(
        self,
        message: str | None = None,
        docs: Optional[list[dict]] = None,
        history: Optional[str] = None,
        **legacy_kwargs: Any,
    ) -> dict[str, Any]:
        message = message or legacy_kwargs.get("student_answer", "")
        context = self._format_docs(docs) if docs is not None else legacy_kwargs.get("reference_content", "")
        prompt = self._format_prompt(
            getattr(self, "_surface_prompt", ""),
            {
                "student_message": message,
                "student_answer": message,
                "reference_docs": context,
                "reference_content": context,
                "history": history or "",
            },
            (
                f"判断学生回答是否正确。学生回答：{message}\n参考资料：{context}\n"
                "返回JSON：{\"is_correct\": true, \"surface_error\": null, \"error_type\": \"none\", \"confidence\": 0.8}"
            ),
        )
        try:
            raw = llm_client.chat(prompt, max_tokens=300)
            data = self._parse_json(raw, {})
        except Exception as exc:
            logger.warning("[Diagnosis] surface detection failed: %s", exc)
            data = {}
        return AwaitableDict(self._normalize_surface(data, message))

    def _analyze_root_cause(
        self,
        message: str | dict | None = None,
        surface_error: str | None = None,
        docs: Optional[list[dict]] = None,
        **legacy_kwargs: Any,
    ) -> dict[str, Any]:
        if message is None:
            message = legacy_kwargs.get("knowledge_point", "")
        if isinstance(message, dict):
            surface_error = json.dumps(message, ensure_ascii=False)
            message = legacy_kwargs.get("knowledge_point", "")
        context = self._format_docs(docs)
        prompt = self._format_prompt(
            getattr(self, "_root_cause_prompt", ""),
            {
                "student_message": message,
                "surface_error": surface_error or "",
                "surface_error_json": surface_error or "",
                "reference_docs": context,
                "profile_json": "{}",
                "knowledge_graph_context": context,
            },
            (
                f"学生回答：{message}\n表层错误：{surface_error}\n参考：{context}\n"
                "返回JSON：{\"root_causes\": [\"原因\"], \"missing_prerequisites\": []}"
            ),
        )
        try:
            data = self._parse_json(llm_client.chat(prompt, max_tokens=300), {})
        except Exception as exc:
            logger.warning("[Diagnosis] root cause failed: %s", exc)
            data = {}
        if isinstance(data, list):
            missing = [item.get("knowledge_node_id", "unknown") for item in data if isinstance(item, dict)]
            causes = [item.get("reason", "前置知识掌握不足") for item in data if isinstance(item, dict)]
            return AwaitableDict({"root_causes": causes or ["前置知识掌握不足"], "missing_prerequisites": missing})
        return AwaitableDict({
            "root_causes": data.get("root_causes", ["概念边界不清"]),
            "missing_prerequisites": data.get("missing_prerequisites", []),
        })

    def _match_pattern(
        self,
        surface_error: str | None = None,
        root_causes: Optional[list[str]] = None,
        **legacy_kwargs: Any,
    ) -> dict[str, Any] | str | None:
        if surface_error is None:
            surface_error = legacy_kwargs.get("error_type", "")
        root_causes = root_causes or legacy_kwargs.get("root_causes", [])
        prompt = self._format_prompt(
            getattr(self, "_pattern_prompt", ""),
            {
                "surface_error": surface_error,
                "surface_error_json": surface_error,
                "root_causes": "；".join(root_causes),
                "root_causes_json": json.dumps(root_causes, ensure_ascii=False),
            },
            (
                f"表层错误：{surface_error}\n根因：{root_causes}\n"
                "返回JSON：{\"pattern\": \"模式\", \"intervention_suggestion\": \"建议\"}"
            ),
        )
        try:
            data = self._parse_json(llm_client.chat(prompt, max_tokens=220), {})
        except Exception as exc:
            logger.warning("[Diagnosis] pattern match failed: %s", exc)
            data = {}
        result = {
            "pattern": data.get("pattern", "无明确模式"),
            "intervention_suggestion": data.get("intervention_suggestion", "用反例和流程追问帮助学生自我修正。"),
        }
        if "error_type" in legacy_kwargs:
            return result["pattern"]
        return AwaitableDict(result)

    @staticmethod
    def _format_docs(docs: Optional[list[dict]]) -> str:
        if not docs:
            return ""
        snippets = []
        for item in docs[:4]:
            text = item.get("document", item.get("content", item.get("text", "")))
            if text:
                snippets.append(text[:240])
        return "\n---\n".join(snippets)

    @staticmethod
    def _format_prompt(template: str, values: dict[str, Any], fallback: str) -> str:
        if not template:
            return fallback
        try:
            return template.format(**values)
        except KeyError as exc:
            logger.warning("[Diagnosis] prompt placeholder missing: %s", exc)
            return fallback

    @staticmethod
    def _parse_json(text: str, default: Any) -> Any:
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
            start = text.find("[")
            end = text.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except Exception:
            pass
        return default

    # 已知误区关键词 → (error_type, surface_error 描述)
    _KNOWN_MISCONCEPTIONS = [
        (["两次握手", "二次握手"], "factual", "把 TCP 三次握手误认为两次握手"),
        (["直接运行在IP", "直接跑在IP", "不需要中间层", "HTTP直接", "HTTP 直接"], "layer_misplacement", "忽略 TCP 中间层，认为 HTTP 直接运行在 IP 上"),
        (["SYN、ACK、FIN", "SYN,ACK,FIN", "SYN ACK FIN 三个包"], "flow_omission", "把三次握手的 SYN/SYN+ACK/ACK 误记为 SYN/ACK/FIN"),
        (["ACK号等于序列号", "ACK号=序列号", "ACK 号 = 序列号"], "field_misunderstanding", "混淆 ACK 号与序列号的关系"),
        (["UDP比TCP好", "UDP 比 TCP 好", "UDP更好"], "concept_confusion", "片面认为 UDP 优于 TCP"),
        (["Ping不通就是网络坏", "Ping 不通就是网络坏", "ping不通"], "reasoning_breakdown", "将 Ping 失败简单等同于网络故障"),
        # 安全机制误解 (RFC 8446 TLS 1.3 / RFC 4301 IPsec)
        (["TLS只加密数据", "TLS 只加密数据", "HTTPS不需要证书", "防火墙能防所有攻击", "内网绝对安全"], "security_misconception", "对 TLS/IPSec/防火墙安全边界的错误理解（违反 RFC 8446 / RFC 4301）"),
        (["加密就是安全", "有HTTPS就安全了", "SSL和TLS一样"], "security_misconception", "混淆加密与安全的概念，或将已废弃的 SSL 等同于 TLS"),
        # 性能指标混淆 (RFC 2544 / RFC 4148)
        (["带宽就是速度", "延迟越低越好", "带宽等于吞吐量", "带宽=吞吐量"], "performance_confusion", "混淆带宽/吞吐量/延迟/抖动等性能指标（违反 RFC 2544 基准测试规范）"),
        (["ping值就是延迟", "丢包率不影响吞吐", "抖动就是延迟"], "performance_confusion", "误解网络性能指标的定义和相互关系"),
    ]

    _PATTERN_TO_ERROR_TYPE = {
        "layer_misplacement": "layer_misplacement",
        "flow_omission": "flow_omission",
        "concept_confusion": "concept_confusion",
        "term_confusion": "field_misunderstanding",
        "over_simplification": "concept_confusion",
        "reasoning_breakdown": "reasoning_breakdown",
        "factual": "factual",
        "security_misconception": "security_misconception",
        "performance_confusion": "performance_confusion",
        "field_misunderstanding": "field_misunderstanding",
    }

    _misconception_rules_cache: list[tuple[list[str], str, str]] | None = None

    @classmethod
    def _get_misconception_rules(cls) -> list[tuple[list[str], str, str]]:
        """合并内置关键词与误解库 JSON，提升 Mock/离线模式诊断命中率。"""
        if cls._misconception_rules_cache is not None:
            return cls._misconception_rules_cache

        rules: list[tuple[list[str], str, str]] = list(cls._KNOWN_MISCONCEPTIONS)
        path = Path("data/raw/misconceptions.json")
        if path.exists():
            try:
                items = json.loads(path.read_text(encoding="utf-8"))
                for item in items:
                    stmt = (item.get("misconception") or "").strip()
                    if len(stmt) < 6:
                        continue
                    pattern = item.get("error_type", "concept_confusion")
                    error_type = cls._PATTERN_TO_ERROR_TYPE.get(pattern, "concept_confusion")
                    keywords = [stmt]
                    for part in re.split(r"[，。、；,.]", stmt):
                        part = part.strip()
                        if len(part) >= 8:
                            keywords.append(part)
                    rules.append((keywords, error_type, stmt[:120]))
            except Exception as exc:
                logger.warning("[Diagnosis] load misconceptions.json failed: %s", exc)

        cls._misconception_rules_cache = rules
        return rules

    @classmethod
    def _detect_known_misconception(cls, message: str) -> tuple[str, str, str] | None:
        """基于关键词检测已知误区模式，弥补 MockLLM 无法识别错误的不足。"""
        for keywords, error_type, description in cls._get_misconception_rules():
            if any(kw in message for kw in keywords):
                return error_type, description
        return None

    @classmethod
    def _normalize_surface(cls, data: dict[str, Any], message: str) -> dict[str, Any]:
        error_type = data.get("error_type", "none")
        is_correct = data.get("is_correct")
        if is_correct is None:
            is_correct = error_type in {"none", "correct", "无", ""}
        surface_error = data.get("surface_error") or data.get("error_description")

        # 已知误区关键词检测（MockLLM 无法识别错误时兜底）
        known = cls._detect_known_misconception(message)
        if known:
            is_correct = False
            error_type, surface_error = known

        return {
            "is_correct": bool(is_correct),
            "surface_error": None if is_correct else surface_error or "存在潜在概念偏差",
            "error_type": "none" if is_correct else error_type,
            "confidence": float(data.get("confidence", 0.78)),
            "related_node_ids": data.get("related_node_ids", ["kp_005"] if "TCP" in message else []),
            "has_error": not bool(is_correct),
        }
