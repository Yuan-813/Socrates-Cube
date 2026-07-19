"""
方向1: LinUCB 上下文赌博机 —— 自适应资源类型选择
=======================================================

设计思路：
  - 每个"臂"(arm) 对应一种学习资源类型(doc/exercise/code/mindmap/script)
  - 上下文(context) 由学生认知风格 + 错误类型 + 掌握度等特征构成
  - UCB 得分 = θ_a^T · x + α · √(x^T · A_a^{-1} · x)
  - 探索项保证系统不停留在次优策略，利用项最大化即时收益

奖励信号来源：
  - 下一轮诊断置信度提升量 Δconfidence
  - Challenger 理解分数 understanding_score
  - 学生主动请求复习同类资源（正向信号）

与现有系统集成：
  ResourceGeneratorAgent._select_resource_types() → get_bandit(user_id).select_arms(context, n)
  奖励更新通过 reward_update_resource() 在 Orchestrator 中调用
"""
from __future__ import annotations

import logging
import math
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 纯 Python 实现 LinUCB（不依赖 numpy，保证在任何环境可用）
# ─────────────────────────────────────────────────────────────────────────────

def _dot(a: list, b: list) -> float:
    return sum(x * y for x, y in zip(a, b))

def _mat_vec(M: list, v: list) -> list:
    return [_dot(row, v) for row in M]

def _outer(a: list, b: list) -> list:
    return [[x * y for y in b] for x in a]

def _mat_add(A: list, B: list) -> list:
    return [[A[i][j] + B[i][j] for j in range(len(A[0]))] for i in range(len(A))]

def _identity(n: int) -> list:
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

def _solve_lower(L: list, b: list) -> list:
    """前向替代（Cholesky分解辅助）"""
    n = len(b)
    x = [0.0] * n
    for i in range(n):
        s = b[i]
        for j in range(i):
            s -= L[i][j] * x[j]
        x[i] = s / L[i][i]
    return x

def _cholesky(A: list) -> Optional[list]:
    """Cholesky分解 A = L·L^T，返回L或None（非正定时）"""
    n = len(A)
    L = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            s = A[i][j] - sum(L[i][k] * L[j][k] for k in range(j))
            if i == j:
                if s <= 1e-10:
                    return None
                L[i][j] = math.sqrt(s)
            else:
                L[i][j] = s / L[j][j]
    return L

