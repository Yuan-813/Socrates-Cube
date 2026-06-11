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
    ("kn_001", "TCP/IP 分层模型", "第1章", "concept", ["TCP/IP", "分层", "网络体系结构"]),
    ("kn_002", "HTTP 与 TCP 的关系", "第1章", "concept", ["HTTP", "TCP", "应用层"]),
    ("kn_003", "IP 地址与子网划分", "第3章", "skill", ["IP", "子网", "CIDR"]),
    ("kn_004", "路由选择基础", "第4章", "concept", ["路由", "转发表", "下一跳"]),
    ("kn_005", "TCP 三次握手", "第5章", "protocol", ["TCP", "SYN", "ACK", "三次握手"]),
    ("kn_006", "TCP 四次挥手", "第5章", "protocol", ["TCP", "FIN", "TIME_WAIT"]),
    ("kn_007", "滑动窗口与流量控制", "第5章", "protocol", ["滑动窗口", "rwnd", "流量控制"]),
    ("kn_008", "拥塞控制", "第5章", "protocol", ["慢启动", "拥塞避免", "cwnd"]),
    ("kn_009", "DNS 解析流程", "第2章", "protocol", ["DNS", "递归查询", "迭代查询"]),
    ("kn_010", "可靠传输机制", "第5章", "concept", ["ARQ", "超时重传", "序号"]),
]
RESOURCE_TYPES = ["doc", "exercise", "code"]
QUESTION_TYPES = ["choice", "judge", "short_answer", "calculation"]
PATTERNS = ["握手次数混淆", "层次归属错误", "窗口含义混淆", "地址位数计算错误", "ACK/SEQ 推导错误"]


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


def init_database(db_path: str = "edu_agent.db", rows: int = 3000) -> None:
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
        mastery = {}
        for j in range(6):
            node_id, *_ = _topic(i + j)
            mastery[node_id] = round(rng.uniform(0.25, 0.95), 3)
        profile = {
            "conceptual_understanding": round(rng.uniform(0.35, 0.95), 3),
            "protocol_analysis": round(rng.uniform(0.3, 0.95), 3),
            "calculation_ability": round(rng.uniform(0.25, 0.9), 3),
            "error_diagnosis": round(rng.uniform(0.25, 0.9), 3),
            "system_design": round(rng.uniform(0.25, 0.85), 3),
            "knowledge_connection": round(rng.uniform(0.25, 0.9), 3),
            "expression_clarity": round(rng.uniform(0.35, 0.98), 3),
            "self_correction": round(rng.uniform(0.2, 0.9), 3),
            "mastery_map": mastery,
            "weak_points": [k for k, v in mastery.items() if v < 0.5],
            "strong_points": [k for k, v in mastery.items() if v >= 0.8],
            "turn_count": rng.randint(0, 80),
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=os.getenv("DB_PATH", "edu_agent.db"))
    parser.add_argument("--rows", type=int, default=3000, help="Base row count for large tables.")
    args = parser.parse_args()
    init_database(args.db, args.rows)
