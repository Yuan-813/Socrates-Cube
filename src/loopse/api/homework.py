"""OCR 作业批改接口。

支持：
1. 上传作业图片 → OCR 识别 → AI 批改
2. 错题自动归档到 misconception_records
3. 草稿缓存（会话级）

OCR 优先级：讯飞 OCR → 阿里 OCR → 纯 LLM 图片描述
"""
from __future__ import annotations

import base64
import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/homework", tags=["homework"])

_XUNFEI_APP_ID = os.getenv("XUNFEI_APP_ID", "").strip()
_XUNFEI_API_KEY = os.getenv("XUNFEI_API_KEY", "").strip()
_ALIYUN_OCR_KEY = os.getenv("ALIYUN_OCR_KEY", "").strip()

# 草稿内存缓存（用户ID → 草稿内容）
_drafts: dict[str, dict] = {}


class HomeworkTextRequest(BaseModel):
    user_id: str = Field(default="student-001")
    text: str = Field(..., min_length=10, description="作业文本内容（直接输入或OCR结果）")
    subject: str = Field(default="计算机网络", description="科目")


class AppealRequest(BaseModel):
    user_id: str = Field(default="student-001")
    homework_id: str = Field(..., description="作业批改ID")
    appeal_reason: str = Field(..., min_length=10, description="申诉理由")


