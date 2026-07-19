"""
方向2 (最重要): HMARL 分层多智能体强化学习元控制器
=====================================================

架构设计
--------
本模块实现"编排层"的强化学习决策器，是三层 HMARL 框架的核心：

  高层（本模块）：HMARLMetaController
      - 状态: StudentProfile(8维) + 会话状态 + 近期诊断错误率
      - 动作: 调整 Challenger触发阈值 / ResourceGenerator激活策略 / 资源难度
      - 奖励: 全局学习效果（Δmastery + Δ置信度 + 误解修复率）
      - 算法: 表格Q-learning + ε-greedy（约320个离散状态 × 18个动作）

  低层（子Agent策略）：
      - DiagnosisAgent   → 现有规则（置信度置信域）
      - ResourceGenerator → LinUCB（方向1，contextual_bandit.py）
      - PathPlanner       → DQN Q学习（方向3，dqn_path.py）
      - Challenger        → 现有自适应多轮机制

集成方式（OrchestratorAgent.async_stream_reply）：
  1. 每轮开始: pre_profile = profiler.get_profile(user_id)
              action = hmarl_controller.get_action(pre_profile, session_state)
  2. 将 action 传入下游 Agent（challenger_threshold / force_resource / difficulty）
  3. 每轮结束: reward = hmarl_controller.compute_global_reward(pre, post, diag)
              hmarl_controller.step_update(pre_state, action, reward, post_state)
  4. SSE 推送: rl_update 事件（含决策可视化数据）
"""
from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 动作空间定义
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class HMARLAction:
    """
    元控制器的单步决策输出

    Attributes
    ----------
    action_id       : 动作编号 (0–17)
    challenger_threshold : Challenger 激活所需的连续无错误轮数 (3/5/8)
    force_resource  : 是否在 qa 意图时也强制触发 ResourceGenerator
    difficulty_delta: 资源难度调整 (-1=降低 / 0=不变 / +1=提高)
    description     : 人类可读的决策描述（用于 SSE 可视化）
    """
    action_id: int
    challenger_threshold: int = 5
    force_resource: bool = False
    difficulty_delta: int = 0
    description: str = ""

    @classmethod
    def from_id(cls, action_id: int) -> "HMARLAction":
        """解码动作ID为具体决策参数
        动作空间编码：
          action_id = challenger_code(0-2) + resource_code(0-1)*3 + diff_code(0-2)*6
          challenger_code → threshold: {0:3, 1:5, 2:8}
          resource_code   → force: {0:False, 1:True}
          diff_code       → difficulty: {0:-1, 1:0, 2:+1}
        """
        action_id = max(0, min(17, action_id))
        c_code = action_id % 3
        r_code = (action_id // 3) % 2
        d_code = (action_id // 6) % 3

        threshold = {0: 3, 1: 5, 2: 8}[c_code]
        force = bool(r_code)
        delta = {0: -1, 1: 0, 2: 1}[d_code]

        desc_parts = [f"挑战阈值={threshold}轮"]
        if force:
            desc_parts.append("主动生成资源")
        if delta > 0:
            desc_parts.append("难度↑")
        elif delta < 0:
            desc_parts.append("难度↓")
        return cls(
            action_id=action_id,
            challenger_threshold=threshold,
            force_resource=force,
            difficulty_delta=delta,
            description="；".join(desc_parts),
        )

    def to_dict(self) -> dict:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────────────────
# 元控制器核心
# ─────────────────────────────────────────────────────────────────────────────

class HMARLMetaController:
    """
    HMARL 元控制器（Hierarchical Multi-Agent Reinforcement Learning）

    使用表格 Q-learning 优化多 Agent 调度策略。

    状态离散化（共 320 个状态桶）：
        mastery_bin(5) × error_rate_bin(4) × style_bin(4) × turn_bin(4) = 320

    动作空间（18个动作）：
        challenger_threshold(3) × force_resource(2) × difficulty_delta(3) = 18
    """

    N_ACTIONS: int = 18
    MASTERY_BINS: int = 5
    ERROR_BINS: int = 4
    STYLE_BINS: int = 4
    TURN_BINS: int = 4
    N_STATES: int = MASTERY_BINS * ERROR_BINS * STYLE_BINS * TURN_BINS  # 320

    EPSILON_START: float = 0.35
    EPSILON_DECAY: float = 0.998
    EPSILON_MIN: float = 0.05
    ALPHA: float = 0.12       # 学习率
    GAMMA: float = 0.85       # 折扣因子

    STYLE_TO_BIN: Dict[str, int] = {
        "visual": 0, "practical": 1, "textual": 2, "analogical": 3,
    }

    def __init__(self):
        # Q 表：states × actions（用嵌套列表，无 numpy 依赖）
        self.Q: List[List[float]] = [
            [0.0] * self.N_ACTIONS for _ in range(self.N_STATES)
        ]
        # 初始化：对"正常模式" (action_id=7: threshold=5, no-force, diff=0) 给予微弱偏好
        for s in range(self.N_STATES):
            self.Q[s][7] = 0.05

        self.epsilon: float = self.EPSILON_START
        self._update_count: int = 0
        self._prev_state: Optional[int] = None
        self._prev_action: Optional[int] = None

        # 全局奖励历史（最近200条）
        self._reward_history: List[float] = []
        # 各子 Agent 本地奖励
        self._local_rewards: Dict[str, List[float]] = {
            "diagnosis": [], "resource": [], "path": [], "challenger": [],
        }
        # 用户级误差历史（计算 error_rate_bin 用）
        self._error_history: Dict[str, List[bool]] = {}

    # ── 状态提取 ──────────────────────────────────────────────────────────────

    def extract_state(
        self,
        profile: dict,
        session_state: dict,
        diag_result: Optional[dict] = None,
        user_id: str = "global",
    ) -> int:
        """将环境观测离散化为状态索引"""

        # Feature 1: 平均掌握度桶 (0-4)
        mastery_map = profile.get("mastery_map", {})
        if mastery_map:
            avg_mastery = sum(mastery_map.values()) / len(mastery_map)
        else:
            avg_mastery = 0.5
        mb = min(self.MASTERY_BINS - 1, int(avg_mastery * self.MASTERY_BINS))

        # Feature 2: 近期错误率桶 (0-3)
        if diag_result is not None:
            is_err = not diag_result.get("is_correct", True)
            hist = self._error_history.setdefault(user_id, [])
            hist.append(is_err)
            if len(hist) > 50:
                self._error_history[user_id] = hist[-30:]
        hist = self._error_history.get(user_id, [])
        if hist:
            recent = hist[-10:]
            err_rate = sum(1 for e in recent if e) / len(recent)
        else:
            err_rate = 0.3
        eb = min(self.ERROR_BINS - 1, int(err_rate * self.ERROR_BINS))

        # Feature 3: 认知风格桶 (0-3)
        style = profile.get("cognitive_style", "textual")
        sb = self.STYLE_TO_BIN.get(style, 2)

        # Feature 4: 对话轮次桶 (0-3)
        turn = profile.get("turn_count", 0)
        if turn <= 2:
            tb = 0
        elif turn <= 6:
            tb = 1
        elif turn <= 12:
            tb = 2
        else:
            tb = 3

        state = (
            mb * (self.ERROR_BINS * self.STYLE_BINS * self.TURN_BINS)
            + eb * (self.STYLE_BINS * self.TURN_BINS)
            + sb * self.TURN_BINS
            + tb
        )
        return state

    # ── 动作选择 ──────────────────────────────────────────────────────────────

    def select_action(self, state: int) -> HMARLAction:
        """ε-greedy 动作选择"""
        if random.random() < self.epsilon:
            action_id = random.randint(0, self.N_ACTIONS - 1)
        else:
            q_row = self.Q[state]
            action_id = q_row.index(max(q_row))

        self._prev_state = state
        self._prev_action = action_id
        return HMARLAction.from_id(action_id)

    def get_action(
        self,
        profile: dict,
        session_state: dict,
        diag_result: Optional[dict] = None,
        user_id: str = "global",
    ) -> HMARLAction:
        """主入口：提取状态 → 选择动作"""
        state = self.extract_state(profile, session_state, diag_result, user_id)
        return self.select_action(state)

    # ── 奖励计算 ──────────────────────────────────────────────────────────────

    def compute_global_reward(
        self,
        pre_profile: dict,
        post_profile: dict,
        diag_result: dict,
    ) -> float:
        """
        全局学习效果奖励信号

        奖励 = 0.40·Δmastery×10 + 0.30·Δconceptual×5 + 0.30·error_signal
        区间裁剪到 [-2.0, 2.0]
        """
        # Δmastery（掌握度均值提升）
        pre_m = list(pre_profile.get("mastery_map", {}).values())
        post_m = list(post_profile.get("mastery_map", {}).values())
        pre_avg = (sum(pre_m) / len(pre_m)) if pre_m else 0.5
        post_avg = (sum(post_m) / len(post_m)) if post_m else 0.5
        mastery_gain = (post_avg - pre_avg) * 10

        # Δ概念理解维度
        pre_cu = float(pre_profile.get("conceptual_understanding", 0.5))
        post_cu = float(post_profile.get("conceptual_understanding", 0.5))
        cu_gain = (post_cu - pre_cu) * 5

        # 错误信号：正确回答 + 置信度越高奖励越大
        is_correct = diag_result.get("is_correct", True)
        conf = float(diag_result.get("confidence", 0.7))
        error_signal = (conf - 0.5) * 2 if is_correct else -(1.0 - conf) * 2

        raw = 0.40 * mastery_gain + 0.30 * cu_gain + 0.30 * error_signal
        reward = max(-2.0, min(2.0, raw))

        self._reward_history.append(reward)
        if len(self._reward_history) > 200:
            self._reward_history = self._reward_history[-100:]
        logger.debug("[HMARL] 全局奖励=%.4f (mastery=%.4f cu=%.4f err=%.4f)",
                     reward, mastery_gain, cu_gain, error_signal)
        return reward

    def compute_local_reward_diagnosis(
        self,
        diag_result: dict,
        challenger_result: Optional[dict] = None,
    ) -> float:
        """诊断 Agent 本地奖励：置信度 + Challenger 确认分"""
        conf = float(diag_result.get("confidence", 0.7))
        base = (conf - 0.5) * 2  # [-1, 1]
        if challenger_result:
            score = challenger_result.get("understanding_score", 50) / 100.0
            bonus = (score - 0.5) * 0.5
            return max(-1.0, min(1.0, base + bonus))
        return max(-1.0, min(1.0, base))

    def compute_local_reward_resource(
        self,
        resource_bundle: dict,
        profile: dict,
    ) -> float:
        """ResourceGenerator 本地奖励：生成数量 + 认知风格匹配度"""
        total = resource_bundle.get("total_resources", 0)
        quality = total / 5.0  # 0-1

        style = profile.get("cognitive_style", "textual")
        selected = resource_bundle.get("selected_types", [])
        preferred = {
            "visual": ["mindmap", "script"],
            "practical": ["code", "exercise"],
            "textual": ["doc"],
            "analogical": ["doc", "script"],
        }.get(style, ["doc"])
        match_bonus = sum(0.1 for t in preferred if t in selected)
        return max(0.0, min(1.0, quality + match_bonus))

    def compute_local_reward_path(
        self,
        path: dict,
        pre_mastery_map: dict,
        post_mastery_map: dict,
    ) -> float:
        """PathPlanner 本地奖励：路径节点掌握度净提升"""
        nodes = path.get("nodes", [])
        if not nodes:
            return 0.0
        total_gain = 0.0
        for n in nodes:
            nid = n.get("node_id", "")
            pre = float(pre_mastery_map.get(nid, 0.5))
            post = float(post_mastery_map.get(nid, 0.5))
            total_gain += max(0.0, post - pre)
        return min(1.0, total_gain / len(nodes) * 10)

    # ── Q 值更新 ──────────────────────────────────────────────────────────────

    def step_update(
        self,
        state: int,
        action: int,
        reward: float,
        next_state: int,
    ):
        """
        TD(0) Q-learning 更新：
            Q(s,a) ← Q(s,a) + α·[r + γ·max_a' Q(s',a') - Q(s,a)]
        """
        q_cur = self.Q[state][action]
        q_next_max = max(self.Q[next_state])
        td_err = reward + self.GAMMA * q_next_max - q_cur
        self.Q[state][action] += self.ALPHA * td_err
        # ε 衰减
        self.epsilon = max(self.EPSILON_MIN, self.epsilon * self.EPSILON_DECAY)
        self._update_count += 1
        logger.debug(
            "[HMARL] Q更新 s=%d a=%d r=%.3f td=%.3f ε=%.3f cnt=%d",
            state, action, reward, td_err, self.epsilon, self._update_count,
        )

    def record_local_reward(self, agent_name: str, reward: float):
        """记录子 Agent 本地奖励（供统计分析）"""
        if agent_name in self._local_rewards:
            lst = self._local_rewards[agent_name]
            lst.append(float(reward))
            if len(lst) > 100:
                self._local_rewards[agent_name] = lst[-50:]

    # ── 统计 / SSE 数据 ───────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """返回 HMARL 实时统计（用于前端 SSE 可视化）"""
        recent = self._reward_history[-20:] if self._reward_history else [0.0]
        avg_r = sum(recent) / len(recent)
        # 各状态下最优动作分布（简化为全局 Q 均值向量）
        q_mean_by_action = [
            round(sum(self.Q[s][a] for s in range(self.N_STATES)) / self.N_STATES, 5)
            for a in range(self.N_ACTIONS)
        ]
        best_action = q_mean_by_action.index(max(q_mean_by_action))

        local_avgs = {
            name: round(sum(vs[-20:]) / len(vs[-20:]), 4) if vs else 0.0
            for name, vs in self._local_rewards.items()
        }
        return {
            "algorithm": "HMARL-TabularQ",
            "epsilon": round(self.epsilon, 4),
            "update_count": self._update_count,
            "avg_global_reward_recent20": round(avg_r, 4),
            "best_action_global": best_action,
            "best_action_desc": HMARLAction.from_id(best_action).description,
            "local_rewards": local_avgs,
            "n_states": self.N_STATES,
            "n_actions": self.N_ACTIONS,
        }

    def to_sse_data(
        self,
        state: int,
        action: HMARLAction,
        reward: float,
    ) -> dict:
        """生成用于 SSE 推送的可视化数据（展示 HMARL 决策过程）"""
        return {
            "rl_module": "HMARL",
            "state_id": state,
            "action": action.to_dict(),
            "reward": round(reward, 4),
            "epsilon": round(self.epsilon, 4),
            "stats": self.get_stats(),
        }

    # ── 持久化 ────────────────────────────────────────────────────────────────

    def to_state_dict(self) -> dict:
        return {
            "Q": self.Q,
            "epsilon": self.epsilon,
            "update_count": self._update_count,
        }

    @classmethod
    def from_state_dict(cls, data: dict) -> "HMARLMetaController":
        inst = cls()
        inst.Q = data["Q"]
        inst.epsilon = float(data.get("epsilon", cls.EPSILON_START))
        inst._update_count = int(data.get("update_count", 0))
        return inst


# ─────────────────────────────────────────────────────────────────────────────
# 全局单例（供 OrchestratorAgent 直接导入使用）
# ─────────────────────────────────────────────────────────────────────────────

hmarl_controller = HMARLMetaController()
