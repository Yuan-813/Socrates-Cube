"""Student profile maintenance agent."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from ..core.llm_client import llm_client
from ..db.repositories import ProfileRepository
from .cognitive_engine import CognitiveAgentMixin

logger = logging.getLogger(__name__)
_PROMPT_DIR = Path("config/prompts/profiler")

PROFILE_DIMENSIONS = [
    "conceptual_understanding",
    "protocol_analysis",
    "calculation_ability",
    "error_diagnosis",
    "system_design",
    "knowledge_connection",
    "expression_clarity",
    "self_correction",
]

_DEFAULT_PROFILE: dict[str, Any] = {dim: 0.5 for dim in PROFILE_DIMENSIONS}
_DEFAULT_PROFILE.update({"mastery_map": {}, "weak_points": [], "strong_points": [], "turn_count": 0})


def _load_prompt(filename: str) -> str:
    path = _PROMPT_DIR / filename
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


class ProfilerAgent(CognitiveAgentMixin):
    """Updates an 8-dimension profile and knowledge-node mastery map."""

    def __init__(self):
        self._update_prompt_tpl = _load_prompt("update_profile.txt")

    def update_from_dialogue(
        self,
        user_id: str,
        user_message: str,
        agent_reply: str,
        diagnosis_result: Optional[dict] = None,
    ) -> dict[str, Any]:
        current = self._load_profile(user_id)
        trace = self.make_trace(f"profile:{user_id}")
        prompt = self._build_prompt(user_message, agent_reply, diagnosis_result, current)
        try:
            raw = llm_client.chat(prompt, max_tokens=500)
            delta = self._parse_delta(raw)
        except Exception as exc:
            logger.warning("[Profiler] LLM profile update failed: %s", exc)
            delta = {}
        updated = self._apply_delta(current, delta, diagnosis_result)
        updated["turn_count"] = current.get("turn_count", 0) + 1
        trace.add_step("profile_delta", user_message[:100], json.dumps(delta, ensure_ascii=False), 0.7)
        updated["last_agent_trace"] = trace.to_dict()
        self._save_profile(user_id, updated)
        logger.info("[Profiler] profile updated user=%s turn=%d", user_id, updated["turn_count"])
        return updated

    def get_profile(self, user_id: str) -> dict[str, Any]:
        return self._load_profile(user_id)

    def _load_profile(self, user_id: str) -> dict[str, Any]:
        raw = ProfileRepository.get(user_id)
        profile = dict(_DEFAULT_PROFILE)
        if isinstance(raw, dict):
            profile.update(raw)
        elif isinstance(raw, str):
            try:
                profile.update(json.loads(raw))
            except json.JSONDecodeError:
                pass
        for dim in PROFILE_DIMENSIONS:
            profile[dim] = float(profile.get(dim, 0.5))
        profile.setdefault("mastery_map", {})
        profile.setdefault("weak_points", [])
        profile.setdefault("strong_points", [])
        profile.setdefault("turn_count", 0)
        return profile

    def _save_profile(self, user_id: str, profile: dict) -> None:
        ProfileRepository.upsert(user_id, profile)

    def _build_prompt(
        self,
        user_msg: str,
        agent_reply: str,
        diagnosis: Optional[dict],
        current: dict,
    ) -> str:
        current_scores = {dim: current.get(dim, 0.5) for dim in PROFILE_DIMENSIONS}
        dialogue = f"学生：{user_msg}\n助教：{agent_reply[:800]}\n诊断：{json.dumps(diagnosis or {}, ensure_ascii=False)}"
        values = {
            "user_message": user_msg,
            "agent_reply": agent_reply,
            "diagnosis_summary": json.dumps(diagnosis or {}, ensure_ascii=False),
            "current_scores": json.dumps(current_scores, ensure_ascii=False),
            "current_profile_json": json.dumps(current, ensure_ascii=False),
            "new_dialogue": dialogue,
        }
        if self._update_prompt_tpl:
            try:
                return self._update_prompt_tpl.format(**values)
            except KeyError as exc:
                logger.warning("[Profiler] prompt placeholder missing: %s", exc)
        return (
            f"当前画像：{values['current_scores']}\n{dialogue}\n"
            "请返回JSON，键为画像维度，值为 -0.2 到 0.2 的增量；没有证据则省略。"
        )

    def _parse_delta(self, text: str) -> dict[str, float]:
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            data = json.loads(text[start:end]) if start >= 0 and end > start else {}
        except Exception:
            return {}
        result: dict[str, float] = {}
        for dim in PROFILE_DIMENSIONS:
            value = data.get(dim)
            if value is None:
                continue
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                continue
            if numeric > 1:
                current_scale_delta = (numeric - 3.0) / 10.0
                numeric = current_scale_delta
            result[dim] = max(-0.2, min(0.2, numeric))
        return result

    def _apply_delta(self, current: dict, delta: dict[str, float], diagnosis: Optional[dict]) -> dict:
        profile = dict(current)
        for dim in PROFILE_DIMENSIONS:
            if dim in delta:
                profile[dim] = round(max(0.1, min(1.0, profile.get(dim, 0.5) + delta[dim])), 3)

        if diagnosis:
            mastery_map = dict(profile.get("mastery_map", {}))
            for node_id in diagnosis.get("related_node_ids", []):
                old = float(mastery_map.get(node_id, 0.5))
                change = 0.05 if diagnosis.get("is_correct", True) else -0.07
                mastery_map[node_id] = round(max(0.0, min(1.0, old + change)), 3)
            profile["mastery_map"] = mastery_map
            profile["weak_points"] = [nid for nid, score in mastery_map.items() if score < 0.5]
            profile["strong_points"] = [nid for nid, score in mastery_map.items() if score >= 0.8]
        return profile
