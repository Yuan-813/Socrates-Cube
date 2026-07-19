"""
RL 强化学习模块统计 API
========================

提供三个 RL 模块的实时统计数据查询接口，用于：
- 演示时展示"系统在学习"的可视化数据
- 调试时监控 Q 值收敛情况
- 奖励反馈（供 Challenger 结果回调 LinUCB/HMARL）
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/rl", tags=["reinforcement-learning"])

# ── 模块可用性检查 ──────────────────────────────────────────────────────────
try:
    from ..rl.hmarl import hmarl_controller
    _HMARL_OK = True
except Exception:
    _HMARL_OK = False
    hmarl_controller = None

try:
    from ..rl.contextual_bandit import get_bandit
    _BANDIT_OK = True
except Exception:
    _BANDIT_OK = False
    get_bandit = None

try:
    from ..rl.dqn_path import get_dqn_selector
    _DQN_OK = True
except Exception:
    _DQN_OK = False
    get_dqn_selector = None


# ── 数据模型 ──────────────────────────────────────────────────────────────

class RewardFeedback(BaseModel):
    user_id: str = Field(default="student-001")
    arm_name: str = Field(..., description="资源类型: doc/exercise/code/mindmap/script")
    reward: float = Field(..., ge=-1.0, le=1.0, description="奖励值 [-1, 1]")
    source: str = Field(default="manual", description="奖励来源: challenger/diagnosis/manual")


# ── 接口 ──────────────────────────────────────────────────────────────────

@router.get("/stats")
def get_rl_stats():
    """获取三个 RL 模块的综合实时统计"""
    result = {
        "rl_modules": {
            "direction_1_linucb": {
                "available": _BANDIT_OK,
                "description": "LinUCB 上下文赌博机：自适应资源类型选择",
            },
            "direction_2_hmarl": {
                "available": _HMARL_OK,
                "description": "HMARL 分层多Agent强化学习：元控制器调度优化",
            },
            "direction_3_dqn": {
                "available": _DQN_OK,
                "description": "DQN Q学习：学习路径节点智能选择",
            },
        }
    }

    if _HMARL_OK and hmarl_controller:
        result["hmarl_stats"] = hmarl_controller.get_stats()

    return result


@router.get("/stats/hmarl")
def get_hmarl_stats():
    """获取 HMARL 元控制器详细统计（含Q表分析）"""
    if not _HMARL_OK or hmarl_controller is None:
        raise HTTPException(status_code=503, detail="HMARL 模块不可用")
    stats = hmarl_controller.get_stats()
    # 附加 Q 表的动作优先级分布（前5个最优动作）
    q_mean = [
        sum(hmarl_controller.Q[s][a] for s in range(hmarl_controller.N_STATES)) / hmarl_controller.N_STATES
        for a in range(hmarl_controller.N_ACTIONS)
    ]
    top5 = sorted(range(hmarl_controller.N_ACTIONS), key=lambda a: q_mean[a], reverse=True)[:5]
    from ..rl.hmarl import HMARLAction
    stats["top5_actions"] = [
        {"action_id": a, "q_mean": round(q_mean[a], 5), "desc": HMARLAction.from_id(a).description}
        for a in top5
    ]
    return stats


@router.get("/stats/bandit/{user_id}")
def get_bandit_stats(user_id: str = "student-001"):
    """获取指定用户的 LinUCB Bandit 统计"""
    if not _BANDIT_OK or get_bandit is None:
        raise HTTPException(status_code=503, detail="LinUCB Bandit 模块不可用")
    bandit = get_bandit(user_id)
    return bandit.get_stats()


@router.get("/stats/dqn/{user_id}")
def get_dqn_stats(user_id: str = "student-001"):
    """获取指定用户的 DQN 路径选择器统计"""
    if not _DQN_OK or get_dqn_selector is None:
        raise HTTPException(status_code=503, detail="DQN 模块不可用")
    dqn = get_dqn_selector(user_id)
    return dqn.get_stats()


@router.post("/feedback/resource")
def submit_resource_feedback(req: RewardFeedback):
    """
    提交资源反馈奖励（用于更新 LinUCB Bandit）

    通常由 Challenger 结果或学生评分触发。
    """
    if not _BANDIT_OK or get_bandit is None:
        raise HTTPException(status_code=503, detail="LinUCB Bandit 模块不可用")
    try:
        bandit = get_bandit(req.user_id)
        bandit.update_from_feedback(req.arm_name, req.reward)
        logger.info("[RL-API] 资源反馈 user=%s arm=%s reward=%.3f src=%s",
                    req.user_id, req.arm_name, req.reward, req.source)
        return {"status": "ok", "arm_name": req.arm_name, "reward": req.reward}
    except Exception as exc:
        logger.error("[RL-API] 反馈更新失败: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
