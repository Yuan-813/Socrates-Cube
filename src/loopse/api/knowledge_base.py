"""知识库管理 API —— 用户上传文档、查询统计、手动检索。"""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from ..kb.document_processor import extract_from_markdown, process_text
from ..kb.vector_store import vector_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/kb", tags=["knowledge_base"])

# 内置教材列表（可扩展）
_BUILTIN_BOOKS = [
    {
        "id": "xjq_cn7",
        "title": "计算机网络（第7版）",
        "author": "谢希仁",
        "description": "国内计算机网络经典教材，覆盖OSI模型、TCP/IP、路由协议、应用层协议",
        "cover": "/assets/books/xjq_cn7.jpg",
        "available": False,
        "tags": ["TCP/IP", "OSI", "路由", "应用层"],
    },
    {
        "id": "hcia_datacom",
        "title": "HCIA-Datacom 学习指南",
        "author": "华为技术有限公司",
        "description": "华为数据通信HCIA官方认证指南，包含路由交换基础、华为OS配置",
        "cover": "/assets/books/hcia_datacom.jpg",
        "available": False,
        "tags": ["HCIA", "华为", "VRP", "路由交换"],
    },
    {
        "id": "ccna_200_301",
        "title": "CCNA 200-301 Official Cert Guide",
        "author": "Wendell Odom",
        "description": "思科CCNA认证官方考试指南，覆盖所有CCNA考试知识点",
        "cover": "/assets/books/ccna.jpg",
        "available": False,
        "tags": ["CCNA", "思科", "Routing", "Switching"],
    },
    {
        "id": "tanenbaum_cn5",
        "title": "Computer Networks (5th Edition)",
        "author": "Andrew S. Tanenbaum",
        "description": "国际经典计算机网络教材，深入讲解网络协议设计原理",
        "cover": "/assets/books/tanenbaum.jpg",
        "available": False,
        "tags": ["网络协议", "TCP", "UDP", "应用层"],
    },
]


class UploadRequest(BaseModel):
    content: str = Field(..., min_length=10, description="文本或 Markdown 内容")
    source: str = Field(default="user_upload", description="来源标注，如文档名/URL")
    is_markdown: bool = Field(default=False, description="内容是否为 Markdown 格式")


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    collection: str = Field(default="user_uploads")
    n_results: int = Field(default=5, ge=1, le=20)


