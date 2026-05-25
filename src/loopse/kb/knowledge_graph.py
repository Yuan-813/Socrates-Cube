"""
知识图谱加载与检索模块
负责从 JSON 文件中加载知识节点、边关系，并提供拓扑排序、依赖分析等功能
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

_DEFAULT_GRAPH_PATH = Path("data/knowledge_graph.json")


class KnowledgeNode:
    """单个知识点节点"""

    def __init__(self, data: dict):
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.chapter: str = data["chapter"]
        self.type: str = data["type"]
        self.difficulty: int = data.get("difficulty", 1)
        self.estimated_time: int = data.get("estimated_time", 30)
        self.keywords: List[str] = data.get("keywords", [])
        self.description: str = data.get("description", "")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "chapter": self.chapter,
            "type": self.type,
            "difficulty": self.difficulty,
            "estimated_time": self.estimated_time,
            "keywords": self.keywords,
            "description": self.description,
        }


class KnowledgeGraph:
    """
    知识图谱：管理知识点节点、有向依赖边，提供拓扑排序与前置分析。
    """

    def __init__(self, graph_path: Path = _DEFAULT_GRAPH_PATH):
        self._nodes: Dict[str, KnowledgeNode] = {}
        # edges[a] = {b, ...} 表示 b 是 a 的后继（a 是 b 的前置条件）
        self._successors: Dict[str, Set[str]] = {}
        # predecessors[b] = {a, ...} 表示 a 是 b 的前置条件
        self._predecessors: Dict[str, Set[str]] = {}
        self._load(graph_path)

    def _load(self, path: Path) -> None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except FileNotFoundError:
            logger.warning("knowledge_graph.json not found at %s, graph is empty", path)
            return

        for nd in raw.get("nodes", []):
            node = KnowledgeNode(nd)
            self._nodes[node.id] = node
            self._successors[node.id] = set()
            self._predecessors[node.id] = set()

        for edge in raw.get("edges", []):
            src, dst = edge["from"], edge["to"]
            if src in self._nodes and dst in self._nodes:
                self._successors.setdefault(src, set()).add(dst)
                self._predecessors.setdefault(dst, set()).add(src)

        logger.info("知识图谱加载完成：%d 个节点，%d 条边",
                    len(self._nodes),
                    sum(len(v) for v in self._successors.values()))

    # ------------------------------------------------------------------
    # 基础访问
    # ------------------------------------------------------------------

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        return self._nodes.get(node_id)

    def get_all_nodes(self) -> List[KnowledgeNode]:
        return list(self._nodes.values())

    def get_prerequisites(self, node_id: str) -> List[KnowledgeNode]:
        """直接前置节点（一跳）"""
        return [self._nodes[nid] for nid in self._predecessors.get(node_id, set())
                if nid in self._nodes]

    # ------------------------------------------------------------------
    # 深度递归：全量前置依赖
    # ------------------------------------------------------------------

    def get_all_prerequisites(self, node_id: str) -> List[KnowledgeNode]:
        """DFS 获取指定节点的所有前置节点（传递闭包，不含自身）"""
        visited: Set[str] = set()
        result: List[KnowledgeNode] = []

        def _dfs(nid: str):
            for pred_id in self._predecessors.get(nid, set()):
                if pred_id not in visited:
                    visited.add(pred_id)
                    if pred_id in self._nodes:
                        result.append(self._nodes[pred_id])
                    _dfs(pred_id)

        _dfs(node_id)
        return result

    # ------------------------------------------------------------------
    # 拓扑排序（Kahn 算法）
    # ------------------------------------------------------------------

    def topological_sort(self, node_ids: Optional[List[str]] = None) -> List[KnowledgeNode]:
        """
        对给定节点子集做拓扑排序（学习顺序）。
        若 node_ids 为 None，则对全图做排序。
        """
        if node_ids is None:
            target_ids = set(self._nodes.keys())
        else:
            target_ids = set(node_ids)

        # 计算子图内的入度
        in_degree: Dict[str, int] = {nid: 0 for nid in target_ids}
        for nid in target_ids:
            for pred in self._predecessors.get(nid, set()):
                if pred in target_ids:
                    in_degree[nid] += 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        queue.sort(key=lambda x: (self._nodes[x].chapter, self._nodes[x].difficulty))
        sorted_nodes: List[KnowledgeNode] = []

        while queue:
            cur = queue.pop(0)
            if cur in self._nodes:
                sorted_nodes.append(self._nodes[cur])
            for succ in self._successors.get(cur, set()):
                if succ in in_degree:
                    in_degree[succ] -= 1
                    if in_degree[succ] == 0:
                        queue.append(succ)
            queue.sort(key=lambda x: (self._nodes[x].chapter, self._nodes[x].difficulty))

        return sorted_nodes

    # ------------------------------------------------------------------
    # 找到掌握度不足的前置节点
    # ------------------------------------------------------------------

    def find_weak_prerequisites(
        self,
        target_node_ids: List[str],
        mastery_map: Dict[str, float],
        threshold: float = 0.6,
    ) -> List[KnowledgeNode]:
        """
        对目标节点集合的所有前置依赖，过滤出掌握度低于阈值的节点。
        mastery_map: {node_id: 0.0~1.0}
        """
        all_prereqs: Set[str] = set()
        for nid in target_node_ids:
            for prereq in self.get_all_prerequisites(nid):
                all_prereqs.add(prereq.id)
            all_prereqs.discard(nid)

        weak = []
        for nid in all_prereqs:
            mastery = mastery_map.get(nid, 0.0)
            if mastery < threshold:
                node = self._nodes.get(nid)
                if node:
                    weak.append(node)
        return weak

    # ------------------------------------------------------------------
    # 关键词搜索
    # ------------------------------------------------------------------

    def search_by_keyword(self, keyword: str) -> List[KnowledgeNode]:
        """模糊匹配关键词，返回相关节点列表"""
        kw_lower = keyword.lower()
        result = []
        for node in self._nodes.values():
            if (kw_lower in node.name.lower()
                    or kw_lower in node.description.lower()
                    or any(kw_lower in k.lower() for k in node.keywords)):
                result.append(node)
        return result


# 全局单例
knowledge_graph = KnowledgeGraph()
