"""
方向3: DQN 路径节点选择器 —— 基于 Q 学习的自适应路径规划
===========================================================

设计思路
--------
将 PathPlanner 的节点选择从"静态拓扑 + 启发式规则"升级为"RL 驱动的动态决策"：

  状态 (State)：
      20 个课程知识节点的掌握度向量（每维 0-1）
      → 直接映射为 mastery_map 中 kp_001~kp_020 的掌握度

  动作 (Action)：
      选择哪个节点作为本轮的重点学习目标（20 个离散动作）
      → 影响路径节点的排列顺序，将焦点节点置于最前

  奖励 (Reward)：
      下一轮该节点掌握度提升量 × 10
      + 低掌握度节点被选中并提升的额外奖励（避免只学已懂的）

  算法：
      线性函数逼近 Q-learning（Q(s,a) = W_a^T · s）
      + ε-greedy 探索
      + 知识图谱先验初始化（低掌握度节点有更高初始 Q 值）

集成方式（PathPlannerAgent.plan）：
  1. 在拓扑排序后，调用 selector.rerank_nodes() 对节点重新排序
  2. 将排序结果传入 _build_path_nodes()，优先生成聚焦节点的推荐理由
  3. 下一轮 Profiler 更新后，调用 selector.update_from_mastery_delta() 反馈奖励
"""
from __future__ import annotations

import logging
import math
import random
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# 知识节点标准顺序（与 knowledge_graph.json 中 kp_xxx 节点对齐）
# 实际节点 ID 由图谱动态获取；此列表为默认降级顺序
_DEFAULT_NODE_ORDER: List[str] = [f"kp_{i:03d}" for i in range(1, 21)]


def _dot(a: list, b: list) -> float:
    return sum(x * y for x, y in zip(a, b))

def _vec_scale(v: list, s: float) -> list:
    return [x * s for x in v]

def _vec_add(a: list, b: list) -> list:
    return [x + y for x, y in zip(a, b)]


