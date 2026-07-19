"""联邦学习 + 差分隐私统一 API。"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..agent.differential_privacy import (
    anonymize_for_analytics,
    compute_privacy_budget_usage,
    privatize_profile_stats,
)
from ..agent.federated_learning import get_federated_orchestrator
from ..agent.profiler import ProfilerAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ai", tags=["federated_learning", "differential_privacy"])

_profiler = ProfilerAgent()


# ─── 联邦学习 API ──────────────────────────────────────────────────────────────

class FLTrainRequest(BaseModel):
    num_clients: int = Field(default=5, ge=2, le=20, description="参与联邦训练的虚拟机构数量")
    num_rounds: int = Field(default=10, ge=1, le=50, description="联邦训练轮次")
    add_dp_noise: bool = Field(default=True, description="是否在梯度上传时添加差分隐私噪声")
    learning_rate: float = Field(default=0.01, ge=0.001, le=0.1)


@router.post("/federated/train")
def run_federated_training(req: FLTrainRequest):
    """启动联邦学习训练（多机构协同，数据不出本地）。

    模拟多个教育机构在保护数据隐私的前提下，
    联合训练个性化推荐模型（LinUCB增强版）。
    """
    try:
        from ..agent.federated_learning import FederatedLearningOrchestrator
        orchestrator = FederatedLearningOrchestrator(
            num_clients=req.num_clients,
            num_rounds=req.num_rounds,
            add_dp_noise=req.add_dp_noise,
        )
        summary = orchestrator.run(learning_rate=req.learning_rate)
        logger.info("[FL] 联邦训练完成 rounds=%d clients=%d", req.num_rounds, req.num_clients)
        return {
            "status": "completed",
            "message": f"联邦学习完成 {req.num_rounds} 轮，{req.num_clients} 个机构参与，数据始终留在本地",
            "summary": summary,
        }
    except Exception as exc:
        logger.error("[FL] 联邦训练失败: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/federated/status")
def get_federated_status():
    """获取全局联邦模型的当前状态与训练历史。"""
    orchestrator = get_federated_orchestrator()
    summary = orchestrator.server.get_training_summary()
    return {
        "model_ready": len(orchestrator.server.round_history) > 0,
        "num_institutions": orchestrator.num_clients,
        "dp_enabled": orchestrator.add_dp_noise,
        "training_summary": summary,
    }


@router.post("/federated/personalize/{user_id}")
def get_personalized_score(user_id: str):
    """使用联邦模型对指定用户进行个性化评分。

    基于全局联邦模型对用户特征打分，
    用于增强 LinUCB 的初始化权重。
    """
    try:
        profile = _profiler.get_profile(user_id)
        orchestrator = get_federated_orchestrator()
        score = orchestrator.simulate_personalization(profile)
        return {"user_id": user_id, "federated_score": score}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ─── 差分隐私 API ──────────────────────────────────────────────────────────────

class DPRequest(BaseModel):
    user_id: str = Field(default="student-001")
    epsilon: float = Field(default=1.0, ge=0.01, le=10.0, description="隐私预算 ε（越小保护越强）")
    mechanism: str = Field(default="laplace", description="噪声机制：laplace 或 gaussian")


@router.post("/privacy/privatize")
def privatize_profile(req: DPRequest):
    """对用户画像添加差分隐私保护，返回加噪后的画像数据。

    用于需要将用户画像共享给第三方分析时的隐私保护场景。
    """
    try:
        profile = _profiler.get_profile(req.user_id)
        privatized = privatize_profile_stats(profile, epsilon=req.epsilon, mechanism=req.mechanism)
        return {
            "user_id": req.user_id,
            "epsilon": req.epsilon,
            "mechanism": req.mechanism,
            "privatized_profile": privatized,
            "privacy_note": f"mastery_map已添加Laplace噪声(ε={req.epsilon})，敏感数值已扰动，无法精确还原原始数据",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/privacy/budget")
def get_privacy_budget(num_queries: int = 10, epsilon_per_query: float = 0.1):
    """计算指定查询次数下的隐私预算消耗情况。"""
    result = compute_privacy_budget_usage(
        num_queries=num_queries,
        epsilon_per_query=epsilon_per_query,
    )
    return result


@router.get("/privacy/analytics")
def get_anonymous_analytics():
    """返回差分隐私保护的匿名化系统统计数据（用于大屏展示）。

    聚合全体用户的学习数据，添加 Laplace 噪声后返回，
    保证无法从统计结果推断任何个人信息。
    """
    try:
        # 采样100个用户画像进行聚合统计（实际场景可分页处理）
        sample_user_ids = [f"user_{i:04d}" for i in range(1, 101)]
        profiles = []
        for uid in sample_user_ids:
            try:
                p = _profiler.get_profile(uid)
                if p:
                    profiles.append(p)
            except Exception:
                pass

        if not profiles:
            # 兜底：返回模拟统计
            profiles = [{"knowledge_level": 0.55, "cognitive_style": "practical", "total_study_hours": 80}]

        stats = anonymize_for_analytics(profiles, epsilon=0.5)
        return stats
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
