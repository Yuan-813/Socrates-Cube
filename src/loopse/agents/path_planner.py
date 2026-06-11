"""Explainable learning-path planning agent."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from ..kb.knowledge_graph import KnowledgeNode, knowledge_graph
from .cognitive_engine import CognitiveAgentMixin


class PathPlannerAgent(CognitiveAgentMixin):
    """Plans learning order from graph prerequisites and student mastery."""

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
        trace.add_step("target_selection", str(target_node_ids or weak_points), str(targets), 0.82)

        weak_prereqs = knowledge_graph.find_weak_prerequisites(targets, mastery_map, threshold=0.65)
        all_ids = list(dict.fromkeys([*(node.id for node in weak_prereqs), *targets]))
        sorted_nodes = knowledge_graph.topological_sort(all_ids)[:max_nodes]
        trace.add_step("graph_ordering", f"candidates={all_ids}", f"ordered={[n.id for n in sorted_nodes]}", 0.86)

        path_nodes = self._build_path_nodes(sorted_nodes, mastery_map, targets)
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
            "generated_at": datetime.utcnow().isoformat(),
            "agent_trace": trace.to_dict(),
            "quality_score": round(reflection["confidence"], 3),
        }

    def _build_path_nodes(
        self,
        nodes: list[KnowledgeNode],
        mastery_map: dict[str, float],
        target_ids: list[str],
    ) -> list[dict[str, Any]]:
        result = []
        completed = set()
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
                    "reason_sources": ["知识图谱前置依赖", "学生画像掌握度", "薄弱点优先级"],
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
    def _default_targets() -> list[str]:
        return ["kn_005", "kn_007", "kn_008"]
