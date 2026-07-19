"""
Mock Provider -- offline mode fallback data for all agents.
When no API key or --mock-mode is set, provides 3 profiles, 3 diagnoses,
5 resource types, and learning path data for full demo chain.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any, AsyncIterator
import asyncio

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mock profiles (3 sets)
# ---------------------------------------------------------------------------
MOCK_PROFILES: list[dict[str, Any]] = [
    {
        "user_id": "mock-student-001", "name": "初学者-小王",
        "conceptual_understanding": 0.35, "protocol_analysis": 0.30,
        "calculation_ability": 0.25, "error_diagnosis": 0.30,
        "system_design": 0.20, "knowledge_connection": 0.25,
        "expression_clarity": 0.40, "self_correction": 0.35,
        "mastery_map": {"kp_001": 0.4, "kp_002": 0.3, "kp_005": 0.2},
        "weak_points": ["kp_005", "kp_007", "kp_013"],
        "strong_points": ["kp_001"], "turn_count": 0,
    },
    {
        "user_id": "mock-student-002", "name": "进阶-小李",
        "conceptual_understanding": 0.65, "protocol_analysis": 0.60,
        "calculation_ability": 0.55, "error_diagnosis": 0.50,
        "system_design": 0.45, "knowledge_connection": 0.60,
        "expression_clarity": 0.70, "self_correction": 0.55,
        "mastery_map": {"kp_001": 0.8, "kp_005": 0.7, "kp_007": 0.6, "kp_013": 0.5},
        "weak_points": ["kp_013", "kp_014", "kp_015"],
        "strong_points": ["kp_001", "kp_005"], "turn_count": 5,
    },
    {
        "user_id": "mock-student-003", "name": "高手-小张",
        "conceptual_understanding": 0.85, "protocol_analysis": 0.80,
        "calculation_ability": 0.75, "error_diagnosis": 0.80,
        "system_design": 0.70, "knowledge_connection": 0.85,
        "expression_clarity": 0.90, "self_correction": 0.80,
        "mastery_map": {"kp_001": 0.9, "kp_005": 0.85, "kp_013": 0.8, "kp_014": 0.75, "kp_015": 0.7},
        "weak_points": ["kp_015"],
        "strong_points": ["kp_001", "kp_005", "kp_013"], "turn_count": 12,
    },
]

# ---------------------------------------------------------------------------
# Mock diagnoses (3 sets)
# ---------------------------------------------------------------------------
MOCK_DIAGNOSES: list[dict[str, Any]] = [
    {
        "is_correct": False, "confidence": 0.88,
        "surface_error": "把 TCP 三次握手误认为两次握手",
        "error_type": "flow_omission",
        "root_causes": ["协议流程记忆不完整", "未理解第三次 ACK 防止历史连接的作用"],
        "missing_prerequisites": ["kp_014"],
        "pattern": "流程遗漏型",
        "intervention_suggestion": "用失效连接请求的反例追问第三次 ACK 的必要性。",
        "related_node_ids": ["kp_014", "kp_013"],
    },
    {
        "is_correct": False, "confidence": 0.82,
        "surface_error": "混淆流量控制和拥塞控制的作用对象",
        "error_type": "concept_confusion",
        "root_causes": ["两种机制都调节发送速率导致混淆", "未区分 rwnd 和 cwnd"],
        "missing_prerequisites": ["kp_015"],
        "pattern": "概念混淆型",
        "intervention_suggestion": "通过对比表格区分流量控制与拥塞控制。",
        "related_node_ids": ["kp_015"],
    },
    {
        "is_correct": False, "confidence": 0.75,
        "surface_error": "认为 HTTP 可以直接运行在 IP 上",
        "error_type": "layer_misplacement",
        "root_causes": ["对协议分层模型缺乏清晰认识"],
        "missing_prerequisites": ["kp_003", "kp_018"],
        "pattern": "层级错位型",
        "intervention_suggestion": "用分层封装动画演示 HTTP->TCP->IP 依赖关系。",
        "related_node_ids": ["kp_003", "kp_018"],
    },
]

# ---------------------------------------------------------------------------
# Mock resources (5 types)
# ---------------------------------------------------------------------------
MOCK_RESOURCES: dict[str, list[dict[str, Any]]] = {
    "doc": [{
        "resource_type": "doc",
        "title": "TCP 三次握手详解",
        "content": "# TCP 三次握手详解\n\n## 概述\nTCP 三次握手是建立可靠连接的核心机制。\n\n## 三次过程\n1. **SYN**: 客户端发送同步报文(seq=x)\n2. **SYN-ACK**: 服务端确认并同步(seq=y, ack=x+1)\n3. **ACK**: 客户端最终确认(ack=y+1)\n\n## 小结\n三次握手确保双方初始序列号同步，防止历史连接干扰。",
        "metadata": {"difficulty": 3, "knowledge_point": "TCP 三次握手"},
    }],
    "exercise": [{
        "resource_type": "exercise",
        "title": "TCP 连接管理练习",
        "content": "判断题：TCP 两次握手即可避免历史连接请求造成的半开连接。\n选项：A.正确 B.错误\n答案：B\n解析：第三次 ACK 用于确认客户端收到 SYN-ACK。",
        "metadata": {"difficulty": 3, "knowledge_point": "TCP 三次握手"},
    }],
    "code": [{
        "resource_type": "code",
        "title": "TCP 报文构造示例",
        "content": "# Python 构造 TCP SYN 报文头部(伪代码)\nimport struct\ndef build_syn(src_port, dst_port, seq):\n    flags = 0x02  # SYN\n    header = struct.pack('!HHIIBBHHH',\n        src_port, dst_port, seq, 0,\n        5 << 4, flags, 65535, 0, 0)\n    return header\n# expected_output: 20 bytes TCP header, SYN=1",
        "metadata": {"difficulty": 4, "knowledge_point": "TCP 报文格式"},
    }],
    "mindmap": [{
        "resource_type": "mindmap",
        "title": "TCP 协议知识图谱",
        "content": json.dumps({
            "root": "TCP 协议",
            "children": [
                {"name": "连接管理", "children": [
                    {"name": "三次握手"}, {"name": "四次挥手"}
                ]},
                {"name": "可靠传输", "children": [
                    {"name": "序列号"}, {"name": "确认应答"}, {"name": "超时重传"}
                ]},
                {"name": "拥塞控制", "children": [
                    {"name": "慢启动"}, {"name": "拥塞避免"},
                    {"name": "快重传", "error_branch": "学生常混淆快重传触发条件"},
                    {"name": "快恢复"},
                ]},
            ],
        }, ensure_ascii=False),
        "metadata": {"difficulty": 3, "knowledge_point": "TCP 协议"},
    }],
    "script": [{
        "resource_type": "script",
        "title": "TCP 三次握手讲解脚本",
        "content": "[00:00] 同学们好！今天讲 TCP 三次握手。\n[00:10] 想象打电话：先拨号(SYN)，朋友说你好(SYN-ACK)，你说听到了(ACK)。\n[00:30] 为什么要第三次确认？如果只两次会怎样？\n[00:40] 答案是旧信号可能延迟到达，导致错误连接被建立！",
        "metadata": {"difficulty": 2, "knowledge_point": "TCP 三次握手", "duration_seconds": 60},
    }],
}

# ---------------------------------------------------------------------------
# Mock learning path (with 3D reasons)
# ---------------------------------------------------------------------------
MOCK_LEARNING_PATH: dict[str, Any] = {
    "path_id": str(uuid.uuid4()),
    "title": "计算机网络个性化学习路径（6 个节点）",
    "description": "根据当前画像、薄弱点和知识图谱前置依赖生成。",
    "total_estimated_time": 280,
    "nodes": [
        {
            "node_id": "kp_005", "node_name": "数据链路层基本概念", "type": "concept",
            "chapter": "第3章", "difficulty": 2, "estimated_time": 35,
            "recommendation_reason": "数据链路层是当前最薄弱的前置基础，需优先补齐。",
            "reason_sources": {
                "graph_dependency": "kp_005 是 kp_006/kp_007 的前置节点",
                "diagnosis_result": "诊断显示数据链路层概念混淆率达 70%",
                "cognitive_style": "概念理解维度偏低(0.35)，适合先从基础概念入手",
            },
            "status": "in_progress", "current_mastery": 0.2, "is_target": True,
        },
        {
            "node_id": "kp_007", "node_name": "网络层基本概念", "type": "concept",
            "chapter": "第4章", "difficulty": 2, "estimated_time": 30,
            "recommendation_reason": "网络层是后续 IP/路由学习的基础。",
            "reason_sources": {
                "graph_dependency": "kp_007 是 kp_008/kp_009/kp_010 的前置",
                "diagnosis_result": "网络层 IP 分片概念存在层级错位误解",
                "cognitive_style": "协议分析维度偏低(0.30)，需强化分层思维",
            },
            "status": "pending", "current_mastery": 0.3, "is_target": True,
        },
        {
            "node_id": "kp_013", "node_name": "TCP协议基础", "type": "protocol",
            "chapter": "第5章", "difficulty": 3, "estimated_time": 55,
            "recommendation_reason": "TCP 是传输层核心协议，连接管理和可靠传输是后续重点。",
            "reason_sources": {
                "graph_dependency": "kp_013 是 kp_014/kp_015 的直接前置",
                "diagnosis_result": "TCP 可靠传输的序列号和重传理解有误",
                "cognitive_style": "计算能力维度 0.25，需加强协议基础",
            },
            "status": "pending", "current_mastery": 0.4, "is_target": True,
        },
        {
            "node_id": "kp_014", "node_name": "TCP三次握手与四次挥手", "type": "protocol",
            "chapter": "第5章", "difficulty": 3, "estimated_time": 60,
            "recommendation_reason": "TCP 握手是连接管理入门，诊断显示流程记忆不完整。",
            "reason_sources": {
                "graph_dependency": "kp_014 是 kp_015 的前置节点",
                "diagnosis_result": "握手流程第三次 ACK 作用理解不足",
                "cognitive_style": "学生倾向细节记忆，适合流程图辅助",
            },
            "status": "pending", "current_mastery": 0.35, "is_target": True,
        },
        {
            "node_id": "kp_015", "node_name": "TCP流量控制与拥塞控制", "type": "protocol",
            "chapter": "第5章", "difficulty": 4, "estimated_time": 70,
            "recommendation_reason": "拥塞控制是当前最大薄弱点，需建立在 TCP 基础之上。",
            "reason_sources": {
                "graph_dependency": "kp_015 依赖 kp_013/kp_014 的前置知识",
                "diagnosis_result": "流量控制和拥塞控制概念混淆",
                "cognitive_style": "系统分析维度偏低，需加强 rwnd/cwnd 区分练习",
            },
            "status": "locked", "current_mastery": 0.3, "is_target": True,
        },
        {
            "node_id": "kp_017", "node_name": "DNS 协议", "type": "protocol",
            "chapter": "第6章", "difficulty": 2, "estimated_time": 30,
            "recommendation_reason": "DNS 递归查询与迭代查询的对比理解。",
            "reason_sources": {
                "graph_dependency": "kp_017 是应用层协议入门",
                "diagnosis_result": "递归查询和迭代查询概念混淆",
                "cognitive_style": "对比学习风格适合 DNS 双模式对比",
            },
            "status": "locked", "current_mastery": 0.5, "is_target": False,
        },
    ],
    "generated_at": datetime.utcnow().isoformat(),
    "quality_score": 0.85,
}


# ---------------------------------------------------------------------------
# Helper: get mock diagnosis by index
# ---------------------------------------------------------------------------
def get_mock_diagnosis(index: int = 0) -> dict[str, Any]:
    """Return a mock diagnosis result by index (0-2)."""
    return MOCK_DIAGNOSES[index % len(MOCK_DIAGNOSES)]


def get_mock_profile(index: int = 0) -> dict[str, Any]:
    """Return a mock student profile by index (0-2)."""
    return MOCK_PROFILES[index % len(MOCK_PROFILES)]


def get_mock_resources() -> dict[str, Any]:
    """Return all 5 types of mock resources merged."""
    all_resources = []
    for rtype, items in MOCK_RESOURCES.items():
        all_resources.extend(items)
    return {
        "resource_id": str(uuid.uuid4()),
        "knowledge_point": "TCP 三次握手",
        "resources": all_resources,
        "total_resources": len(all_resources),
        "created_at": datetime.utcnow().isoformat(),
    }


def get_mock_path() -> dict[str, Any]:
    """Return mock learning path."""
    return dict(MOCK_LEARNING_PATH)


async def mock_stream_tokens(text: str, chunk_size: int = 6) -> AsyncIterator[str]:
    """Simulate streaming token output."""
    for i in range(0, len(text), chunk_size):
        yield text[i:i + chunk_size]
        await asyncio.sleep(0.03)


logger.info("[MockProvider] Loaded %d profiles, %d diagnoses, %d resource types",
            len(MOCK_PROFILES), len(MOCK_DIAGNOSES), len(MOCK_RESOURCES))
