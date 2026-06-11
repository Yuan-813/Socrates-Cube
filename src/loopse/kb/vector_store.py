"""Vector-store facade with a deterministic local fallback index."""
from __future__ import annotations

import json
import logging
import math
import os
import re
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
CHROMA_PATH = Path(os.getenv("CHROMA_PATH", str(ROOT / "data" / "vector_db")))
LOCAL_INDEX_PATH = Path(os.getenv("LOCAL_KB_INDEX", str(ROOT / "data" / "vector_db" / "local_index.json")))


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    latin = re.findall(r"[a-z0-9][a-z0-9_\-./]{1,}", text)
    cjk = re.findall(r"[\u4e00-\u9fff]{2,}", text)
    return latin + cjk


class VectorStore:
    """Stable add/search API.

    If ChromaDB is installed, writes go to Chroma as before. Every write also
    updates a compact JSON index used for local keyword retrieval, so demos and
    tests keep working when vector dependencies are missing or not initialized.
    """

    COLLECTIONS = ["course_docs", "protocol_specs", "misconceptions"]

    def __init__(self, persist_dir: Path = CHROMA_PATH, index_path: Path = LOCAL_INDEX_PATH):
        self.index_path = index_path
        self.available = False
        self.client: Any = None
        self._collections: dict[str, Any] = {}
        self._local_docs: dict[str, list[dict[str, Any]]] = {name: [] for name in self.COLLECTIONS}
        self._load_local_index()
        try:
            import numpy as np

            if not hasattr(np, "float_"):
                np.float_ = np.float64  # type: ignore[attr-defined]
            if not hasattr(np, "int_"):
                np.int_ = np.int64  # type: ignore[attr-defined]
            import chromadb

            self.client = chromadb.PersistentClient(path=str(persist_dir))
            for name in self.COLLECTIONS:
                self._collections[name] = self.client.get_or_create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"},
                )
            self.available = True
        except Exception as exc:
            logger.warning("ChromaDB unavailable; local KB index will be used: %s", exc)

    def _load_local_index(self) -> None:
        if not self.index_path.exists():
            return
        try:
            data = json.loads(self.index_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for name in self.COLLECTIONS:
                    self._local_docs[name] = list(data.get(name, []))
        except Exception as exc:
            logger.warning("failed to load local KB index: %s", exc)

    def _save_local_index(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps(self._local_docs, ensure_ascii=False, indent=2), encoding="utf-8")

    def reset(self, collection_name: Optional[str] = None) -> None:
        names = [collection_name] if collection_name else self.COLLECTIONS
        for name in names:
            self._local_docs[name] = []
            col = self._collections.get(name)
            if col is not None:
                existing = col.get()
                ids = existing.get("ids", [])
                if ids:
                    col.delete(ids=ids)
        self._save_local_index()

    def add_documents(
        self,
        collection_name: str,
        documents: list[str],
        metadatas: list[dict],
        ids: list[str],
    ) -> None:
        if collection_name not in self.COLLECTIONS:
            raise ValueError(f"unknown collection: {collection_name}")
        rows = []
        for index, doc_id in enumerate(ids):
            rows.append(
                {
                    "id": doc_id,
                    "document": documents[index],
                    "metadata": metadatas[index] if index < len(metadatas) else {},
                    "tokens": _tokenize(documents[index] + " " + json.dumps(metadatas[index] if index < len(metadatas) else {}, ensure_ascii=False)),
                }
            )
        existing = {row["id"]: row for row in self._local_docs[collection_name]}
        for row in rows:
            existing[row["id"]] = row
        self._local_docs[collection_name] = list(existing.values())
        self._save_local_index()

        col = self._collections.get(collection_name)
        if col is not None:
            col.upsert(ids=ids, documents=documents, metadatas=metadatas)

    def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        where: Optional[dict] = None,
    ) -> list[dict]:
        col = self._collections.get(collection_name)
        if col is not None:
            try:
                kwargs: dict[str, Any] = {"query_texts": [query], "n_results": n_results}
                if where:
                    kwargs["where"] = where
                raw = col.query(**kwargs)
                docs = raw.get("documents", [[]])[0]
                metas = raw.get("metadatas", [[]])[0]
                distances = raw.get("distances", [[]])[0]
                if docs:
                    return [
                        {
                            "document": doc,
                            "metadata": metas[index] if index < len(metas) else {},
                            "distance": distances[index] if index < len(distances) else None,
                            "source": "chroma",
                        }
                        for index, doc in enumerate(docs)
                    ]
            except Exception as exc:
                logger.warning("vector search failed collection=%s: %s", collection_name, exc)
        return self._search_local(collection_name, query, n_results, where)

    def _search_local(
        self,
        collection_name: str,
        query: str,
        n_results: int,
        where: Optional[dict],
    ) -> list[dict]:
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []
        query_set = set(query_tokens)
        rows = self._local_docs.get(collection_name, [])
        total_docs = max(1, len(rows))
        doc_freq: dict[str, int] = {}
        for row in rows:
            for token in set(row.get("tokens", [])):
                doc_freq[token] = doc_freq.get(token, 0) + 1

        scored = []
        for row in rows:
            metadata = row.get("metadata", {})
            if where and any(metadata.get(k) != v for k, v in where.items()):
                continue
            tokens = row.get("tokens", [])
            if not tokens:
                continue
            counts = {token: tokens.count(token) for token in query_set}
            score = 0.0
            for token, tf in counts.items():
                if tf <= 0:
                    continue
                idf = math.log((1 + total_docs) / (1 + doc_freq.get(token, 0))) + 1
                score += (1 + math.log(tf)) * idf
            if score > 0:
                scored.append((score, row))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "document": row["document"],
                "metadata": row.get("metadata", {}),
                "distance": round(1 / (1 + score), 6),
                "source": "local_index",
            }
            for score, row in scored[:n_results]
        ]

    def count(self, collection_name: str) -> int:
        col = self._collections.get(collection_name)
        if col is not None:
            try:
                return col.count()
            except Exception:
                pass
        return len(self._local_docs.get(collection_name, []))


vector_store = VectorStore()
