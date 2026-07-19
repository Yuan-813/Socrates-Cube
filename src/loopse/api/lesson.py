"""互动课程生成 API — 受 OpenMAIC 启发。

OpenMAIC v0.3.0: https://github.com/THU-MAIC/OpenMAIC
Open Multi-Agent Interactive Classroom - 多智能体互动课堂

v0.3.0 (2026-06-28) 新特性:
  - PBL v2 (Project-Based Learning) 项目式学习，含课堂UI
  - Edit with AI Pro-mode 编辑器 Agent
  - @openmaic/* SDK 家族：DSL/renderer/importer 发布到 npm
  - 每阶段模型路由（不同 stage 可用不同 LLM）
  - 导出 .pptx 幻灯片 + 展山 .html 互动页面
  - 新市场模型：GLM-5.2、Kimi K2.7 Code、Qwen3.7 Plus/Max

本模块借鉴 OpenMAIC 的课程结构化设计，利用 Socrates-Cube 已有的 LLM 能力
生成包含幻灯片、测验、互动仿真、PBL 项目的结构化课程，适配网络协议教学场景。

端点：
- POST /api/v1/lesson/generate  — 一键生成完整互动课程
- POST /api/v1/lesson/slide     — 单页幻灯片生成
- GET  /api/v1/lesson/templates — 获取课程模板列表
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/lesson", tags=["lesson"])

# 预置课程模板（计算机网络领域）
LESSON_TEMPLATES = [
    {
        "id": "tcp_handshake",
        "title": "TCP 三次握手与四次挥手",
        "description": "可视化展示 TCP 连接建立与释放的完整流程",
        "chapter": "第5章",
        "duration_min": 20,
        "slide_count": 6,
        "has_quiz": True,
        "has_simulation": True,
        "tags": ["TCP", "三次握手", "四次挥手", "RFC 9293"],
    },
    {
        "id": "dns_resolution",
        "title": "DNS 域名解析全流程",
        "description": "从浏览器输入到 IP 地址返回，完整解析流程图解",
        "chapter": "第6章",
        "duration_min": 15,
        "slide_count": 5,
        "has_quiz": True,
        "has_simulation": False,
        "tags": ["DNS", "递归查询", "迭代查询", "RFC 1034"],
    },
    {
        "id": "osi_layers",
        "title": "OSI 七层模型与协议栈",
        "description": "每层功能、对应协议、PDU 名称的互动讲解",
        "chapter": "第1章",
        "duration_min": 25,
        "slide_count": 8,
        "has_quiz": True,
        "has_simulation": False,
        "tags": ["OSI", "七层模型", "封装", "PDU"],
    },
    {
        "id": "tcp_congestion",
        "title": "TCP 拥塞控制算法详解",
        "description": "慢启动、拥塞避免、快重传、快恢复四个阶段可视化",
        "chapter": "第5章",
        "duration_min": 30,
        "slide_count": 8,
        "has_quiz": True,
        "has_simulation": True,
        "tags": ["TCP", "拥塞控制", "cwnd", "RFC 5681"],
    },
    {
        "id": "bgp_routing",
        "title": "BGP 路径矢量路由协议",
        "description": "自治系统间路由选择、AS Path 属性、策略路由",
        "chapter": "第4章",
        "duration_min": 35,
        "slide_count": 10,
        "has_quiz": True,
        "has_simulation": False,
        "tags": ["BGP", "AS", "路径矢量", "RFC 4271"],
    },
    # PBL 项目式学习模板（参考 OpenMAIC v0.3.0 PBL v2 设计）
    {
        "id": "pbl_network_troubleshoot",
        "title": "PBL: 企业网络故障诊断与排查",
        "description": "项目式学习：模拟真实企业网络故障，分层诊断、抓包分析、方案设计",
        "chapter": "第5章",
        "duration_min": 60,
        "slide_count": 8,
        "has_quiz": True,
        "has_simulation": True,
        "pbl_type": "network_fault",
        "export_formats": ["html", "pptx"],
        "tags": ["PBL", "故障排查", "Wireshark", "tcpdump", "RFC 2151"],
    },
    {
        "id": "pbl_tls_security",
        "title": "PBL: TLS 1.3 安全通信实践",
        "description": "项目式学习：部署 HTTPS 服务、证书页、威胁模型分析与防御方案",
        "chapter": "第6章",
        "duration_min": 45,
        "slide_count": 7,
        "has_quiz": True,
        "has_simulation": False,
        "pbl_type": "security",
        "export_formats": ["html", "pptx"],
        "tags": ["PBL", "TLS 1.3", "PKI", "RFC 8446", "X.509"],
    },
]


# ── 数据模型 ────────────────────────────────────────────────────────
class LessonGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2, description="课程主题")
    user_id: str = Field(default="student-001")
    target_audience: str = Field(default="计算机网络课程学生", description="目标受众")
    difficulty: int = Field(default=2, ge=1, le=5, description="1=入门 5=专家")
    slide_count: int = Field(default=5, ge=3, le=10, description="幻灯片数量")
    include_quiz: bool = Field(default=True, description="是否包含测验")
    include_simulation: bool = Field(default=False, description="是否包含互动仿真")
    language: str = Field(default="zh", description="语言 zh/en")


class SlideGenerateRequest(BaseModel):
    topic: str = Field(..., description="幻灯片主题")
    slide_type: str = Field(default="concept", description="concept/protocol/diagram/quiz")
    context: Optional[str] = Field(default=None, description="前序幻灯片上下文")


class LessonSlide(BaseModel):
    id: str
    title: str
    type: str  # title/concept/protocol/diagram/quiz/summary
    content: str
    key_points: list[str]
    speaker_notes: str
    rfc_refs: list[str] = []
    visual_hint: str = ""  # 告知前端展示什么图形


class LessonQuiz(BaseModel):
    question: str
    options: list[str]
    answer_index: int
    explanation: str


class LessonData(BaseModel):
    lesson_id: str
    title: str
    topic: str
    difficulty: int
    duration_min: int
    slides: list[LessonSlide]
    quiz: list[LessonQuiz] = []
    summary: str
    references: list[str] = []
    generated_at: str
    source: str = "socrates-cube"
    inspired_by: str = "OpenMAIC (https://github.com/THU-MAIC/OpenMAIC)"


# ── 生成逻辑 ────────────────────────────────────────────────────────
_SLIDE_TYPE_PROMPTS = {
    "title":    "封面幻灯片，包含课程标题、学习目标（3条）、重要性说明",
    "concept":  "概念讲解幻灯片，用简洁文字+要点列表解释核心概念",
    "protocol": "协议分析幻灯片，包含报文格式、字段说明、工作流程",
    "diagram":  "图示幻灯片，描述需要绘制的图示内容（状态图/时序图/拓扑图）",
    "quiz":     "测验幻灯片，提出1-2个思考题帮助学生验证理解",
    "summary":  "总结幻灯片，回顾关键点、拓展阅读、下一节预告",
}

_DIFFICULTY_LABELS = {1: "入门", 2: "基础", 3: "中等", 4: "进阶", 5: "专家"}


async def _generate_lesson_with_llm(req: LessonGenerateRequest) -> LessonData:
    """使用 LLM 生成完整互动课程（OpenMAIC 风格）。"""
    from ..core.llm_client import get_client_for_persona

    client = get_client_for_persona("expert")
    diff_label = _DIFFICULTY_LABELS.get(req.difficulty, "中等")
    lesson_id = f"lesson_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # 生成课程整体结构
    structure_prompt = f"""你是一位计算机网络领域的专业教育者，请为主题「{req.topic}」设计一套{diff_label}难度的互动课程大纲。

