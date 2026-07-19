#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL / PostgreSQL 兼容的数据库初始化脚本（不依赖 sqlite3）。
使用 SQLAlchemy ORM，支持 SQLite / MySQL / PostgreSQL 三种后端。

运行方式：
    python scripts/init_mysql.py          # 建表 + 演示数据 + 知识节点
    python scripts/init_mysql.py --demo   # 仅插入3个演示账号
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _ensure_mysql_database() -> None:
    """MySQL 专用：若 edu_agent 库不存在则自动创建。"""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    db_url = os.getenv("DATABASE_URL", "")
    if "mysql" not in db_url:
        return
    # 解析连接串，去掉数据库名后连接 MySQL
    try:
        import pymysql
        # 格式: mysql+pymysql://user:pass@host:port/dbname?...
        rest = db_url.split("://", 1)[1].split("?")[0]  # user:pass@host:port/dbname
        userpass, hostpart = rest.rsplit("@", 1)
        user, password = userpass.split(":", 1)
        hostport, dbname = hostpart.rsplit("/", 1)
        if ":" in hostport:
            host, port = hostport.rsplit(":", 1)
            port = int(port)
        else:
            host, port = hostport, 3306
        conn = pymysql.connect(host=host, port=port, user=user, password=password,
                               charset="utf8mb4", connect_timeout=15)
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{dbname}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.close()
        print(f"   database `{dbname}` ready [OK]")
    except Exception as e:
        print(f"   [WARN] _ensure_mysql_database: {e}")


from src.loopse.db.connection import SessionLocal, init_db
from src.loopse.db.models import (
    AgentLog, AssessmentRecord, ChatSession, KnowledgeNodeRecord,
    LearningPath, LearningPathNode, LearningResource,
    MisconceptionRecord, StudentProfile, User,
)

# ─────────────────────────────────────────
# 基础数据
# ─────────────────────────────────────────
TOPICS = [
    ("kn_001", "TCP/IP 分层模型",   "第1章", "concept",  ["TCP/IP", "分层", "网络体系结构"]),
    ("kn_002", "HTTP 与 TCP 的关系","第1章", "concept",  ["HTTP", "TCP", "应用层"]),
    ("kn_003", "IP 地址与子网划分", "第3章", "skill",    ["IP", "子网", "CIDR"]),
    ("kn_004", "路由选择基础",      "第4章", "concept",  ["路由", "转发表", "下一跳"]),
    ("kn_005", "TCP 三次握手",      "第5章", "protocol", ["TCP", "SYN", "ACK", "三次握手"]),
    ("kn_006", "TCP 四次挥手",      "第5章", "protocol", ["TCP", "FIN", "TIME_WAIT"]),
    ("kn_007", "滑动窗口与流量控制","第5章", "protocol", ["滑动窗口", "rwnd", "流量控制"]),
    ("kn_008", "拥塞控制",          "第5章", "protocol", ["慢启动", "拥塞避免", "cwnd"]),
    ("kn_009", "DNS 解析流程",      "第2章", "protocol", ["DNS", "递归查询", "迭代查询"]),
    ("kn_010", "可靠传输机制",      "第5章", "concept",  ["ARQ", "超时重传", "序号"]),
]

PATTERNS = [
    "握手次数混淆", "层次归属错误", "窗口含义混淆",
    "地址位数计算错误", "ACK/SEQ 推导错误",
]

