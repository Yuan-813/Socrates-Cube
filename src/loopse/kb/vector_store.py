"""
向量数据库封装 —— ChromaDB 三个 Collection 统一管理
collections: course_docs / protocol_specs / misconceptions
"""
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = os.getenv("CHROMA_PATH", "data/vector_db")


class VectorStore:
    """ChromaDB 封装，暴露简单的 add / search 接口"""

    COLLECTIONS = ["course_docs", "protocol_specs", "misconceptions"]

    def __init__(self, persist_dir: str = CHROMA_PATH):
        self.client = chromadb.PersistentClient(path=persist_dir)
        # 预先获取（若不存在则创建）三个 collection
        self._collections: Dict[str, Any] = {}
        for name in self.COLLECTIONS:
            self._collections[name] = self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[dict],
        ids: List[str],
    ):
        col = self._collections.get(collection_name)
        if col is None:
            raise ValueError(f"未知 collection：{collection_name}")
        col.add(documents=documents, metadatas=metadatas, ids=ids)

    def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        where: Optional[dict] = None,
    ) -> dict:
        col = self._collections.get(collection_name)
        if col is None:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        kwargs = {"query_texts": [query], "n_results": n_results}
        if where:
            kwargs["where"] = where
        try:
            return col.query(**kwargs)
        except Exception:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    def count(self, collection_name: str) -> int:
        col = self._collections.get(collection_name)
        return col.count() if col else 0


# 全局单例
vector_store = VectorStore()
