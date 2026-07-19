"""
AI视频生成 API
对接火山引擎 Seedance API；未配置 API Key 时自动进入 Mock 演示模式。
"""
import os
import time
import asyncio
import logging

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/video", tags=["video"])

ARK_VIDEO_API_KEY = os.getenv("ARK_VIDEO_API_KEY", "")
ARK_VIDEO_MODEL   = os.getenv("ARK_VIDEO_MODEL", "seedance-1-lite")
ARK_BASE_URL      = "https://ark.cn-beijing.volces.com/api/v3"

# Mock 任务存储（内存，仅演示用）
_mock_tasks: dict[str, dict] = {}

# 每个 Topic 对应的演示描述文字
TOPIC_DESC: dict[str, str] = {
    "TCP三次握手":  "本视频详解 TCP 三次握手建立连接的完整过程，包含 SYN/SYN-ACK/ACK 报文交互动画演示及 Wireshark 抓包分析。",
    "IP路由原理":   "本视频深度解析 IP 路由转发原理，涵盖路由表查找、最长前缀匹配与静态/动态路由对比实验演示。",
    "HTTP/HTTPS":   "本视频讲解 HTTP/1.1 与 HTTPS TLS 握手全流程，包含报文结构分析、证书验证动画及性能对比。",
    "DNS解析":      "本视频演示 DNS 递归/迭代查询流程，包含根服务器、权威服务器交互动画及常见故障排查案例。",
    "ARP协议":      "本视频详细讲解 ARP 地址解析协议工作机制，包含 ARP 广播、缓存更新过程及 ARP 欺骗防护实验。",
    "VLAN配置":     "本视频实操演示基于 802.1Q 的 VLAN 划分配置流程，含 Trunk 口配置、不同 VLAN 间路由实验。",
    "防火墙策略":   "本视频讲解企业级防火墙 ACL 策略设计与配置，包含状态检测、区域划分与入侵检测联动演示。",
}

MOCK_VIDEO_URL = (
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
)


# ─── Pydantic ────────────────────────────────────────────────────────────────

class VideoGenRequest(BaseModel):
    prompt: str = ""
    topic:  str = ""


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _build_prompt(req: VideoGenRequest) -> str:
    if req.topic and not req.prompt:
        return (
            f"生成一个关于计算机网络知识点「{req.topic}」的教学演示视频，"
            f"要求包含原理讲解、动画演示和实验操作，时长约2-3分钟，"
            f"语言专业简洁，适合计算机网络课程学习。"
        )
    return req.prompt or "生成一个计算机网络基础教学视频"


def _get_title(req: VideoGenRequest) -> str:
    topic = req.topic or "计算机网络"
    return f"【AI生成】{topic} · 智能教学视频"


def _get_desc(req: VideoGenRequest) -> str:
    topic = req.topic or "计算机网络"
    return TOPIC_DESC.get(
        topic,
        f"本视频由 AI 智能生成系统根据「{topic}」课题自动编撰，"
        "内容涵盖相关知识点讲解、实操演示及案例分析，"
        "旨在为学习者提供高效、精准的教学内容。",
    )


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/generate")
async def generate_video(req: VideoGenRequest):
    """提交视频生成任务，返回 task_id。"""
    prompt = _build_prompt(req)

    if not ARK_VIDEO_API_KEY:
        # Mock 模式：立即创建任务，3 秒后视为完成
        task_id = f"mock_{int(time.time() * 1000)}"
        _mock_tasks[task_id] = {
            "created_at": time.time(),
            "title": _get_title(req),
            "description": _get_desc(req),
            "topic": req.topic,
        }
        logger.info("[VideoGen] Mock mode – task_id=%s", task_id)
        return {"task_id": task_id, "status": "pending", "mock": True}

    # 真实 Seedance API
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{ARK_BASE_URL}/contents/generations/tasks",
                headers={
                    "Authorization": f"Bearer {ARK_VIDEO_API_KEY}",
                    "Content-Type":  "application/json",
                },
                json={
                    "model": ARK_VIDEO_MODEL,
                    "content": [{"type": "text", "text": prompt}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            task_id = data.get("id", "")
            logger.info("[VideoGen] Ark task submitted: %s", task_id)
            return {"task_id": task_id, "status": "pending", "mock": False}
    except Exception as exc:
        logger.error("[VideoGen] Ark API error: %s", exc)
        # 降级为 mock
        task_id = f"mock_{int(time.time() * 1000)}"
        _mock_tasks[task_id] = {
            "created_at": time.time(),
            "title": _get_title(req),
            "description": _get_desc(req),
            "topic": req.topic,
        }
        return {"task_id": task_id, "status": "pending", "mock": True, "fallback": True}


@router.get("/status/{task_id}")
async def get_video_status(task_id: str):
    """查询任务状态，完成后返回 video_url。"""

    # Mock 模式
    if task_id.startswith("mock_"):
        meta = _mock_tasks.get(task_id, {})
        created_at = meta.get("created_at", time.time())
        elapsed = time.time() - created_at

        if elapsed < 5:
            # 模拟生成中
            progress = min(95, int(elapsed / 5 * 100))
            return {"status": "running", "progress": progress}

        return {
            "status": "succeeded",
            "video_url":   MOCK_VIDEO_URL,
            "title":       meta.get("title", "【AI生成】智能教学视频"),
            "description": meta.get("description", "AI 自动生成的教学视频。"),
            "topic":       meta.get("topic", ""),
            "generated_at": time.strftime(
                "%Y-%m-%d", time.localtime(created_at)
            ),
        }

    # 真实 Seedance API 查询
    if not ARK_VIDEO_API_KEY:
        return {"status": "failed", "error": "API key not configured"}

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                f"{ARK_BASE_URL}/contents/generations/tasks/{task_id}",
                headers={"Authorization": f"Bearer {ARK_VIDEO_API_KEY}"},
            )
            resp.raise_for_status()
            data = resp.json()

        status = data.get("status", "running")  # queued / running / succeeded / failed

        if status == "succeeded":
            # 从 content 列表中提取视频 URL
            content = data.get("content", [])
            video_url = ""
            for item in content:
                if item.get("type") == "video":
                    video_url = item.get("video_url", "")
                    break

            return {
                "status": "succeeded",
                "video_url":   video_url,
                "title":       f"【AI生成】智能教学视频",
                "description": "由 Seedance 模型生成的计算机网络教学视频。",
                "generated_at": time.strftime("%Y-%m-%d"),
            }

        return {"status": status, "progress": data.get("progress", 0)}

    except Exception as exc:
        logger.error("[VideoGen] status query error: %s", exc)
        return {"status": "failed", "error": str(exc)}
