"""
Path Planner Agent — 可解释学习路径规划
算法：拓扑排序 + 薄弱点优先 + LLM辅助生成推荐理由
"""
import json
import uuid
from datetime import datetime
from typing import List, Optional

from src.loopse.kb.knowledge_graph import knowledge_graph, KnowledgeGraph
from src.loopse.core.llm_client import llm_client
from pathlib import Path


PLAN_PROMPT = Path("config/prompts/path_planner/plan_path.txt").read_text(encoding="utf-8") \
    if Path("config/prompts/path_planner/plan_path.txt").exists() else ""


class PathPlannerAgent:

    def __init__(self, kg: KnowledgeGraph = None):
        self.kg = kg or knowledge_graph

    def plan(
        self,
        user_id: str,
        profile: dict,
        target_topic: str = "TCP/IP协议",
        diagnosis_result: Optional[dict] = None,
        max_nodes: int = 6,
    ) -> dict:
        # Step 1：确定目标节点
        target_nodes = self._find_target_nodes(target_topic, diagnosis_result)

        # Step 2：收集前置薄弱点
        weak_nodes = []
        seen = set()
        for tnid in target_nodes:
            for wn in self.kg.find_weak_prerequisites(tnid, profile, threshold=0.6):
                if wn["node_id"] not in seen:
                    weak_nodes.append(wn)
                    seen.add(wn["node_id"])

        # 合并目标节点自身（如果画像也未达标）
        for tnid in target_nodes:
            node = self.kg.get_node(tnid)
            if node and tnid not in seen:
                mastery = self.kg._estimate_mastery(tnid, profile)
                if mastery < 0.7:
                    weak_nodes.append({
                        "node_id": tnid,
                        "node_name": node["name"],
                        "chapter": node.get("chapter", ""),
                        "mastery": mastery,
                        "estimated_time": node.get("estimated_time", 45),
                    })
                    seen.add(tnid)

        if not weak_nodes:
            return self._plan_advanced(user_id, profile, target_nodes)

        # Step 3：拓扑排序
        all_node_ids = [n["node_id"] for n in weak_nodes]
        sorted_ids = self.kg.topological_sort(all_node_ids)
        remaining = [nid for nid in all_node_ids if nid not in sorted_ids]
        sorted_ids = sorted_ids + remaining

        # Step 4：限制节点数量
        final_ids = sorted_ids[:max_nodes]

        # Step 5：生成路径节点
        path_nodes = []
        for nid in final_ids:
            node = self.kg.get_node(nid)
            if not node:
                continue
            wn_data = next((w for w in weak_nodes if w["node_id"] == nid), {})
            reason = self._generate_reason(nid, node, wn_data, profile, diagnosis_result)
            prerequisites_met = all(
                self.kg._estimate_mastery(pre, profile) >= 0.5
                for pre in self.kg.get_prerequisites(nid)
            )
            path_nodes.append({
                "node_id": nid,
                "node_name": node["name"],
                "type": "learning",
                "chapter": node.get("chapter", ""),
                "estimated_time": node.get("estimated_time", 30),
                "recommendation_reason": reason,
                "reason_sources": ["画像维度证据", "知识图谱前置依赖"],
                "suggested_resources": ["doc", "exercise"],
                "prerequisites": self.kg.get_prerequisites(nid),
                "prerequisites_met": prerequisites_met,
                "status": "pending" if prerequisites_met else "locked",
                "current_mastery": wn_data.get("mastery", 0.0),
            })

        return {
            "path_id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": f"针对「{target_topic}」的个性化学习路径",
            "description": f"根据你的画像，检测到{len(weak_nodes)}个薄弱前置知识点，以下路径将帮助你系统补强。",
            "total_estimated_time": sum(n["estimated_time"] for n in path_nodes),
            "nodes": path_nodes,
            "generated_at": datetime.now().isoformat(),
        }

    def _find_target_nodes(self, topic: str, diagnosis_result: Optional[dict]) -> List[str]:
        target_ids = []
        if diagnosis_result and not diagnosis_result.get("is_correct", True):
            for rc in diagnosis_result.get("root_causes", []):
                if rc.get("knowledge_node_id"):
                    target_ids.append(rc["knowledge_node_id"])
        if not target_ids:
            matches = self.kg.search_by_keyword(topic)
            if not matches:
                for word in topic.split():
                    matches.extend(self.kg.search_by_keyword(word))
            target_ids = [m["id"] for m in matches[:3]]
        if not target_ids:
            target_ids = ["kn_008"]
        return list(set(target_ids))

    def _generate_reason(self, node_id: str, node: dict, wn_data: dict,
                         profile: dict, diagnosis_result: Optional[dict]) -> str:
        mastery = wn_data.get("mastery", 0.0)
        mastery_desc = "掌握度极低" if mastery < 0.3 else ("掌握度偏低" if mastery < 0.6 else "需要巩固")
        node_name = node["name"]

        if diagnosis_result and not diagnosis_result.get("is_correct", True):
            error_desc = diagnosis_result.get("surface_error", {}).get("error_description", "")
            if error_desc:
                return f"诊断发现你对「{node_name}」的理解存在偏差（{error_desc[:30]}），建议优先补强此前置知识。"

        return (
            f"根据你的学习画像，「{node_name}」当前{mastery_desc}（评分 {mastery:.1f}/1.0）。"
            f"这是后续学习「{node['chapter']}」核心内容的必要前置知识，建议优先掌握。"
        )

    def _plan_advanced(self, user_id: str, profile: dict, target_nodes: List[str]) -> dict:
        advanced_map = {
            "kn_008": ["kn_009", "kn_010"],
            "kn_006": ["kn_011", "kn_012"],
            "kn_013": ["kn_014", "kn_015"],
        }
        next_nodes = []
        for tnid in target_nodes:
            next_nodes.extend(advanced_map.get(tnid, []))
        next_nodes = next_nodes[:4] if next_nodes else ["kn_012", "kn_014"]

        path_nodes = []
        for nid in next_nodes:
            node = self.kg.get_node(nid)
            if node:
                path_nodes.append({
                    "node_id": nid,
                    "node_name": node["name"],
                    "type": "learning",
                    "chapter": node.get("chapter", ""),
                    "estimated_time": node.get("estimated_time", 45),
                    "recommendation_reason": f"你已掌握前置知识，「{node['name']}」是下一个自然进阶方向。",
                    "reason_sources": ["知识图谱进阶路径"],
                    "suggested_resources": ["doc", "exercise"],
                    "prerequisites": self.kg.get_prerequisites(nid),
                    "prerequisites_met": True,
                    "status": "pending",
                    "current_mastery": 0.0,
                })

        return {
            "path_id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": "进阶学习路径",
            "description": "当前知识点掌握良好，以下是推荐的进阶方向。",
            "total_estimated_time": sum(n["estimated_time"] for n in path_nodes),
            "nodes": path_nodes,
            "generated_at": datetime.now().isoformat(),
        }


path_planner = PathPlannerAgent()
