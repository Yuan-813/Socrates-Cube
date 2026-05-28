"""Optional ChromaDB vector store wrapper."""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

CHROMA_PATH = os.getenv("CHROMA_PATH", "data/vector_db")


class VectorStore:
    """Provides a stable add/search API even when chromadb is not installed."""

    COLLECTIONS = ["course_docs", "protocol_specs", "misconceptions"]

    def __init__(self, persist_dir: str = CHROMA_PATH):
        self.available = False
        self.client: Any = None
        self._collections: dict[str, Any] = {}
        try:
            import chromadb

            self.client = chromadb.PersistentClient(path=persist_dir)
            for name in self.COLLECTIONS:
                self._collections[name] = self.client.get_or_create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"},
                )
            self.available = True
        except Exception as exc:
            logger.warning("ChromaDB unavailable; vector search will use empty fallback: %s", exc)

    def add_documents(
        self,
        collection_name: str,
        documents: list[str],
        metadatas: list[dict],
        ids: list[str],
    ) -> None:
        col = self._collections.get(collection_name)
        if col is None:
            logger.info("skip vector insert because collection is unavailable: %s", collection_name)
            return
        col.add(documents=documents, metadatas=metadatas, ids=ids)

    def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        where: Optional[dict] = None,
    ) -> list[dict]:
        col = self._collections.get(collection_name)
        if col is None:
            return []
        kwargs: dict[str, Any] = {"query_texts": [query], "n_results": n_results}
        if where:
            kwargs["where"] = where
        try:
            raw = col.query(**kwargs)
        except Exception as exc:
            logger.warning("vector search failed collection=%s: %s", collection_name, exc)
            return []
        docs = raw.get("documents", [[]])[0]
        metas = raw.get("metadatas", [[]])[0]
        distances = raw.get("distances", [[]])[0]
        return [
            {
                "document": doc,
                "metadata": metas[index] if index < len(metas) else {},
                "distance": distances[index] if index < len(distances) else None,
            }
            for index, doc in enumerate(docs)
        ]

    def count(self, collection_name: str) -> int:
        col = self._collections.get(collection_name)
        return col.count() if col else 0


vector_store = VectorStore()
