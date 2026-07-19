"""
InterventionSelector —— 根据诊断误解 + 学生画像动态选择最优干预方式。

设计原则：
- 数据驱动：优先使用 misconception 中预配置的 interventions 列表
- 规则增强：根据 error_type 和 cognitive_style 动态调整优先级
- 可解释性：每条推荐附带 rationale 说明选择原因
- 无外部依赖：纯内存计算，不调用 LLM/DB
"""
import logging
from typing import Optional

from ..schema.intervention import InterventionRecommendation

logger = logging.getLogger(__name__)


# 知识主题关键词 → 仿真场景 ID 映射
# 通过 related_node_ids 关联的节点 topic 推断用户讨论的协议主题
SCENARIO_MAPPING = {
    "tcp_handshake": "three_way_handshake",
    "tcp_connection": "three_way_handshake",
    "three_way": "three_way_handshake",
    "connection_close": "four_way_wavehand",
    "four_way": "four_way_wavehand",
    "tcp_close": "four_way_wavehand",
    "fin": "four_way_wavehand",
    "dns": "dns_resolution",
    "domain": "dns_resolution",
    "http": "http_request",
    "request_response": "http_request",
    "encapsulation": "http_encapsulation",
    "layer": "http_encapsulation",
    "congestion": "congestion_control_basic",
    "sliding_window": "sliding_window",
    "window": "sliding_window",
    "flow_control": "sliding_window",
}