class DQNPathSelector:
    """
    基于线性函数逼近的 Q-learning 路径节点选择器

    Q(s, a) = W_a^T · s，其中:
      s ∈ ℝ^{N_NODES}  各节点掌握度
      a ∈ {0, …, N_NODES-1}  选择某节点

    TD 更新：
      W_a += α · (r + γ · max_{a'} Q(s', a') - Q(s, a)) · s
    """

    N_NODES: int = 20
    GAMMA: float = 0.90
    ALPHA: float = 0.015
    EPSILON_START: float = 0.40
    EPSILON_DECAY: float = 0.995
    EPSILON_MIN: float = 0.05

    def __init__(self):
        # W[a] ∈ ℝ^{N_NODES}，线性权重（每个动作一组）
        self.W: List[List[float]] = self._init_weights()
        self.epsilon: float = self.EPSILON_START
        self._update_count: int = 0
        # 上一步记录（供延迟奖励使用）
        self._last_state: Optional[list] = None
        self._last_action: Optional[int] = None
        self._last_node_order: Optional[List[str]] = None

    def _init_weights(self) -> List[List[float]]:
        """
        知识图谱先验初始化：
        - 对角线 W[a][a] = -2.0：节点 a 掌握度越低 → Q 值越高 → 越倾向选它
        - 相邻 W[a][a-1] = 0.5：前置节点掌握度高时，当前节点更易学
        - 其余为 0
        """
        W = [[0.0] * self.N_NODES for _ in range(self.N_NODES)]
        for i in range(self.N_NODES):
            W[i][i] = -2.0         # 低掌握 → 高优先
            if i > 0:
                W[i][i - 1] = 0.5  # 前置已学 → 当前可学
        return W

    # ── 状态编码 ──────────────────────────────────────────────────────────────

    def build_state(
        self,
        mastery_map: dict,
        node_order: Optional[List[str]] = None,
    ) -> Tuple[list, List[str]]:
        """
        将掌握度字典编码为状态向量，同时返回实际使用的节点顺序

        Returns
        -------
        (state_vector, node_order_used)
        """
        order = node_order or _DEFAULT_NODE_ORDER
        state = [float(mastery_map.get(nid, 0.5)) for nid in order[:self.N_NODES]]
        # 补齐到 N_NODES
        while len(state) < self.N_NODES:
            state.append(0.5)
        return state[:self.N_NODES], order[:self.N_NODES]

    # ── Q 值计算 ──────────────────────────────────────────────────────────────

    def q_values(self, state: list) -> List[float]:
        """Q(s, a) = W[a]^T · s, for all a"""
        return [_dot(self.W[a], state) for a in range(self.N_NODES)]

    # ── 动作选择 ──────────────────────────────────────────────────────────────

    def select_focus_node(
        self,
        mastery_map: dict,
        candidate_node_ids: List[str],
        node_order: Optional[List[str]] = None,
    ) -> Tuple[str, float]:
        """
        在候选节点中选择重点节点（ε-greedy）

        Returns
        -------
        (selected_node_id, q_value)
        """
        if not candidate_node_ids:
            return "", 0.0

        state, order = self.build_state(mastery_map, node_order)
        qs = self.q_values(state)

        # 只考虑候选节点
        cands = [(nid, order.index(nid) if nid in order else -1) for nid in candidate_node_ids]
        cands = [(nid, idx) for nid, idx in cands if 0 <= idx < self.N_NODES]
        if not cands:
            return candidate_node_ids[0], 0.0

        if random.random() < self.epsilon:
            nid, idx = random.choice(cands)
        else:
            nid, idx = max(cands, key=lambda x: qs[x[1]])

        # 记录上一步（供延迟奖励）
        self._last_state = state
        self._last_action = idx
        self._last_node_order = order

        q_val = qs[idx] if idx < len(qs) else 0.0
        logger.debug("[DQN] 焦点节点=%s Q=%.3f ε=%.3f", nid, q_val, self.epsilon)
        return nid, round(q_val, 4)

    # ── 路径重排 ──────────────────────────────────────────────────────────────

    def rerank_nodes(
        self,
        nodes: List[Dict[str, Any]],
        mastery_map: dict,
        focus_node_id: Optional[str] = None,
        node_order: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        基于 Q 值对路径节点重排（保持 locked 节点在末尾，focus 节点置首）

        排序规则：
          1. locked 节点排最后（保持依赖约束）
          2. focus_node 置最前
          3. 其余节点按 Q 值降序（Q值越高=掌握度越低=越需学）
        """
        if len(nodes) <= 1:
            return nodes

        state, order = self.build_state(mastery_map, node_order)
        qs = self.q_values(state)

        def node_q(nd: Dict[str, Any]) -> float:
            nid = nd.get("node_id", "")
            if nid in order:
                idx = order.index(nid)
                if idx < self.N_NODES:
                    return qs[idx]
            return 0.0

        locked = [n for n in nodes if n.get("status") == "locked"]
        active = [n for n in nodes if n.get("status") != "locked"]
        active_sorted = sorted(active, key=node_q, reverse=True)

        if focus_node_id:
            focus = [n for n in active_sorted if n.get("node_id") == focus_node_id]
            rest  = [n for n in active_sorted if n.get("node_id") != focus_node_id]
            active_sorted = focus + rest

        result = active_sorted + locked
        logger.debug("[DQN] 重排路径: %s", [n.get("node_id") for n in result[:5]])
        return result

    # ── TD 更新 ───────────────────────────────────────────────────────────────

    def update(
        self,
        state: list,
        action_idx: int,
        reward: float,
        next_state: list,
    ):
        """
        TD(0) 线性 Q-learning 更新：
            W[a] += α · (r + γ·max Q(s') - Q(s,a)) · s
        """
        if action_idx < 0 or action_idx >= self.N_NODES:
            return
        q_cur = _dot(self.W[action_idx], state)
        q_next_max = max(self.q_values(next_state))
        td_err = reward + self.GAMMA * q_next_max - q_cur
        delta = _vec_scale(state, self.ALPHA * td_err)
        self.W[action_idx] = _vec_add(self.W[action_idx], delta)
        # ε 衰减
        self.epsilon = max(self.EPSILON_MIN, self.epsilon * self.EPSILON_DECAY)
        self._update_count += 1
        logger.debug("[DQN] TD更新 a=%d r=%.3f td=%.3f ε=%.3f cnt=%d",
                     action_idx, reward, td_err, self.epsilon, self._update_count)

    def update_from_mastery_delta(
        self,
        node_id: str,
        pre_mastery_map: dict,
        post_mastery_map: dict,
        node_order: Optional[List[str]] = None,
    ):
        """
        从掌握度变化计算奖励并更新（Profiler 更新后调用）

        奖励 = (post_mastery - pre_mastery) × 10（裁剪到 -3.0~3.0）
        """
        order = node_order or _DEFAULT_NODE_ORDER
        if node_id not in order:
            return
        idx = order.index(node_id)
        if idx >= self.N_NODES:
            return

        pre_state, _ = self.build_state(pre_mastery_map, order)
        post_state, _ = self.build_state(post_mastery_map, order)
        pre_m = float(pre_mastery_map.get(node_id, 0.5))
        post_m = float(post_mastery_map.get(node_id, 0.5))
        reward = max(-3.0, min(3.0, (post_m - pre_m) * 10))
        self.update(pre_state, idx, reward, post_state)

    # ── 统计 / 持久化 ─────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        w_flat = [v for row in self.W for v in row]
        w_max = max(w_flat) if w_flat else 0.0
        w_min = min(w_flat) if w_flat else 0.0
        return {
            "algorithm": "LinearQ-DQN",
            "epsilon": round(self.epsilon, 4),
            "update_count": self._update_count,
            "weight_range": {"min": round(w_min, 4), "max": round(w_max, 4)},
        }

    def to_state_dict(self) -> dict:
        return {
            "W": self.W,
            "epsilon": self.epsilon,
            "update_count": self._update_count,
        }

    @classmethod
    def from_state_dict(cls, data: dict) -> "DQNPathSelector":
        inst = cls()
        inst.W = data["W"]
        inst.epsilon = float(data.get("epsilon", cls.EPSILON_START))
        inst._update_count = int(data.get("update_count", 0))
        return inst


# ─────────────────────────────────────────────────────────────────────────────
# 用户级实例管理
# ─────────────────────────────────────────────────────────────────────────────

_DQN_STORE: Dict[str, DQNPathSelector] = {}


def get_dqn_selector(user_id: str = "global") -> DQNPathSelector:
    """获取用户级 DQN 实例（按需创建）"""
    if user_id not in _DQN_STORE:
        _DQN_STORE[user_id] = DQNPathSelector()
    return _DQN_STORE[user_id]
