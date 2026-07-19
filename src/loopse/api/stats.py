"""学习数据统计聚合 API — /api/v1/stats

提供面向前端 Dashboard 的数据聚合端点，从多个数据表汇总用户学习数据。
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/stats", tags=["stats"])

_PROFILE_DIMS = [
    "conceptual_understanding",
    "protocol_analysis",
    "calculation_ability",
    "error_diagnosis",
    "system_design",
    "knowledge_connection",
    "expression_clarity",
    "self_correction",
]


def _safe_loads(text: Optional[str], default: Any = None) -> Any:
    if not text:
        return default
    try:
        return json.loads(text)
    except Exception:
        return default


@router.get("/summary")
def get_stats_summary(user_id: str = Query(..., description="用户ID")):
    """聚合返回用户学习统计数据，用于 Dashboard 展示。"""
    from ..db.repositories import get_db_session
    from ..db.models import (
        ChatSession,
        StudentProfile,
        AssessmentRecord,
        LearningPathNode,
        KnowledgeNodeRecord,
        AgentLog,
    )
    from sqlalchemy import func as sa_func, distinct

    try:
        with get_db_session() as db:
            # ── 对话统计 ─────────────────────────────────────────
            total_sessions = (
                db.query(sa_func.count(ChatSession.session_id))
                .filter(ChatSession.user_id == user_id)
                .scalar() or 0
            )

            # 累计消息数：解析每个 session 的 messages JSON
            sessions = (
                db.query(ChatSession.messages)
                .filter(ChatSession.user_id == user_id)
                .all()
            )
            total_messages = 0
            for (msgs_raw,) in sessions:
                msgs = _safe_loads(msgs_raw, [])
                if isinstance(msgs, list):
                    total_messages += len(msgs)

            # 学习天数（按日期去重）
            session_dates = (
                db.query(sa_func.date(ChatSession.create_time))
                .filter(ChatSession.user_id == user_id)
                .distinct()
                .all()
            )
            learning_days = len(session_dates)

            # ── 用户画像 ─────────────────────────────────────────
            profile_record = (
                db.query(StudentProfile)
                .filter(StudentProfile.user_id == user_id)
                .first()
            )
            profile_data = _safe_loads(
                profile_record.profile_json if profile_record else None, {}
            )

            # 8 维雷达分数 (0-100)
            radar_scores = [
                round(float(profile_data.get(dim, 0.5)) * 100)
                for dim in _PROFILE_DIMS
            ]

            # 整体掌握度
            overall_mastery = round(sum(radar_scores) / len(radar_scores))

            # 掌握度历史
            mastery_history: list[int] = profile_data.get("masteryHistory", [])
            if not mastery_history and overall_mastery > 0:
                mastery_history = [overall_mastery]

            # 薄弱知识点
            weak_points: list[str] = profile_data.get("weak_points", [])[:5]

            # ── 诊断/评估统计 ─────────────────────────────────────
            assessment_count = (
                db.query(sa_func.count(AssessmentRecord.assessment_id))
                .filter(AssessmentRecord.user_id == user_id)
                .scalar() or 0
            )

            diagnosis_avg_score_raw = (
                db.query(sa_func.avg(AssessmentRecord.score))
                .filter(AssessmentRecord.user_id == user_id)
                .scalar()
            )
            diagnosis_avg_score = round(float(diagnosis_avg_score_raw or 0), 1)

            # 最近 10 条评估得分趋势
            recent_assessments = (
                db.query(
                    AssessmentRecord.score,
                    AssessmentRecord.knowledge_node_id,
                    AssessmentRecord.create_time,
                )
                .filter(AssessmentRecord.user_id == user_id)
                .order_by(AssessmentRecord.create_time.desc())
                .limit(10)
                .all()
            )
            score_trend = [
                {
                    "score": round(float(r.score), 1),
                    "node_id": r.knowledge_node_id,
                    "time": r.create_time.strftime("%m-%d") if r.create_time else "",
                }
                for r in reversed(recent_assessments)
            ]

            # ── 学习路径进度 ─────────────────────────────────────
            from ..db.models import LearningPath
            path_nodes = (
                db.query(LearningPathNode.status)
                .join(LearningPath, LearningPathNode.path_id == LearningPath.path_id)
                .filter(LearningPath.user_id == user_id)
                .all()
            )
            total_nodes = len(path_nodes)
            completed_nodes = sum(
                1 for (s,) in path_nodes if s in ("completed", "done", "mastered")
            )
            chapter_progress = (
                round(completed_nodes / total_nodes * 100) if total_nodes > 0 else 0
            )

            # ── 知识节点总量（系统级） ──────────────────────────
            knowledge_nodes_count = (
                db.query(sa_func.count(KnowledgeNodeRecord.node_id)).scalar() or 0
            )

    except Exception as exc:
        logger.warning("[Stats] 聚合查询异常，返回默认值: %s", exc)
        return {
            "user_id": user_id,
            "total_sessions": 0,
            "total_messages": 0,
            "learning_days": 0,
            "overall_mastery": 50,
            "mastery_history": [50],
            "radar_scores": [50] * 8,
            "radar_dims": _PROFILE_DIMS,
            "weak_points": [],
            "assessment_count": 0,
            "diagnosis_avg_score": 0.0,
            "score_trend": [],
            "chapter_progress": 0,
            "knowledge_nodes_count": 0,
        }

    return {
        "user_id": user_id,
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "learning_days": learning_days,
        "overall_mastery": overall_mastery,
        "mastery_history": mastery_history,
        "radar_scores": radar_scores,
        "radar_dims": _PROFILE_DIMS,
        "weak_points": weak_points,
        "assessment_count": assessment_count,
        "diagnosis_avg_score": diagnosis_avg_score,
        "score_trend": score_trend,
        "chapter_progress": chapter_progress,
        "knowledge_nodes_count": knowledge_nodes_count,
    }