@router.post("/upload")
def upload_document(req: UploadRequest):
    """上传文本内容到用户知识库。

    支持纯文本和 Markdown；自动切块后存入 user_uploads 集合。
    """
    try:
        if req.is_markdown:
            docs = extract_from_markdown(req.content, source=req.source)
        else:
            docs = process_text(req.content, source=req.source)

        if not docs:
            raise HTTPException(status_code=400, detail="内容为空，无法入库")

        documents = [d["document"] for d in docs]
        metadatas = [d["metadata"] for d in docs]
        ids = [d["id"] for d in docs]

        vector_store.add_documents(
            collection_name="user_uploads",
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

        logger.info("[KB] 用户上传 source=%s 入库 %d 个块", req.source, len(docs))
        return {
            "success": True,
            "chunks_added": len(docs),
            "source": req.source,
            "message": f"已将「{req.source}」切分为 {len(docs)} 个知识块并入库，AI 将自动检索引用",
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[KB] 上传失败 source=%s: %s", req.source, exc)
        raise HTTPException(status_code=500, detail="上传处理失败") from exc


@router.get("/stats")
def get_stats():
    """返回各集合的文档数量统计。"""
    collections = ["course_docs", "protocol_specs", "misconceptions", "user_uploads"]
    stats = {}
    for name in collections:
        try:
            stats[name] = vector_store.count(name)
        except Exception:
            stats[name] = 0
    return {"collections": stats, "total": sum(stats.values())}


@router.post("/search")
def search_kb(req: SearchRequest):
    """手动检索指定集合，用于验证上传效果。"""
    valid = ["course_docs", "protocol_specs", "misconceptions", "user_uploads"]
    if req.collection not in valid:
        raise HTTPException(status_code=400, detail=f"未知集合，可选：{valid}")
    try:
        results = vector_store.search(req.collection, req.query, n_results=req.n_results)
        return {"query": req.query, "collection": req.collection, "results": results}
    except Exception as exc:
        logger.error("[KB] 检索失败: %s", exc)
        raise HTTPException(status_code=500, detail="检索失败") from exc


@router.delete("/clear")
def clear_user_uploads():
    """清空 user_uploads 集合（调试用）。"""
    try:
        vector_store.reset("user_uploads")
        return {"success": True, "message": "user_uploads 集合已清空"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/books")
def get_builtin_books():
    """返回内置教材列表。"""
    return {
        "books": _BUILTIN_BOOKS,
        "total": len(_BUILTIN_BOOKS),
        "note": "目前为所汁内置教材列表，可通过 /kb/upload-pdf 上传自定义 PDF 入库",
    }


@router.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(..., description="PDF 文件"),
    source_name: str = Form(default="", description="数据来源名称"),
    use_mineru: bool = Form(default=False, description="是否启用 MinerU 解析（需安装 magic-pdf）"),
):
    """上传 PDF 文件并解析入库。

    解析策略优先级： MinerU → PyMuPDF → 纯文本备用。
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 文件")

    name = source_name.strip() or (file.filename or "uploaded_pdf")
    content_bytes = await file.read()
    if len(content_bytes) > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(status_code=413, detail="PDF 文件不能超过 50MB")

    text_content = ""

    # 方法一： MinerU
    if use_mineru:
        try:
            import magic_pdf.data.dataset as ds
            from magic_pdf.pipe.StandardJsonMidDataPipe import StandardJsonMidDataPipe
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(content_bytes)
                tmp_path = tmp.name
            try:
                from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
                from magic_pdf.config.make_content_config import DropMode, MakeMode
                output_dir = tempfile.mkdtemp()
                image_dir = os.path.join(output_dir, "images")
                os.makedirs(image_dir, exist_ok=True)
                pdf_bytes = content_bytes
                ds_obj = ds.PymuPdfDataset(pdf_bytes)
                pipe = StandardJsonMidDataPipe(ds_obj, [], {"_pdf_type": "", "model_list": []})
                pipe.pipe_classify()
                pipe.pipe_parse()
                md_content = pipe.pipe_mk_markdown(image_dir, drop_mode=DropMode.NONE)
                text_content = md_content if isinstance(md_content, str) else ""
            finally:
                os.unlink(tmp_path)
        except ImportError:
            logger.info("[KB] MinerU 未安装，使用 PyMuPDF 降级")
        except Exception as e:
            logger.warning("[KB] MinerU 解析失败: %s，尝试 PyMuPDF", e)

    # 方法二： PyMuPDF
    if not text_content:
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=content_bytes, filetype="pdf")
            parts = []
            for page in doc:
                parts.append(page.get_text())
            doc.close()
            text_content = "\n".join(parts)
        except ImportError:
            logger.info("[KB] PyMuPDF 未安装，使用文本备用")
        except Exception as e:
            logger.warning("[KB] PyMuPDF 解析失败: %s", e)

    if not text_content.strip():
        raise HTTPException(status_code=422, detail="无法从 PDF 提取文本，请确认文件包含可选择文字")

    # 切块并入库
    try:
        docs = process_text(text_content, source=name)
        if not docs:
            raise HTTPException(status_code=400, detail="PDF 内容为空")
        documents = [d["document"] for d in docs]
        metadatas = [d["metadata"] for d in docs]
        ids = [d["id"] for d in docs]
        vector_store.add_documents(
            collection_name="user_uploads",
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info("[KB] PDF 入库 source=%s chunks=%d", name, len(docs))
        return {
            "success": True,
            "source": name,
            "chunks_added": len(docs),
            "char_count": len(text_content),
            "message": f"「{name}」已解析为 {len(docs)} 个知识块并入库，AI 将自动检索引用",
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[KB] PDF 入库失败: %s", exc)
        raise HTTPException(status_code=500, detail="PDF 入库失败") from exc
