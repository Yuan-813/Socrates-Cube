"""文档处理器：将文本内容切块并准备入库。

支持两种输入格式：
- 纯文本：按字符数切块（500字符/块，50字符重叠）
- Markdown：先按标题分割，再对过长段落按字符数切块

扩展支持（可选）：
- MinerU (magic-pdf) 高精度解析：公式/表格/图文混合 PDF
  开源地址：https://github.com/opendatalab/MinerU
  安装：pip install magic-pdf[full] --cache-dir D:\\pip-cache
  未安装时自动降级为 PyMuPDF

- OpenMAIC 架构参考：清华大学 MAIC 实验室多智能体教学平台
  本模块的文档切块策略参考 OpenMAIC 的语义分块思想
  开源地址：https://github.com/THU-MAIC/OpenMAIC
"""
from __future__ import annotations

import hashlib
import re
from typing import Optional


def process_text(
    text: str,
    source: str = "user_upload",
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[dict]:
    """将纯文本切成固定大小的块，返回可直接入库的文档列表。

    Args:
        text: 原始文本内容
        source: 来源标注（显示给用户和 AI 引用时使用）
        chunk_size: 每个块的目标字符数
        overlap: 相邻块的重叠字符数（保持上下文连贯性）

    Returns:
        列表，每项包含 {"id", "document", "metadata"}
    """
    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        # 尽量在句尾断开，避免截断单词/句子
        if end < len(text):
            # 优先在句号/换行处断开
            break_pos = _find_break(chunk)
            if break_pos > chunk_size // 2:
                chunk = chunk[:break_pos + 1]
        chunks.append(chunk.strip())
        start += len(chunk) - overlap
        if start >= len(text):
            break

    return _build_docs(chunks, source)


def extract_from_markdown(md_text: str, source: str = "user_upload") -> list[dict]:
    """将 Markdown 文本按标题分割，对过长章节再切块。

    Args:
        md_text: Markdown 格式文本
        source: 来源标注

    Returns:
        列表，每项包含 {"id", "document", "metadata"}
    """
    md_text = md_text.strip()
    if not md_text:
        return []

    # 按 h1/h2/h3 标题分割
    sections = re.split(r"(?m)^(#{1,3}\s+.+)$", md_text)
    chunks: list[str] = []
    current_title = ""
    current_body = ""

    for part in sections:
        heading_match = re.match(r"^(#{1,3})\s+(.+)$", part.strip())
        if heading_match:
            if current_body.strip():
                text = f"{current_title}\n{current_body}".strip() if current_title else current_body.strip()
                chunks.extend(_split_if_long(text))
            current_title = part.strip()
            current_body = ""
        else:
            current_body += part

    # 最后一段
    if current_body.strip():
        text = f"{current_title}\n{current_body}".strip() if current_title else current_body.strip()
        chunks.extend(_split_if_long(text))

    return _build_docs(chunks, source)


def _split_if_long(text: str, max_len: int = 500, overlap: int = 50) -> list[str]:
    """若文本超过最大长度，进一步切块；否则直接返回单元素列表。"""
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_len:
        return [text]

    result: list[str] = []
    start = 0
    while start < len(text):
        end = start + max_len
        chunk = text[start:end]
        if end < len(text):
            break_pos = _find_break(chunk)
            if break_pos > max_len // 2:
                chunk = chunk[:break_pos + 1]
        result.append(chunk.strip())
        start += len(chunk) - overlap
        if start >= len(text):
            break
    return [c for c in result if c]


def _find_break(text: str) -> int:
    """在文本末尾附近找到最合适的断点（句号、换行）。"""
    for i in range(len(text) - 1, max(len(text) // 2, 0), -1):
        if text[i] in ("。", ".", "\n", "！", "？", "!", "?"):
            return i
    return len(text) - 1


def _build_docs(chunks: list[str], source: str) -> list[dict]:
    """将文本块列表转换为入库格式。"""
    docs = []
    for idx, chunk in enumerate(chunks):
        if not chunk:
            continue
        doc_id = hashlib.md5(f"{source}::{idx}::{chunk[:50]}".encode()).hexdigest()
        docs.append({
            "id": doc_id,
            "document": chunk,
            "metadata": {
                "source": source,
                "chunk_index": idx,
                "char_count": len(chunk),
            },
        })
    return docs