def _inv_sym_pd(A: list) -> list:
    """正定对称矩阵的逆（Cholesky法），失败时返回单位阵"""
    n = len(A)
    L = _cholesky(A)
    if L is None:
        return _identity(n)
    # L^{-1} via forward substitution
    L_inv = []
    for j in range(n):
        e = [1.0 if i == j else 0.0 for i in range(n)]
        L_inv.append(_solve_lower(L, e))
    # A^{-1} = (L^T)^{-1} · L^{-1}
    # L_inv rows are columns of L^{-1}
    # A^{-1}[i][j] = sum_k L_inv[k][i] * L_inv[k][j]
    inv = [[sum(L_inv[k][i] * L_inv[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
    return inv


class LinUCBBandit:
    """
    LinUCB 上下文赌博机（纯 Python 实现）

    参数
    -----
    alpha : float
        UCB 探索系数。越大越倾向探索；建议范围 0.2–1.5。
        默认 0.5（演示场景下平衡探索与利用）。
    """

    ARM_NAMES: List[str] = ["doc", "exercise", "code", "mindmap", "script"]
    CONTEXT_DIM: int = 13
    # 各维度说明:
    #   0-3  : cognitive_style one-hot (visual/practical/textual/analogical)
    #   4-10 : error_type one-hot (7类)
    #   11   : 当前知识节点平均掌握度 (0-1)
    #   12   : 归一化对话轮次 (0-1，除以50截断)

    ERROR_TYPE_INDEX: Dict[str, int] = {
        "flow_omission": 0,
        "layer_misplacement": 1,
        "field_misunderstanding": 2,
        "concept_confusion": 3,
        "reasoning_breakdown": 4,
        "factual": 5,
        "none": 6,
    }
    STYLE_INDEX: Dict[str, int] = {
        "visual": 0, "practical": 1, "textual": 2, "analogical": 3,
    }

    def __init__(self, alpha: float = 0.5):
        self.alpha = alpha
        n = self.n_arms = len(self.ARM_NAMES)
        d = self.CONTEXT_DIM
        # A_a: d×d feature covariance matrix (init identity)
        self.A: List[list] = [_identity(d) for _ in range(n)]
        # b_a: d-dim reward accumulator
        self.b: List[list] = [[0.0] * d for _ in range(n)]
        # θ_a = A_a^{-1} b_a (cached)
        self._theta: List[list] = [[0.0] * d for _ in range(n)]
        # Selection stats
        self._arm_counts: List[int] = [0] * n
        self._total: int = 0
        # Pending context for delayed reward update: (arm_idx, context)
        self._pending: List[Tuple[int, list]] = []

    # ── 核心接口 ──────────────────────────────────────────────────────────────

    def build_context(self, profile: dict, diagnosis: Optional[dict]) -> list:
        """将学生画像 + 诊断结果编码为 CONTEXT_DIM 维特征向量"""
        x = [0.0] * self.CONTEXT_DIM

        # Cognitive style one-hot
        style = profile.get("cognitive_style", "textual")
        x[self.STYLE_INDEX.get(style, 2)] = 1.0

        # Error type one-hot
        error_type = (diagnosis or {}).get("error_type", "none")
        x[4 + self.ERROR_TYPE_INDEX.get(error_type, 6)] = 1.0

        # Average mastery
        mastery_map = profile.get("mastery_map", {})
        if mastery_map:
            x[11] = sum(mastery_map.values()) / len(mastery_map)
        else:
            x[11] = 0.5

        # Normalized turn count
        x[12] = min(1.0, profile.get("turn_count", 0) / 50.0)
        return x

    def select_arms(
        self,
        context: list,
        n: int = 3,
    ) -> Tuple[List[str], List[float]]:
        """
        UCB 选臂：返回 (selected_type_names, ucb_scores)

        UCB_a = θ_a^T · x + α · √(x^T · A_a^{-1} · x)
        """
        ucb_scores: List[float] = []
        for i in range(self.n_arms):
            A_inv = _inv_sym_pd(self.A[i])
            theta = _mat_vec(A_inv, self.b[i])
            self._theta[i] = theta
            exploitation = _dot(theta, context)
            # exploration = α * sqrt(x^T A^{-1} x)
            Ax = _mat_vec(A_inv, context)
            quad = max(0.0, _dot(context, Ax))
            exploration = self.alpha * math.sqrt(quad)
            ucb_scores.append(exploitation + exploration)

        ranked = sorted(range(self.n_arms), key=lambda i: ucb_scores[i], reverse=True)
        top_n = ranked[:n]
        self._total += 1
        for idx in top_n:
            self._arm_counts[idx] += 1

        # 记录主选臂，供延迟奖励使用
        self._pending.append((top_n[0], list(context)))
        if len(self._pending) > 100:
            self._pending = self._pending[-50:]

        names = [self.ARM_NAMES[i] for i in top_n]
        scores = [round(ucb_scores[i], 4) for i in top_n]
        logger.debug("[LinUCB] 选臂结果 %s | UCB=%s | total=%d", names, scores, self._total)
        return names, scores

    def update(self, arm_idx: int, context: list, reward: float):
        """
        LinUCB 在线参数更新：
            A_a += x · x^T
            b_a += r · x
        """
        reward = max(-1.0, min(1.0, float(reward)))
        outer = _outer(context, context)
        self.A[arm_idx] = _mat_add(self.A[arm_idx], outer)
        self.b[arm_idx] = [self.b[arm_idx][k] + reward * context[k] for k in range(self.CONTEXT_DIM)]
        logger.debug("[LinUCB] 更新臂 %s | 奖励=%.4f", self.ARM_NAMES[arm_idx], reward)

    def update_from_feedback(self, arm_name: str, reward: float):
        """按资源类型名称更新（外部接口，奖励由 Orchestrator 计算后调用）"""
        if arm_name not in self.ARM_NAMES:
            return
        arm_idx = self.ARM_NAMES.index(arm_name)
        if self._pending:
            _, ctx = self._pending[-1]
            self.update(arm_idx, ctx, reward)

    def reward_from_diagnosis_delta(
        self,
        arm_name: str,
        pre_confidence: float,
        post_confidence: float,
    ):
        """
        用相邻两轮诊断置信度差值作为奖励信号（最常用接口）
        reward = (post_conf - pre_conf) * 2，区间约 -2~+2，裁剪到 -1~+1
        """
        reward = (post_confidence - pre_confidence) * 2
        self.update_from_feedback(arm_name, reward)

    # ── 统计 / 序列化 ─────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """返回可视化统计信息"""
        theta_norms = []
        for i in range(self.n_arms):
            A_inv = _inv_sym_pd(self.A[i])
            t = _mat_vec(A_inv, self.b[i])
            theta_norms.append(round(math.sqrt(sum(v * v for v in t)), 4))
        return {
            "algorithm": "LinUCB",
            "alpha": self.alpha,
            "total_selections": self._total,
            "arm_counts": dict(zip(self.ARM_NAMES, self._arm_counts)),
            "theta_norms": dict(zip(self.ARM_NAMES, theta_norms)),
        }

    def to_state_dict(self) -> dict:
        return {
            "A": self.A,
            "b": self.b,
            "arm_counts": self._arm_counts,
            "total": self._total,
            "alpha": self.alpha,
        }

    @classmethod
    def from_state_dict(cls, data: dict) -> "LinUCBBandit":
        inst = cls(alpha=data.get("alpha", 0.5))
        inst.A = data["A"]
        inst.b = data["b"]
        inst._arm_counts = data.get("arm_counts", [0] * 5)
        inst._total = data.get("total", 0)
        return inst


# ─────────────────────────────────────────────────────────────────────────────
# 全局/用户级 Bandit 实例管理
# ─────────────────────────────────────────────────────────────────────────────

_BANDIT_STORE: Dict[str, LinUCBBandit] = {}


def get_bandit(user_id: str = "global") -> LinUCBBandit:
    """获取用户级别的 Bandit 实例（按需创建，共享全局先验）"""
    if user_id not in _BANDIT_STORE:
        _BANDIT_STORE[user_id] = LinUCBBandit(alpha=0.5)
    return _BANDIT_STORE[user_id]
