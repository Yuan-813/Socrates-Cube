"""多模态图生成接口 — SenseNova-U1 信息图 + Mermaid 拓扑图。

SenseNova-U1 系列（OpenSenseNova/SenseNova-U1）：
  - SenseNova-U1-8B-MoT-Infographic-V3（2026-07-16）：密集信息图生成+编辑，支持局部文字/版式修改
  - SenseNova-U1-8B-MoT-Interleaved：图文交织生成，适合步骤图
  - SenseNova-U1-8B-MoT：通用T2I + 多模态理解

优先级：
1. SenseNova-U1 Infographic-V3 REST API（images/generations）
2. SenseNova-U1 Chat Completions（降级文字描述）
3. SkyClaw / OpenAI compat 生成 Mermaid/SVG 代码（前端渲染）
4. 内置 Mermaid 模板兜底
"""
from __future__ import annotations

import logging
import os
import re
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/media", tags=["media"])

_SENOVAU1_API_KEY = os.getenv("SENOVAU1_API_KEY", "").strip()
_SENOVAU1_BASE_URL = os.getenv("SENOVAU1_BASE_URL", "https://api.sensecore.cn/v1").strip()
# 信息图专用模型（SenseNova-U1-8B-MoT-Infographic-V3 — 2026-07-16发布）
# 支持：密集信息图生成+编辑、局部文字/内容/版式/全局风格编辑、黑底问题已修复
# Ref: https://github.com/OpenSenseNova/SenseNova-U1
_SENOVAU1_MODEL_INFOGRAPHIC = os.getenv(
    "SENOVAU1_MODEL",
    "SenseNova-U1-8B-MoT-Infographic-V3",
).strip()
_SENOVAU1_MODEL_INTERLEAVED = "SenseNova-U1-8B-MoT-Interleaved"  # 图文交织


# ── 内置 Mermaid 拓扑模板 ───────────────────────────────────────────────────
_MERMAID_TEMPLATES = {
    "tcp_handshake": """sequenceDiagram
    participant C as 客户端
    participant S as 服务器
    C->>S: SYN (seq=x)
    S->>C: SYN+ACK (seq=y, ack=x+1)
    C->>S: ACK (ack=y+1)
    Note over C,S: 连接建立""",

    "tcp_teardown": """sequenceDiagram
    participant C as 主动关闭方
    participant S as 被动关闭方
    C->>S: FIN (seq=u)
    S->>C: ACK (ack=u+1)
    S->>C: FIN (seq=v)
    C->>S: ACK (ack=v+1)
    Note over C: TIME_WAIT (2MSL)""",

    "osi_model": """graph TB
    A7[应用层 HTTP/DNS/FTP]
    A6[表示层 加密/压缩]
    A5[会话层 会话管理]
    A4[传输层 TCP/UDP]
    A3[网络层 IP/路由]
    A2[数据链路层 帧/MAC]
    A1[物理层 比特流]
    A7-->A6-->A5-->A4-->A3-->A2-->A1""",

    "network_topology": """graph LR
    PC1[PC1] -- 以太网 --> SW1[交换机]
    PC2[PC2] -- 以太网 --> SW1
    SW1 -- 千兆链路 --> R1[路由器]
    R1 -- WAN --> Internet[互联网]
    R1 -- LAN --> SW2[交换机2]
    SW2 --> SRV[服务器]""",

    "dns_resolution": """sequenceDiagram
    participant C as 客户端
    participant L as 本地DNS
    participant R as 根DNS
    participant T as TLD DNS
    participant A as 权威DNS
    C->>L: 查询 www.example.com
    L->>R: 递归查询
    R->>L: 返回TLD地址
    L->>T: 查询
    T->>L: 返回权威DNS
    L->>A: 查询
    A->>L: 返回IP地址
    L->>C: 返回IP""",
}


class GenerateImageRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=500, description="图像描述（网络拓扑/信息图主题）")
    style: str = Field(default="infographic", description="infographic/topology/flowchart")
    knowledge_point: Optional[str] = Field(default=None)


class GenerateTopologyRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=100, description="网络拓扑主题")
    diagram_type: str = Field(default="auto", description="auto/sequence/flowchart/graph")
    knowledge_point: Optional[str] = Field(default=None)


# ── 路由 ──────────────────────────────────────────────────────────────────