DEMO_ACCOUNTS = [
    {
        "id": "demo-student-001",
        "username": "初学者-小王",
        "profile": {
            "conceptual_understanding": 0.45, "protocol_analysis": 0.35,
            "calculation_ability": 0.30,      "error_diagnosis": 0.28,
            "system_design": 0.25,            "knowledge_connection": 0.30,
            "expression_clarity": 0.55,       "self_correction": 0.40,
            "mastery_map": {"kn_001": 0.45, "kn_002": 0.50, "kn_005": 0.30},
            "weak_points": ["kn_005", "kn_007"], "strong_points": [],
            "turn_count": 8, "cognitive_style": "visual",
        },
    },
    {
        "id": "demo-student-002",
        "username": "进阶-小李",
        "profile": {
            "conceptual_understanding": 0.68, "protocol_analysis": 0.65,
            "calculation_ability": 0.58,      "error_diagnosis": 0.55,
            "system_design": 0.50,            "knowledge_connection": 0.60,
            "expression_clarity": 0.72,       "self_correction": 0.62,
            "mastery_map": {"kn_001": 0.75, "kn_002": 0.70, "kn_005": 0.65, "kn_007": 0.55},
            "weak_points": ["kn_007", "kn_008"], "strong_points": ["kn_001"],
            "turn_count": 22, "cognitive_style": "practical",
        },
    },
    {
        "id": "demo-student-003",
        "username": "高手-小张",
        "profile": {
            "conceptual_understanding": 0.88, "protocol_analysis": 0.85,
            "calculation_ability": 0.82,      "error_diagnosis": 0.80,
            "system_design": 0.78,            "knowledge_connection": 0.85,
            "expression_clarity": 0.90,       "self_correction": 0.85,
            "mastery_map": {"kn_001": 0.92, "kn_002": 0.88, "kn_005": 0.85, "kn_007": 0.80, "kn_008": 0.75},
            "weak_points": [], "strong_points": ["kn_001", "kn_002", "kn_005"],
            "turn_count": 45, "cognitive_style": "textual",
        },
    },
]

DEMO_SESSIONS = [
    {
        "session_id": "demo-session-001",
        "user_id": "demo-student-001",
        "messages": [
            {"role": "user",      "content": "什么是TCP三次握手？",          "timestamp": (datetime.now() - timedelta(days=2)).isoformat()},
            {"role": "assistant", "content": "TCP三次握手是建立连接的标准流程：SYN → SYN+ACK → ACK", "timestamp": (datetime.now() - timedelta(days=2)).isoformat()},
            {"role": "user",      "content": "两次握手不行吗？",              "timestamp": (datetime.now() - timedelta(days=1)).isoformat()},
            {"role": "assistant", "content": "两次握手无法防止历史失效连接，第三次ACK确认客户端的接收能力。", "timestamp": (datetime.now() - timedelta(days=1)).isoformat()},
        ],
    },
    {
        "session_id": "demo-session-002",
        "user_id": "demo-student-002",
        "messages": [
            {"role": "user",      "content": "HTTP是直接基于IP的吗？",        "timestamp": (datetime.now() - timedelta(days=3)).isoformat()},
            {"role": "assistant", "content": "不是，HTTP基于TCP，TCP再基于IP。正确的层次是：HTTP → TCP → IP。", "timestamp": (datetime.now() - timedelta(days=3)).isoformat()},
            {"role": "user",      "content": "滑动窗口和拥塞窗口有什么区别？", "timestamp": (datetime.now() - timedelta(days=1)).isoformat()},
            {"role": "assistant", "content": "滑动窗口(rwnd)用于流量控制，由接收方通告；拥塞窗口(cwnd)用于拥塞控制，由发送方根据网络状况调整。", "timestamp": (datetime.now() - timedelta(days=1)).isoformat()},
        ],
    },
    {
        "session_id": "demo-session-003",
        "user_id": "demo-student-003",
        "messages": [
            {"role": "user",      "content": "TCP拥塞控制的四个阶段是什么？", "timestamp": (datetime.now() - timedelta(days=2)).isoformat()},
            {"role": "assistant", "content": "慢启动（指数增长）→拥塞避免（线性增长）→快重传（3个重复ACK）→快恢复（cwnd减半）。", "timestamp": (datetime.now() - timedelta(days=2)).isoformat()},
        ],
    },
]


def _try_add(session, obj) -> bool:
    """尝试插入，重复主键则跳过。"""
    try:
        session.merge(obj)
        return True
    except Exception:
        session.rollback()
        return False


def seed_knowledge_nodes(session) -> int:
    """写入10个核心知识节点。"""
    count = 0
    for node_id, name, chapter, node_type, keywords in TOPICS:
        obj = KnowledgeNodeRecord(
            node_id=node_id,
            name=name,
            chapter=chapter,
            node_type=node_type,
            difficulty=3,
            estimated_time=30,
            keywords_json=json.dumps(keywords, ensure_ascii=False),
            description=f"{name} 的核心概念、流程和常见误区。",
            prerequisite_ids_json="[]",
        )
        session.merge(obj)
        count += 1
    session.commit()
    print(f"  knowledge_nodes: {count} 条")
    return count