课程要求：
- 目标受众：{req.target_audience}
- 幻灯片数量：{req.slide_count} 张
- 包含测验：{'是' if req.include_quiz else '否'}
- 语言：中文

请以 JSON 格式返回：
{{
  "title": "课程标题",
  "summary": "一句话课程摘要",
  "duration_min": 预计学习时长（分钟数字）,
  "slides": [
    {{
      "id": "s1",
      "title": "幻灯片标题",
      "type": "title|concept|protocol|diagram|quiz|summary",
      "content": "主要内容（200字以内）",
      "key_points": ["要点1", "要点2", "要点3"],
      "speaker_notes": "讲师备注（100字以内）",
      "rfc_refs": ["RFC XXXX"],
      "visual_hint": "建议展示什么图形（时序图/状态机/拓扑图等）"
    }}
  ],
  "references": ["参考资料1", "参考资料2"]
}}

只返回 JSON，不要包含其他文字。"""

    try:
        raw = client.chat(structure_prompt, max_tokens=3000)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(raw[start:end])
        else:
            raise ValueError("LLM 未返回有效 JSON")

        slides = [
            LessonSlide(
                id=s.get("id", f"s{i+1}"),
                title=s.get("title", ""),
                type=s.get("type", "concept"),
                content=s.get("content", ""),
                key_points=s.get("key_points", []),
                speaker_notes=s.get("speaker_notes", ""),
                rfc_refs=s.get("rfc_refs", []),
                visual_hint=s.get("visual_hint", ""),
            )
            for i, s in enumerate(data.get("slides", []))
        ]

        quiz: list[LessonQuiz] = []
        if req.include_quiz and slides:
            quiz = await _generate_quiz(req.topic, diff_label, client)

        return LessonData(
            lesson_id=lesson_id,
            title=data.get("title", req.topic),
            topic=req.topic,
            difficulty=req.difficulty,
            duration_min=int(data.get("duration_min", req.slide_count * 3)),
            slides=slides,
            quiz=quiz,
            summary=data.get("summary", ""),
            references=data.get("references", []),
            generated_at=datetime.now().isoformat(),
        )

    except Exception as exc:
        logger.error("[Lesson] 课程生成失败: %s", exc)
        return _fallback_lesson(req, lesson_id)


async def _generate_quiz(topic: str, diff_label: str, client) -> list[LessonQuiz]:
    """生成随堂测验题组。"""
    prompt = f"""请为「{topic}」主题生成3道{diff_label}难度的选择题。

