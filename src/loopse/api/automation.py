"""自动化 AI 功能接口 — 周报/提纲/批量试卷/批量入库。"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auto", tags=["automation"])


# ── 请求模型 ───────────────────────────────────────────────────────────────

class WeeklyReportRequest(BaseModel):
    user_id: str = Field(default="student-001")
    days: int = Field(default=7, ge=1, le=30, description="统计最近几天的学习数据")


class ReviewOutlineRequest(BaseModel):
    user_id: str = Field(default="student-001")
    exam_type: str = Field(default="final_exam", description="复习目标：final_exam/hcia/ccna/job_interview")
    focus_kp_ids: list[str] = Field(default_factory=list, description="重点知识点ID列表（空则自动取薄弱点）")


class MockExamRequest(BaseModel):
    user_id: str = Field(default="student-001")
    question_count: int = Field(default=30, ge=10, le=60)
    difficulty: int = Field(default=3, ge=1, le=5)
    knowledge_points: list[str] = Field(
        default_factory=lambda: ["TCP三次握手", "IP地址与子网划分", "路由选择协议", "HTTP与HTTPS"],
        description="涵盖的知识点范围",
    )


class BatchIngestRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, description="待入库文本块列表")
    source: str = Field(default="batch_upload")


# ── 工具函数 ───────────────────────────────────────────────────────────────

def _get_user_stats(user_id: str, days: int = 7) -> dict:
    """从 DB 获取用户近 N 天的学习统计。"""
    from ..db.repositories import get_db_session
    from ..db.models import AssessmentRecord, MisconceptionRecord
    since = datetime.now() - timedelta(days=days)
    try:
        with get_db_session() as db:
            assessments = db.query(AssessmentRecord).filter(
                AssessmentRecord.user_id == user_id,
                AssessmentRecord.create_time >= since,
            ).all()
            misconceptions = db.query(MisconceptionRecord).filter(
                MisconceptionRecord.user_id == user_id,
                MisconceptionRecord.last_seen >= since,
            ).all()
            return {
                "total_attempts": len(assessments),
                "avg_score": sum(a.score for a in assessments) / max(len(assessments), 1),
                "wrong_patterns": [m.pattern for m in misconceptions[:10]],
                "weak_nodes": list({m.knowledge_node_id for m in misconceptions}),
            }
    except Exception as exc:
        logger.warning("[Auto] 获取用户统计失败 user=%s: %s", user_id, exc)
        return {"total_attempts": 0, "avg_score": 0, "wrong_patterns": [], "weak_nodes": []}


# ── 路由 ──────────────────────────────────────────────────────────────────

@router.post("/weekly-report")
def generate_weekly_report(req: WeeklyReportRequest):
    """生成用户学习周报（Markdown 格式）。"""
    from ..core.llm_client import get_client_for_persona
    from ..agent.profiler import ProfilerAgent

    profiler = ProfilerAgent()
    profile = profiler.get_profile(req.user_id)
    stats = _get_user_stats(req.user_id, req.days)

    dim_labels = {
        "conceptual_understanding": "概念理解", "protocol_analysis": "协议分析",
        "calculation_ability": "计算能力", "error_diagnosis": "错误诊断",
        "system_design": "系统设计", "knowledge_connection": "知识关联",
        "expression_clarity": "表达清晰", "self_correction": "自我纠错",
    }
    dims_text = "\n".join(
        f"  - {label}: {round(profile.get(dim, 0.5) * 100)}分"
        for dim, label in dim_labels.items()
    )
    wrong_text = "、".join(stats["wrong_patterns"][:5]) or "暂无"
    weak_text = "、".join(stats["weak_nodes"][:5]) or "暂无"

    prompt = (
        f"请为计算机网络学习者生成一份专业的{req.days}天学习周报（Markdown格式）。\n\n"
        f"学习数据：\n"
        f"- 练习次数：{stats['total_attempts']} 次\n"
        f"- 平均得分：{round(stats['avg_score'], 1)} 分\n"
        f"- 近期错误模式：{wrong_text}\n"
        f"- 薄弱知识节点：{weak_text}\n\n"
        f"8维能力画像：\n{dims_text}\n\n"
        "周报需包含：学习摘要、进步亮点、薄弱项分析、下周学习建议（具体到知识点）。"
        "使用温暖鼓励的语气，格式美观。"
    )
    try:
        client = get_client_for_persona("professor")
        report = client.chat(prompt, max_tokens=1500)
    except Exception as exc:
        logger.error("[Auto] 周报生成失败: %s", exc)
        raise HTTPException(status_code=500, detail="周报生成失败，请稍后重试")

    return {
        "user_id": req.user_id,
        "period_days": req.days,
        "generated_at": datetime.now().isoformat(),
        "report_markdown": report,
        "stats_summary": stats,
    }


@router.post("/review-outline")
def generate_review_outline(req: ReviewOutlineRequest):
    """生成复习提纲/考前速查卡（Markdown 格式）。"""
    from ..core.llm_client import get_client_for_persona
    from ..agent.profiler import ProfilerAgent

    profiler = ProfilerAgent()
    profile = profiler.get_profile(req.user_id)
    weak_points = profile.get("weak_points", [])
    focus_kps = req.focus_kp_ids or weak_points[:8]

    exam_map = {
        "final_exam": "计算机网络期末考试",
        "hcia": "华为HCIA-Datacom认证考试",
        "ccna": "思科CCNA认证考试",
        "job_interview": "网络工程师求职面试",
    }
    exam_name = exam_map.get(req.exam_type, req.exam_type)

    prompt = (
        f"请生成一份针对「{exam_name}」的精华复习提纲（Markdown格式）。\n\n"
        f"学习者薄弱点：{', '.join(focus_kps) or '通用网络知识'}\n\n"
        "复习提纲要求：\n"
        "1. 按知识模块分章节，每章包含核心概念速记（表格/要点）\n"
        "2. 高频考点标注⭐，易混淆点标注⚠️\n"
        "3. 每节末尾附 2-3 道经典真题或模拟题（含答案）\n"
        "4. 总长度控制在 1500-2500 字，便于考前速查\n"
        "5. 使用 Markdown 标题、表格、代码块等增强可读性"
    )
    try:
        client = get_client_for_persona("professor")
        outline = client.chat(prompt, max_tokens=3000)
    except Exception as exc:
        logger.error("[Auto] 复习提纲生成失败: %s", exc)
        raise HTTPException(status_code=500, detail="复习提纲生成失败")

    return {
        "user_id": req.user_id,
        "exam_type": req.exam_type,
        "exam_name": exam_name,
        "focus_kp_ids": focus_kps,
        "generated_at": datetime.now().isoformat(),
        "outline_markdown": outline,
    }


@router.post("/mock-exam")
def generate_mock_exam(req: MockExamRequest):
    """批量生成模拟试卷（多知识点混合）。"""
    from ..core.llm_client import llm_client
    import json, re

    all_questions = []
    per_kp = max(1, req.question_count // len(req.knowledge_points))

    for kp in req.knowledge_points:
        prompt = (
            f"请为计算机网络知识点「{kp}」生成 {per_kp} 道难度{req.difficulty}级的混合题目。\n"
            "包含单选题（choice）和判断题（judge），以JSON数组格式返回。\n"
            "每道题包含：id(唯一字符串)、type(choice/judge)、question、options(选择题用，"
            "{'A':'...','B':'...','C':'...','D':'...'})、answer、explanation、knowledge_point。\n"
            "不要任何多余文字，只返回JSON数组。"
        )
        try:
            raw = llm_client.chat(prompt, max_tokens=2000)
            clean = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
            parsed = json.loads(clean)
            if isinstance(parsed, list):
                for q in parsed:
                    q.setdefault("knowledge_point", kp)
                all_questions.extend(parsed[:per_kp])
        except Exception as exc:
            logger.warning("[Auto] 知识点 %s 题目生成失败: %s", kp, exc)
            # 兜底题目
            all_questions.append({
                "id": f"fallback_{len(all_questions)}",
                "type": "choice",
                "question": f"关于{kp}，以下说法正确的是？",
                "options": {"A": "需进一步学习", "B": "详见教材相关章节", "C": "参考RFC标准", "D": "实践中验证"},
                "answer": "A",
                "explanation": f"请学习{kp}相关章节以获得正确答案。",
                "knowledge_point": kp,
            })

    return {
        "user_id": req.user_id,
        "total_questions": len(all_questions),
        "difficulty": req.difficulty,
        "knowledge_points": req.knowledge_points,
        "generated_at": datetime.now().isoformat(),
        "questions": all_questions[:req.question_count],
    }


@router.post("/batch-ingest")
def batch_ingest(req: BatchIngestRequest):
    """批量将文本块存入用户知识库（user_uploads 集合）。"""
    from ..kb.document_processor import process_text
    from ..kb.vector_store import vector_store

    total_chunks = 0
    for text in req.texts:
        if not text.strip():
            continue
        try:
            docs = process_text(text.strip(), source=req.source)
            if docs:
                vector_store.add_documents(
                    collection_name="user_uploads",
                    documents=[d["document"] for d in docs],
                    metadatas=[d["metadata"] for d in docs],
                    ids=[d["id"] for d in docs],
                )
                total_chunks += len(docs)
        except Exception as exc:
            logger.warning("[Auto] 批量入库块处理失败: %s", exc)

    return {
        "source": req.source,
        "input_count": len(req.texts),
        "chunks_added": total_chunks,
        "message": f"已将 {len(req.texts)} 段文本切分为 {total_chunks} 个知识块并入库",
    }


@router.post("/memory/archive")
def archive_session_memory(user_id: str, session_id: str, persona: str = "general"):
    """将指定会话归档为长期记忆。"""
    from ..agent.memory_manager import memory_manager
    record_id = memory_manager.archive_session(user_id, session_id, persona)
    return {
        "success": bool(record_id),
        "memory_id": record_id,
        "message": "会话已归档到长期记忆" if record_id else "会话内容不足，无需归档",
    }


@router.get("/memory/{user_id}")
def get_memories(user_id: str, persona: str = "general", limit: int = 10):
    """获取用户的长期记忆列表。"""
    from ..agent.memory_manager import memory_manager
    memories = memory_manager.get_memories(user_id, persona=persona, limit=limit)
    return {"user_id": user_id, "persona": persona, "memories": memories, "count": len(memories)}


@router.delete("/memory/{user_id}")
def clear_memories(user_id: str, persona: Optional[str] = None, memory_type: Optional[str] = None):
    """清理用户记忆（归档标记）。"""
    from ..agent.memory_manager import memory_manager
    count = memory_manager.clear(user_id, persona=persona, memory_type=memory_type)
    return {"success": True, "cleared_count": count, "message": f"已清理 {count} 条记忆"}
