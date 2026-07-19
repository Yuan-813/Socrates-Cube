"""M4 PDF智能书架 API。

功能：
- GET  /api/v1/books          — 获取预置书单 + 用户上传书籍列表
- POST /api/v1/books/upload   — 上传 PDF，提取文本并分块存入知识库
- POST /api/v1/books/ask      — 基于书籍内容的 RAG 问答
- GET  /api/v1/books/{book_id}/chunks — 获取某本书的分块列表（调试/标注用）

PDF解析引擎优先级：
  1. MinerU v3.4 API（高精度，支持OCR/公式/表格）— 需要 MINERU_API_KEY
     GitHub: https://github.com/opendatalab/MinerU
     v3.4新特性: PP-OCRv6(精度提11%)、hybrid-engine(支持effort=medium/high)
     MCP Server: 支持 Cursor / Claude Desktop / Windsurf 集成
     支持: VLM+OCR双引擎、109种语言、扬行文档、跨页表格合并、公式转LaTeX
  2. OpenDataloader-PDF（配套数据加载）— https://github.com/opendataloader-project/opendataloader-pdf
  3. pypdf（基础文本提取，免安装）— MinerU未配置时的默认方案
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/books", tags=["books"])

# 书籍数据存储目录
BOOKS_DIR = Path("data/books")
BOOKS_DIR.mkdir(parents=True, exist_ok=True)
BOOKS_INDEX_FILE = BOOKS_DIR / "index.json"

# MinerU 配置（高精度PDF解析）
_MINERU_KEY = os.getenv("MINERU_API_KEY", "")
_MINERU_BASE = "https://mineru.net/api/v4"

# ── 预置书单 ──────────────────────────────────────────────────────────
PRESET_BOOKS: list[dict[str, Any]] = [
    {
        "book_id": "preset_001",
        "title": "计算机网络：自顶向下方法",
        "author": "James F. Kurose / Keith W. Ross",
        "edition": "第8版",
        "cover_emoji": "📘",
        "tags": ["计算机网络", "TCP/IP", "经典教材"],
        "description": "全球最广泛使用的计算机网络教材，从应用层到物理层逐层讲解。",
        "is_preset": True,
        "chunks": [],
    },
    {
        "book_id": "preset_002",
        "title": "TCP/IP详解 卷1：协议",
        "author": "W. Richard Stevens",
        "edition": "第2版",
        "cover_emoji": "📗",
        "tags": ["TCP/IP", "协议分析", "深度参考"],
        "description": "TCP/IP协议族权威参考，深入剖析各层协议实现细节。",
        "is_preset": True,
        "chunks": [],
    },
    {
        "book_id": "preset_003",
        "title": "路由与交换技术",
        "author": "贾铁军 等",
        "edition": "第3版",
        "cover_emoji": "📙",
        "tags": ["路由", "交换", "华为认证"],
        "description": "面向华为HCIA/HCIP认证，涵盖OSPF、BGP、VLAN等核心技术。",
        "is_preset": True,
        "chunks": [],
    },
    {
        "book_id": "preset_004",
        "title": "HCIA-Datacom学习指南",
        "author": "华为技术有限公司",
        "edition": "官方版",
        "cover_emoji": "🔴",
        "tags": ["华为认证", "HCIA", "数通"],
        "description": "华为官方HCIA-Datacom认证备考指南，含题库与实验。",
        "is_preset": True,
        "chunks": [],
    },
    {
        "book_id": "preset_005",
        "title": "Cisco CCNA 200-301 Official Guide",
        "author": "Wendell Odom",
        "edition": "第1版",
        "cover_emoji": "🔵",
        "tags": ["Cisco", "CCNA", "认证"],
        "description": "思科CCNA官方认证指南，全面覆盖200-301考试范围。",
        "is_preset": True,
        "chunks": [],
    },
]


# ── 工具函数 ──────────────────────────────────────────────────────────
def _load_index() -> dict[str, dict]:
    """加载用户上传书籍索引。"""
    if BOOKS_INDEX_FILE.exists():
        try:
            return json.loads(BOOKS_INDEX_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_index(index: dict[str, dict]) -> None:
    BOOKS_INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    """使用 pypdf 提取 PDF 全文（基础方案，MinerU 未配置时使用）。"""
    try:
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages: list[str] = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages.append(text)
        return "\n\n".join(pages)
    except Exception as exc:
        logger.warning("[Books] PDF 文本提取失败: %s", exc)
        return ""


async def _extract_pdf_mineru(pdf_bytes: bytes, filename: str = "document.pdf", effort: str = "medium") -> str:
    """使用 MinerU v3.4 API 高精度解析 PDF。

    来源: https://github.com/opendatalab/MinerU
    v3.4 新特性:
      - PP-OCRv6 模型（OmniDocBench v1.6 精度提11%，OCR处理速度提100%）
      - hybrid-engine: effort=medium(默认速度优先) / effort=high(最高精度+图片分析)
      - 自动模型源选择，本地缓存复用减少重复下载
    MCP Server: 支持 Cursor/Claude Desktop/Windsurf 集成
    支持: VLM+OCR双引擎、109种语言、扬行文档、跨页表格合并、公式转LaTeX

    Args:
        effort: 解析强度 medium(速度优先) | high(精度优先+图片分析)
    """
    if not _MINERU_KEY:
        return ""
    try:
        import asyncio
        import io as _io
        import zipfile
        import httpx

        hdrs = {"Authorization": f"Bearer {_MINERU_KEY}", "Content-Type": "application/json"}

        # Step 1: 获取预签名上传 URL
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                f"{_MINERU_BASE}/file/batch_urls",
                headers=hdrs,
                json={
                    "enable_formula": True,
                    "enable_table": True,
                    "language": "ch",  # v3.4: ch模型覆盖中英日文等主要语言
                    "parse_method": "auto",  # auto自动选择hybrid/pipeline
                    "effort": effort,  # v3.4: medium(35%~220%速度提升) / high(最高精度)
                    "files": [{"name": filename, "is_ocr": True, "data_id": "socrates"}],
                },
            )
        if r.status_code != 200:
            logger.warning("[MinerU] batch_urls 失败 status=%d", r.status_code)
            return ""
        resp_d = r.json().get("data", {})
        batch_id = resp_d.get("batch_id", "")
        file_infos = resp_d.get("files", [])
        if not batch_id or not file_infos:
            return ""
        presigned_url = file_infos[0].get("presigned_url", "")
        if not presigned_url:
            return ""

        # Step 2: 上传 PDF 内容到 S3预签名 URL
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.put(presigned_url, content=pdf_bytes, headers={"Content-Type": "application/pdf"})
        if r.status_code not in (200, 204):
            logger.warning("[MinerU] 文件上传失败 status=%d", r.status_code)
            return ""

        # Step 3: 轮询解析任务状态（最多 120 秒）
        auth_hdr = {"Authorization": f"Bearer {_MINERU_KEY}"}
        for attempt in range(40):
            await asyncio.sleep(3)
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.get(f"{_MINERU_BASE}/extract/task/{batch_id}", headers=auth_hdr)
            result = r.json().get("data", {})
            state = result.get("state", "")
            logger.debug("[MinerU] 轮询 #%d state=%s", attempt, state)

            if state == "done":
                files_result = result.get("files", [])
                if not files_result:
                    break
                zip_url = files_result[0].get("full_zip_url", "")
                if zip_url:
                    async with httpx.AsyncClient(timeout=60) as c:
                        zr = await c.get(zip_url)
                    with zipfile.ZipFile(_io.BytesIO(zr.content)) as z:
                        md_files = sorted(
                            [n for n in z.namelist() if n.endswith(".md")],
                            key=lambda x: z.getinfo(x).file_size, reverse=True
                        )
                        if md_files:
                            content = z.read(md_files[0]).decode("utf-8", errors="replace")
                            logger.info("[MinerU] 解析完成 chars=%d", len(content))
                            return content
                # 尝试直接 md_url
                md_url = files_result[0].get("md_url", "")
                if md_url:
                    async with httpx.AsyncClient(timeout=30) as c:
                        mr = await c.get(md_url)
                    return mr.text
                break
            elif state in ("failed", "error"):
                logger.warning("[MinerU] 解析失败 batch_id=%s", batch_id)
                break
        return ""
    except Exception as exc:
        logger.warning("[MinerU] API 调用异常: %s", exc)
        return ""


def _chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> list[dict]:
    """将文本切分为 chunk_size 字符的块（支持重叠）。"""
    chunks: list[dict] = []
    start = 0
    idx = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append({
                "chunk_id": idx,
                "text": chunk.strip(),
                "start_char": start,
                "end_char": end,
            })
            idx += 1
        start = end - overlap
    return chunks


def _simple_bm25_search(query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    """极简关键词匹配搜索（无向量库时的 fallback）。"""
    query_terms = set(re.sub(r'\s+', ' ', query.lower()).split())
    scored: list[tuple[float, dict]] = []
    for chunk in chunks:
        text_lower = chunk["text"].lower()
        score = sum(1.0 for t in query_terms if t in text_lower)
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k]]


# ── 路由 ──────────────────────────────────────────────────────────────
@router.get("")
async def list_books():
    """返回预置书单 + 用户上传书籍（不含 chunks，仅元数据）。"""
    user_index = _load_index()
    user_books = [
        {**meta, "is_preset": False}
        for meta in user_index.values()
    ]
    # 预置书籍去掉 chunks 字段（前端不需要完整 chunk 列表）
    preset = [{k: v for k, v in b.items() if k != "chunks"} for b in PRESET_BOOKS]
    return {"books": preset + user_books, "total": len(preset) + len(user_books)}


@router.post("/upload")
async def upload_book(
    file: UploadFile = File(...),
    title: str = Form(""),
    author: str = Form(""),
):
    """上传 PDF 书籍，提取文本并分块存储。"""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 文件")

    pdf_bytes = await file.read()
    if len(pdf_bytes) > 50 * 1024 * 1024:  # 50 MB 限制
        raise HTTPException(status_code=413, detail="文件大小不能超过 50MB")

    book_id = "user_" + hashlib.md5(pdf_bytes[:1024]).hexdigest()[:12]

    # 提取文本：MinerU API 优先（高精度），降级到 pypdf
    safe_filename = (file.filename or "document.pdf").replace(" ", "_")
    full_text = await _extract_pdf_mineru(pdf_bytes, filename=safe_filename)
    parse_engine = "mineru"
    if not full_text:
        full_text = _extract_pdf_text(pdf_bytes)
        parse_engine = "pypdf"
    chunks = _chunk_text(full_text) if full_text else []

    book_title = title.strip() or (file.filename.removesuffix(".pdf") if file.filename else "未命名")
    meta = {
        "book_id": book_id,
        "title": book_title,
        "author": author.strip() or "未知",
        "cover_emoji": "📄",
        "tags": ["用户上传"],
        "description": f"共提取 {len(chunks)} 个文本块（{parse_engine}解析）",
        "chunk_count": len(chunks),
        "uploaded_at": datetime.now().isoformat(),
    }

    # 保存分块到文件
    chunk_file = BOOKS_DIR / f"{book_id}_chunks.json"
    chunk_file.write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")

    # 更新索引
    index = _load_index()
    index[book_id] = meta
    _save_index(index)

    logger.info("[Books] 上传成功: %s | chunks=%d | engine=%s", book_title, len(chunks), parse_engine)
    return {
        "book_id": book_id,
        "title": book_title,
        "chunk_count": len(chunks),
        "parse_engine": parse_engine,
        "message": f"上传成功（{parse_engine}解析，共 {len(chunks)} 个知识块）",
    }


class AskRequest(BaseModel):
    book_id: str
    question: str
    top_k: int = 5


@router.post("/ask")
async def ask_book(req: AskRequest):
    """基于书籍内容 RAG 问答。"""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    # 加载 chunks
    chunks: list[dict] = []
    if req.book_id.startswith("preset_"):
        # 预置书籍暂无 chunks，返回提示
        return {
            "answer": f"预置书籍《{next((b['title'] for b in PRESET_BOOKS if b['book_id'] == req.book_id), req.book_id)}》"
                      "暂未上传 PDF 文件。请上传该书的 PDF 后即可使用 AI 检索功能。",
            "sources": [],
            "book_id": req.book_id,
        }

    chunk_file = BOOKS_DIR / f"{req.book_id}_chunks.json"
    if not chunk_file.exists():
        raise HTTPException(status_code=404, detail="未找到该书籍的文本内容，请重新上传 PDF")

    try:
        chunks = json.loads(chunk_file.read_text(encoding="utf-8"))
    except Exception:
        raise HTTPException(status_code=500, detail="书籍数据读取失败")

    # 检索相关段落
    relevant = _simple_bm25_search(req.question, chunks, top_k=req.top_k)
    if not relevant:
        return {
            "answer": "在该书籍中未找到与您问题相关的内容，请尝试更换关键词。",
            "sources": [],
            "book_id": req.book_id,
        }

    # 构建回答（使用 LLM）
    context = "\n\n---\n\n".join(c["text"] for c in relevant)
    prompt = (
        f"请根据以下书籍段落回答用户问题。\n\n"
        f"【参考段落】\n{context[:3000]}\n\n"
        f"【用户问题】\n{req.question}\n\n"
        f"请给出详细、准确的回答，并指出相关内容在哪个段落中。"
    )

    try:
        from ..core.llm_client import llm_client
        answer_parts: list[str] = []
        async for token in llm_client.async_stream_chat(prompt):
            answer_parts.append(token)
        answer = "".join(answer_parts)
    except Exception as exc:
        logger.warning("[Books] LLM 调用失败，返回摘录: %s", exc)
        answer = f"相关内容摘录：\n\n{relevant[0]['text'][:500]}"

    sources = [{"chunk_id": c["chunk_id"], "preview": c["text"][:150] + "..."} for c in relevant]
    return {"answer": answer, "sources": sources, "book_id": req.book_id}


@router.get("/{book_id}/chunks")
async def get_book_chunks(book_id: str, page: int = 1, page_size: int = 20):
    """分页获取书籍分块（用于调试/AI标注）。"""
    if book_id.startswith("preset_"):
        return {"chunks": [], "total": 0, "message": "预置书籍尚未上传 PDF"}

    chunk_file = BOOKS_DIR / f"{book_id}_chunks.json"
    if not chunk_file.exists():
        raise HTTPException(status_code=404, detail="未找到分块数据")

    chunks = json.loads(chunk_file.read_text(encoding="utf-8"))
    start = (page - 1) * page_size
    return {
        "chunks": chunks[start:start + page_size],
        "total": len(chunks),
        "page": page,
        "page_size": page_size,
    }
