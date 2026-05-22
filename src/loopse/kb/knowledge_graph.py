"""
JSON知识图谱管理，基于A设计的data/knowledge_graph.json
Phase 3：只实现路径规划需要的核心方法
"""
import json
from pathlib import Path
from typing import List, Dict, Optional


class KnowledgeGraph:
    def __init__(self, graph_path: str = "data/knowledge_graph.json"):
        self.graph_path = Path(graph_path)
        self.nodes: Dict[str, dict] = {}
        self.edges: List[dict] = []
        self.adj: Dict[str, List[str]] = {}
        self.rev_adj: Dict[str, List[str]] = {}
        self._load()

    def _load(self):
        if not self.graph_path.exists():
            print(f"⚠️  知识图谱文件不存在：{self.graph_path}，使用空图谱")
            return
        data = json.loads(self.graph_path.read_text(encoding="utf-8-sig"))
        self.nodes = {n["id"]: n for n in data.get("nodes", [])}
        self.edges = data.get("edges", [])
        for e in self.edges:
            self.adj.setdefault(e["from"], []).append(e["to"])
            self.rev_adj.setdefault(e["to"], []).append(e["from"])

    def get_node(self, node_id: str) -> Optional[dict]:
        return self.nodes.get(node_id)

    def get_prerequisites(self, node_id: str) -> List[str]:
        return self.rev_adj.get(node_id, [])

    def get_all_prerequisites(self, node_id: str) -> List[str]:
        visited, result = set(), []
        def dfs(nid):
            for pre in self.rev_adj.get(nid, []):
                if pre not in visited:
                    visited.add(pre)
                    dfs(pre)
                    result.append(pre)
        dfs(node_id)
        return result

    def topological_sort(self, node_ids: List[str]) -> List[str]:
        node_set = set(node_ids)
        in_degree = {n: 0 for n in node_ids}
        for e in self.edges:
            if e["from"] in node_set and e["to"] in node_set:
                in_degree[e["to"]] += 1
        queue = [n for n, d in in_degree.items() if d == 0]
        result = []
        while queue:
            node = queue.pop(0)
            result.append(node)
            for succ in self.adj.get(node, []):
                if succ in in_degree:
                    in_degree[succ] -= 1
                    if in_degree[succ] == 0:
                        queue.append(succ)
        return result

    def find_weak_prerequisites(
        self, target_node_id: str, profile: dict, threshold: float = 0.6,
    ) -> List[dict]:
        all_pres = self.get_all_prerequisites(target_node_id)
        weak = []
        for nid in all_pres:
            node = self.nodes.get(nid)
            if not node:
                continue
            mastery = self._estimate_mastery(nid, profile)
            if mastery < threshold:
                weak.append({
                    "node_id": nid,
                    "node_name": node["name"],
                    "chapter": node.get("chapter", ""),
                    "mastery": mastery,
                    "estimated_time": node.get("estimated_time", 30),
                })
        return weak

    def _estimate_mastery(self, node_id: str, profile: dict) -> float:
        node = self.nodes.get(node_id, {})
        chapter = node.get("chapter", "")
        dim_map = {
            "第1章": "network_layer_cognition",
            "第3章": "hands_on_ability",
            "第4章": "protocol_relationship",
            "第5章": "protocol_flow_memory",
            "第6章": "protocol_relationship",
        }
        dim = dim_map.get(chapter, "network_layer_cognition")
        raw = profile.get(dim)
        if raw is None:
            return 0.2
        if isinstance(raw, (int, float)) and raw > 1:
            return min(raw / 5.0, 1.0)
        return float(raw) if raw else 0.2

    def get_chapter_nodes(self, chapter: str) -> List[dict]:
        return [n for n in self.nodes.values() if n.get("chapter") == chapter]

    def search_by_keyword(self, keyword: str) -> List[dict]:
        return [
            n for n in self.nodes.values()
            if keyword in n.get("keywords", []) or keyword in n.get("name", "")
        ]


knowledge_graph = KnowledgeGraph()
