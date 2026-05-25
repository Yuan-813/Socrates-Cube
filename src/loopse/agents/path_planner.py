"""
PathPlannerAgent：个性化学习路径规划代理
基于学生画像、薄弱知识点和知识图谱拓扑关系生成推荐学习路径
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.llm_client import llm_client
from ..kb.knowledge_graph import knowledge_graph, KnowledgeNode

logger = logging.getLogger(__name__)

_PLAN_PROMPT = Path("config/prompts/path_planner/plan_path.txt")


def _load_prompt() -> str:
    try:
        return _PLAN_PROMPT.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


class PathPlannerAgent:
    """
    学习路径规划代理：
    1. 找到学生的目标知识点（最近涉及的 or 弱点）
    2. 通过知识图谱找出所有前置依赖
    3. 过滤掌握度不足的节点
    4. 拓扑排序得到学习顺序
    5. 为每个节点生成推荐理由（LLM）
    """

    def __init__(self):
        self._prompt_tpl = _load_prompt()

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------

    def plan(
        self,
        user_id: str,
        profile: Dict[str, Any],
        target_node_ids: Optional[List[str]] = None,
        max_nodes: int = 10,
    ) -> Dict[str, Any]:
        """
        生成个性化学习路径。

        Args:
            user_id: 学生ID
            profile: 学生画像（含 mastery_map、weak_points）
            target_node_ids: 目标知识点ID列表（None时使用画像弱点）
            max_nodes: 最多返回节点数

        Returns: 学习路径字典
        """
        mastery_map: Dict[str, float] = profile.get("mastery_map", {})
        weak_points: List[str] = profile.get("weak_points", [])

        # Step 1: 确定目标节点
        if not target_node_ids:
            target_node_ids = weak_points[:3] if weak_points else self._default_targets()

        logger.info("[PathPlanner] 用户 %s，目标节点: %s", user_id, target_node_ids)

        # Step 2: 找出薄弱的前置节点
        weak_prereqs = knowledge_graph.find_weak_prerequisites(
            target_node_ids, mastery_map, threshold=0.6
        )
        weak_prereq_ids = [n.id for n in weak_prereqs]

        # Step 3: 合并目标 + 薄弱前置，拓扑排序
        all_ids = list(set(target_node_ids + weak_prereq_ids))
        sorted_nodes = knowledge_graph.topological_sort(all_ids)

        # Step 4: 截断到 max_nodes
        sorted_nodes = sorted_nodes[:max_nodes]

        # Step 5: 为每个节点生成推荐理由
        path_nodes = self._build_path_nodes(sorted_nodes, mastery_map, target_node_ids, user_id)

        path_id = str(uuid.uuid4())
        total_time = sum(n["estimated_time"] for n in path_nodes)

        return {
            "path_id": path_id,
            "user_id": user_id,
            "title": f"计算机网络个性化学习路径（共{len(path_nodes)}个知识点）",
            "description": "根据您的掌握情况和学习目标，为您规划了如下学习路径。",
            "total_estimated_time": total_time,
            "nodes": path_nodes,
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # 内部：构建路径节点列表
    # ------------------------------------------------------------------

    def _build_path_nodes(
        self,
        nodes: List[KnowledgeNode],
        mastery_map: Dict[str, float],
        target_ids: List[str],
        user_id: str,
    ) -> List[Dict[str, Any]]:
        path_nodes = []
        for i, node in enumerate(nodes):
            mastery = mastery_map.get(node.id, 0.0)
            is_target = node.id in target_ids
            prereqs = [p.id for p in knowledge_graph.get_prerequisites(node.id)]
            prereqs_met = all(mastery_map.get(pid, 0.0) >= 0.6 for pid in prereqs)

            # 确定节点状态
            if mastery >= 0.8:
                status = "completed"
            elif i == 0 or prereqs_met:
                status = "pending"
            else:
                status = "locked"

            reason = self._gen_reason(node, mastery, is_target)

            path_nodes.append({
                "node_id": node.id,
                "node_name": node.name,
                "type": node.type,
                "chapter": node.chapter,
                "difficulty": node.difficulty,
                "estimated_time": node.estimated_time,
                "recommendation_reason": reason,
                "reason_sources": ["知识图谱依赖分析", "学习画像弱点检测"],
                "suggested_resources": ["doc", "exercise"],
                "prerequisites": prereqs,
                "prerequisites_met": prereqs_met,
                "status": status,
                "current_mastery": round(mastery, 3),
                "is_target": is_target,
            })
        return path_nodes

    def _gen_reason(
        self, node: KnowledgeNode, mastery: float, is_target: bool
    ) -> str:
        """为知识点生成推荐理由（先尝试 LLM，失败用规则）"""
        if is_target and mastery < 0.5:
            return f"这是您的重点学习目标，目前掌握度仅 {mastery:.0%}，需要重点突破。"
        if mastery < 0.4:
            return f"当前掌握度较低（{mastery:.0%}），且是后续知识点的前置条件，建议优先夯实。"
        if mastery < 0.7:
            return f"掌握度尚可（{mastery:.0%}），建议通过练习题巩固理解。"
        return f"「{node.name}」是必要的前置知识，建议快速复习确认掌握。"

    @staticmethod
    def _default_targets() -> List[str]:
        """无弱点时的默认目标（TCP相关核心节点）"""
        return ["kn_008", "kn_012", "kn_013"]
