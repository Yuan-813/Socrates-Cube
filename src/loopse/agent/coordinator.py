"""
多智能体协调器 —— 意图识别与流程路由

职责：
  1. 根据用户输入识别意图（qa / resource / planning / simulation）
  2. 决定本轮需要激活哪些下游 Agent
  3. 提取关键知识点，供资源生成等 Agent 使用

OrchestratorAgent 调用本模块后，只需按照返回的 DispatchPlan 依次驱动各 Agent，
自身不再承担意图判断逻辑，职责更纯粹。
"""
from __future__ import annotations

from dataclasses import dataclass, field


# ------------------------------------------------------------------ #
# 意图类型
# ------------------------------------------------------------------ #
INTENT_QA = "qa"
INTENT_RESOURCE = "resource"
INTENT_PLANNING = "planning"
INTENT_SIMULATION = "simulation"
INTENT_CAREER = "career"
INTENT_INTERVIEW = "interview"

_PLANNING_KW = ["先学什么", "学习计划", "学习路径", "我该", "建议我", "学习顺序"]
_RESOURCE_KW = ["给我", "生成", "总结", "思维导图", "练习题", "代码示例", "代码", "例题"]
_SIMULATION_KW = ["步骤", "过程", "握手", "挥手", "流程", "演示", "模拟"]
_CAREER_KW = ["华为认证", "HCIA", "HCIP", "CCNA", "CCNP", "岗位", "找工作", "职业规划", "求职", "技能差距", "gap分析"]
_INTERVIEW_KW = ["面试", "考察我", "模拟面试", "面试题", "面试官", "面试准备"]

_KNOWLEDGE_TOKENS = [
    "TCP 三次握手", "TCP 四次挥手", "滑动窗口", "拥塞控制",
    "流量控制", "HTTP", "DNS", "子网划分", "IP 分片", "ARP",
]


# ------------------------------------------------------------------ #
# 调度计划（数据类）
# ------------------------------------------------------------------ #
@dataclass
class DispatchPlan:
    """协调器输出：描述本轮应激活的 Agent 和关键参数。"""

    intent: str
    """识别出的用户意图：qa / resource / planning / simulation / career / interview"""

    activate_resource: bool = False
    """是否需要激活 ResourceGeneratorAgent"""

    activate_planning: bool = False
    """是否需要激活 PathPlannerAgent"""

    activate_career: bool = False
    """是否需要激活 CareerNavigatorAgent"""

    resource_type: str = "doc"
    """资源生成类型：doc / exercise / code"""

    knowledge_point: str = "TCP 三次握手"
    """本轮涉及的核心知识点"""

    persona_id: str = "professor"
    """当前 AI 人格 ID：professor / engineer / peer / interviewer"""

    extra: dict = field(default_factory=dict)
    """供扩展使用的附加上下文"""


# ------------------------------------------------------------------ #
# 协调器
# ------------------------------------------------------------------ #
class AgentCoordinator:
    """
    多智能体协调器。

    职责仅限于：意图识别 → 路由决策 → 知识点提取。
    不持有任何 Agent 实例，不执行 LLM 调用，可独立单元测试。
    """

    def dispatch(
        self,
        message: str,
        retrieval: dict | None = None,
        persona_id: str = "professor",
    ) -> DispatchPlan:
        """
        分析用户消息，返回本轮的调度计划。

        Args:
            message:    用户输入原文
            retrieval:  可选，检索结果（含 graph_nodes）；用于知识点提取
            persona_id: 当前选择的 AI 人格 ID

        Returns:
            DispatchPlan
        """
        intent = self._detect_intent(message)
        knowledge_point = self._extract_knowledge_point(message, retrieval or {})
        resource_type = self._pick_resource_type(message)

        return DispatchPlan(
            intent=intent,
            activate_resource=(intent == INTENT_RESOURCE),
            activate_planning=(intent == INTENT_PLANNING),
            activate_career=(intent == INTENT_CAREER),
            resource_type=resource_type,
            knowledge_point=knowledge_point,
            persona_id=persona_id,
        )

    # ------------------------------------------------------------------ #
    # 内部方法
    # ------------------------------------------------------------------ #
    @staticmethod
    def _detect_intent(message: str) -> str:
        if any(kw in message for kw in _INTERVIEW_KW):
            return INTENT_INTERVIEW
        if any(kw in message for kw in _CAREER_KW):
            return INTENT_CAREER
        if any(kw in message for kw in _PLANNING_KW):
            return INTENT_PLANNING
        if any(kw in message for kw in _RESOURCE_KW):
            return INTENT_RESOURCE
        if any(kw in message for kw in _SIMULATION_KW):
            return INTENT_SIMULATION
        return INTENT_QA

    @staticmethod
    def _extract_knowledge_point(message: str, retrieval: dict) -> str:
        nodes = retrieval.get("graph_nodes", [])
        if nodes:
            return nodes[0].get("name", _KNOWLEDGE_TOKENS[0])
        for token in _KNOWLEDGE_TOKENS:
            if token.lower() in message.lower():
                return token
        return _KNOWLEDGE_TOKENS[0]

    @staticmethod
    def _pick_resource_type(message: str) -> str:
        if "代码" in message:
            return "code"
        if "练习" in message or "例题" in message:
            return "exercise"
        return "doc"
