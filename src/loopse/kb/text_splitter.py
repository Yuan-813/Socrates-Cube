"""Text chunking utilities for knowledge-base ingestion."""
from __future__ import annotations

import re

DEFAULT_CHUNK_SIZE = 900
DEFAULT_OVERLAP = 140
MIN_CHUNK_LEN = 80


def split_text(
    text: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    min_chunk_len: int = MIN_CHUNK_LEN,
) -> list[str]:
    """Split markdown/plain text into retrieval-sized chunks.

    Splits on ``##`` / ``###`` headings first, then further splits long
    sections with a sliding window.
    """
    sections = re.split(r"\n(?=#{1,3}\s)", text)
    chunks: list[str] = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        if len(section) <= chunk_size:
            chunks.append(section)
            continue
        start = 0
        while start < len(section):
            end = min(start + chunk_size, len(section))
            chunks.append(section[start:end].strip())
            if end >= len(section):
                break
            start = max(0, end - overlap)
    return [chunk for chunk in chunks if len(chunk) >= min_chunk_len]
