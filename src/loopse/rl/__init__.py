"""
Socrates-Cube 强化学习模块
============================

三层强化学习架构（对应三个创新方向）：

方向1 - contextual_bandit.py:
    LinUCB 上下文赌博机，自适应选择资源类型（doc/exercise/code/mindmap/script）。
    集成到 ResourceGeneratorAgent._select_resource_types()。

方向2 - hmarl.py（最重要）:
    HMARL 分层多Agent强化学习元控制器。
    高层元控制器（Orchestrator级）优化Agent调度策略；
    低层子Agent策略包含 LinUCB(方向1) 和 DQN(方向3)。
    集成到 OrchestratorAgent.async_stream_reply()。

方向3 - dqn_path.py:
    DQN（Q学习 + 函数逼近）路径节点选择器。
    将PathPlanner从"静态拓扑查询"升级为"动态强化学习决策"。
    集成到 PathPlannerAgent.plan()。
"""

from .contextual_bandit import LinUCBBandit, get_bandit
from .hmarl import HMARLMetaController, HMARLAction, hmarl_controller
from .dqn_path import DQNPathSelector, get_dqn_selector

__all__ = [
    "LinUCBBandit",
    "get_bandit",
    "HMARLMetaController",
    "HMARLAction",
    "hmarl_controller",
    "DQNPathSelector",
    "get_dqn_selector",
]
