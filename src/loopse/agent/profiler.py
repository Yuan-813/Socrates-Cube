"""学生认知画像维护 Agent（Profiler）。

本模块维护 Socrates-Cube 的 8 维认知画像，包括：

- **8 个能力维度**：概念理解、协议分析、计算能力、错误诊断、
  系统设计、知识关联、表达清晰、自我修正。
- **掌握度映射** (mastery_map)：20 个知识点的掌握度分数。
- **薄弱点 / 优势点列表**：基于掌握度阈值自动计算。
- **认知风格** (cognitive_style)：visual / practical / textual，
  驱动资源生成的优先级策略。

更新策略（混合更新）：
1. **确定性增量更新**：每轮对话后根据诊断结果直接调整掌握度和
   相关维度，无需 LLM 调用，延迟 <50ms。
2. **LLM 全量校准**：每 5 轮对话触发一次 LLM 分析，结合历史
   对话重新评估画像，并设置 10 秒去抖窗口避免频繁调用。

异常处理：LLM 返回非法 JSON 或画像加载失败时回退到默认画像。
"""
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
_DEFAULT_PROFILE.update({
    "mastery_map": {},
    "weak_points": [],
    "strong_points": [],
    "turn_count": 0,
    "cognitive_style": "textual",  # 确保认知风格始终有默认值
})


def _load_prompt(filename: str) -> str:
    path = _PROMPT_DIR / filename
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


