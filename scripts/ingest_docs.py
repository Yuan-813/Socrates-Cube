"""Ingest cleaned markdown and misconception data into the KB search index."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.loopse.kb.vector_store import vector_store  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

CLEANED_DIR = ROOT / "data" / "cleaned"
MISCONCEPTIONS_FILE = ROOT / "data" / "raw" / "misconceptions.json"
CHUNK_SIZE = 900
OVERLAP = 140


def _split_text(text: str) -> list[str]:
    sections = re.split(r"\n(?=#{1,3}\s)", text)
    chunks: list[str] = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        if len(section) <= CHUNK_SIZE:
            chunks.append(section)
            continue
        start = 0
        while start < len(section):
            end = min(start + CHUNK_SIZE, len(section))
            chunks.append(section[start:end].strip())
            if end >= len(section):
                break
            start = max(0, end - OVERLAP)
    return [chunk for chunk in chunks if len(chunk) >= 80]


def _doc_id(source: str, index: int) -> str:
    return hashlib.sha1(f"{source}:{index}".encode("utf-8")).hexdigest()[:20]


def _collection_for_file(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")[:800]
    match = re.search(r"Collection:\s*(\w+)", text)
    if match:
        return match.group(1)
    return "course_docs"


def ingest_course_docs(dry_run: bool = False) -> dict[str, int]:
    counts = {"course_docs": 0, "protocol_specs": 0}
    if not CLEANED_DIR.exists():
        log.warning("data/cleaned does not exist")
        return counts

    for path in sorted(CLEANED_DIR.glob("*.md")):
        raw = path.read_text(encoding="utf-8", errors="ignore")
        chunks = _split_text(raw)
        collection = _collection_for_file(path)
        if collection not in counts:
            collection = "course_docs"
        log.info("%s -> %s chunks=%d", path.name, collection, len(chunks))
        if not dry_run and chunks:
            ids = [_doc_id(path.name, index) for index in range(len(chunks))]
            metadatas = [
                {
                    "source": path.name,
                    "chapter": path.stem,
                    "chunk_index": index,
                    "collection": collection,
                }
                for index in range(len(chunks))
            ]
            vector_store.add_documents(collection, chunks, metadatas, ids)
        counts[collection] += len(chunks)
    return counts


def ingest_misconceptions(dry_run: bool = False) -> int:
    if not MISCONCEPTIONS_FILE.exists():
        log.warning("misconceptions file missing: %s", MISCONCEPTIONS_FILE)
        return 0
    items = json.loads(MISCONCEPTIONS_FILE.read_text(encoding="utf-8"))
    docs = []
    ids = []
    metas = []
    for item in items:
        ids.append(item.get("id") or _doc_id("misconception", len(ids)))
        docs.append(
            "\n".join(
                [
                    f"知识点：{item.get('knowledge_point') or item.get('knowledge_node', '')}",
                    f"常见误区：{item.get('misconception', '')}",
                    f"错误类型：{item.get('error_type', '')}",
                    f"正确理解：{item.get('correct_answer') or item.get('correct_concept', '')}",
                ]
            )
        )
        metas.append(
            {
                "knowledge_point": item.get("knowledge_point") or item.get("knowledge_node", ""),
                "error_type": item.get("error_type", ""),
                "chapter": item.get("chapter", ""),
            }
        )
    if not dry_run and docs:
        vector_store.add_documents("misconceptions", docs, metas, ids)
    return len(docs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    if args.reset and not args.dry_run:
        vector_store.reset()

    doc_counts = ingest_course_docs(dry_run=args.dry_run)
    misc_count = ingest_misconceptions(dry_run=args.dry_run)
    log.info(
        "KB ingest complete: course_docs=%d protocol_specs=%d misconceptions=%d",
        doc_counts["course_docs"],
        doc_counts["protocol_specs"],
        misc_count,
    )
    if not args.dry_run:
        log.info(
            "Index counts: course_docs=%d protocol_specs=%d misconceptions=%d",
            vector_store.count("course_docs"),
            vector_store.count("protocol_specs"),
            vector_store.count("misconceptions"),
        )


if __name__ == "__main__":
    main()
