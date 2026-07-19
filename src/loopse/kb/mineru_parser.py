"""
MinerU 高精度 PDF 解析器适配模块

基于 MinerU (https://github.com/opendatalab/MinerU) v3.4+
支持多种解析后端：
- pipeline: CPU 友好，精度 86.2%
- vlm: GPU 加速，精度 95.39%
- hybrid: 自动混合，最佳平衡

核心能力：
- 公式 → LaTeX 自动识别
- 表格 → HTML 准确还原
- 多列版面正确处理
- OCR 109种语言支持
"""
import logging
import subprocess
import json
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def parse_pdf_with_mineru(
    pdf_path: str,
    backend: str = "pipeline",
    effort: str = "medium",
    force_ocr: bool = False,
    output_dir: Optional[str] = None,
) -> dict:
    """
    使用 MinerU 解析 PDF，返回结构化内容。

    Args:
        pdf_path: PDF 文件路径
        backend: 解析后端 ("pipeline" | "vlm" | "hybrid")
        effort: 精度等级 ("medium" | "high")
        force_ocr: 强制OCR（扫描PDF时使用）
        output_dir: 输出目录（默认为临时目录）

    Returns:
        {
            "status": "success" | "error",
            "content": {
                "markdown": str,
                "text": str,
                "elements": [
                    {"type": "heading", "level": int, "content": str},
                    {"type": "table", "content": str, "format": "html"},
                    {"type": "formula", "content": str, "format": "latex"},
                    {"type": "paragraph", "content": str},
                    {"type": "image", "path": str, "caption": str},
                ]
            },
            "metadata": {
                "total_pages": int,
                "processing_time": float,
                "backend_used": str,
                "pdf_path": str,
            },
            "error": str | None
        }
    """
    import time
    start_time = time.time()

    if not os.path.exists(pdf_path):
        return {"status": "error", "content": None, "metadata": {}, "error": f"文件不存在: {pdf_path}"}

    if output_dir is None:
        output_dir = str(Path(pdf_path).parent / "mineru_output")

    os.makedirs(output_dir, exist_ok=True)

    try:
        # 尝试使用 MinerU CLI
        cmd = ["mineru", pdf_path, "-o", output_dir, "-b", backend]
        if force_ocr:
            cmd.append("--force-ocr")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            # 解析 MinerU 输出
            content = _parse_mineru_output(output_dir, Path(pdf_path).stem)
            elapsed = time.time() - start_time
            return {
                "status": "success",
                "content": content,
                "metadata": {
                    "total_pages": content.get("page_count", 0),
                    "processing_time": elapsed,
                    "backend_used": backend,
                    "pdf_path": pdf_path,
                },
                "error": None,
            }
        else:
            logger.warning(f"[MinerU] CLI 返回非零: {result.stderr[:500]}")
            return _fallback_parse(pdf_path, start_time)

    except FileNotFoundError:
        logger.info("[MinerU] CLI 未安装，尝试 Python SDK...")
        return _try_python_sdk(pdf_path, backend, output_dir, start_time)
    except subprocess.TimeoutExpired:
        logger.warning("[MinerU] 解析超时(300s)")
        return _fallback_parse(pdf_path, start_time)
    except Exception as e:
        logger.error(f"[MinerU] 解析异常: {e}")
        return _fallback_parse(pdf_path, start_time)


def _try_python_sdk(pdf_path: str, backend: str, output_dir: str, start_time: float) -> dict:
    """尝试使用 MinerU Python SDK"""
    try:
        from mineru import MinerU
        miner = MinerU(backend=backend)
        result = miner.parse(pdf_path, output_dir=output_dir)
        content = {
            "markdown": result.get("markdown", ""),
            "text": result.get("text", ""),
            "elements": result.get("elements", []),
            "page_count": result.get("page_count", 0),
        }
        import time
        elapsed = time.time() - start_time
        return {
            "status": "success",
            "content": content,
            "metadata": {
                "total_pages": content.get("page_count", 0),
                "processing_time": elapsed,
                "backend_used": backend,
                "pdf_path": pdf_path,
            },
            "error": None,
        }
    except ImportError:
        logger.info("[MinerU] Python SDK 未安装，降级到 PyMuPDF")
        return _fallback_parse(pdf_path, start_time)
    except Exception as e:
        logger.warning(f"[MinerU] SDK 调用失败: {e}")
        return _fallback_parse(pdf_path, start_time)


def _fallback_parse(pdf_path: str, start_time: float) -> dict:
    """降级到 PyMuPDF 解析"""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        text = "\n".join(text_parts)
        import time
        elapsed = time.time() - start_time
        return {
            "status": "success",
            "content": {
                "markdown": text,
                "text": text,
                "elements": [{"type": "paragraph", "content": text}],
                "page_count": len(doc),
            },
            "metadata": {
                "total_pages": len(doc),
                "processing_time": elapsed,
                "backend_used": "pymupdf_fallback",
                "pdf_path": pdf_path,
            },
            "error": None,
        }
    except Exception as e:
        import time
        elapsed = time.time() - start_time
        return {
            "status": "error",
            "content": None,
            "metadata": {"processing_time": elapsed, "pdf_path": pdf_path},
            "error": f"所有解析方法均失败: {e}",
        }


def _parse_mineru_output(output_dir: str, stem: str) -> dict:
    """解析 MinerU CLI 输出目录"""
    md_path = Path(output_dir) / f"{stem}.md"
    json_path = Path(output_dir) / f"{stem}.json"

    markdown = ""
    if md_path.exists():
        markdown = md_path.read_text(encoding="utf-8")

    elements = []
    page_count = 0
    if json_path.exists():
        data = json.loads(json_path.read_text(encoding="utf-8"))
        elements = data.get("elements", [])
        page_count = data.get("page_count", 0)

    text = markdown or ""

    return {
        "markdown": markdown,
        "text": text,
        "elements": elements,
        "page_count": page_count,
    }
