#!/usr/bin/env python3
"""演示环境一键预热脚本。

功能：
  1. 创建 3 个预置演示账号（不同认知风格 / 不同学习进度）
  2. 为每个账号预置画像数据和历史对话
  3. 预置学习路径和资源数据
  4. 支持正常模式和 Mock 模式切换

Usage:
    python scripts/demo_warmup.py              # 正常模式预热
    python scripts/demo_warmup.py --mock-mode  # Mock 模式预热
    python scripts/demo_warmup.py --reset      # 清空并重建演示数据
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.loopse.db.connection import init_db, SessionLocal
from src.loopse.db.models import (
    AgentLog,
    ChatSession,
    LearningPath,
    LearningPathNode,
    LearningResource,
    StudentProfile,
    User,
)
from src.loopse.core.mock_provider import (
    MOCK_PROFILES,
    MOCK_DIAGNOSES,
    MOCK_RESOURCES,
    MOCK_LEARNING_PATH,
)

DEMO_USERS = [
    {"id": "demo-student-001", "username": "初学者-小王"},
    {"id": "demo-student-002", "username": "进阶-小李"},
    {"id": "demo-student-003", "username": "高手-小张"},
]

DEMO_SESSIONS = [
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

DEMO_LOGS = [
    {"session_id": "demo-session-001", "agent_name": "Retriever", "action": "hybrid_search", "state": {"query": "TCP三次握手"}, "result": {"docs": 5, "misconceptions": 2}},
    {"session_id": "demo-session-001", "agent_name": "Diagnosis", "action": "three_layer_diagnosis", "state": {"message": "两次握手不行吗"}, "result": MOCK_DIAGNOSES[0]},
    {"session_id": "demo-session-001", "agent_name": "Profiler", "action": "update_from_dialogue", "state": {"user": "demo-student-001"}, "result": {"updated": True}},
    {"session_id": "demo-session-002", "agent_name": "Retriever", "action": "hybrid_search", "state": {"query": "HTTP IP"}, "result": {"docs": 3, "misconceptions": 1}},
    {"session_id": "demo-session-002", "agent_name": "Diagnosis", "action": "three_layer_diagnosis", "state": {"message": "HTTP直接基于IP"}, "result": MOCK_DIAGNOSES[2]},
    {"session_id": "demo-session-002", "agent_name": "PathPlanner", "action": "plan", "state": {"user": "demo-student-002"}, "result": {"nodes": 5}},
    {"session_id": "demo-session-003", "agent_name": "Diagnosis", "action": "three_layer_diagnosis", "state": {"message": "拥塞控制四阶段"}, "result": {"is_correct": True}},
]


def _now(offset_hours: int = 0) -> str:
    return (datetime.now() + timedelta(hours=offset_hours)).isoformat(sep=" ", timespec="seconds")


def reset_demo_data(db):
    """清空演示数据（仅演示相关记录）。"""
    db.query(AgentLog).filter(AgentLog.session_id.like("demo-session-%")).delete()
    db.query(ChatSession).filter(ChatSession.session_id.like("demo-session-%")).delete()
    db.query(StudentProfile).filter(StudentProfile.user_id.like("demo-student-%")).delete()
    db.query(LearningPath).filter(LearningPath.user_id.like("demo-student-%")).delete()
    db.query(LearningPathNode).filter(LearningPathNode.path_id.like("demo-path-%")).delete()
    db.query(User).filter(User.id.like("demo-student-%")).delete()
    db.commit()
    print("[Reset] 演示数据已清空")


def seed_demo_data(db):
    """创建预置演示数据。"""
    # 1. 创建演示用户
    for user in DEMO_USERS:
        exists = db.query(User).filter(User.id == user["id"]).first()
        if not exists:
            db.add(User(id=user["id"], username=user["username"]))
    db.flush()

    # 2. 预置画像（3 套不同认知风格）
    for i, profile_data in enumerate(MOCK_PROFILES):
        user_id = DEMO_USERS[i]["id"]
        exists = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
        if not exists:
            db.add(StudentProfile(
                user_id=user_id,
                profile_json=json.dumps(profile_data, ensure_ascii=False),
                update_time=datetime.now(),
            ))
    db.flush()

    # 3. 预置历史对话
    for session_data in DEMO_SESSIONS:
        exists = db.query(ChatSession).filter(ChatSession.session_id == session_data["session_id"]).first()
        if not exists:
            db.add(ChatSession(
                session_id=session_data["session_id"],
                user_id=session_data["user_id"],
                messages=json.dumps(session_data["messages"], ensure_ascii=False),
            ))
    db.flush()

    # 4. 预置 Agent 日志
    for log_data in DEMO_LOGS:
        db.add(AgentLog(
            log_id=str(uuid.uuid4()),
            session_id=log_data["session_id"],
            agent_name=log_data["agent_name"],
            action=log_data["action"],
            state=json.dumps(log_data["state"], ensure_ascii=False),
            result=json.dumps(log_data["result"], ensure_ascii=False, default=str),
            timestamp=datetime.now(),
        ))

    # 5. 预置学习路径（为第一个学生）
    demo_path = dict(MOCK_LEARNING_PATH)
    demo_path["path_id"] = "demo-path-001"
    demo_path["user_id"] = "demo-student-001"
    db.add(LearningPath(
        path_id=demo_path["path_id"],
        user_id=demo_path["user_id"],
        title=demo_path["title"],
        description=demo_path.get("description", ""),
        total_estimated_time=demo_path.get("total_estimated_time", 0),
        plan_json=json.dumps(demo_path, ensure_ascii=False),
    ))
    for idx, node in enumerate(demo_path.get("nodes", []), start=1):
        db.add(LearningPathNode(
            id=f"demo-path-001:{node['node_id']}",
            path_id="demo-path-001",
            node_id=node["node_id"],
            sequence=idx,
            status=node.get("status", "pending"),
            current_mastery=node.get("current_mastery", 0.0),
            recommendation_reason=node.get("recommendation_reason", ""),
        ))

    # 6. 预置资源数据
    all_resources = []
    for res_type, items in MOCK_RESOURCES.items():
        for item in items:
            resource = dict(item)
            resource["resource_id"] = f"demo-res-{res_type}-001"
            resource["knowledge_node_id"] = "kn_005"
            resource["knowledge_point"] = resource.get("knowledge_point", "TCP 三次握手")
            resource["title"] = resource.get("title", f"演示资源-{res_type}")
            resource["content"] = resource.get("content", "")
            resource["metadata_json"] = json.dumps(resource.get("metadata", {}), ensure_ascii=False)
            resource["quality_score"] = 0.85
            all_resources.append(resource)

    for res in all_resources:
        db.merge(LearningResource(
            resource_id=res["resource_id"],
            knowledge_node_id=res.get("knowledge_node_id"),
            knowledge_point=res["knowledge_point"],
            resource_type=res["resource_type"],
            difficulty=res.get("metadata", {}).get("difficulty", 3),
            title=res["title"],
            content=res["content"],
            metadata_json=res.get("metadata_json", "{}"),
            quality_score=res.get("quality_score", 0.75),
        ))

    db.commit()


def print_summary(db):
    """打印演示数据摘要。"""
    print("\n" + "=" * 60)
    print("  Socrates-Cube 演示环境预热完成")
    print("=" * 60)

    user_count = db.query(User).filter(User.id.like("demo-student-%")).count()
    profile_count = db.query(StudentProfile).filter(StudentProfile.user_id.like("demo-student-%")).count()
    session_count = db.query(ChatSession).filter(ChatSession.session_id.like("demo-session-%")).count()
    log_count = db.query(AgentLog).filter(AgentLog.session_id.like("demo-session-%")).count()
    path_count = db.query(LearningPath).filter(LearningPath.user_id.like("demo-student-%")).count()
    resource_count = db.query(LearningResource).filter(LearningResource.resource_id.like("demo-res-%")).count()

    print(f"  演示账号:    {user_count} 个")
    for user in DEMO_USERS:
        print(f"    - {user['username']} ({user['id']})")
    print(f"  学生画像:    {profile_count} 套")
    print(f"  历史对话:    {session_count} 个会话")
    print(f"  Agent 日志:  {log_count} 条")
    print(f"  学习路径:    {path_count} 条")
    print(f"  演示资源:    {resource_count} 条")
    print("=" * 60)
    print("\n演示账号说明:")
    print("  demo-student-001 (初学者-小王): 认知风格=visual, 进度=低, 适合演示诊断+仿真")
    print("  demo-student-002 (进阶-小李):   认知风格=practical, 进度=中, 适合演示路径+资源")
    print("  demo-student-003 (高手-小张):   认知风格=textual, 进度=高, 适合演示Challenger")
    print()


def main():
    parser = argparse.ArgumentParser(description="Socrates-Cube 演示环境一键预热")
    parser.add_argument("--mock-mode", action="store_true", help="使用 Mock 模式（不依赖 LLM API）")
    parser.add_argument("--reset", action="store_true", help="清空并重建演示数据")
    args = parser.parse_args()

    if args.mock_mode:
        os.environ["MOCK_MODE"] = "true"
        print("[Mode] Mock 模式已启用（离线演示）")
    else:
        print("[Mode] 正常模式")

    # 确保数据库已初始化
    print("[1/3] 初始化数据库...")
    init_db()

    db = SessionLocal()
    try:
        if args.reset:
            print("[2/3] 清空旧演示数据...")
            reset_demo_data(db)

        print("[3/3] 创建预置演示数据...")
        seed_demo_data(db)

        print_summary(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
