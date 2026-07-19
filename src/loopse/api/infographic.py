"""M3 信息图生成 API。

功能：
- POST /api/v1/infographic/generate — 生成主题信息图（结构化 JSON）

生成引擎优先级：
  1. SenseNova-U1-8B-MoT-Infographic-V3 商业 API（需 SENSENOVA_API_KEY）
     GitHub: https://github.com/OpenSenseNova/SenseNova-U1
     V3新功能(2026-07-16)：局部文字/内容编辑、全局风格编辑、全局版式编辑
     NEO-unify 架构：统一多模态理解+生成，高密度信息图排版SoTA
  2. LLM 结构化输出 + 前端 SVG 渲染（小程序降级方案）
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/infographic", tags=["infographic"])

_SENSENOVA_KEY = os.getenv("SENSENOVA_API_KEY", "")


# ── 数据模型 ──────────────────────────────────────────────────────────
class InfographicRequest(BaseModel):
    topic: str
    style: str = "flowchart"   # flowchart | mindmap | timeline | comparison | topology | packet
    user_id: str = "anonymous"


class InfographicNode(BaseModel):
    id: str
    label: str
    type: str = "default"      # root | branch | leaf | step | compare
    description: str = ""
    icon: str = ""


class InfographicEdge(BaseModel):
    from_id: str
    to_id: str
    label: str = ""


class InfographicData(BaseModel):
    title: str
    topic: str
    style: str
    nodes: list[InfographicNode]
    edges: list[InfographicEdge]
    summary: str
    source: str = "llm"        # "sensenova" | "llm"


# ── SenseNova 调用（有 key 时）────────────────────────────────────────
async def _call_sensenova(topic: str, style: str) -> dict[str, Any] | None:
    """调用 SenseNova-U1-Infographic-V3 信息图专用模型。
    
    模型版本: SenseNova-U1-8B-MoT-Infographic-V3
    包含指向编辑、局部文本编辑、全局风格编辑功能
    """
    if not _SENSENOVA_KEY:
        return None
    try:
        import httpx
        style_desc = {
            "flowchart": "流程图风格，路径清晰层次分明，箭头连接",
            "mindmap": "思维导图风格，中心主题向外发散",
            "timeline": "时间线风格，历史演进顺序展示",
            "comparison": "对比表风格，多概念横向对比属性",
        }.get(style, "专业信息图")
        prompt = (
            f"请生成一张关于「{topic}」的高质量{style_desc}。"
            f"要求：设计风格专业、内容准确、文字清晰、布局美观。"
            f"语言：中文。网络技术领域，包含 RFC 标准引用。"
        )
        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.post(
                "https://api.sensenova.cn/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {_SENSENOVA_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "SenseNova-U1-8B-MoT-Infographic-V3",  # V3最新发布 2026-07-16
                    "prompt": prompt,
                    "n": 1,
                    "size": "1024x1024",
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                url = data.get("data", [{}])[0].get("url", "")
                if url:
                    return {"image_url": url, "source": "sensenova-u1-infographic-v3"}
    except Exception as exc:
        logger.warning("[Infographic] SenseNova 调用失败，降级: %s", exc)
    return None


# ── LLM 结构化输出生成 ────────────────────────────────────────────────
_STYLE_PROMPTS = {
    "flowchart": "流程图（步骤分解，箭头连接，展示执行流程）",
    "mindmap":   "思维导图（中心主题向外发散，树状层次）",
    "timeline":  "时间线（历史演进/版本迭代顺序展示）",
    "comparison": "对比表格（两个或多个概念横向对比核心属性）",
    "topology":  "网络拓扑图（主机/路由器/交换机节点连接，展示网络结构）",
    "packet":    "报文格式图（各层PDU字段位宽标注，展示完整包头结构）",
}


async def _generate_llm_infographic(topic: str, style: str) -> InfographicData:
    """使用 LLM 生成结构化信息图数据（前端 SVG 渲染）。"""
    from ..core.llm_client import llm_client

    style_desc = _STYLE_PROMPTS.get(style, "流程图")
    prompt = f"""请为主题「{topic}」生成一个{style_desc}的结构化数据，用于渲染为信息图。