@router.post("/generate-image")
def generate_image(req: GenerateImageRequest):
    """生成信息图/示意图。
    
    优先调用 SenseNova-U1-8B-MoT-Infographic-V3（images/generations），
    降级链: 图片API → Chat Completions → Mermaid Markdown。
    
    Ref: https://github.com/OpenSenseNova/SenseNova-U1
    """
    if _SENOVAU1_API_KEY:
        # ── 优先：SenseNova-U1 Infographic-V3 图像生成 endpoint ────────────
        try:
            import urllib.request
            import json
            # 构建计算机网络领域 prompt（中英双语提升渲染质量）
            cn_kp = req.knowledge_point or req.prompt[:30]
            enhanced_prompt = (
                f"{req.prompt}\n"
                f"教学信息图风格，蓝白配色，包含：图表/流程/RFC标注/注释框，"
                f"知识点：{cn_kp}，中文标注，专业简洁"
            )
            headers_dict = {
                "Authorization": f"Bearer {_SENOVAU1_API_KEY}",
                "Content-Type": "application/json",
            }
            body = json.dumps({
                "model": _SENOVAU1_MODEL_INFOGRAPHIC,
                "prompt": enhanced_prompt,
                "size": "1024x768",
                "n": 1,
                "response_format": "url",
            }).encode()
            request = urllib.request.Request(
                f"{_SENOVAU1_BASE_URL}/images/generations",
                data=body,
                headers=headers_dict,
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=60) as resp:
                data = json.loads(resp.read().decode())
            image_url = data["data"][0].get("url") or data["data"][0].get("b64_json", "")
            if image_url:
                logger.info("[Media] SenseNova-U1 Infographic-V3 生成成功: kp=%s", cn_kp)
                return {
                    "type": "image",
                    "provider": "senovau1_infographic_v3",
                    "model": _SENOVAU1_MODEL_INFOGRAPHIC,
                    "image_url": image_url,
                    "prompt": enhanced_prompt,
                    "knowledge_point": req.knowledge_point,
                }
        except Exception as exc:
            logger.warning("[Media] SenseNova-U1 Infographic-V3 失败，尝试 Chat: %s", exc)

        # ── 降级一：Chat Completions（文字描述信息图内容）─────────────────────
        try:
            import urllib.request
            import json
            headers_dict = {
                "Authorization": f"Bearer {_SENOVAU1_API_KEY}",
                "Content-Type": "application/json",
            }
            body = json.dumps({
                "model": "SenseNova-U1-8B",
                "messages": [{
                    "role": "user",
                    "content": (
                        f"请用 Mermaid 代码描述以下信息图布局：{req.prompt}\n"
                        "要求：中文标注，包含关键协议流程，不超过20个节点"
                    )
                }],
                "max_tokens": 800,
            }).encode()
            request = urllib.request.Request(
                f"{_SENOVAU1_BASE_URL}/chat/completions",
                data=body,
                headers=headers_dict,
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=30) as resp:
                data = json.loads(resp.read().decode())
            content = data["choices"][0]["message"]["content"]
            return {
                "type": "text",
                "provider": "senovau1_chat",
                "content": content,
                "knowledge_point": req.knowledge_point,
            }
        except Exception as exc:
            logger.warning("[Media] SenseNova-U1 Chat 失败，降级到Mermaid: %s", exc)

    # ── 最终降级：LLM 生成 Mermaid 代码（前端 mermaid.js 渲染）─────────────
    return generate_topology(GenerateTopologyRequest(
        topic=req.prompt,
        diagram_type="auto" if req.style == "infographic" else req.style,
        knowledge_point=req.knowledge_point,
    ))


@router.post("/generate-topology")
def generate_topology(req: GenerateTopologyRequest):
    """生成网络拓扑 Mermaid 代码（前端用 mermaid.js 渲染）。"""
    from ..core.llm_client import get_client_for_persona

    # 检查内置模板
    topic_lower = req.topic.lower()
    template_key = None
    if any(kw in topic_lower for kw in ["三次握手", "handshake", "syn"]):
        template_key = "tcp_handshake"
    elif any(kw in topic_lower for kw in ["四次挥手", "teardown", "fin"]):
        template_key = "tcp_teardown"
    elif any(kw in topic_lower for kw in ["osi", "七层", "分层"]):
        template_key = "osi_model"
    elif any(kw in topic_lower for kw in ["dns", "域名解析"]):
        template_key = "dns_resolution"
    elif any(kw in topic_lower for kw in ["拓扑", "topology", "网络图"]):
        template_key = "network_topology"

    if template_key:
        return {
            "type": "mermaid",
            "provider": "builtin",
            "mermaid_code": _MERMAID_TEMPLATES[template_key],
            "topic": req.topic,
            "knowledge_point": req.knowledge_point,
        }

    # 用 LLM 生成 Mermaid 代码
    diagram_hint = {
        "sequence": "sequenceDiagram（时序图）",
        "flowchart": "flowchart TD（流程图）",
        "graph": "graph LR（拓扑图）",
        "auto": "最适合主题的Mermaid图类型",
    }.get(req.diagram_type, "最适合主题的Mermaid图类型")

    prompt = (
        f"请为「{req.topic}」生成{diagram_hint}的Mermaid代码，用于展示计算机网络概念。\n"
        "要求：\n"
        "1. 只返回纯Mermaid代码，不含代码块标记\n"
        "2. 节点标签使用中文，清晰表达网络流程\n"
        "3. 不超过20个节点，保持可读性\n"
        "4. 确保语法正确可被mermaid.js渲染"
    )
    try:
        client = get_client_for_persona("professor")
        mermaid_code = client.chat(prompt, max_tokens=600)
        # 清理代码块标记
        mermaid_code = re.sub(r"```(?:mermaid)?\s*|\s*```", "", mermaid_code).strip()
        if not mermaid_code:
            raise ValueError("空响应")
        return {
            "type": "mermaid",
            "provider": "llm",
            "mermaid_code": mermaid_code,
            "topic": req.topic,
            "knowledge_point": req.knowledge_point,
        }
    except Exception as exc:
        logger.error("[Media] Mermaid代码生成失败 topic=%s: %s", req.topic, exc)
        # 最终兜底：通用网络拓扑
        return {
            "type": "mermaid",
            "provider": "fallback",
            "mermaid_code": _MERMAID_TEMPLATES["network_topology"],
            "topic": req.topic,
            "knowledge_point": req.knowledge_point,
        }


@router.get("/templates")
def list_templates():
    """获取内置 Mermaid 模板列表。"""
    return {
        "templates": [
            {"key": k, "title": k.replace("_", " ").title(), "mermaid_code": v}
            for k, v in _MERMAID_TEMPLATES.items()
        ]
    }
