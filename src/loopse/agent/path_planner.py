"""可解释学习路径规划 Agent（PathPlanner）。

本模块基于知识图谱拓扑排序和学生画像生成个性化学习路径，核心特性：

1. **图谱驱动排序**：从 KnowledgeGraph 的 20 个课程节点、48 个认知理解单元（ACU）
   和 87 条关系边中，通过拓扑排序确定合理的学习顺序。
2. **三维推荐理由**：每个节点附带 graph_dependency（图谱依赖）、
   diagnosis_result（诊断结果关联）、cognitive_style（认知风格匹配）
   三个维度的推荐理由，确保路径可解释。
3. **动态状态**：节点状态自动计算为 completed / in_progress /
   pending / locked，基于当前掌握度和前置依赖满足度。
4. **高级目标选择**：当所有目标掌握度均较高时，自动选择高难度
   或下游未达标的节点作为新目标。

输出格式：包含 path_id、节点列表、预估总时长、质量评分的字典。
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from ..kb.knowledge_graph import KnowledgeNode, knowledge_graph
from .cognitive_engine import CognitiveAgentMixin

# ── RL 方向3: DQN 路径节点选择器（软依赖）──
try:
    from ..rl.dqn_path import get_dqn_selector as _get_dqn
    _RL_DQN_AVAILABLE = True
except Exception:
    _RL_DQN_AVAILABLE = False


class PathPlannerAgent(CognitiveAgentMixin):
    """基于知识图谱的个性化学习路径规划 Agent。

    继承 CognitiveAgentMixin，在规划过程中记录推理轨迹和工具调用，
    并通过 self_reflection 质量检查确保每个节点都有推荐理由且数量不超限。
    """

    def plan(
        self,
        user_id: str,
        profile: dict[str, Any],
        target_node_ids: Optional[list[str]] = None,
        max_nodes: int = 10,
    ) -> dict[str, Any]:
        trace = self.make_trace(f"path:{user_id}")
        mastery_map: dict[str, float] = profile.get("mastery_map", {})
        weak_points: list[str] = profile.get("weak_points", [])

        targets = [nid for nid in (target_node_ids or weak_points[:3] or self._default_targets()) if knowledge_graph.get_node(nid)]
        if not targets:
            targets = [node.id for node in knowledge_graph.get_all_nodes()[:3]]

        all_mastery_high = all(knowledge_graph.estimate_mastery(nid, mastery_map) >= 0.82 for nid in targets)
        if all_mastery_high:
            targets = self._select_advanced_targets(mastery_map)
            trace.add_step("advanced_target", "all targets have high mastery", f"selected advanced: {targets}", 0.85)
        else:
            trace.add_step("target_selection", str(target_node_ids or weak_points), str(targets), 0.82)

        weak_prereqs = knowledge_graph.find_weak_prerequisites(targets, mastery_map, threshold=0.65)
        all_ids = list(dict.fromkeys([*(node.id for node in weak_prereqs), *targets]))
        sorted_nodes = knowledge_graph.topological_sort(all_ids)[:max_nodes]
        trace.add_step("graph_ordering", f"candidates={all_ids}", f"ordered={[n.id for n in sorted_nodes]}", 0.86)

        # RL方向3: DQN 对拓扑排序后的节点进行智能重排
        dqn_focus_node = None
        dqn_q_value = 0.0
        if _RL_DQN_AVAILABLE and len(sorted_nodes) > 1:
            try:
                dqn = _get_dqn(user_id)
                candidate_ids = [n.id for n in sorted_nodes]
                node_order = [n.id for n in knowledge_graph.get_all_nodes()]
                dqn_focus_node, dqn_q_value = dqn.select_focus_node(
                    mastery_map, candidate_ids, node_order
                )
                sorted_nodes_dicts = []
                # 将 KnowledgeNode 列表转为临时字典以供重排
                _tmp_dicts = [{"node_id": n.id, "_node": n} for n in sorted_nodes]
                reranked = dqn.rerank_nodes(
                    _tmp_dicts, mastery_map, dqn_focus_node, node_order
                )
                sorted_nodes = [d["_node"] for d in reranked]
                trace.add_step(
                    "dqn_rerank",
                    f"focus={dqn_focus_node} q={dqn_q_value:.3f}",
                    f"reranked=[{','.join(n.id for n in sorted_nodes[:3])}...]",
                    0.80,
                )
            except Exception as _dqn_exc:
                import logging as _log
                _log.getLogger(__name__).warning("[PathPlanner] DQN重排失败: %s", _dqn_exc)

        path_nodes = self._build_path_nodes(sorted_nodes, mastery_map, targets, profile)
        total_time = sum(node["estimated_time"] for node in path_nodes)
        reflection = self.reflect(
            trace,
            {
                "has_nodes": len(path_nodes) > 0,
                "reasons_present": all(len(node["recommendation_reason"]) >= 12 for node in path_nodes),
                "within_limit": len(path_nodes) <= max_nodes,
            },
        )

        return {
            "path_id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": f"计算机网络个性化学习路径（{len(path_nodes)} 个节点）",
            "description": "根据当前画像、薄弱点和知识图谱前置依赖生成。",
            "total_estimated_time": total_time,
            "nodes": path_nodes,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "agent_trace": trace.to_dict(),
            "quality_score": round(reflection["confidence"], 3),
            # RL附加信息（供前端可视化）
            "rl_info": {
                "algorithm": "DQN-LinearQ",
                "focus_node": dqn_focus_node,
                "focus_q_value": round(dqn_q_value, 4),
                "dqn_available": _RL_DQN_AVAILABLE,
            } if _RL_DQN_AVAILABLE else {"algorithm": "topology_heuristic"},
        }

    def _build_path_nodes(
        self,
        nodes: list[KnowledgeNode],
        mastery_map: dict[str, float],
        target_ids: list[str],
        profile: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        result = []
        completed = set()
        profile = profile or {}
        weak_points: list[str] = profile.get("weak_points", [])
        for index, node in enumerate(nodes):
            mastery = knowledge_graph.estimate_mastery(node.id, mastery_map)
            prereqs = [item.id for item in knowledge_graph.get_prerequisites(node.id)]
            prereqs_met = all(knowledge_graph.estimate_mastery(pid, mastery_map) >= 0.65 for pid in prereqs)
            if mastery >= 0.82:
                status = "completed"
                completed.add(node.id)
            elif index == 0 or prereqs_met or all(pid in completed for pid in prereqs):
                status = "in_progress" if not result else "pending"
            else:
                status = "locked"
            result.append(
                {
                    "node_id": node.id,
                    "node_name": node.name,
                    "type": node.type,
                    "chapter": node.chapter,
                    "difficulty": node.difficulty,
                    "estimated_time": node.estimated_time,
                    "recommendation_reason": self._reason(node, mastery, node.id in target_ids, prereqs_met),
                    "reason_sources": self._build_3d_reasons(
                        node, mastery, prereqs, node.id in target_ids,
                        node.id in weak_points, profile,
                    ),
                    "suggested_resources": ["doc", "exercise"] if node.difficulty <= 3 else ["doc", "exercise", "code"],
                    "prerequisites": prereqs,
                    "prerequisites_met": prereqs_met,
                    "status": status,
                    "current_mastery": mastery,
                    "is_target": node.id in target_ids,
                }
            )
        return result

    @staticmethod
    def _reason(node: KnowledgeNode, mastery: float, is_target: bool, prereqs_met: bool) -> str:
        if is_target and mastery < 0.5:
            return f"{node.name} 是本轮核心目标，当前掌握度约 {mastery:.0%}，需要优先用讲解和练习补齐。"
        if not prereqs_met:
            return f"{node.name} 依赖的前置知识尚未完全达标，先排入路径可降低后续学习断层。"
        if mastery < 0.65:
            return f"{node.name} 掌握度约 {mastery:.0%}，适合通过对比题和流程追问进一步巩固。"
        return f"{node.name} 与目标主题强相关，建议快速复习并用一组变式题确认迁移能力。"

    @staticmethod
    def _build_3d_reasons(
        node: KnowledgeNode,
        mastery: float,
        prereqs: list[str],
        is_target: bool,
        is_weak: bool,
        profile: dict[str, Any],
    ) -> dict[str, str]:
        """Build three-dimensional recommendation reasons.

        Dimensions:
        - graph_dependency: why this node is a prerequisite (from knowledge graph)
        - diagnosis_result: what weak points need repair (from Diagnosis)
        - cognitive_style: why this order is optimal (from Profiler)
        """
        # 1. Graph dependency
        if prereqs:
            graph_reason = (
                f"{node.name} 的前置节点 {', '.join(prereqs[:3])} 构成学习依赖链，"
                f"需先掌握前置知识才能有效学习本节点。"
            )
        else:
            graph_reason = f"{node.name} 是基础概念节点，无严格前置依赖，适合直接学习。"

        # 2. Diagnosis result
        if is_weak:
            diag_reason = (
                f"诊断结果显示 {node.name} 相关概念存在误解或掌握不足(当前掌握度 {mastery:.0%})，"
                f"需要针对性修复和巩固。"
            )
        elif is_target:
            diag_reason = (
                f"{node.name} 是本轮学习目标，当前掌握度 {mastery:.0%}，"
                f"需要通过变式题和对比练习提升理解深度。"
            )
        else:
            diag_reason = (
                f"{node.name} 当前掌握度 {mastery:.0%}，可通过快速复习巩固。"
            )

        # 3. Cognitive style
        conceptual = float(profile.get("conceptual_understanding", 0.5))
        protocol = float(profile.get("protocol_analysis", 0.5))
        calculation = float(profile.get("calculation_ability", 0.5))
        if node.type == "protocol" and protocol < 0.6:
            style_reason = (
                f"学生协议分析维度偏低({protocol:.2f})，"
                f"建议先通过仿真动画理解 {node.name} 的协议流程，再进入文本学习。"
            )
        elif node.type == "concept" and conceptual < 0.6:
            style_reason = (
                f"学生概念理解维度偏低({conceptual:.2f})，"
                f"建议先通过对比题和概念图建立 {node.name} 的知识框架。"
            )
        elif node.difficulty >= 4 and calculation < 0.6:
            style_reason = (
                f"{node.name} 难度较高(难度{node.difficulty})，学生计算能力偏弱({calculation:.2f})，"
                f"建议配合代码示例和计算练习逐步掌握。"
            )
        else:
            style_reason = (
                f"根据学生学习风格画像，{node.name} 适合当前的学习顺序和方式。"
            )

        return {
            "graph_dependency": graph_reason,
            "diagnosis_result": diag_reason,
            "cognitive_style": style_reason,
            "career_relevance": _build_career_reason(node),
        }

    @staticmethod
    def _default_targets() -> list[str]:
        return ["kp_005", "kp_007", "kp_008"]

    @staticmethod
    def _select_advanced_targets(mastery_map: dict[str, float]) -> list[str]:
        """When all current targets are mastered, select next-level advanced targets."""
        all_nodes = knowledge_graph.get_all_nodes()
        high_mastery_nodes = [n for n in all_nodes if knowledge_graph.estimate_mastery(n.id, mastery_map) >= 0.82]

        if len(high_mastery_nodes) >= len(all_nodes) * 0.7:
            high_diff_nodes = [n.id for n in all_nodes if n.difficulty >= 4]
            if high_diff_nodes:
                return high_diff_nodes[:3]

        downstream_nodes = []
        for node in high_mastery_nodes:
            downstream = knowledge_graph.get_downstream_nodes(node.id)
            for dnode in downstream:
                if knowledge_graph.estimate_mastery(dnode.id, mastery_map) < 0.7:
                    downstream_nodes.append(dnode.id)
        if downstream_nodes:
            return list(dict.fromkeys(downstream_nodes))[:3]

        review_nodes = [n.id for n in all_nodes if 0.65 <= knowledge_graph.estimate_mastery(n.id, mastery_map) < 0.82]
        if review_nodes:
            return review_nodes[:3]

        return [node.id for node in all_nodes if node.difficulty >= 4][:3] or ["kp_005", "kp_007", "kp_008"]


def _build_career_reason(node) -> str:
    """生成职业相关性推荐理由（模块级常量函数）。"""
    node_type = getattr(node, "type", "concept")
    node_name = getattr(node, "name", "")
    if node_type == "skill":
        return f"{node_name} 是实践技能节点，直接对应工程师岗位所需能力，建议通过实验巩固。"
    elif node_type == "certification":
        return f"{node_name} 是行业认证节点，通过该认证可显著提升求职竞争力。"
    elif node_type == "career_target":
        return f"{node_name} 是目标职业方向，了解该岗位要求有助于针对性学习。"
    else:
        career_map: dict[str, str] = {
            "kp_010": "路由选择协议是网络工程师和云工程师岗位的核心技能要求。",
            "kp_014": "TCP连接管理是后端开发和网络工程师面试的高频考点。",
            "kp_015": "TCP流量/拥塞控制是网络性能调优岗位的必备知识。",
            "kp_018": "HTTP/HTTPS是后端开发岗位的基础必备知识。",
            "kp_019": "网络安全基础是安全工程师岗位的核心要求。",
        }
        node_id = getattr(node, "id", "")
        return career_map.get(node_id, f"{node_name} 是计算机网络工程师必须掌握的基础知识点。")
