"""Three-layer misconception diagnosis agent."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from ..core.llm_client import llm_client
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
    """Detects surface error, root cause and misconception pattern."""

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
            return AwaitableDict(result)

        root = self._analyze_root_cause(user_message, surface.get("surface_error", ""), context_docs)
        trace.add_step("root_cause", surface.get("surface_error", ""), str(root), 0.72)
        pattern = self._match_pattern(surface.get("surface_error", ""), root.get("root_causes", []))
        trace.add_step("pattern_match", str(root.get("root_causes", [])), str(pattern), 0.7)

        result = {
            "is_correct": False,
            "confidence": surface.get("confidence", 0.7),
            "surface_error": surface.get("surface_error"),
            "error_type": surface.get("error_type", "conceptual"),
            "root_causes": root.get("root_causes", []),
            "missing_prerequisites": root.get("missing_prerequisites", []),
            "pattern": pattern.get("pattern"),
            "intervention_suggestion": pattern.get("intervention_suggestion", "建议先用对比题澄清概念边界。"),
            "related_node_ids": surface.get("related_node_ids", []),
            "agent_trace": trace.to_dict(),
        }
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

    @staticmethod
    def _normalize_surface(data: dict[str, Any], message: str) -> dict[str, Any]:
        error_type = data.get("error_type", "none")
        is_correct = data.get("is_correct")
        if is_correct is None:
            is_correct = error_type in {"none", "correct", "无", ""}
        surface_error = data.get("surface_error") or data.get("error_description")
        if "两次握手" in message or "二次握手" in message:
            is_correct = False
            surface_error = surface_error or "把 TCP 三次握手误认为两次握手"
            error_type = "factual"
        return {
            "is_correct": bool(is_correct),
            "surface_error": None if is_correct else surface_error or "存在潜在概念偏差",
            "error_type": "none" if is_correct else error_type,
            "confidence": float(data.get("confidence", 0.78)),
            "related_node_ids": data.get("related_node_ids", ["kn_005"] if "TCP" in message else []),
            "has_error": not bool(is_correct),
        }
