"""
RetrieverAgent：知识检索代理
从向量数据库和知识图谱中检索与当前问题相关的资料
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..core.llm_client import llm_client
from ..kb.knowledge_graph import knowledge_graph
from ..kb.vector_store import vector_store

logger = logging.getLogger(__name__)

_SEARCH_PROMPT_TEMPLATE = """\
你是一位计算机网络课程助教，需要为学生的问题生成精确的检索查询词。

学生问题：{question}
学生最近对话历史：{recent_history}

请生成3-5个检索关键词，覆盖问题的核心概念。
只输出关键词列表，每行一个，不要解释。"""


class RetrieverAgent:
    """
    知识检索代理：接收问题文本，返回向量相似度检索 + 知识图谱节点的综合结果。
    """

    def __init__(self, top_k: int = 5):
        self.top_k = top_k

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------

    def search_all(
        self,
        question: str,
        recent_history: str = "",
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        综合检索：向量库检索 + 知识图谱关键词匹配 + 错误概念库检索。
        返回格式：
        {
            "query": str,
            "docs": [...],          # 课程文档片段
            "protocols": [...],     # 协议规范片段
            "misconceptions": [...],# 相关常见错误
            "graph_nodes": [...]    # 知识图谱节点
        }
        """
        logger.info("[Retriever] 开始检索，问题: %s", question[:50])

        # Step 1: 生成检索查询（基于 LLM 扩展关键词）
        query = self._expand_query(question, recent_history)

        # Step 2: 向量库多集合检索
        docs = self._search_docs(query)
        protocols = self._search_protocols(query)
        misconceptions = self._search_misconceptions(query)

        # Step 3: 知识图谱关键词节点检索
        graph_nodes = self._search_graph(query)

        result = {
            "query": query,
            "docs": docs,
            "protocols": protocols,
            "misconceptions": misconceptions,
            "graph_nodes": [n.to_dict() for n in graph_nodes],
        }
        logger.info("[Retriever] 检索完成，docs=%d, misconceptions=%d, graph_nodes=%d",
                    len(docs), len(misconceptions), len(graph_nodes))
        return result

    # ------------------------------------------------------------------
    # 向量库检索
    # ------------------------------------------------------------------

    def search_knowledge(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        """仅检索课程文档集合"""
        return self._search_docs(query, top_k or self.top_k)

    def search_misconceptions(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        """仅检索错误概念集合"""
        return self._search_misconceptions(query, top_k or self.top_k)

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _expand_query(self, question: str, recent_history: str) -> str:
        """调用 LLM 扩展检索关键词，失败时直接使用原始问题"""
        try:
            prompt = _SEARCH_PROMPT_TEMPLATE.format(
                question=question,
                recent_history=recent_history[:300] if recent_history else "无",
            )
            keywords = llm_client.chat(prompt, max_tokens=80)
            # 提取第一行作为主查询词，并拼接原始问题
            first_kw = keywords.strip().split("\n")[0].strip()
            expanded = f"{question} {first_kw}"
            logger.debug("[Retriever] 扩展查询: %s", expanded[:80])
            return expanded
        except Exception as e:
            logger.warning("[Retriever] 查询扩展失败，使用原始问题: %s", e)
            return question

    def _search_docs(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        n = top_k or self.top_k
        try:
            return vector_store.search("course_docs", query, n_results=n)
        except Exception as e:
            logger.warning("[Retriever] course_docs 检索失败: %s", e)
            return []

    def _search_protocols(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        n = top_k or self.top_k
        try:
            return vector_store.search("protocol_specs", query, n_results=n)
        except Exception as e:
            logger.warning("[Retriever] protocol_specs 检索失败: %s", e)
            return []

    def _search_misconceptions(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        n = top_k or self.top_k
        try:
            return vector_store.search("misconceptions", query, n_results=n)
        except Exception as e:
            logger.warning("[Retriever] misconceptions 检索失败: %s", e)
            return []

    def _search_graph(self, query: str) -> list:
        """知识图谱关键词检索，取前5个最相关节点"""
        nodes = knowledge_graph.search_by_keyword(query)
        # 按关键词匹配程度粗排（目前返回前5）
        return nodes[:5]
