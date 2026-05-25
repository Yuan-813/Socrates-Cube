"""
ProfilerAgent：学生画像维护代理
分析对话内容，更新学生的8维能力画像
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from ..core.llm_client import llm_client
from ..db.repositories import ProfileRepository

logger = logging.getLogger(__name__)

_PROMPT_DIR = Path("config/prompts/profiler")

# 8 维度定义
PROFILE_DIMENSIONS = [
    "conceptual_understanding",  # 概念理解
    "protocol_analysis",         # 协议分析
    "calculation_ability",       # 计算能力
    "error_diagnosis",           # 错误诊断
    "system_design",             # 系统设计
    "knowledge_connection",      # 知识迁移
    "expression_clarity",        # 表达清晰度
    "self_correction",           # 自我纠错
]

_DEFAULT_PROFILE: Dict[str, Any] = {
    dim: 0.5 for dim in PROFILE_DIMENSIONS
}
_DEFAULT_PROFILE["mastery_map"] = {}   # {knowledge_node_id: float}
_DEFAULT_PROFILE["weak_points"] = []   # [knowledge_node_id, ...]
_DEFAULT_PROFILE["strong_points"] = [] # [knowledge_node_id, ...]
_DEFAULT_PROFILE["turn_count"] = 0


def _load_prompt(filename: str) -> str:
    path = _PROMPT_DIR / filename
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("[Profiler] Prompt 文件不存在: %s", path)
        return ""


class ProfilerAgent:
    """
    学生画像维护代理。
    每轮对话结束后，分析学生回答并更新8维画像与知识点掌握度。
    """

    def __init__(self):
        self._update_prompt_tpl = _load_prompt("update_profile.txt")

    # ------------------------------------------------------------------
    # 主入口：分析对话并更新画像
    # ------------------------------------------------------------------

    def update_from_dialogue(
        self,
        user_id: str,
        user_message: str,
        agent_reply: str,
        diagnosis_result: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        分析一轮对话，更新并持久化学生画像。

        返回：更新后的 profile dict
        """
        # 1. 读取当前画像
        current = self._load_profile(user_id)

        # 2. 构造 prompt
        prompt = self._build_prompt(user_message, agent_reply, diagnosis_result, current)

        # 3. 调用 LLM 获取更新差量
        try:
            raw_resp = llm_client.chat(prompt, max_tokens=500)
            delta = self._parse_delta(raw_resp)
        except Exception as e:
            logger.warning("[Profiler] LLM 调用失败，跳过本轮画像更新: %s", e)
            delta = {}

        # 4. 应用更新
        updated = self._apply_delta(current, delta, diagnosis_result)
        updated["turn_count"] = current.get("turn_count", 0) + 1

        # 5. 持久化
        self._save_profile(user_id, updated)
        logger.info("[Profiler] 用户 %s 画像已更新，第 %d 轮", user_id, updated["turn_count"])
        return updated

    def get_profile(self, user_id: str) -> Dict[str, Any]:
        """获取学生当前画像（不存在时返回默认值）"""
        return self._load_profile(user_id)

    # ------------------------------------------------------------------
    # 内部：画像持久化
    # ------------------------------------------------------------------

    def _load_profile(self, user_id: str) -> Dict[str, Any]:
        raw = ProfileRepository.get(user_id)
        if raw is None:
            return dict(_DEFAULT_PROFILE)
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
            # 补全缺失维度
            for dim in PROFILE_DIMENSIONS:
                data.setdefault(dim, 0.5)
            data.setdefault("mastery_map", {})
            data.setdefault("weak_points", [])
            data.setdefault("strong_points", [])
            data.setdefault("turn_count", 0)
            return data
        except Exception:
            return dict(_DEFAULT_PROFILE)

    def _save_profile(self, user_id: str, profile: Dict) -> None:
        try:
            ProfileRepository.upsert(user_id, json.dumps(profile, ensure_ascii=False))
        except Exception as e:
            logger.error("[Profiler] 画像持久化失败: %s", e)

    # ------------------------------------------------------------------
    # 内部：prompt 构建与 delta 解析
    # ------------------------------------------------------------------

    def _build_prompt(
        self,
        user_msg: str,
        agent_reply: str,
        diagnosis: Optional[Dict],
        current: Dict,
    ) -> str:
        # 提取当前8维评分
        current_scores = {dim: current.get(dim, 0.5) for dim in PROFILE_DIMENSIONS}
        diag_summary = ""
        if diagnosis:
            is_correct = diagnosis.get("is_correct", True)
            surface = diagnosis.get("surface_error", "无")
            diag_summary = f"诊断结果：{'正确' if is_correct else '有错误'}；表层错误：{surface}"

        if self._update_prompt_tpl:
            return self._update_prompt_tpl.format(
                user_message=user_msg,
                agent_reply=agent_reply,
                diagnosis_summary=diag_summary,
                current_scores=json.dumps(current_scores, ensure_ascii=False),
            )

        # fallback 简化 prompt
        return (
            f"学生问题：{user_msg}\n"
            f"助教回复：{agent_reply}\n"
            f"{diag_summary}\n"
            f"当前评分：{current_scores}\n"
            "请给出8个维度的评分调整量（JSON格式，每个维度一个-0.1到+0.1的浮点数）。"
        )

    def _parse_delta(self, text: str) -> Dict[str, float]:
        """从 LLM 输出中解析 JSON 格式的差量"""
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])
                result = {}
                for dim in PROFILE_DIMENSIONS:
                    if dim in data:
                        try:
                            val = float(data[dim])
                            result[dim] = max(-0.2, min(0.2, val))
                        except (ValueError, TypeError):
                            pass
                return result
        except Exception as e:
            logger.debug("[Profiler] delta 解析失败: %s", e)
        return {}

    def _apply_delta(
        self,
        current: Dict,
        delta: Dict[str, float],
        diagnosis: Optional[Dict],
    ) -> Dict:
        profile = dict(current)

        # 应用 LLM 给出的差量
        for dim in PROFILE_DIMENSIONS:
            if dim in delta:
                old_val = profile.get(dim, 0.5)
                profile[dim] = round(max(0.1, min(1.0, old_val + delta[dim])), 3)

        # 根据诊断结果更新知识点掌握度
        if diagnosis:
            mastery_map: Dict[str, float] = dict(profile.get("mastery_map", {}))
            # 如果回答正确，提升相关知识点掌握度
            for node_id in diagnosis.get("related_node_ids", []):
                old = mastery_map.get(node_id, 0.5)
                delta_m = 0.05 if diagnosis.get("is_correct", True) else -0.05
                mastery_map[node_id] = round(max(0.0, min(1.0, old + delta_m)), 3)
            profile["mastery_map"] = mastery_map

            # 更新薄弱点列表
            weak = [nid for nid, m in mastery_map.items() if m < 0.5]
            strong = [nid for nid, m in mastery_map.items() if m >= 0.8]
            profile["weak_points"] = weak
            profile["strong_points"] = strong

        return profile