class InterventionSelector:
    """根据诊断误解 + 学生画像选择最优干预方式"""

    # 干预类型的展示标签
    TYPE_LABELS = {
        "simulation": "🎬 协议仿真演示",
        "exercise": "📝 对比练习题",
        "challenge": "🎯 智能追问验证",
        "doc": "📚 知识文档讲解",
    }

    # 干预类型的描述
    TYPE_DESCRIPTIONS = {
        "simulation": "通过可视化动画演示协议交互流程，直观理解正确行为",
        "exercise": "通过针对性练习题巩固概念，对比正确与错误认知",
        "challenge": "通过多角度追问检验理解深度，暴露隐藏的认知盲区",
        "doc": "阅读结构化知识文档，系统补充缺失的理论基础",
    }

    # 错误类型 → 干预类型亲和度（位置越靠前优先级越高）
    TYPE_AFFINITY = {
        "flow_omission": ["simulation", "exercise", "doc"],
        "layer_misplacement": ["simulation", "doc", "exercise"],
        "concept_confusion": ["exercise", "challenge", "doc"],
        "term_confusion": ["exercise", "challenge", "doc"],
        "over_simplification": ["doc", "exercise", "challenge"],
        "calculation_error": ["exercise", "doc", "challenge"],
        "reasoning_breakdown": ["doc", "exercise", "challenge"],
        "field_misunderstanding": ["exercise", "simulation", "doc"],
    }

    # 认知风格 → 干预偏好加权（正数提升优先级，负数降低）
    STYLE_BOOST = {
        "visual": {"simulation": 2, "exercise": 0, "doc": -1, "challenge": 0},
        "practical": {"simulation": 1, "exercise": 2, "doc": -1, "challenge": 0},
        "textual": {"simulation": -1, "exercise": 0, "doc": 2, "challenge": 0},
        "analogical": {"simulation": 1, "exercise": 0, "doc": 1, "challenge": 0},
    }

    def select(
        self,
        misconception: Optional[dict],
        error_type: str,
        profile: Optional[dict] = None,
        max_options: int = 3,
        diagnosis_result: Optional[dict] = None,
    ) -> list[InterventionRecommendation]:
        """
        返回排序后的干预建议列表（最多 max_options 条）。

        Args:
            misconception: 匹配到的误解记录（含 interventions 字段），可为 None
            error_type: 诊断识别的错误类型
            profile: 学生画像 dict，可包含 cognitive_style 等信息
            max_options: 最多返回的推荐数量
            diagnosis_result: 诊断结果 dict，含 related_node_ids/knowledge_node_ids

        Returns:
            list[InterventionRecommendation] 按优先级排序
        """
        profile = profile or {}

        # Step 1: 获取候选干预列表
        candidates = self._get_candidates(misconception, error_type)

        # Step 2: 应用认知风格加权
        cognitive_style = self._extract_cognitive_style(profile)
        scored_candidates = self._apply_style_boost(candidates, cognitive_style)

        # Step 3: 排序并生成推荐
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)

        recommendations = []
        for item in scored_candidates[:max_options]:
            rationale = self._build_rationale(item, error_type, cognitive_style)
            # 对 simulation 类型尝试解析具体仿真场景 ID
            item_id = item.get("id")
            if item["type"] == "simulation" and not item_id and diagnosis_result:
                item_id = self._resolve_simulation_scenario(diagnosis_result)
            rec = InterventionRecommendation(
                type=item["type"],
                id=item_id,
                label=self.TYPE_LABELS.get(item["type"], item["type"]),
                description=self.TYPE_DESCRIPTIONS.get(item["type"], ""),
                rationale=rationale,
                priority=item.get("priority", 1),
            )
            recommendations.append(rec)

        return recommendations

    def _get_candidates(self, misconception: Optional[dict], error_type: str) -> list[dict]:
        """从误解记录或默认规则获取候选干预"""
        candidates = []

        # 优先使用误解记录中预配置的 interventions
        if misconception and misconception.get("interventions"):
            for intv in misconception["interventions"]:
                candidates.append({
                    "type": intv["type"],
                    "id": intv.get("id"),
                    "priority": intv.get("priority", 1),
                    "score": 10 - intv.get("priority", 1),  # priority 越小分越高
                    "source": "data",
                })
        else:
            # Fallback: 根据 error_type 使用默认亲和度
            affinity = self.TYPE_AFFINITY.get(error_type, ["exercise", "doc", "challenge"])
            for i, int_type in enumerate(affinity):
                candidates.append({
                    "type": int_type,
                    "id": None,
                    "priority": i + 1,
                    "score": 10 - i,
                    "source": "rule",
                })

        return candidates

    def _extract_cognitive_style(self, profile: dict) -> str:
        """从学生画像中提取认知风格"""
        # 兼容多种画像结构
        if "cognitive_style" in profile:
            style = profile["cognitive_style"]
            if isinstance(style, dict):
                return style.get("type", "textual")
            return str(style)
        if "profile" in profile:
            return profile["profile"].get("cognitive_style", {}).get("type", "textual")
        return "textual"

    def _apply_style_boost(self, candidates: list[dict], cognitive_style: str) -> list[dict]:
        """根据认知风格调整候选分数"""
        boosts = self.STYLE_BOOST.get(cognitive_style, {})
        for candidate in candidates:
            boost = boosts.get(candidate["type"], 0)
            candidate["score"] += boost
        return candidates

    def _resolve_simulation_scenario(self, diagnosis_result: dict) -> Optional[str]:
        """
        从诊断结果中的知识节点 ID 推断仿真场景名称。

        策略：提取 related_node_ids 和 knowledge_node_ids 中的节点 ID，
        将节点 ID 字符串拆解为关键词片段，匹配 SCENARIO_MAPPING。
        """
        node_ids: list[str] = []
        node_ids.extend(diagnosis_result.get("related_node_ids", []))
        node_ids.extend(diagnosis_result.get("knowledge_node_ids", []))

        if not node_ids:
            return None

        # 从节点 ID 字符串中提取关键词片段并匹配
        for node_id in node_ids:
            # 节点 ID 通常形如 "kn_tcp_handshake"、"kp_014" 等
            node_lower = node_id.lower()
            for keyword, scenario_id in SCENARIO_MAPPING.items():
                if keyword in node_lower:
                    logger.debug(
                        "[InterventionSelector] 场景映射命中: node=%s keyword=%s -> %s",
                        node_id, keyword, scenario_id,
                    )
                    return scenario_id

        return None

    def _build_rationale(self, item: dict, error_type: str, cognitive_style: str) -> str:
        """生成推荐理由（可解释性）"""
        parts = []

        if item.get("source") == "data":
            parts.append("基于该误解的专属修复策略")
        else:
            type_reason = {
                "flow_omission": "流程遗漏类错误适合通过可视化演示纠正",
                "concept_confusion": "概念混淆适合通过对比练习澄清",
                "term_confusion": "术语混淆适合通过针对性练习区分",
                "layer_misplacement": "层次错位适合通过分层动画理解",
                "over_simplification": "过度简化适合通过文档补充完整认知",
                "calculation_error": "计算错误适合通过练习强化",
            }
            parts.append(type_reason.get(error_type, f"基于{error_type}错误类型推荐"))

        style_labels = {
            "visual": "视觉型学习风格偏好",
            "practical": "实践型学习风格偏好",
            "textual": "文本型学习风格偏好",
        }
        if cognitive_style in style_labels and cognitive_style != "textual":
            parts.append(style_labels[cognitive_style])

        return "；".join(parts) if parts else "通用推荐"


# 模块级单例
intervention_selector = InterventionSelector()
