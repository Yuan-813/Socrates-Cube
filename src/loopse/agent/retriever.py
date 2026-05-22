"""
Retriever Agent — 知识库检索
从ChromaDB的3个Collection中检索相关内容，支持查询改写
"""
import json
from pathlib import Path
from typing import Optional

from src.loopse.kb.vector_store import vector_store
from src.loopse.core.llm_client import llm_client

SEARCH_QUERY_PROMPT_PATH = Path("config/prompts/retriever/search_query.txt")


class RetrieverAgent:

    def __init__(self):
        self.search_query_prompt = ""
        if SEARCH_QUERY_PROMPT_PATH.exists():
            self.search_query_prompt = SEARCH_QUERY_PROMPT_PATH.read_text(encoding="utf-8")

    def search_knowledge(self, query: str, n_results: int = 5) -> list:
        """在course_docs和protocol_specs中检索"""
        results = vector_store.search("course_docs", query, n_results)
        docs = []
        if results.get("documents") and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                meta = {}
                if results.get("metadatas") and results["metadatas"][0]:
                    meta = results["metadatas"][0][i] if i < len(results["metadatas"][0]) else {}
                docs.append({"content": doc, "metadata": meta})
        return docs

    def search_misconceptions(self, query: str, n_results: int = 3) -> list:
        """在misconceptions中检索"""
        results = vector_store.search("misconceptions", query, n_results)
        docs = []
        if results.get("documents") and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                meta = {}
                if results.get("metadatas") and results["metadatas"][0]:
                    meta = results["metadatas"][0][i] if i < len(results["metadatas"][0]) else {}
                docs.append({"content": doc, "metadata": meta})
        return docs

    def search_all(self, query: str, n_results: int = 3) -> dict:
        """在所有Collection中检索"""
        knowledge = self.search_knowledge(query, n_results)
        misconceptions = self.search_misconceptions(query, n_results)
        return {"knowledge": knowledge, "misconceptions": misconceptions}

    def rewrite_queries(self, user_message: str) -> list:
        """用LLM改写查询语句，提升检索效果"""
        if not self.search_query_prompt:
            return [user_message]
        prompt = self.search_query_prompt.replace("{user_message}", user_message)
        try:
            result = llm_client.chat(user_message=prompt)
            clean = result.strip().strip("```json").strip("```").strip()
            queries = json.loads(clean)
            if isinstance(queries, list):
                return queries
        except Exception:
            pass
        return [user_message]


retriever_agent = RetrieverAgent()