def seed_demo_accounts(session) -> None:
    """写入3个演示账号 + 画像 + 对话 + Agent日志。"""
    now = datetime.now()

    # 第1步：先提交用户（chat_sessions 有外键依赖 users）
    for acc in DEMO_ACCOUNTS:
        session.merge(User(
            id=acc["id"],
            username=acc["username"],
            create_time=now - timedelta(days=30),
            update_time=now,
        ))
    session.commit()  # users 先入库

    # 第2步：画像
    for acc in DEMO_ACCOUNTS:
        session.merge(StudentProfile(
            user_id=acc["id"],
            profile_json=json.dumps(acc["profile"], ensure_ascii=False),
            update_time=now,
        ))
    session.commit()

    # 第3步：对话（依赖 users）
    for sess in DEMO_SESSIONS:
        session.merge(ChatSession(
            session_id=sess["session_id"],
            user_id=sess["user_id"],
            messages=json.dumps(sess["messages"], ensure_ascii=False),
            create_time=now - timedelta(days=3),
            update_time=now,
        ))
    session.commit()

    # 第4步：Agent 日志
    for log_data in [
        ("demo-session-001", "Retriever",  "hybrid_search",        {"query": "TCP"},             {"docs": 5}),
        ("demo-session-001", "Diagnosis",  "three_layer_diagnosis", {"message": "two-way"},       {"is_correct": False}),
        ("demo-session-002", "Diagnosis",  "three_layer_diagnosis", {"message": "HTTP on IP"},    {"is_correct": False}),
        ("demo-session-002", "PathPlanner","plan",                  {"user": "demo-02"},          {"nodes": 5}),
        ("demo-session-003", "Diagnosis",  "three_layer_diagnosis", {"message": "congestion"},    {"is_correct": True}),
    ]:
        session.add(AgentLog(
            log_id=str(uuid.uuid4()),
            session_id=log_data[0],
            agent_name=log_data[1],
            action=log_data[2],
            state=json.dumps(log_data[3], ensure_ascii=False),
            timestamp=now - timedelta(days=1),
            result=json.dumps(log_data[4], ensure_ascii=False),
        ))
    session.commit()

    print(f"  demo_accounts: {len(DEMO_ACCOUNTS)} done")


