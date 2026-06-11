"""Knowledge graph loading, dependency analysis and fuzzy search."""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)
_DEFAULT_GRAPH_PATH = Path("data/knowledge_graph.json")


class KnowledgeNode:
    def __init__(self, data: dict):
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.chapter: str = data.get("chapter", "unknown")
        self.type: str = data.get("type", "concept")
        self.difficulty: int = int(data.get("difficulty", 1))
        self.estimated_time: int = int(data.get("estimated_time", 30))
        self.keywords: list[str] = data.get("keywords", [])
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
    def __init__(self, graph_path: Path = _DEFAULT_GRAPH_PATH):
        self._nodes: dict[str, KnowledgeNode] = {}
        self._successors: dict[str, set[str]] = {}
        self._predecessors: dict[str, set[str]] = {}
        self._load(graph_path)

    def _load(self, path: Path) -> None:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            logger.warning("knowledge graph not found: %s", path)
            return
        except json.JSONDecodeError as exc:
            logger.error("knowledge graph JSON invalid: %s", exc)
            return

        for item in raw.get("nodes", []):
            node = KnowledgeNode(item)
            self._nodes[node.id] = node
            self._successors.setdefault(node.id, set())
            self._predecessors.setdefault(node.id, set())

        for edge in raw.get("edges", []):
            src = edge.get("from")
            dst = edge.get("to")
            if src in self._nodes and dst in self._nodes:
                self._successors.setdefault(src, set()).add(dst)
                self._predecessors.setdefault(dst, set()).add(src)

        logger.info(
            "knowledge graph loaded: %d nodes, %d edges",
            len(self._nodes),
            sum(len(items) for items in self._successors.values()),
        )

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        return self._nodes.get(node_id)

    def get_all_nodes(self) -> list[KnowledgeNode]:
        return list(self._nodes.values())

    def get_prerequisites(self, node_id: str) -> list[KnowledgeNode]:
        return [self._nodes[nid] for nid in self._predecessors.get(node_id, set()) if nid in self._nodes]

    def get_all_prerequisites(self, node_id: str) -> list[KnowledgeNode]:
        visited: set[str] = set()
        result: list[KnowledgeNode] = []

        def dfs(nid: str) -> None:
            for pred_id in self._predecessors.get(nid, set()):
                if pred_id in visited:
                    continue
                visited.add(pred_id)
                node = self._nodes.get(pred_id)
                if node:
                    result.append(node)
                dfs(pred_id)

        dfs(node_id)
        return result

    def topological_sort(self, node_ids: Optional[list[str]] = None) -> list[KnowledgeNode]:
        target_ids = set(self._nodes.keys()) if node_ids is None else {nid for nid in node_ids if nid in self._nodes}
        in_degree = {nid: 0 for nid in target_ids}
        for nid in target_ids:
            for pred in self._predecessors.get(nid, set()):
                if pred in target_ids:
                    in_degree[nid] += 1

        queue = sorted(
            [nid for nid, degree in in_degree.items() if degree == 0],
            key=lambda nid: (self._nodes[nid].chapter, self._nodes[nid].difficulty, nid),
        )
        sorted_nodes: list[KnowledgeNode] = []
        while queue:
            current = queue.pop(0)
            sorted_nodes.append(self._nodes[current])
            for succ in self._successors.get(current, set()):
                if succ not in in_degree:
                    continue
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    queue.append(succ)
            queue.sort(key=lambda nid: (self._nodes[nid].chapter, self._nodes[nid].difficulty, nid))
        return sorted_nodes

    def find_weak_prerequisites(
        self,
        target_node_ids: list[str],
        mastery_map: dict[str, float],
        threshold: float = 0.6,
    ) -> list[KnowledgeNode]:
        prereq_ids: set[str] = set()
        for node_id in target_node_ids:
            for prereq in self.get_all_prerequisites(node_id):
                prereq_ids.add(prereq.id)
        weak = []
        for node_id in prereq_ids:
            if self.estimate_mastery(node_id, mastery_map) < threshold:
                node = self._nodes.get(node_id)
                if node:
                    weak.append(node)
        return weak

    def search_by_keyword(self, keyword: str) -> list[KnowledgeNode]:
        tokens = self._tokenize(keyword)
        if not tokens:
            return []
        scored: list[tuple[int, KnowledgeNode]] = []
        for node in self._nodes.values():
            name = node.name.lower()
            haystack = " ".join([node.name, node.description, *node.keywords]).lower()
            score = 0
            for token in tokens:
                if token in name:
                    score += 4
                elif token in haystack:
                    score += 1
            if score:
                scored.append((score, node))
        scored.sort(key=lambda item: (-item[0], item[1].difficulty, item[1].id))
        return [node for _, node in scored]

    def estimate_mastery(self, node_id: str, mastery_map: Dict[str, float]) -> float:
        direct = mastery_map.get(node_id)
        prereqs = self.get_prerequisites(node_id)
        if direct is not None:
            if not prereqs:
                return round(float(direct), 3)
            prereq_avg = sum(float(mastery_map.get(p.id, 0.35)) for p in prereqs) / len(prereqs)
            return round(0.75 * float(direct) + 0.25 * prereq_avg, 3)
        if not prereqs:
            return 0.35
        return round(sum(float(mastery_map.get(p.id, 0.35)) for p in prereqs) / len(prereqs) * 0.85, 3)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        text = text.lower()
        latin = re.findall(r"[a-z0-9][a-z0-9_\-./]{1,}", text)
        known_terms = [
            "三次握手",
            "四次挥手",
            "滑动窗口",
            "拥塞控制",
            "流量控制",
            "子网",
            "路由",
            "交换",
            "可靠传输",
            "dns",
            "http",
            "tcp",
            "udp",
            "ip",
            "tls",
            "quic",
        ]
        terms = [term for term in known_terms if term in text]
        cjk = re.findall(r"[\u4e00-\u9fff]{2,}", text)
        return list(dict.fromkeys(latin + terms + cjk))


knowledge_graph = KnowledgeGraph()