class ProfilerAgent(CognitiveAgentMixin):
    """Updates an 8-dimension profile and knowledge-node mastery map.

    去抖策略：连续对话不重复触发全量画像校准。LLM 校准仅在每 5 轮触发一次，
    其余轮次仅做确定性增量更新，避免频繁 LLM 调用。
    """

    # 去抖时间窗口（秒）：同一 user_id 在此窗口内不重复触发 LLM 校准
    _DEBOUNCE_WINDOW = 10
    _last_calibration_time: dict[str, float] = {}  # user_id -> timestamp

    def __init__(self):
        self._update_prompt_tpl = _load_prompt("update_profile.txt")
        self._extract_prompt_tpl = _load_prompt("extract_profile.txt")

    def update_from_dialogue(
        self,
        user_id: str,
        user_message: str,
        agent_reply: str,
        diagnosis_result: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Update profile with hybrid strategy:

        - Deterministic update: diagnosis results directly adjust mastery
          and related dimensions without LLM call (every turn).
        - LLM calibration: full profile recalibration via LLM every 5 turns.
        """
        current = self._load_profile(user_id)
        turn_count = current.get("turn_count", 0) + 1
        trace = self.make_trace(f"profile:{user_id}")

        # Step 1: Deterministic update from diagnosis (no LLM call)
        updated = self._apply_deterministic_update(current, diagnosis_result)

        # Step 2: LLM calibration every 5 turns (with debounce)
        import time as _time
        now = _time.time()
        last_cal = ProfilerAgent._last_calibration_time.get(user_id, 0)
        should_calibrate = turn_count % 5 == 0 and (now - last_cal) > ProfilerAgent._DEBOUNCE_WINDOW
        if should_calibrate:
            ProfilerAgent._last_calibration_time[user_id] = now
            prompt = self._build_prompt(user_message, agent_reply, diagnosis_result, current)
            try:
                raw = llm_client.chat(prompt, max_tokens=500)
                delta = self._parse_delta(raw)
                updated = self._apply_delta(updated, delta, None)
                trace.add_step("llm_calibration", user_message[:100], json.dumps(delta, ensure_ascii=False), 0.7)
            except Exception as exc:
                logger.warning("[Profiler] LLM calibration skipped: %s", exc)
                trace.add_step("llm_calibration_skipped", str(exc), "fallback", 0.3)
        else:
            trace.add_step(
                "deterministic_update",
                f"turn={turn_count}, next_llm_at={5 - (turn_count % 5)}",
                "applied diagnosis-based update",
                0.85,
            )

        updated["turn_count"] = turn_count
        updated["last_agent_trace"] = trace.to_dict()
        self._save_profile(user_id, updated)
        logger.info("[Profiler] profile updated user=%s turn=%d mode=%s",
                     user_id, turn_count, "llm" if turn_count % 5 == 0 else "deterministic")
        return updated

    def _apply_deterministic_update(
        self, current: dict, diagnosis: Optional[dict],
    ) -> dict:
        """Apply deterministic dimension adjustments from diagnosis results.

        Mapping:
        - is_correct=True  -> +0.03 on conceptual_understanding, expression_clarity
        - is_correct=False -> -0.02 on conceptual_understanding, +0.01 on self_correction
        - root_causes present -> adjust related dimensions
        """
        profile = dict(current)
        if not diagnosis:
            return profile

        is_correct = diagnosis.get("is_correct", True)
        root_causes = diagnosis.get("root_causes", [])

        if is_correct:
            profile["conceptual_understanding"] = round(
                min(1.0, profile.get("conceptual_understanding", 0.5) + 0.03), 3
            )
            profile["expression_clarity"] = round(
                min(1.0, profile.get("expression_clarity", 0.5) + 0.02), 3
            )
        else:
            profile["conceptual_understanding"] = round(
                max(0.1, profile.get("conceptual_understanding", 0.5) - 0.02), 3
            )
            profile["self_correction"] = round(
                min(1.0, profile.get("self_correction", 0.5) + 0.01), 3
            )

        # Update mastery map from diagnosis
        mastery_map = dict(profile.get("mastery_map", {}))
        # 合并两个节点源：related_node_ids（表层检测）+ knowledge_node_ids（误解映射）
        node_ids = set(diagnosis.get("related_node_ids", []))
        node_ids.update(diagnosis.get("knowledge_node_ids", []))
        for node_id in node_ids:
            old = float(mastery_map.get(node_id, 0.5))
            change = 0.05 if is_correct else -0.07
            mastery_map[node_id] = round(max(0.0, min(1.0, old + change)), 3)
        profile["mastery_map"] = mastery_map
        profile["weak_points"] = [nid for nid, score in mastery_map.items() if score < 0.5]
        profile["strong_points"] = [nid for nid, score in mastery_map.items() if score >= 0.8]

        # Adjust error_diagnosis based on root_cause count
        if root_causes:
            profile["error_diagnosis"] = round(
                max(0.1, profile.get("error_diagnosis", 0.5) - 0.01 * len(root_causes)), 3
            )

        return profile

    def get_profile(self, user_id: str) -> dict[str, Any]:
        return self._load_profile(user_id)

    def extract_profile(
        self,
        user_id: str,
        dialogue_history: str,
    ) -> dict[str, Any]:
        """Extract / initialise an 8-dimension profile from dialogue history.

        Unlike ``update_from_dialogue`` (which applies a *delta*), this method
        asks the LLM to produce **absolute scores** for every dimension based
        on the full conversation transcript.  It is intended for cold-start or
        re-calibration scenarios.

        Args:
            user_id: 学生唯一标识
            dialogue_history: 完整对话文本（多轮拼接）

        Returns:
            更新后的 8 维画像字典
        """
        current = self._load_profile(user_id)
        trace = self.make_trace(f"extract_profile:{user_id}")

        prompt = self._build_extract_prompt(dialogue_history, current)
        try:
            raw = llm_client.chat(prompt, max_tokens=500)
            scores = self._parse_absolute_scores(raw)
        except Exception as exc:
            logger.warning("[Profiler] LLM extract_profile failed: %s", exc)
            scores = {}

        # Merge scores into current profile (only overwrite when LLM gave a value)
        updated = dict(current)
        for dim in PROFILE_DIMENSIONS:
            if dim in scores:
                updated[dim] = round(max(0.1, min(1.0, scores[dim])), 3)

        updated["turn_count"] = current.get("turn_count", 0)
        trace.add_step(
            "extract_profile",
            dialogue_history[:100],
            json.dumps(scores, ensure_ascii=False),
            0.75,
        )
        updated["last_agent_trace"] = trace.to_dict()
        self._save_profile(user_id, updated)
        logger.info("[Profiler] extract_profile done user=%s", user_id)
        return updated

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
        profile.setdefault("cognitive_style", "textual")  # 画像同步修复：确保 cognitive_style 不丢失
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

    def _parse_absolute_scores(self, text: str) -> dict[str, float]:
        """Parse LLM JSON output into absolute 0.1-1.0 scores."""
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
            # Normalise: if LLM returned a 1-5 scale, convert to 0-1
            if numeric > 1:
                numeric = (numeric - 1.0) / 4.0
            result[dim] = max(0.1, min(1.0, numeric))
        return result

    def _build_extract_prompt(self, dialogue_history: str, current: dict) -> str:
        current_scores = {dim: current.get(dim, 0.5) for dim in PROFILE_DIMENSIONS}
        values = {
            "dialogue_history": dialogue_history[:2000],
            "current_profile_json": json.dumps(current_scores, ensure_ascii=False),
        }
        if self._extract_prompt_tpl:
            try:
                return self._extract_prompt_tpl.format(**values)
            except KeyError as exc:
                logger.warning("[Profiler] extract prompt placeholder missing: %s", exc)
        return (
            f"对话记录：{values['dialogue_history']}\n"
            f"当前画像：{values['current_profile_json']}\n"
            "请返回JSON，键为画像维度，值为0.1到1.0的评估分数。"
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
            node_ids = set(diagnosis.get("related_node_ids", []))
            node_ids.update(diagnosis.get("knowledge_node_ids", []))
            for node_id in node_ids:
                old = float(mastery_map.get(node_id, 0.5))
                change = 0.05 if diagnosis.get("is_correct", True) else -0.07
                mastery_map[node_id] = round(max(0.0, min(1.0, old + change)), 3)
            profile["mastery_map"] = mastery_map
            profile["weak_points"] = [nid for nid, score in mastery_map.items() if score < 0.5]
            profile["strong_points"] = [nid for nid, score in mastery_map.items() if score >= 0.8]
        return profile