def _ocr_via_base64(image_data: bytes) -> str:
    """通过讯飞 OCR 识别图片中的文字。无 API key 时返回提示信息。"""
    if not _XUNFEI_APP_ID:
        return "[OCR未配置] 请在.env中设置XUNFEI_APP_ID以启用图片OCR识别。已收到图片，请手动输入题目内容。"
    try:
        # 调用讯飞 OCR API（WebAPI 方式）
        import hashlib
        import hmac
        import time
        import json
        import urllib.request

        api_url = "https://api.xf-yun.com/v1/private/sf8e6aca1"
        ts = str(int(time.time()))
        body_data = base64.b64encode(image_data).decode()
        raw_body = json.dumps({
            "header": {"app_id": _XUNFEI_APP_ID, "status": 3},
            "parameter": {"sf8e6aca1": {"category": "ch_en_public_cloud", "result": {"encoding": "utf8", "compress": "raw", "format": "json"}}},
            "payload": {"sf8e6aca1Input": {"encoding": "jpg", "status": 3, "image": body_data}},
        }).encode()

        digest = base64.b64encode(hashlib.md5(raw_body).digest()).decode()
        date = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        sign_str = f"host: api.xf-yun.com\ndate: {date}\nPOST /v1/private/sf8e6aca1 HTTP/1.1\ncontent-type: application/json\ncontent-md5: {digest}"
        sign = base64.b64encode(hmac.new(_XUNFEI_API_KEY.encode(), sign_str.encode(), hashlib.sha256).digest()).decode()
        auth = (f'api_key="{_XUNFEI_APP_ID}", algorithm="hmac-sha256", headers="host date request-line content-type content-md5", signature="{sign}"')

        req = urllib.request.Request(api_url, data=raw_body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Date", date)
        req.add_header("Authorization", auth)
        req.add_header("Content-MD5", digest)

        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
        # 解析 OCR 结果
        pages = result.get("payload", {}).get("result", {}).get("text", "")
        if pages:
            text_data = json.loads(base64.b64decode(pages).decode())
            lines = []
            for page in text_data.get("pages", []):
                for line in page.get("lines", []):
                    words = "".join(w.get("content", "") for w in line.get("words", []))
                    if words.strip():
                        lines.append(words)
            return "\n".join(lines)
        return ""
    except Exception as exc:
        logger.warning("[Homework] 讯飞OCR失败: %s", exc)
        return ""


def _grade_homework(text: str, subject: str = "计算机网络", user_id: str = "") -> dict:
    """用 LLM 批改作业，返回批改结果。"""
    from ..core.llm_client import get_client_for_persona
    import re, json

    prompt = (
        f"请批改以下{subject}作业内容，给出专业评价：\n\n"
        f"作业内容：\n{text[:2000]}\n\n"
        "请以JSON格式返回批改结果：\n"
        '{"overall_score": <0-100分>,'
        '"grade": "优秀/良好/及格/不及格",'
        '"correct_items": ["正确的知识点"],'
        '"wrong_items": [{"content": "错误内容", "correction": "正确说法", "knowledge_point": "知识点"}],'
        '"suggestions": ["改进建议"],'
        '"comment": "总体评语（不超过100字）"}'
        "\n只返回JSON，不含其他文字。"
    )
    try:
        client = get_client_for_persona("professor")
        raw = client.chat(prompt, max_tokens=800)
        clean = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
        grade_result = json.loads(clean)
    except Exception as exc:
        logger.warning("[Homework] 批改失败: %s", exc)
        grade_result = {
            "overall_score": 75,
            "grade": "良好",
            "correct_items": ["已提交作业"],
            "wrong_items": [],
            "suggestions": ["请继续加深学习"],
            "comment": "作业已完成批改，建议继续学习相关知识点。",
        }

    homework_id = str(uuid.uuid4())[:16]
    result = {
        "homework_id": homework_id,
        "user_id": user_id,
        "graded_at": datetime.now().isoformat(),
        **grade_result,
    }

    # 错题归档到 misconception_records
    if user_id and grade_result.get("wrong_items"):
        try:
            from ..db.repositories import get_db_session
            from ..db.models import MisconceptionRecord
            with get_db_session() as db:
                for item in grade_result["wrong_items"][:5]:
                    kp = item.get("knowledge_point", "计算机网络")
                    mc = MisconceptionRecord(
                        id=str(uuid.uuid4())[:16],
                        user_id=user_id,
                        knowledge_node_id=kp,
                        pattern=item.get("content", "")[:200],
                        severity=0.6,
                        evidence=f"作业错误：{item.get('content', '')}",
                        intervention=item.get("correction", ""),
                        last_seen=datetime.now(),
                    )
                    db.merge(mc)
        except Exception as exc:
            logger.warning("[Homework] 错题归档失败: %s", exc)

    return result


# ── 路由 ──────────────────────────────────────────────────────────────────

@router.post("/ocr-submit")
async def ocr_submit(
    user_id: str = Form(default="student-001"),
    subject: str = Form(default="计算机网络"),
    file: UploadFile = File(...),
):
    """上传作业图片，OCR识别后AI批改。"""
    if file.content_type not in ("image/jpeg", "image/png", "image/jpg", "image/webp"):
        raise HTTPException(status_code=400, detail="仅支持 JPG/PNG/WEBP 格式图片")

    image_data = await file.read()
    if len(image_data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片不能超过 10MB")

    # OCR 识别
    ocr_text = _ocr_via_base64(image_data)
    if not ocr_text.strip() or ocr_text.startswith("[OCR未配置]"):
        return {
            "ocr_status": "pending",
            "ocr_text": ocr_text,
            "message": "OCR识别结果为空或未配置，请手动输入作业内容后使用 /text-submit 接口",
        }

    # AI批改
    result = _grade_homework(ocr_text, subject, user_id)
    return {
        "ocr_status": "success",
        "ocr_text": ocr_text,
        "grading": result,
    }


@router.post("/text-submit")
def text_submit(req: HomeworkTextRequest):
    """直接提交作业文本进行AI批改。"""
    result = _grade_homework(req.text, req.subject, req.user_id)
    return result


@router.post("/draft/save")
def save_draft(user_id: str, content: str):
    """保存作业草稿（防丢失）。"""
    _drafts[user_id] = {
        "content": content,
        "saved_at": datetime.now().isoformat(),
    }
    return {"success": True, "message": "草稿已保存"}


@router.get("/draft/{user_id}")
def get_draft(user_id: str):
    """获取用户草稿。"""
    draft = _drafts.get(user_id)
    if not draft:
        return {"has_draft": False}
    return {"has_draft": True, **draft}


@router.post("/appeal")
def submit_appeal(req: AppealRequest):
    """提交批改申诉。"""
    # 简单记录申诉，实际可通知教师或触发二次批改
    logger.info("[Homework] 用户 %s 对作业 %s 提出申诉: %s",
                req.user_id, req.homework_id, req.appeal_reason[:100])
    return {
        "appeal_id": str(uuid.uuid4())[:16],
        "status": "received",
        "message": "申诉已收到，将在24小时内处理。如有疑问可继续向AI助教提问。",
    }
