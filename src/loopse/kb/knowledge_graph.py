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
        self.name: str = data.get("name") or data.get("title", data["id"])
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
            src = edge.get("from") or edge.get("source")
            dst = edge.get("to") or edge.get("target")
            if src in self._nodes and dst in self._nodes:
                self._successors.setdefault(src, set()).add(dst)
                self._predecessors.setdefault(dst, set()).add(src)

        # 加载认知层节点（ACU）
        for item in raw.get("cognitive_nodes", []):
            parent_id = item.get("parent_curriculum_node", "")
            parent_node = self._nodes.get(parent_id)
            node_data = {
                "id": item["id"],
                "name": item.get("label", item.get("name", item["id"])),
                "chapter": parent_node.chapter if parent_node else "unknown",
                "type": "cognitive_unit",
                "difficulty": parent_node.difficulty if parent_node else 2,
                "estimated_time": 15,
                "keywords": [],
                "description": item.get("label", ""),
            }
            node = KnowledgeNode(node_data)
            self._nodes[node.id] = node
            self._successors.setdefault(node.id, set())
            self._predecessors.setdefault(node.id, set())

        # 加载认知层边（仅 prerequisite 类型参与图算法）
        for edge in raw.get("cognitive_edges", []):
            if edge.get("type") != "prerequisite":
                continue
            src = edge.get("source")
            dst = edge.get("target")
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

    def get_downstream_nodes(self, node_id: str) -> list[KnowledgeNode]:
        visited: set[str] = set()
        result: list[KnowledgeNode] = []

        def dfs(nid: str) -> None:
            for succ_id in self._successors.get(nid, set()):
                if succ_id in visited:
                    continue
                visited.add(succ_id)
                node = self._nodes.get(succ_id)
                if node:
                    result.append(node)
                dfs(succ_id)

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

    def _estimate_mastery(self, node_id: str, profile: dict) -> float:
        """C-role 版本兼容接口：从 profile 字典中提取 mastery_map 后估计掌握度。"""
        mastery_map = profile.get("mastery_map", {}) if isinstance(profile, dict) else {}
        return self.estimate_mastery(node_id, mastery_map)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        text = text.lower()
        latin = re.findall(r"[a-z0-9][a-z0-9_\-./]{1,}", text)
        known_terms = [
            # TCP/IP 核心协议
            "三次握手", "四次挥手", "滑动窗口", "拥塞控制", "流量控制",
            "子网", "路由", "交换", "可靠传输",
            # 应用层协议
            "dns", "http", "https", "ftp", "smtp", "imap", "pop3",
            "websocket", "grpc", "rest", "graphql",
            # 传输层
            "tcp", "udp", "quic", "sctp",
            "syn", "ack", "fin", "rst", "psh", "urg",
            "拥塞窗口", "接收窗口", "cwnd", "rwnd",
            "nagle", "超时重传", "rtt", "快起动",
            # 网络层
            "ip", "ipv4", "ipv6", "icmp", "icmpv6", "arp", "rarp",
            "nat", "pat", "cidr", "子网掩码", "默认网关",
            "ospf", "bgp", "rip", "eigrp", "is-is",
            "路由表", "路由协议", "跳数", "ttl",
            "vlan", "trunk", "access", "stp", "rstp", "lacp",
            # 安全协议
            "tls", "ssl", "https", "ssh", "ipsec", "vpn",
            "acl", "dpi", "ids", "ips", "ddos", "syn洪泛",
            "证书", "ca", "pki", "x.509",
            # 数据链路层
            "mac", "ethernet", "802.1q", "802.3", "802.11",
            "wi-fi", "wifi", "帧", "广播", "单播", "多播",
            "poe", "sfp", "光纤",
            # 物理层
            "调制", "信道编码", "复用", "ofdm", "mimo",
            "带宽", "延迟", "局域网", "域网",
            # 网络工程实战
            "抓包", "wireshark", "tcpdump", "ping", "traceroute",
            "nmap", "netstat", "防火墙", "sdn", "nfv", "openflow",
        ]
        terms = [term for term in known_terms if term in text]
        cjk = re.findall(r"[\u4e00-\u9fff]{2,}", text)
        return list(dict.fromkeys(latin + terms + cjk))


knowledge_graph = KnowledgeGraph()