def seed_bulk_data(session, rows: int = 500) -> None:
    """写入批量演示数据（用户/画像/对话/路径/评估/误解）。"""
    rng = random.Random(20260528)
    now = datetime.now()

    users, profiles, chats, paths, path_nodes = [], [], [], [], []
    assessments, misconceptions = [], []

    for i in range(rows):
        uid = f"user-{i:05d}"
        topic = TOPICS[i % len(TOPICS)]
        node_id, topic_name = topic[0], topic[1]

        users.append(User(
            id=uid, username=f"student_{i:05d}",
            create_time=now - timedelta(days=rng.randint(1, 180)),
            update_time=now,
        ))

        mastery = {TOPICS[j % len(TOPICS)][0]: round(rng.uniform(0.25, 0.95), 3) for j in range(i, i + 6)}
        profiles.append(StudentProfile(
            user_id=uid,
            profile_json=json.dumps({
                "conceptual_understanding": round(rng.uniform(0.35, 0.95), 3),
                "protocol_analysis":        round(rng.uniform(0.30, 0.95), 3),
                "calculation_ability":      round(rng.uniform(0.25, 0.90), 3),
                "error_diagnosis":          round(rng.uniform(0.25, 0.90), 3),
                "system_design":            round(rng.uniform(0.25, 0.85), 3),
                "knowledge_connection":     round(rng.uniform(0.25, 0.90), 3),
                "expression_clarity":       round(rng.uniform(0.35, 0.98), 3),
                "self_correction":          round(rng.uniform(0.20, 0.90), 3),
                "mastery_map": mastery,
                "weak_points":   [k for k, v in mastery.items() if v < 0.5],
                "strong_points": [k for k, v in mastery.items() if v >= 0.8],
                "turn_count": rng.randint(0, 80),
            }, ensure_ascii=False),
            update_time=now,
        ))

        chats.append(ChatSession(
            session_id=f"session-{i:05d}", user_id=uid,
            messages=json.dumps([
                {"role": "user",      "content": f"我想理解{topic_name}",           "timestamp": (now - timedelta(days=2)).isoformat()},
                {"role": "assistant", "content": f"我们先从{topic_name}的关键问题开始。", "timestamp": (now - timedelta(days=2)).isoformat()},
            ], ensure_ascii=False),
            create_time=now - timedelta(days=2),
            update_time=now,
        ))

        path_id = f"path-{i:05d}"
        plan_nodes = []
        for seq in range(1, 5):
            nid, nname = TOPICS[(i + seq) % len(TOPICS)][:2]
            m = round(rng.uniform(0.15, 0.85), 3)
            plan_nodes.append({"node_id": nid, "node_name": nname, "sequence": seq, "current_mastery": m})
            path_nodes.append(LearningPathNode(
                id=f"{path_id}:{nid}:{seq}", path_id=path_id, node_id=nid,
                sequence=seq, status="pending", current_mastery=m,
                recommendation_reason=f"根据画像补强{nname}",
                create_time=now,
            ))
        paths.append(LearningPath(
            path_id=path_id, user_id=uid,
            title=f"{topic_name} 个性化学习路径",
            description=f"围绕{topic_name}补齐前置知识并安排练习。",
            status="active", total_estimated_time=120,
            plan_json=json.dumps({"nodes": plan_nodes}, ensure_ascii=False),
            create_time=now - timedelta(days=1), update_time=now,
        ))

        for k in range(2):
            score = round(rng.uniform(45, 100), 1)
            assessments.append(AssessmentRecord(
                assessment_id=str(uuid.uuid4()), user_id=uid,
                knowledge_node_id=TOPICS[(i + k) % len(TOPICS)][0],
                question_type=rng.choice(["choice", "judge", "short_answer"]),
                score=score, max_score=100.0,
                answer_json=json.dumps({"answer": "demo"}, ensure_ascii=False),
                diagnosis_json=json.dumps({"is_correct": score >= 60, "confidence": 0.75}, ensure_ascii=False),
                create_time=now - timedelta(days=rng.randint(0, 60)),
            ))

        misconceptions.append(MisconceptionRecord(
            id=str(uuid.uuid4()), user_id=uid, knowledge_node_id=node_id,
            pattern=rng.choice(PATTERNS), severity=round(rng.uniform(0.2, 0.95), 3),
            evidence=f"在{topic_name}相关问答中暴露出理解偏差。",
            intervention="安排对比题、流程图和追问式纠偏。",
            last_seen=now - timedelta(days=rng.randint(0, 30)),
        ))

    # 批量写入（注意顺序：users 先，再 paths，再 path_nodes)
    for obj in users:
        session.merge(obj)
    session.commit()

    for obj in profiles:
        session.merge(obj)
    session.commit()

    for obj in chats:
        session.merge(obj)
    session.commit()

    for obj in paths:
        session.merge(obj)
    session.commit()

    for obj in path_nodes:
        session.merge(obj)
    session.commit()

    for obj in assessments:
        session.add(obj)
    session.commit()

    for obj in misconceptions:
        session.add(obj)
    session.commit()

    print(f"  bulk data: {rows} rows done")


def main(demo_only: bool = False, rows: int = 500) -> None:
    print("=== Socrates-Cube MySQL 初始化 ===")
    print("1. 检查并创建数据库...")
    _ensure_mysql_database()
    print("2. 创建数据库表结构...")
    init_db()
    print("   tables created [OK]")

    session = SessionLocal()
    try:
        print("3. 写入知识节点...")
        seed_knowledge_nodes(session)

        print("4. 写入演示账号...")
        seed_demo_accounts(session)

        if not demo_only:
            print(f"5. 写入批量演示数据（{rows} 行）...")
            seed_bulk_data(session, rows)

        print("\n=== init done ===")
    except Exception as e:
        session.rollback()
        print(f"[ERROR] {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="仅插入演示账号，跳过批量数据")
    parser.add_argument("--rows", type=int, default=500, help="批量数据行数（默认500）")
    args = parser.parse_args()
    main(demo_only=args.demo, rows=args.rows)
