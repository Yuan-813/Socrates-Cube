"""Create database tables and seed realistic demo data.

Usage:
    python scripts/init_db.py
    python scripts/init_db.py --db data/demo.db --rows 3000
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sqlite3
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TOPICS = [
    ("kp_001", "计算机网络概述",       "第1章", "concept",  ["计算机网络", "体系结构", "性能指标"]),
    ("kp_002", "OSI七层模型",          "第1章", "concept",  ["OSI", "七层", "分层模型"]),
    ("kp_003", "TCP/IP体系结构",       "第1章", "concept",  ["TCP/IP", "四层", "协议栈"]),
    ("kp_004", "物理层基本概念",       "第2章", "concept",  ["物理层", "信道", "编码"]),
    ("kp_005", "数据链路层基本概念",   "第3章", "concept",  ["数据链路层", "帧", "差错控制"]),
    ("kp_006", "局域网技术",           "第3章", "concept",  ["以太网", "CSMA/CD", "MAC地址"]),
    ("kp_007", "网络层基本概念",       "第4章", "concept",  ["网络层", "路由", "IP协议"]),
    ("kp_008", "IP地址与子网划分",   "第4章", "skill",    ["IP地址", "子网掩码", "CIDR"]),
    ("kp_009", "ARP协议",               "第4章", "protocol", ["ARP", "MAC地址解析", "地址映射"]),
    ("kp_010", "路由选择协议",         "第4章", "protocol", ["路由协议", "RIP", "OSPF", "BGP"]),
    ("kp_011", "运输层基本概念",       "第5章", "concept",  ["运输层", "端口", "套接字"]),
    ("kp_012", "UDP协议",               "第5章", "protocol", ["UDP", "无连接", "实时传输"]),
    ("kp_013", "TCP协议基础",           "第5章", "protocol", ["TCP", "可靠传输", "序号"]),
    ("kp_014", "TCP三次握手与四次挥手", "第5章", "protocol", ["TCP", "SYN", "FIN", "握手"]),
    ("kp_015", "TCP流量控制与拥塞控制", "第5章", "protocol", ["滑动窗口", "慢启动", "拥塞避免"]),
    ("kp_016", "应用层基本概念",       "第6章", "concept",  ["应用层", "客户服务器", "P2P"]),
    ("kp_017", "DNS协议",               "第6章", "protocol", ["DNS", "域名解析", "递归查询"]),
    ("kp_018", "HTTP与HTTPS",             "第6章", "protocol", ["HTTP", "HTTPS", "TLS", "请求响应"]),
    ("kp_019", "网络安全基础",         "第7章", "concept",  ["加密", "认证", "TLS", "防火墙"]),
    ("kp_020", "综合应用与故障排查",   "第7章", "skill",    ["故障排查", "抓包", "网络测试"]),
]
RESOURCE_TYPES = ["doc", "exercise", "code"]
QUESTION_TYPES = ["choice", "judge", "short_answer", "calculation"]
PATTERNS = [
    "握手次数混淡", "层次归属错误", "窗口含义混淡",
    "地址位数计算错误", "ACK/SEQ推导错误", "流程遗漏型",
    "概念混淡型", "过度简化型", "理解不完整型", "因果倒置型",
]


def _now(offset_days: int = 0) -> str:
    return (datetime.now() + timedelta(days=offset_days)).isoformat(sep=" ", timespec="seconds")


def _load_graph_nodes() -> list[dict]:
    graph_path = ROOT / "data" / "knowledge_graph.json"
    if not graph_path.exists():
        return []
    try:
        raw = json.loads(graph_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    predecessors: dict[str, list[str]] = {}
    for edge in raw.get("edges", []):
        predecessors.setdefault(edge.get("to", ""), []).append(edge.get("from", ""))
    nodes = []
    for item in raw.get("nodes", []):
        nodes.append(
            {
                "node_id": item["id"],
                "name": item["name"],
                "chapter": item.get("chapter", "课程知识"),
                "node_type": item.get("type", "concept"),
                "difficulty": item.get("difficulty", 3),
                "estimated_time": item.get("estimated_time", 30),
                "keywords_json": json.dumps(item.get("keywords", []), ensure_ascii=False),
                "description": item.get("description", ""),
                "prerequisite_ids_json": json.dumps(predecessors.get(item["id"], []), ensure_ascii=False),
            }
        )
    return nodes


def _topic(index: int) -> tuple[str, str, str, str, list[str]]:
    return TOPICS[index % len(TOPICS)]


def init_database(db_path: str = "edu_agent.db", rows: int = 6000) -> None:
    os.environ["DB_PATH"] = db_path
    from src.loopse.db.connection import init_db

    init_db()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    rng = random.Random(20260528)

    graph_nodes = _load_graph_nodes()
    if not graph_nodes:
        graph_nodes = [
            {
                "node_id": node_id,
                "name": name,
                "chapter": chapter,
                "node_type": node_type,
                "difficulty": rng.randint(1, 5),
                "estimated_time": rng.choice([20, 30, 40, 50]),
                "keywords_json": json.dumps(keywords, ensure_ascii=False),
                "description": f"{name} 的核心概念、流程和常见误区。",
                "prerequisite_ids_json": "[]",
            }
            for node_id, name, chapter, node_type, keywords in TOPICS
        ]
    existing_ids = {node["node_id"] for node in graph_nodes}
    synthetic_index = 0
    while len(graph_nodes) < rows:
        base_id, base_name, chapter, node_type, keywords = _topic(synthetic_index)
        node_id = f"{base_id}_micro_{synthetic_index:05d}"
        if node_id not in existing_ids:
            existing_ids.add(node_id)
            prereq = base_id if base_id in existing_ids else ""
            graph_nodes.append(
                {
                    "node_id": node_id,
                    "name": f"{base_name} 微技能 {synthetic_index + 1}",
                    "chapter": chapter,
                    "node_type": node_type,
                    "difficulty": 1 + (synthetic_index % 5),
                    "estimated_time": 15 + (synthetic_index % 4) * 10,
                    "keywords_json": json.dumps(keywords + ["微技能", "自适应学习"], ensure_ascii=False),
                    "description": f"{base_name} 的细粒度训练点，用于路径规划、练习推荐和误区诊断。",
                    "prerequisite_ids_json": json.dumps([prereq] if prereq else [], ensure_ascii=False),
                }
            )
        synthetic_index += 1

    cur.executemany(
        """
        INSERT OR IGNORE INTO knowledge_nodes
        (node_id, name, chapter, node_type, difficulty, estimated_time, keywords_json, description, prerequisite_ids_json)
        VALUES (:node_id, :name, :chapter, :node_type, :difficulty, :estimated_time, :keywords_json, :description, :prerequisite_ids_json)
        """,
        graph_nodes,
    )

    users = [(f"user-{i:05d}", f"student_{i:05d}", _now(-rng.randint(1, 180)), _now()) for i in range(rows)]
    cur.executemany(
        "INSERT OR IGNORE INTO users (id, username, create_time, update_time) VALUES (?, ?, ?, ?)",
        users,
    )

    profiles = []
    for i in range(rows):
        # 三段式学生画像分布: 初学40%, 中等45%, 高手15%
        tier = rng.choices(['beginner', 'intermediate', 'advanced'], weights=[0.40, 0.45, 0.15])[0]
        if tier == 'beginner':
            lo, hi = 0.20, 0.55
            turn_range = (2, 25)
        elif tier == 'intermediate':
            lo, hi = 0.45, 0.80
            turn_range = (15, 55)
        else:
            lo, hi = 0.65, 0.95
            turn_range = (40, 90)

        mastery = {}
        for j in range(8):  # 每个学生覆盖8个KP节点
            node_id, *_ = _topic(i + j)
            mastery[node_id] = round(rng.uniform(lo, hi), 3)

        # 高手学生有几个强项，初学者有清晰弱项
        if tier == 'advanced':
            for k in mastery:
                if rng.random() < 0.3:
                    mastery[k] = round(rng.uniform(0.85, 0.98), 3)
        elif tier == 'beginner':
            for k in mastery:
                if rng.random() < 0.4:
                    mastery[k] = round(rng.uniform(0.10, 0.35), 3)

        profile = {
            "conceptual_understanding": round(rng.uniform(lo, hi), 3),
            "protocol_analysis":        round(rng.uniform(lo, hi - 0.05), 3),
            "calculation_ability":      round(rng.uniform(lo - 0.05, hi - 0.05), 3),
            "error_diagnosis":          round(rng.uniform(lo - 0.05, hi - 0.10), 3),
            "system_design":            round(rng.uniform(lo - 0.10, hi - 0.10), 3),
            "knowledge_connection":     round(rng.uniform(lo, hi), 3),
            "expression_clarity":       round(rng.uniform(lo + 0.05, hi + 0.03), 3),
            "self_correction":          round(rng.uniform(lo - 0.05, hi - 0.05), 3),
            "mastery_map":   mastery,
            "weak_points":   [k for k, v in mastery.items() if v < 0.5],
            "strong_points": [k for k, v in mastery.items() if v >= 0.8],
            "turn_count":    rng.randint(*turn_range),
            "tier":          tier,
        }
        profiles.append((f"user-{i:05d}", json.dumps(profile, ensure_ascii=False), _now()))
    cur.executemany(
        "INSERT OR REPLACE INTO student_profiles (user_id, profile_json, update_time) VALUES (?, ?, ?)",
        profiles,
    )

    sessions = []
    logs = []
    paths = []
    path_nodes = []
    assessments = []
    misconceptions = []
    resources = []

    for i in range(rows):
        user_id = f"user-{i:05d}"
        session_id = f"session-{i:05d}"
        node_id, topic_name, chapter, _, _ = _topic(i)
        messages = [
            {"role": "user", "content": f"我想理解{topic_name}", "timestamp": _now(-2)},
            {"role": "assistant", "content": f"我们先从{topic_name}的关键问题开始。", "timestamp": _now(-2)},
        ]
        sessions.append((session_id, user_id, json.dumps(messages, ensure_ascii=False), _now(-2), _now()))

        path_id = f"path-{i:05d}"
        plan_nodes = []
        total_time = 0
        for seq in range(1, 5):
            nid, name, _, _, _ = _topic(i + seq)
            mastery = round(rng.uniform(0.15, 0.85), 3)
            total_time += 30
            plan_nodes.append({"node_id": nid, "node_name": name, "sequence": seq, "current_mastery": mastery})
            path_nodes.append((f"{path_id}:{nid}:{seq}", path_id, nid, seq, "pending", mastery, f"根据画像补强{name}", _now()))
        paths.append(
            (
                path_id,
                user_id,
                f"{topic_name} 个性化学习路径",
                f"围绕{topic_name}补齐前置知识并安排练习。",
                "active",
                total_time,
                json.dumps({"nodes": plan_nodes}, ensure_ascii=False),
                _now(-1),
                _now(),
            )
        )

        for agent_name, action in [
            ("Retriever", "hybrid_search"),
            ("Diagnosis", "three_layer_diagnosis"),
            ("PathPlanner", "topological_plan"),
        ]:
            logs.append(
                (
                    str(uuid.uuid4()),
                    session_id,
                    agent_name,
                    action,
                    json.dumps({"node": node_id, "policy": "seed"}, ensure_ascii=False),
                    _now(-1),
                    json.dumps({"status": "ok"}, ensure_ascii=False),
                )
            )

        for k in range(2):
            score = round(rng.uniform(45, 100), 1)
            assessments.append(
                (
                    str(uuid.uuid4()),
                    user_id,
                    _topic(i + k)[0],
                    rng.choice(QUESTION_TYPES),
                    score,
                    100,
                    json.dumps({"answer": "demo answer"}, ensure_ascii=False),
                    json.dumps({"is_correct": score >= 60, "confidence": 0.75}, ensure_ascii=False),
                    _now(-rng.randint(0, 60)),
                )
            )
        misconceptions.append(
            (
                str(uuid.uuid4()),
                user_id,
                node_id,
                rng.choice(PATTERNS),
                round(rng.uniform(0.2, 0.95), 3),
                f"在{topic_name}相关问答中暴露出理解偏差。",
                "安排对比题、流程图和追问式纠偏。",
                _now(-rng.randint(0, 30)),
            )
        )

    for i in range(rows):
        node_id, topic_name, _, _, _ = _topic(i)
        res_type = RESOURCE_TYPES[i % len(RESOURCE_TYPES)]
        resources.append(
            (
                f"resource-{i:05d}",
                node_id,
                topic_name,
                res_type,
                1 + (i % 5),
                f"{topic_name} {res_type} 资源 {i}",
                f"这是面向{topic_name}的{res_type}学习资源，包含概念、例题和纠错提示。",
                json.dumps({"source": "seed", "difficulty": 1 + (i % 5)}, ensure_ascii=False),
                round(rng.uniform(0.65, 0.98), 3),
                _now(-rng.randint(0, 90)),
                _now(),
            )
        )

    cur.executemany(
        "INSERT OR IGNORE INTO chat_sessions (session_id, user_id, messages, create_time, update_time) VALUES (?, ?, ?, ?, ?)",
        sessions,
    )
    cur.executemany(
        "INSERT OR IGNORE INTO agent_logs (log_id, session_id, agent_name, action, state, timestamp, result) VALUES (?, ?, ?, ?, ?, ?, ?)",
        logs,
    )
    cur.executemany(
        """
        INSERT OR REPLACE INTO learning_paths
        (path_id, user_id, title, description, status, total_estimated_time, plan_json, create_time, update_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        paths,
    )
    cur.executemany(
        """
        INSERT OR REPLACE INTO learning_path_nodes
        (id, path_id, node_id, sequence, status, current_mastery, recommendation_reason, create_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        path_nodes,
    )
    cur.executemany(
        """
        INSERT OR IGNORE INTO assessment_records
        (assessment_id, user_id, knowledge_node_id, question_type, score, max_score, answer_json, diagnosis_json, create_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        assessments,
    )
    cur.executemany(
        """
        INSERT OR IGNORE INTO misconception_records
        (id, user_id, knowledge_node_id, pattern, severity, evidence, intervention, last_seen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        misconceptions,
    )
    cur.executemany(
        """
        INSERT OR REPLACE INTO learning_resources
        (resource_id, knowledge_node_id, knowledge_point, resource_type, difficulty, title, content, metadata_json, quality_score, create_time, update_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        resources,
    )

    conn.commit()

    # --- 演示账号预置 ---
    seed_demo_accounts(conn)

    counts = {
        name: cur.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        for name in [
            "users",
            "student_profiles",
            "chat_sessions",
            "agent_logs",
            "knowledge_nodes",
            "learning_resources",
            "learning_paths",
            "learning_path_nodes",
            "assessment_records",
            "misconception_records",
        ]
    }
    conn.close()
    print(f"Database initialized: {Path(db_path).resolve()}")
    for table, count in counts.items():
        print(f"{table}: {count}")


# ---------------------------------------------------------------------------
# 演示账号预置：3 个不同认知风格 / 进度的学生
# ---------------------------------------------------------------------------

DEMO_ACCOUNTS = [
    {
        "id": "demo-student-001",
        "username": "初学者-小王",
        "profile": {
            "conceptual_understanding": 0.45,
            "protocol_analysis": 0.35,
            "calculation_ability": 0.30,
            "error_diagnosis": 0.28,
            "system_design": 0.25,
            "knowledge_connection": 0.30,
            "expression_clarity": 0.55,
            "self_correction": 0.40,
            "mastery_map": {"kp_001": 0.45, "kp_003": 0.50, "kp_014": 0.30},
            "weak_points": ["kp_014", "kp_015"],
            "strong_points": [],
            "turn_count": 8,
            "cognitive_style": "visual",
        },
    },
    {
        "id": "demo-student-002",
        "username": "进阶-小李",
        "profile": {
            "conceptual_understanding": 0.68,
            "protocol_analysis": 0.65,
            "calculation_ability": 0.58,
            "error_diagnosis": 0.55,
            "system_design": 0.50,
            "knowledge_connection": 0.60,
            "expression_clarity": 0.72,
            "self_correction": 0.62,
            "mastery_map": {"kp_001": 0.75, "kp_003": 0.70, "kp_014": 0.65, "kp_015": 0.55},
            "weak_points": ["kp_015", "kp_019"],
            "strong_points": ["kp_001"],
            "turn_count": 22,
            "cognitive_style": "practical",
        },
    },
    {
        "id": "demo-student-003",
        "username": "高手-小张",
        "profile": {
            "conceptual_understanding": 0.88,
            "protocol_analysis": 0.85,
            "calculation_ability": 0.82,
            "error_diagnosis": 0.80,
            "system_design": 0.78,
            "knowledge_connection": 0.85,
            "expression_clarity": 0.90,
            "self_correction": 0.85,
            "mastery_map": {"kp_001": 0.92, "kp_003": 0.88, "kp_014": 0.85, "kp_015": 0.80, "kp_018": 0.75},
            "weak_points": [],
            "strong_points": ["kp_001", "kp_003", "kp_014"],
            "turn_count": 45,
            "cognitive_style": "textual",
        },
    },
]

DEMO_CHAT_SESSIONS = [
    {
        "session_id": "demo-session-001",
        "user_id": "demo-student-001",
        "messages": [
            {"role": "user", "content": "什么是TCP三次握手？", "timestamp": _now(-2)},
            {"role": "assistant", "content": "TCP三次握手是建立连接的标准流程：SYN → SYN+ACK → ACK", "timestamp": _now(-2)},
            {"role": "user", "content": "两次握手不行吗？", "timestamp": _now(-1)},
            {"role": "assistant", "content": "两次握手无法防止历史失效连接，第三次ACK确认客户端的接收能力。", "timestamp": _now(-1)},
        ],
    },
    {
        "session_id": "demo-session-002",
        "user_id": "demo-student-002",
        "messages": [
            {"role": "user", "content": "HTTP是直接基于IP的吗？", "timestamp": _now(-3)},
            {"role": "assistant", "content": "不是，HTTP基于TCP，TCP再基于IP。正确的层次是：HTTP → TCP → IP。", "timestamp": _now(-3)},
            {"role": "user", "content": "滑动窗口和拥塞窗口有什么区别？", "timestamp": _now(-1)},
            {"role": "assistant", "content": "滑动窗口(rwnd)用于流量控制，由接收方通告；拥塞窗口(cwnd)用于拥塞控制，由发送方根据网络状况调整。", "timestamp": _now(-1)},
        ],
    },
    {
        "session_id": "demo-session-003",
        "user_id": "demo-student-003",
        "messages": [
            {"role": "user", "content": "TCP拥塞控制的四个阶段是什么？", "timestamp": _now(-2)},
            {"role": "assistant", "content": "慢启动（指数增长）→拥塞避免（线性增长）→快重传（3个重复ACK）→快恢复（cwnd减半）。", "timestamp": _now(-2)},
        ],
    },
]


def seed_demo_accounts(conn: sqlite3.Connection) -> None:
    """创建 3 个演示账号，预置画像和对话数据。"""
    cur = conn.cursor()

    # 用户
    for acc in DEMO_ACCOUNTS:
        cur.execute(
            "INSERT OR IGNORE INTO users (id, username, create_time, update_time) VALUES (?, ?, ?, ?)",
            (acc["id"], acc["username"], _now(-30), _now()),
        )

    # 画像
    for acc in DEMO_ACCOUNTS:
        cur.execute(
            "INSERT OR REPLACE INTO student_profiles (user_id, profile_json, update_time) VALUES (?, ?, ?)",
            (acc["id"], json.dumps(acc["profile"], ensure_ascii=False), _now()),
        )

    # 历史对话
    for sess in DEMO_CHAT_SESSIONS:
        cur.execute(
            "INSERT OR IGNORE INTO chat_sessions (session_id, user_id, messages, create_time, update_time) VALUES (?, ?, ?, ?, ?)",
            (sess["session_id"], sess["user_id"], json.dumps(sess["messages"], ensure_ascii=False), _now(-3), _now()),
        )

    # Agent 日志
    demo_logs = [
        (str(uuid.uuid4()), "demo-session-001", "Retriever", "hybrid_search", json.dumps({"query": "TCP三次握手"}, ensure_ascii=False), _now(-2), json.dumps({"docs": 5, "misconceptions": 2}, ensure_ascii=False)),
        (str(uuid.uuid4()), "demo-session-001", "Diagnosis", "three_layer_diagnosis", json.dumps({"message": "两次握手不行吗"}, ensure_ascii=False), _now(-1), json.dumps({"is_correct": False, "error_type": "flow_omission", "surface_error": "TCP三次握手流程遗漏", "pattern": "流程遗漏型", "knowledge_node_ids": ["kp_014"], "acu_ids": ["acu_025"], "misconception_id": "mc_001", "confidence": 0.92}, ensure_ascii=False)),
        (str(uuid.uuid4()), "demo-session-002", "Diagnosis", "three_layer_diagnosis", json.dumps({"message": "HTTP直接基于IP"}, ensure_ascii=False), _now(-3), json.dumps({"is_correct": False, "error_type": "layer_misplacement", "surface_error": "HTTP层次归属错误", "pattern": "层次归属错误", "knowledge_node_ids": ["kp_018"], "acu_ids": ["acu_038"], "misconception_id": "mc_003", "confidence": 0.88}, ensure_ascii=False)),
        (str(uuid.uuid4()), "demo-session-002", "PathPlanner", "plan", json.dumps({"user": "demo-student-002"}, ensure_ascii=False), _now(-1), json.dumps({"nodes": 5, "target_node_ids": ["kp_018"]}, ensure_ascii=False)),
        (str(uuid.uuid4()), "demo-session-003", "Diagnosis", "three_layer_diagnosis", json.dumps({"message": "拥塞控制四阶段"}, ensure_ascii=False), _now(-2), json.dumps({"is_correct": True, "confidence": 0.95}, ensure_ascii=False)),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO agent_logs (log_id, session_id, agent_name, action, state, timestamp, result) VALUES (?, ?, ?, ?, ?, ?, ?)",
        demo_logs,
    )

    conn.commit()
    print("[Demo] 3 demo accounts seeded:")
    for acc in DEMO_ACCOUNTS:
        print(f"  - {acc['username']} ({acc['id']}) style={acc['profile']['cognitive_style']} turns={acc['profile']['turn_count']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=os.getenv("DB_PATH", "edu_agent.db"))
    parser.add_argument("--rows", type=int, default=3000, help="Base row count for large tables.")
    parser.add_argument("--demo-only", action="store_true", help="Only seed demo accounts (skip bulk data).")
    args = parser.parse_args()
    if args.demo_only:
        os.environ["DB_PATH"] = args.db
        from src.loopse.db.connection import init_db
        init_db()
        conn = sqlite3.connect(args.db)
        seed_demo_accounts(conn)
        conn.close()
    else:
        init_database(args.db, args.rows)
