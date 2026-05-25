"""
DiagnosisAgent：三层错误诊断代理
层次1：表层错误识别 → 层次2：根因分析 → 层次3：错误模式匹配
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.llm_client import llm_client

logger = logging.getLogger(__name__)

_PROMPT_DIR = Path("config/prompts/diagnosis")


def _load_prompt(name: str) -> str:
    p = _PROMPT_DIR / name
    try:
        return p.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("[Diagnosis] prompt 文件缺失: %s", p)
        return ""


class DiagnosisAgent:
    """
    三层错误诊断代理：
    1. 检测表层错误（事实性/概念性/计算性）
    2. 分析根因（前置知识缺失、理解偏差、记忆混淆）
    3. 匹配常见错误模式
    """

    def __init__(self):
        self._surface_prompt = _load_prompt("surface_error.txt")
        self._root_cause_prompt = _load_prompt("root_cause.txt")
        self._pattern_prompt = _load_prompt("pattern_match.txt")

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------

    def diagnose(
        self,
        user_message: str,
        context_docs: Optional[List[Dict]] = None,
        session_history: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        对学生输入做三层诊断。

        返回结构：
        {
            "is_correct": bool,
            "confidence": float,
            "surface_error": str | None,
            "error_type": "factual|conceptual|calculation|none",
            "root_causes": [str],
            "missing_prerequisites": [str],      # 缺失的前置知识点名称
            "pattern": str | None,               # 匹配到的错误模式名
            "intervention_suggestion": str,
            "related_node_ids": [str],           # 涉及的知识图谱节点
        }
        """
        logger.info("[Diagnosis] 开始三层诊断，消息长度: %d", len(user_message))

        # 第1层：表层错误识别
        surface_result = self._detect_surface_error(user_message, context_docs, session_history)

        # 若判断为正确，后两层跳过
        if surface_result.get("is_correct", True):
            logger.info("[Diagnosis] 判断为正确，跳过根因与模式分析")
            return {
                "is_correct": True,
                "confidence": surface_result.get("confidence", 0.85),
                "surface_error": None,
                "error_type": "none",
                "root_causes": [],
                "missing_prerequisites": [],
                "pattern": None,
                "intervention_suggestion": "理解正确，继续保持。",
                "related_node_ids": surface_result.get("related_node_ids", []),
            }

        # 第2层：根因分析
        root_result = self._analyze_root_cause(
            user_message,
            surface_result.get("surface_error", ""),
            context_docs,
        )

        # 第3层：错误模式匹配
        pattern_result = self._match_pattern(
            surface_result.get("surface_error", ""),
            root_result.get("root_causes", []),
        )

        return {
            "is_correct": False,
            "confidence": surface_result.get("confidence", 0.7),
            "surface_error": surface_result.get("surface_error"),
            "error_type": surface_result.get("error_type", "conceptual"),
            "root_causes": root_result.get("root_causes", []),
            "missing_prerequisites": root_result.get("missing_prerequisites", []),
            "pattern": pattern_result.get("pattern"),
            "intervention_suggestion": pattern_result.get("intervention_suggestion", "建议回顾相关章节。"),
            "related_node_ids": surface_result.get("related_node_ids", []),
        }

    # ------------------------------------------------------------------
    # 第1层：表层错误检测
    # ------------------------------------------------------------------

    def _detect_surface_error(
        self,
        message: str,
        docs: Optional[List[Dict]],
        history: Optional[str],
    ) -> Dict[str, Any]:
        context_str = self._format_docs(docs)
        hist_str = history or "（无历史）"

        if self._surface_prompt:
            prompt = self._surface_prompt.format(
                student_message=message,
                reference_docs=context_str,
                history=hist_str,
            )
        else:
            prompt = (
                f"参考资料：{context_str}\n\n"
                f"学生陈述：{message}\n\n"
                "请判断学生的陈述是否有错误。若有错误，指出错误内容和类型（factual/conceptual/calculation）。"
                "以JSON格式输出：{\"is_correct\": true/false, \"surface_error\": \"...\", "
                "\"error_type\": \"...\", \"confidence\": 0.8, \"related_node_ids\": []}"
            )

        try:
            resp = llm_client.chat(prompt, max_tokens=300)
            return self._parse_json_response(resp, {
                "is_correct": True,
                "surface_error": None,
                "error_type": "none",
                "confidence": 0.7,
                "related_node_ids": [],
            })
        except Exception as e:
            logger.warning("[Diagnosis] 表层诊断失败: %s", e)
            return {"is_correct": True, "confidence": 0.5, "related_node_ids": []}

    # ------------------------------------------------------------------
    # 第2层：根因分析
    # ------------------------------------------------------------------

    def _analyze_root_cause(
        self,
        message: str,
        surface_error: str,
        docs: Optional[List[Dict]],
    ) -> Dict[str, Any]:
        context_str = self._format_docs(docs)

        if self._root_cause_prompt:
            prompt = self._root_cause_prompt.format(
                student_message=message,
                surface_error=surface_error,
                reference_docs=context_str,
            )
        else:
            prompt = (
                f"学生陈述：{message}\n"
                f"表层错误：{surface_error}\n\n"
                "请分析这个错误的根本原因（前置知识缺失/理解偏差/记忆混淆/计算失误）。"
                "以JSON格式输出：{\"root_causes\": [\"原因1\", \"原因2\"], "
                "\"missing_prerequisites\": [\"知识点名称\"]}"
            )

        try:
            resp = llm_client.chat(prompt, max_tokens=300)
            return self._parse_json_response(resp, {
                "root_causes": ["理解偏差"],
                "missing_prerequisites": [],
            })
        except Exception as e:
            logger.warning("[Diagnosis] 根因分析失败: %s", e)
            return {"root_causes": [], "missing_prerequisites": []}

    # ------------------------------------------------------------------
    # 第3层：错误模式匹配
    # ------------------------------------------------------------------

    def _match_pattern(
        self,
        surface_error: str,
        root_causes: List[str],
    ) -> Dict[str, Any]:
        cause_text = "；".join(root_causes) if root_causes else "未知"

        if self._pattern_prompt:
            prompt = self._pattern_prompt.format(
                surface_error=surface_error,
                root_causes=cause_text,
            )
        else:
            prompt = (
                f"表层错误：{surface_error}\n"
                f"根本原因：{cause_text}\n\n"
                "请从常见错误模式中匹配最相近的类型，并给出干预建议。"
                "以JSON格式输出：{\"pattern\": \"模式名称\", \"intervention_suggestion\": \"建议内容\"}"
            )

        try:
            resp = llm_client.chat(prompt, max_tokens=200)
            return self._parse_json_response(resp, {
                "pattern": None,
                "intervention_suggestion": "建议结合例题重新理解该概念。",
            })
        except Exception as e:
            logger.warning("[Diagnosis] 模式匹配失败: %s", e)
            return {"pattern": None, "intervention_suggestion": "建议回顾相关教材章节。"}

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    @staticmethod
    def _format_docs(docs: Optional[List[Dict]]) -> str:
        if not docs:
            return "（无参考文档）"
        snippets = []
        for d in docs[:3]:
            text = d.get("document", d.get("text", ""))
            if text:
                snippets.append(text[:200])
        return "\n---\n".join(snippets) if snippets else "（无参考文档）"

    @staticmethod
    def _parse_json_response(text: str, default: Dict) -> Dict:
        """尝试从 LLM 输出中提取 JSON，失败时返回 default"""
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except Exception:
            pass
        return default
