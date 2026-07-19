"""管理员后台 API — /api/v1/admin

所有端点均需要 admin 权限（JWT role_type == "admin"）。
提供用户管理、系统统计、日志查看等管理功能。
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# ═══════════════════════════════════════════════════════════════════════════
# 权限验证
# ═══════════════════════════════════════════════════════════════════════════

def _require_admin(authorization: Optional[str] = Header(default=None)):
    """从 Authorization: Bearer <token> 中解码 JWT，要求 role_type == admin。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="需要登录认证")
    token = authorization[7:]
    try:
        from .auth import decode_token
        payload = decode_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="无效或过期的 token")
        role = payload.get("role_type", "")
        if role != "admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")
        return payload
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[Admin] 权限验证异常: %s", exc)
        raise HTTPException(status_code=401, detail="认证异常")


# ═══════════════════════════════════════════════════════════════════════════
# 请求/响应模型
# ═══════════════════════════════════════════════════════════════════════════

class UpdateRoleRequest(BaseModel):
    role_type: str


class UserItem(BaseModel):
    id: str
    username: str
    email: Optional[str]
    phone: Optional[str]
    role_type: str
    onboarded: bool
    create_time: Optional[str]


class PagedUsers(BaseModel):
    total: int
    page: int
    size: int
    items: list[UserItem]


# ═══════════════════════════════════════════════════════════════════════════
# 端点实现
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/users", response_model=PagedUsers)
def list_users(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    keyword: Optional[str] = Query(default=None, description="按用户名/邮箱搜索"),
    _admin=Depends(_require_admin),
):
    """获取用户列表（分页）。支持按用户名/邮箱关键词搜索。"""
    from ..db.repositories import get_db_session
    from ..db.models import User
    from sqlalchemy import func as sa_func

    with get_db_session() as db:
        q = db.query(User)
        if keyword:
            like = f"%{keyword}%"
            q = q.filter(
                (User.username.like(like)) | (User.email.like(like))
            )
        total = q.count()
        users = q.order_by(User.create_time.desc()).offset((page - 1) * size).limit(size).all()

    items = [
        UserItem(
            id=u.id,
            username=u.username,
            email=u.email,
            phone=u.phone,
            role_type=u.role_type or "student",
            onboarded=bool(u.onboarded),
            create_time=u.create_time.strftime("%Y-%m-%d %H:%M") if u.create_time else None,
        )
        for u in users
    ]
    return PagedUsers(total=total, page=page, size=size, items=items)


@router.get("/stats")
def get_system_stats(_admin=Depends(_require_admin)):
    """系统级统计概览：用户总量、今日活跃、会话数、诊断数等。"""
    from ..db.repositories import get_db_session
    from ..db.models import User, ChatSession, AssessmentRecord, KnowledgeNodeRecord, StudentProfile
    from sqlalchemy import func as sa_func

    try:
        with get_db_session() as db:
            total_users = db.query(sa_func.count(User.id)).scalar() or 0

            # 今日活跃（今日有 chat_session 的用户数）
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            active_today = (
                db.query(sa_func.count(sa_func.distinct(ChatSession.user_id)))
                .filter(ChatSession.create_time >= today_start)
                .scalar() or 0
            )

            total_sessions = db.query(sa_func.count(ChatSession.session_id)).scalar() or 0
            total_diagnoses = db.query(sa_func.count(AssessmentRecord.assessment_id)).scalar() or 0
            knowledge_nodes_count = db.query(sa_func.count(KnowledgeNodeRecord.node_id)).scalar() or 0

            # 平均掌握度（从 StudentProfile 汇总）
            profiles = db.query(StudentProfile.profile_json).all()
            mastery_vals = []
            for (pj,) in profiles:
                try:
                    import json as _json
                    pd = _json.loads(pj or "{}")
                    dims = [
                        "conceptual_understanding", "protocol_analysis",
                        "calculation_ability", "error_diagnosis",
                        "system_design", "knowledge_connection",
                        "expression_clarity", "self_correction",
                    ]
                    avg = sum(float(pd.get(d, 0.5)) for d in dims) / len(dims)
                    mastery_vals.append(avg)
                except Exception:
                    pass
            avg_mastery = round(sum(mastery_vals) / len(mastery_vals) * 100) if mastery_vals else 0

            # 近 7 天每日新增用户（用于折线图）
            daily_new = []
            for i in range(6, -1, -1):
                day = datetime.now().date() - timedelta(days=i)
                day_start = datetime.combine(day, datetime.min.time())
                day_end = datetime.combine(day, datetime.max.time())
                cnt = (
                    db.query(sa_func.count(User.id))
                    .filter(User.create_time.between(day_start, day_end))
                    .scalar() or 0
                )
                daily_new.append({"date": day.strftime("%m-%d"), "count": cnt})

    except Exception as exc:
        logger.warning("[Admin] stats 查询异常: %s", exc)
        return {
            "total_users": 0, "active_today": 0, "total_sessions": 0,
            "total_diagnoses": 0, "avg_mastery": 0, "knowledge_nodes_count": 0,
            "daily_new_users": [],
        }

    return {
        "total_users": total_users,
        "active_today": active_today,
        "total_sessions": total_sessions,
        "total_diagnoses": total_diagnoses,
        "avg_mastery": avg_mastery,
        "knowledge_nodes_count": knowledge_nodes_count,
        "daily_new_users": daily_new,
    }


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    req: UpdateRoleRequest,
    _admin=Depends(_require_admin),
):
    """修改指定用户的角色。"""
    allowed_roles = {"student", "professional", "self_learner", "job_seeker", "admin", "teacher"}
    if req.role_type not in allowed_roles:
        raise HTTPException(status_code=400, detail=f"无效角色，允许值: {', '.join(allowed_roles)}")

    from ..db.repositories import get_db_session
    from ..db.models import User

    with get_db_session() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        old_role = user.role_type
        user.role_type = req.role_type
        user.update_time = datetime.now()

    logger.info("[Admin] 用户角色变更 id=%s %s -> %s", user_id, old_role, req.role_type)
    return {"status": "ok", "user_id": user_id, "role_type": req.role_type}


@router.get("/logs")
def get_agent_logs(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=100),
    _admin=Depends(_require_admin),
):
    """获取 Agent 执行日志（分页，最新优先）。"""
    from ..db.repositories import get_db_session
    from ..db.models import AgentLog
    from sqlalchemy import func as sa_func

    with get_db_session() as db:
        total = db.query(sa_func.count(AgentLog.log_id)).scalar() or 0
        logs = (
            db.query(AgentLog)
            .order_by(AgentLog.timestamp.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

    items = [
        {
            "log_id": lg.log_id,
            "session_id": lg.session_id,
            "agent_name": lg.agent_name,
            "action": lg.action,
            "timestamp": lg.timestamp.strftime("%Y-%m-%d %H:%M:%S") if lg.timestamp else "",
        }
        for lg in logs
    ]
    return {"total": total, "page": page, "size": size, "items": items}
