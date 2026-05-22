"""
Vector Store — ChromaDB 向量知识库管理
支持3个Collection: course_docs, protocol_specs, misconceptions
"""
import os
from typing import List, Optional

try:
    import chromadb
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "data/chroma_db")


class VectorStore:
    """ChromaDB向量知识库封装"""

    def __init__(self):
        self.client = None
        self.collections = {}
        self._init_client()

    def _init_client(self):
        if not HAS_CHROMA:
            print("[VectorStore] chromadb未安装，使用内存模式")
            return
        try:
            if os.path.exists(CHROMA_PERSIST_DIR):
                self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
            else:
                self.client = chromadb.Client()  # Ephemeral
            # 初始化3个Collection
            for name in ["course_docs", "protocol_specs", "misconceptions"]:
                self.collections[name] = self.client.get_or_create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"}
                )
            print(f"[VectorStore] 初始化成功，3个Collection已就绪")
        except Exception as e:
            print(f"[VectorStore] 初始化失败: {e}")

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        ids: List[str],
        metadatas: Optional[List[dict]] = None,
    ):
        if not self.client or collection_name not in self.collections:
            return 0
        try:
            self.collections[collection_name].add(
                documents=documents,
                ids=ids,
                metadatas=metadatas or [{}] * len(documents),
            )
            return len(documents)
        except Exception as e:
            print(f"[VectorStore] add_documents失败: {e}")
            return 0

    def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
    ) -> dict:
        if not self.client or collection_name not in self.collections:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        try:
            col = self.collections[collection_name]
            if col.count() == 0:
                return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
            return col.query(query_texts=[query], n_results=min(n_results, col.count()))
        except Exception as e:
            print(f"[VectorStore] search失败: {e}")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

    def get_collection_count(self, collection_name: str) -> int:
        if not self.client or collection_name not in self.collections:
            return 0
        try:
            return self.collections[collection_name].count()
        except Exception:
            return 0

    def search_all(self, query: str, n_results: int = 3) -> dict:
        """在所有Collection中检索，返回合并结果"""
        results = {"knowledge": [], "misconceptions": []}
        for col_name, key in [("course_docs", "knowledge"), ("protocol_specs", "knowledge"), ("misconceptions", "misconceptions")]:
            res = self.search(col_name, query, n_results)
            for i, doc in enumerate(res.get("documents", [[]])[0] if res.get("documents") else []):
                meta = {}
                if res.get("metadatas") and res["metadatas"][0]:
                    meta = res["metadatas"][0][i] if i < len(res["metadatas"][0]) else {}
                results[key].append({"content": doc, "metadata": meta})
        return results


vector_store = VectorStore()
