"""
MinerU 离线教材清洗与入库脚本
=====================================

功能：
  1. 扫描 data/raw/external/ 下的 PDF 文件（或已存在的 .txt 文件）
  2. 使用 MinerU (magic-pdf) 解析 PDF，精准提取段落/公式/表格
  3. 输出高质量 Markdown 到 data/cleaned/
  4. 调用现有 ingest_docs.py 的入库逻辑重新构建向量库索引

前置条件：
  pip install magic-pdf[full]  （MinerU 完整版，支持 CPU/GPU 解析）

用法：
  # 仅清洗（不重建索引）
  python scripts/reingest_with_mineru.py --clean-only

  # 清洗 + 重建向量库（推荐）
  python scripts/reingest_with_mineru.py

  # 指定单个 PDF
  python scripts/reingest_with_mineru.py --file data/raw/external/rfc9293_tcp.pdf

  # 重置向量库后重新入库
  python scripts/reingest_with_mineru.py --reset

注意：
  - MinerU 使用讯飞/本地模型做 OCR，不涉及非法外部 LLM 调用
  - 该脚本离线运行，不影响任何在线 API 调用
  - 核心推理仍使用讯飞星火大模型（llm_client 不变）
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# ── 路径配置 ──────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
RAW_DIR     = ROOT / "data" / "raw" / "external"
CLEANED_DIR = ROOT / "data" / "cleaned"
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── MinerU 可用性检查 ─────────────────────────────────────────────────
try:
    from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
    from magic_pdf.pipe.UnicodeFormula import UnicodeFormulaDetect
    from magic_pdf.model.doc_analyze_by_custom_model import ModelSingleton
    from magic_pdf.config.make_content_config import DropMode, MakeMode
    from magic_pdf.data.dataset import PymuPDFDataset
    _MINERU_OK = True
    logger.info("MinerU (magic-pdf) 已成功导入")
except ImportError:
    _MINERU_OK = False
    logger.warning(
        "MinerU 未安装。请运行：pip install magic-pdf[full]\n"
        "脚本将回退到原始文本提取模式（质量较低）。"
    )


def extract_with_mineru(pdf_path: Path, out_md_path: Path) -> bool:
    """使用 MinerU 提取 PDF 为高质量 Markdown。"""
    if not _MINERU_OK:
        return False
    try:
        logger.info("MinerU 解析: %s", pdf_path.name)
        pdf_bytes = pdf_path.read_bytes()
        dataset = PymuPDFDataset(pdf_bytes)

        # 图片输出目录（与 md 同目录）
        img_dir = out_md_path.parent / (out_md_path.stem + "_images")
        img_dir.mkdir(parents=True, exist_ok=True)

        img_writer = FileBasedDataWriter(str(img_dir))
        md_writer   = FileBasedDataWriter(str(out_md_path.parent))

        from magic_pdf.pipe.BasicPipeline import BasicPipeline
        pipe = BasicPipeline(
            pdf_bytes,
            img_writer=img_writer,
            is_debug=False,
            start_page_id=0,
            end_page_id=None,
        )
        pipe.pipe_classify()
        pipe.pipe_analyze()
        pipe.pipe_parse()

        md_content = pipe.pipe_mk_markdown(
            img_dir.name,
            drop_mode=DropMode.NONE,
            md_make_mode=MakeMode.MM_MD,
        )
        out_md_path.write_text(md_content, encoding="utf-8")
        logger.info("  ✓ 输出: %s (%.1f KB)", out_md_path.name, len(md_content) / 1024)
        return True
    except Exception as exc:
        logger.error("MinerU 解析失败 %s: %s", pdf_path.name, exc)
        return False


def extract_fallback(src_path: Path, out_md_path: Path) -> bool:
    """回退方案：直接复制 .txt/.md 文件或用 pdfminer 提取文本。"""
    suffix = src_path.suffix.lower()
    if suffix in (".txt", ".md"):
        content = src_path.read_text(encoding="utf-8", errors="replace")
        # 简单转 Markdown：添加标题
        md = f"# {src_path.stem}\n\n{content}"
        out_md_path.write_text(md, encoding="utf-8")
        logger.info("  ✓ 复制: %s → %s", src_path.name, out_md_path.name)
        return True

    if suffix == ".pdf":
        try:
            from pdfminer.high_level import extract_text
            text = extract_text(str(src_path))
            md = f"# {src_path.stem}\n\n{text}"
            out_md_path.write_text(md, encoding="utf-8")
            logger.info("  ✓ pdfminer 提取: %s", out_md_path.name)
            return True
        except ImportError:
            logger.warning("pdfminer 未安装，跳过: %s", src_path.name)
        except Exception as exc:
            logger.error("pdfminer 提取失败 %s: %s", src_path.name, exc)
    return False


def clean_all(target_file: Path | None = None) -> list[Path]:
    """清洗所有（或指定）源文件，返回生成的 Markdown 路径列表。"""
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if target_file:
        sources = [target_file]
    else:
        sources = sorted(RAW_DIR.glob("*"))

    generated: list[Path] = []
    for src in sources:
        if src.suffix.lower() not in (".pdf", ".txt", ".md"):
            continue
        out_md = CLEANED_DIR / (src.stem + ".md")

        # 优先 MinerU，失败则回退
        success = False
        if src.suffix.lower() == ".pdf" and _MINERU_OK:
            success = extract_with_mineru(src, out_md)
        if not success:
            success = extract_fallback(src, out_md)

        if success:
            generated.append(out_md)

    logger.info("共处理 %d 个源文件，生成 %d 个 Markdown", len(sources), len(generated))
    return generated


def rebuild_index(reset: bool = False) -> None:
    """调用现有 ingest_docs.py 逻辑重建向量库索引。"""
    logger.info("开始重建向量库索引 (reset=%s)...", reset)
    try:
        # 直接调用 ingest_docs 模块
        ingest_path = ROOT / "scripts" / "ingest_docs.py"
        if not ingest_path.exists():
            logger.error("ingest_docs.py 不存在: %s", ingest_path)
            return

        import importlib.util
        spec = importlib.util.spec_from_file_location("ingest_docs", ingest_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            # 注入 reset 参数
            sys.argv = ["ingest_docs.py"] + (["--reset"] if reset else [])
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            logger.info("向量库重建完成")
    except SystemExit:
        pass  # ingest_docs.py 可能调用 sys.exit(0)
    except Exception as exc:
        logger.error("重建索引失败: %s", exc)


def main() -> None:
    parser = argparse.ArgumentParser(description="MinerU 教材清洗与向量库重建")
    parser.add_argument("--clean-only", action="store_true", help="仅清洗，不重建索引")
    parser.add_argument("--reset", action="store_true", help="重置向量库后重建")
    parser.add_argument("--file", type=Path, default=None, help="指定单个文件路径")
    args = parser.parse_args()

    if args.file and not args.file.exists():
        logger.error("文件不存在: %s", args.file)
        sys.exit(1)

    # Step 1: 清洗
    logger.info("=" * 50)
    logger.info("Step 1: 清洗源文件 → Markdown")
    logger.info("=" * 50)
    generated = clean_all(args.file)

    if not generated:
        logger.warning("没有生成任何 Markdown 文件，检查 %s 是否有源文件", RAW_DIR)
        return

    # Step 2: 重建索引
    if not args.clean_only:
        logger.info("=" * 50)
        logger.info("Step 2: 重建向量库索引")
        logger.info("=" * 50)
        rebuild_index(args.reset)
    else:
        logger.info("--clean-only 模式，跳过向量库重建")

    logger.info("=" * 50)
    logger.info("全部完成！共生成 %d 个 Markdown 文件", len(generated))
    for p in generated:
        logger.info("  %s", p.relative_to(ROOT))


if __name__ == "__main__":
    main()
