"""
Coordinator — Agent调度协调器基类
定义调度接口，Orchestrator继承实现
"""
from enum import Enum
from typing import List


class SessionPhase(str, Enum):
    PROFILING = "profiling"
    LEARNING = "learning"
    DIAGNOSING = "diagnosing"
    SIMULATING = "simulating"
    PLANNING = "planning"


class AgentCoordinator:
    """Agent调度协调器，在Orchestrator中使用"""

    def _determine_phase(
        self,
        turn_count: int,
        profile_completeness: float,
        user_message: str,
    ) -> SessionPhase:
        """根据上下文判断当前阶段"""
        raise NotImplementedError

    def _build_agent_chain(
        self,
        phase: SessionPhase,
        user_message: str,
    ) -> List[str]:
        """构建Agent调用链"""
        raise NotImplementedError