输出严格遵循以下 JSON 格式（不要包含任何其他文字）：
{{
  "title": "图表标题（10字以内）",
  "summary": "一句话说明（20字以内）",
  "nodes": [
    {{"id": "n1", "label": "节点标签（≤8字）", "type": "root/branch/leaf/step", "description": "简短描述（≤20字）", "icon": "emoji图标"}}
  ],
  "edges": [
    {{"from_id": "n1", "to_id": "n2", "label": "关系描述（≤4字，可空）"}}
  ]
}}

要求：
- nodes 共 6-12 个，{style} 结构合理
- edges 连接逻辑正确
- 必须包含 1 个 root 类型节点
- icon 使用相关 emoji"""

    try:
        tokens: list[str] = []
        async for token in llm_client.async_stream_chat(prompt):
            tokens.append(token)
        raw = "".join(tokens)

        # 提取 JSON
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(raw[start:end])
        else:
            raise ValueError("LLM 未返回有效 JSON")

        nodes = [InfographicNode(**n) for n in data.get("nodes", [])]
        edges = [InfographicEdge(**e) for e in data.get("edges", [])]
        return InfographicData(
            title=data.get("title", topic),
            topic=topic,
            style=style,
            nodes=nodes,
            edges=edges,
            summary=data.get("summary", ""),
            source="llm",
        )

    except Exception as exc:
        logger.warning("[Infographic] LLM 生成失败，返回默认结构: %s", exc)
        # 最小化兜底
        return InfographicData(
            title=topic,
            topic=topic,
            style=style,
            nodes=[
                InfographicNode(id="n0", label=topic, type="root", icon="📌"),
                InfographicNode(id="n1", label="概念定义", type="branch", icon="📖"),
                InfographicNode(id="n2", label="工作原理", type="branch", icon="⚙️"),
                InfographicNode(id="n3", label="应用场景", type="branch", icon="🎯"),
            ],
            edges=[
                InfographicEdge(from_id="n0", to_id="n1"),
                InfographicEdge(from_id="n0", to_id="n2"),
                InfographicEdge(from_id="n0", to_id="n3"),
            ],
            summary=f"{topic} 知识图谱概览",
            source="llm",
        )


# ── 路由 ──────────────────────────────────────────────────────────────
@router.post("/generate", response_model=InfographicData)
async def generate_infographic(req: InfographicRequest):
    """生成信息图数据。"""
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="主题不能为空")

    # 优先尝试 SenseNova
    sn_result = await _call_sensenova(req.topic, req.style)
    if sn_result:
        # SenseNova 返回图片 URL，包装为特殊节点
        return InfographicData(
            title=req.topic,
            topic=req.topic,
            style="image",
            nodes=[InfographicNode(
                id="img",
                label=req.topic,
                type="root",
                description=sn_result["image_url"],
                icon="🖼️",
            )],
            edges=[],
            summary="由 SenseNova-U1 生成",
            source="sensenova",
        )

    # 降级到 LLM 结构化输出
    return await _generate_llm_infographic(req.topic, req.style)


@router.get("/styles")
async def get_styles():
    """返回支持的信息图样式列表。"""
    return {"styles": [
        {"value": "flowchart",   "label": "流程图", "icon": "🔄"},
        {"value": "mindmap",     "label": "思维导图", "icon": "🧠"},
        {"value": "timeline",    "label": "时间线", "icon": "📅"},
        {"value": "comparison",  "label": "对比图", "icon": "⚖️"},
        {"value": "topology",    "label": "网络拓扑", "icon": "🕸️"},
        {"value": "packet",      "label": "报文格式", "icon": "📦"},
    ]}