JSON格式：
[
  {{
    "question": "题目",
    "options": ["A. 选项", "B. 选项", "C. 选项", "D. 选项"],
    "answer_index": 0,
    "explanation": "解析"
  }}
]
只返回JSON。"""
    try:
        raw = client.chat(prompt, max_tokens=800)
        clean = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
        items = json.loads(clean)
        return [LessonQuiz(**q) for q in items if isinstance(q, dict)]
    except Exception:
        return []


def _fallback_lesson(req: LessonGenerateRequest, lesson_id: str) -> LessonData:
    """LLM 失败时的兜底结构。"""
    return LessonData(
        lesson_id=lesson_id,
        title=req.topic,
        topic=req.topic,
        difficulty=req.difficulty,
        duration_min=15,
        slides=[
            LessonSlide(
                id="s1", title=f"{req.topic} — 概述",
                type="title",
                content=f"本课程介绍 {req.topic} 的核心概念与应用场景。",
                key_points=["理解基本原理", "掌握关键流程", "应用到实际场景"],
                speaker_notes="课程介绍",
            ),
            LessonSlide(
                id="s2", title="核心概念",
                type="concept",
                content="请参考教材或 RFC 标准文档了解详细内容。",
                key_points=["概念定义", "工作原理", "适用场景"],
                speaker_notes="深入讲解核心概念",
            ),
        ],
        summary=f"本课程介绍了 {req.topic} 的基本内容。",
        generated_at=datetime.now().isoformat(),
    )


# ── 路由 ────────────────────────────────────────────────────────────
@router.post("/generate", response_model=LessonData)
async def generate_lesson(req: LessonGenerateRequest):
    """一键生成互动课程（OpenMAIC 风格）。"""
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="课程主题不能为空")
    return await _generate_lesson_with_llm(req)


@router.get("/templates")
async def list_templates():
    """获取预置课程模板列表。"""
    return {
        "templates": LESSON_TEMPLATES,
        "total": len(LESSON_TEMPLATES),
        "source": "Socrates-Cube",
        "inspired_by": "OpenMAIC (https://github.com/THU-MAIC/OpenMAIC)",
    }


@router.post("/slide")
async def generate_single_slide(req: SlideGenerateRequest):
    """生成单页幻灯片内容。"""
    from ..core.llm_client import get_client_for_persona
    client = get_client_for_persona("expert")

    slide_desc = _SLIDE_TYPE_PROMPTS.get(req.slide_type, "讲解幻灯片")
    context_text = f"\n上下文：{req.context[:200]}" if req.context else ""
    prompt = (
        f"请为计算机网络课程生成一页关于「{req.topic}」的{slide_desc}。{context_text}\n\n"
        "以 JSON 返回：{\"title\": \"\", \"content\": \"\", \"key_points\": [], "
        "\"speaker_notes\": \"\", \"rfc_refs\": [], \"visual_hint\": \"\"}\n只返回JSON。"
    )
    try:
        raw = client.chat(prompt, max_tokens=600)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(raw[start:end])
            return {"slide": data, "slide_type": req.slide_type}
    except Exception as exc:
        logger.error("[Lesson] 幻灯片生成失败: %s", exc)

    return {
        "slide": {
            "title": req.topic,
            "content": f"关于 {req.topic} 的{slide_desc}内容",
            "key_points": [], "speaker_notes": "", "rfc_refs": [],
        },
        "slide_type": req.slide_type,
    }
