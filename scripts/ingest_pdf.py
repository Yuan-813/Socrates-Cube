#!/usr/bin/env python3
"""
PDF 批量解析入库脚本（Socrates-Cube）

集成 MinerU（优先）→ PyMuPDF（降级）→ 纯文本读取（最终降级）

用法:
    # 单个 PDF
    python scripts/ingest_pdf.py path/to/book.pdf

    # 批量处理目录
    python scripts/ingest_pdf.py path/to/pdf_dir/ --pattern "*.pdf"

    # 使用 MinerU 高质量解析（需要 pip install magic-pdf）
    python scripts/ingest_pdf.py book.pdf --use-mineru

    # 指定向量库路径
    python scripts/ingest_pdf.py book.pdf --chroma-path ./chroma_db

    # 批量处理多个文件
    python scripts/ingest_pdf.py book1.pdf book2.pdf --collection user_uploads
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
import uuid
from pathlib import Path

# 确保能找到 loopse 包（从项目根目录运行）
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("ingest_pdf")


# ── 文本提取 ────────────────────────────────────────────────────────────────

def extract_text_mineru(pdf_path: str, backend: str = "pipeline") -> str:
    """使用 MinerU（magic-pdf）提取 PDF 文本（高质量，支持图文混合）。

    优先尝试新版 mineru_parser 适配模块（v3.4+ CLI/SDK），
    若不可用则降级到旧版 magic_pdf 直接调用。

    Args:
        pdf_path: PDF 文件路径
        backend: 解析后端 ("pipeline" | "vlm" | "hybrid")
    """
    # 优先尝试新版 mineru_parser 适配模块
    try:
        from loopse.kb.mineru_parser import parse_pdf_with_mineru
        logger.info("[MinerU] 使用 mineru_parser 适配模块（backend=%s）: %s", backend, pdf_path)
        result = parse_pdf_with_mineru(pdf_path, backend=backend)
        if result["status"] == "success" and result["content"]:
            text = result["content"].get("markdown") or result["content"].get("text", "")
            if text:
                logger.info("[MinerU] 解析完成，字符数: %d（后端: %s）",
                            len(text), result["metadata"].get("backend_used", backend))
                return text
    except ImportError:
        pass
    except Exception as e:
        logger.warning("[MinerU] mineru_parser 调用失败: %s", e)

    # 降级：旧版 magic_pdf 直接调用
    try:
        import magic_pdf.data.dataset as ds
        from magic_pdf.pipe.StandardJsonMidDataPipe import StandardJsonMidDataPipe
        from magic_pdf.config.make_content_config import DropMode
        import tempfile

        logger.info("[MinerU] 降级到 magic_pdf 直接调用: %s", pdf_path)
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        output_dir = tempfile.mkdtemp()
        image_dir = os.path.join(output_dir, "images")
        os.makedirs(image_dir, exist_ok=True)

        ds_obj = ds.PymuPdfDataset(pdf_bytes)
        pipe = StandardJsonMidDataPipe(ds_obj, [], {"_pdf_type": "", "model_list": []})
        pipe.pipe_classify()
        pipe.pipe_parse()
        md_content = pipe.pipe_mk_markdown(image_dir, drop_mode=DropMode.NONE)
        text = md_content if isinstance(md_content, str) else ""
        logger.info("[MinerU] 解析完成，字符数: %d", len(text))
        return text
    except ImportError:
        logger.warning("[MinerU] 未安装，跳过（pip install mineru>=3.4.0 或 magic-pdf）")
        return ""
    except Exception as e:
        logger.warning("[MinerU] 解析失败: %s", e)
        return ""


def extract_text_mineru_api(pdf_path: str) -> str:
    """MinerU 3.4+ REST API 云端解析（无需本地安装，需 MINERU_API_KEY）。

    Ref: https://github.com/opendatalab/MinerU
    支持: PDF/DOCX/PPTX/XLSX → Markdown/JSON。
    VLM+OCR 双引擎，109种语言，公式->LaTeX，表格->HTML。
    """
    api_key = os.getenv("MINERU_API_KEY", "").strip()
    base_url = os.getenv("MINERU_API_URL", "https://api.mineru.net/v1").strip()
    if not api_key:
        logger.debug("[MinerU-API] MINERU_API_KEY 未配置，跳过云端解析")
        return ""

    try:
        import urllib.request
        import json
        import base64
        logger.info("[MinerU-API] 调用云端解析 API (backend=hybrid): %s", pdf_path)
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        pdf_b64 = base64.b64encode(pdf_bytes).decode()
        body = json.dumps({
            "file": pdf_b64,
            "filename": os.path.basename(pdf_path),
            "backend": "hybrid",
            "parsing_strength": "medium",
            "output_format": "markdown",
        }).encode()
        request = urllib.request.Request(
            f"{base_url}/parse",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as resp:
            data = json.loads(resp.read().decode())
        text = data.get("content", {}).get("markdown") or data.get("markdown", "")
        if text:
            logger.info("[MinerU-API] 解析完成，字符数: %d", len(text))
        return text
    except Exception as e:
        logger.warning("[MinerU-API] 云端解析失败: %s", e)
        return ""


def extract_text_pymupdf(pdf_path: str) -> str:
    """使用 PyMuPDF 提取 PDF 文本（中等质量，速度快）。"""
    try:
        import fitz  # PyMuPDF
        logger.info("[PyMuPDF] 开始解析: %s", pdf_path)
        doc = fitz.open(pdf_path)
        parts = []
        for i, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                parts.append(f"\n--- 第 {i + 1} 页 ---\n{text}")
        doc.close()
        text = "\n".join(parts)
        logger.info("[PyMuPDF] 解析完成，字符数: %d", len(text))
        return text
    except ImportError:
        logger.warning("[PyMuPDF] 未安装，跳过（pip install PyMuPDF）")
        return ""
    except Exception as e:
        logger.warning("[PyMuPDF] 解析失败: %s", e)
        return ""


def extract_text(pdf_path: str, use_mineru: bool = False, mineru_backend: str = "pipeline") -> str:
    """提取 PDF 文本。

    优先级：
    1. MinerU 云端 REST API（配置 MINERU_API_KEY + --use-mineru）
    2. 本地 MinerU（magic-pdf/mineru>=3.4 已安装）
    3. PyMuPDF（中等质量，快速）
    4. 失败报错
    """
    if use_mineru:
        text = extract_text_mineru_api(pdf_path)
        if text:
            return text
        text = extract_text_mineru(pdf_path, backend=mineru_backend)
        if text:
            return text

    text = extract_text_pymupdf(pdf_path)
    if text:
        return text

    raise RuntimeError(f"无法从 {pdf_path} 提取文本，请安装 magic-pdf 或 PyMuPDF")


# ── 文本分块 ────────────────────────────────────────────────────────────────

def chunk_text(text: str, source: str, chunk_size: int = 800, overlap: int = 100) -> list[dict]:
    """将长文本按固定大小分块，返回 ChromaDB 可用格式。"""
    chunks = []
    start = 0
    total = len(text)
    while start < total:
        end = min(start + chunk_size, total)
        # 优先在句号/换行处截断
        if end < total:
            for sep in ["\n\n", "。", "\n", ".", " "]:
                last_sep = text.rfind(sep, start, end)
                if last_sep > start + chunk_size // 2:
                    end = last_sep + len(sep)
                    break
        chunk = text[start:end].strip()
        if chunk:
            chunks.append({
                "id": f"pdf_{uuid.uuid4().hex[:12]}",
                "document": chunk,
                "metadata": {
                    "source": source,
                    "chunk_index": len(chunks),
                    "char_start": start,
                    "char_end": end,
                },
            })
        start = end - overlap if end < total else total
    return chunks


# ── 入库 ────────────────────────────────────────────────────────────────────

def ingest_to_chromadb(
    chunks: list[dict],
    collection: str = "user_uploads",
    chroma_path: str = "./chroma_db",
    batch_size: int = 50,
):
    """将文本块批量写入 ChromaDB 向量库。"""
    try:
        import chromadb
    except ImportError:
        raise RuntimeError("请安装 ChromaDB: pip install chromadb")

    client = chromadb.PersistentClient(path=chroma_path)
    col = client.get_or_create_collection(
        name=collection,
        metadata={"hnsw:space": "cosine"},
    )

    # 批量写入
    total = len(chunks)
    ingested = 0
    for i in range(0, total, batch_size):
        batch = chunks[i:i + batch_size]
        col.upsert(
            ids=[c["id"] for c in batch],
            documents=[c["document"] for c in batch],
            metadatas=[c["metadata"] for c in batch],
        )
        ingested += len(batch)
        logger.info("[ChromaDB] 已入库 %d/%d 块", ingested, total)

    return ingested


def ingest_via_api(
    chunks: list[dict],
    api_url: str = "http://localhost:8000/api/v1/kb/upload",
    source: str = "script_upload",
):
    """通过 REST API 将文本块写入（适合远程部署）。"""
    try:
        import urllib.request
        import json
        full_text = "\n\n".join(c["document"] for c in chunks)
        payload = json.dumps({
            "content": full_text,
            "source": source,
            "is_markdown": False,
        }).encode("utf-8")
        req = urllib.request.Request(
            api_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            logger.info("[API] 入库成功: %s", result)
            return result.get("chunks_added", 0)
    except Exception as e:
        logger.error("[API] 入库失败: %s", e)
        return 0


# ── 主函数 ──────────────────────────────────────────────────────────────────

def process_pdf(
    pdf_path: str,
    use_mineru: bool = False,
    mineru_backend: str = "pipeline",
    collection: str = "user_uploads",
    chroma_path: str = "./chroma_db",
    chunk_size: int = 800,
    use_api: bool = False,
    api_url: str = "http://localhost:8000/api/v1/kb/upload",
) -> dict:
    """处理单个 PDF 文件并入库，返回统计信息。"""
    start_time = time.time()
    path = Path(pdf_path)
    if not path.exists():
        return {"file": pdf_path, "success": False, "error": "文件不存在"}

    source = path.stem  # 用文件名（无扩展名）作来源标注
    logger.info("=== 开始处理: %s ===", path.name)

    try:
        # 提取文本
        text = extract_text(str(path), use_mineru=use_mineru, mineru_backend=mineru_backend)
        logger.info("提取文本完成，共 %d 字", len(text))

        # 分块
        chunks = chunk_text(text, source=source, chunk_size=chunk_size)
        logger.info("分块完成，共 %d 块", len(chunks))

        # 入库
        if use_api:
            count = ingest_via_api(chunks, api_url=api_url, source=source)
        else:
            count = ingest_to_chromadb(chunks, collection=collection, chroma_path=chroma_path)

        elapsed = time.time() - start_time
        logger.info("=== 完成: %s | 入库 %d 块 | 耗时 %.1fs ===", path.name, count, elapsed)
        return {
            "file": pdf_path,
            "success": True,
            "source": source,
            "char_count": len(text),
            "chunks_added": count,
            "elapsed_s": round(elapsed, 1),
        }
    except Exception as e:
        logger.error("处理失败: %s", e)
        return {"file": pdf_path, "success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Socrates-Cube PDF 批量解析入库工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("inputs", nargs="+", help="PDF 文件路径或目录")
    parser.add_argument("--use-mineru", action="store_true", help="使用 MinerU 高质量解析")
    parser.add_argument("--mineru-backend", default="pipeline", choices=["pipeline", "vlm", "hybrid"],
                        help="MinerU 解析后端（默认：pipeline）。vlm 需 GPU，hybrid 自动混合")
    parser.add_argument("--collection", default="user_uploads", help="向量库集合名称（默认：user_uploads）")
    parser.add_argument("--chroma-path", default="./chroma_db", help="ChromaDB 数据目录")
    parser.add_argument("--chunk-size", type=int, default=800, help="每块字符数（默认：800）")
    parser.add_argument("--pattern", default="*.pdf", help="目录扫描 glob 模式（默认：*.pdf）")
    parser.add_argument("--use-api", action="store_true", help="通过 REST API 入库（适合远程部署）")
    parser.add_argument("--api-url", default="http://localhost:8000/api/v1/kb/upload", help="API 地址")

    args = parser.parse_args()

    # 收集所有 PDF 路径
    pdf_files: list[str] = []
    for inp in args.inputs:
        p = Path(inp)
        if p.is_dir():
            found = list(p.glob(args.pattern))
            pdf_files.extend(str(f) for f in found)
            logger.info("目录 %s 中找到 %d 个 PDF", inp, len(found))
        elif p.is_file():
            pdf_files.append(str(p))
        else:
            logger.warning("路径不存在: %s", inp)

    if not pdf_files:
        logger.error("没有找到可处理的 PDF 文件")
        sys.exit(1)

    logger.info("共 %d 个 PDF 待处理", len(pdf_files))

    results = []
    for pdf_path in pdf_files:
        result = process_pdf(
            pdf_path,
            use_mineru=args.use_mineru,
            mineru_backend=args.mineru_backend,
            collection=args.collection,
            chroma_path=args.chroma_path,
            chunk_size=args.chunk_size,
            use_api=args.use_api,
            api_url=args.api_url,
        )
        results.append(result)

    # 汇总
    success_count = sum(1 for r in results if r["success"])
    total_chunks = sum(r.get("chunks_added", 0) for r in results)
    print(f"\n{'=' * 50}")
    print(f"处理完成: {success_count}/{len(results)} 成功 | 共入库 {total_chunks} 个知识块")
    for r in results:
        status = "✅" if r["success"] else "❌"
        if r["success"]:
            print(f"  {status} {r['file']} → {r['chunks_added']} 块 ({r['elapsed_s']}s)")
        else:
            print(f"  {status} {r['file']} → 失败: {r.get('error', '')}")
    print("=" * 50)


if __name__ == "__main__":
    main()
