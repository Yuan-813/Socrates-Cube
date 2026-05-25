"""
ResourceGeneratorAgent：学习资源生成代理
支持三种资源类型：知识文档（doc）、练习题（exercise）、代码示例（code）
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.llm_client import llm_client

logger = logging.getLogger(__name__)

_PROMPT_DIR = Path("config/prompts/resource_generator")


def _load_prompt(name: str) -> str:
    p = _PROMPT_DIR / name
    try:
        return p.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("[ResourceGen] prompt 文件缺失: %s", p)
        return ""


class ResourceGeneratorAgent:
    """
    学习资源生成代理，支持：
    - doc：知识点总结文档（含 Markdown 格式）
    - exercise：练习题（含答案与解析）
    - code：代码/协议模拟示例
    """

    RESOURCE_TYPES = ("doc", "exercise", "code")

    def __init__(self):
        self._doc_prompt = _load_prompt("generate_doc.txt")
        self._exercise_prompt = _load_prompt("generate_exercise.txt")
        self._code_prompt = _load_prompt("generate_code.txt")

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------

    def generate(
        self,
        resource_type: str,
        knowledge_point: str,
        context_docs: Optional[List[Dict]] = None,
        difficulty: int = 3,
    ) -> Dict[str, Any]:
        """
        生成指定类型的学习资源。

        Args:
            resource_type: "doc" / "exercise" / "code"
            knowledge_point: 目标知识点名称（如 "TCP三次握手"）
            context_docs: 检索到的参考文档片段
            difficulty: 难度（1-5）

        Returns:
            {
                "resource_id": str,
                "resource_type": str,
                "knowledge_point": str,
                "title": str,
                "content": str,
                "metadata": {...},
                "created_at": str,
            }
        """
        if resource_type not in self.RESOURCE_TYPES:
            raise ValueError(f"不支持的资源类型: {resource_type}，可选: {self.RESOURCE_TYPES}")

        logger.info("[ResourceGen] 生成 %s 类型资源，知识点: %s", resource_type, knowledge_point)

        if resource_type == "doc":
            return self._generate_doc(knowledge_point, context_docs, difficulty)
        elif resource_type == "exercise":
            return self._generate_exercise(knowledge_point, context_docs, difficulty)
        else:
            return self._generate_code(knowledge_point, context_docs, difficulty)

    # ------------------------------------------------------------------
    # 类型1：知识文档
    # ------------------------------------------------------------------

    def _generate_doc(
        self,
        knowledge_point: str,
        docs: Optional[List[Dict]],
        difficulty: int,
    ) -> Dict[str, Any]:
        context = self._format_context(docs)

        if self._doc_prompt:
            prompt = self._doc_prompt.format(
                knowledge_point=knowledge_point,
                context_docs=context,
                difficulty=difficulty,
            )
        else:
            prompt = (
                f"请为计算机网络课程的「{knowledge_point}」知识点，"
                f"生成一份适合难度{difficulty}级学生的学习文档。\n"
                f"参考材料：{context[:500]}\n"
                "要求：结构清晰，包含定义、核心原理、要点总结，Markdown格式输出。"
            )

        content = llm_client.chat(prompt, max_tokens=1000)
        title = f"【知识文档】{knowledge_point}"

        return self._build_resource("doc", knowledge_point, title, content, {"difficulty": difficulty})

    # ------------------------------------------------------------------
    # 类型2：练习题
    # ------------------------------------------------------------------

    def _generate_exercise(
        self,
        knowledge_point: str,
        docs: Optional[List[Dict]],
        difficulty: int,
    ) -> Dict[str, Any]:
        context = self._format_context(docs)

        if self._exercise_prompt:
            prompt = self._exercise_prompt.format(
                knowledge_point=knowledge_point,
                context_docs=context,
                difficulty=difficulty,
            )
        else:
            prompt = (
                f"请为「{knowledge_point}」生成3道练习题（难度{difficulty}级）。\n"
                f"参考材料：{context[:500]}\n"
                "要求：包含选择题1道、判断题1道、简答题1道，每题附标准答案和解析。"
            )

        content = llm_client.chat(prompt, max_tokens=800)
        title = f"【练习题】{knowledge_point}"

        return self._build_resource("exercise", knowledge_point, title, content, {
            "difficulty": difficulty,
            "question_count": 3,
        })

    # ------------------------------------------------------------------
    # 类型3：代码/协议示例
    # ------------------------------------------------------------------

    def _generate_code(
        self,
        knowledge_point: str,
        docs: Optional[List[Dict]],
        difficulty: int,
    ) -> Dict[str, Any]:
        context = self._format_context(docs)

        if self._code_prompt:
            prompt = self._code_prompt.format(
                knowledge_point=knowledge_point,
                context_docs=context,
                difficulty=difficulty,
            )
        else:
            prompt = (
                f"请为「{knowledge_point}」生成一个 Python 代码示例，模拟或演示该协议/概念的核心逻辑。\n"
                f"参考材料：{context[:300]}\n"
                "要求：代码可运行，包含详细注释，展示关键状态变化。"
            )

        content = llm_client.chat(prompt, max_tokens=800)
        title = f"【代码示例】{knowledge_point}"

        return self._build_resource("code", knowledge_point, title, content, {
            "language": "python",
            "difficulty": difficulty,
        })

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    @staticmethod
    def _format_context(docs: Optional[List[Dict]]) -> str:
        if not docs:
            return "（无参考文档）"
        snippets = [d.get("document", d.get("text", ""))[:200] for d in docs[:3] if d]
        return "\n".join(filter(None, snippets)) or "（无参考文档）"

    @staticmethod
    def _build_resource(
        res_type: str,
        knowledge_point: str,
        title: str,
        content: str,
        metadata: Dict,
    ) -> Dict[str, Any]:
        return {
            "resource_id": str(uuid.uuid4()),
            "resource_type": res_type,
            "knowledge_point": knowledge_point,
            "title": title,
            "content": content,
            "metadata": metadata,
            "created_at": datetime.utcnow().isoformat(),
        }
