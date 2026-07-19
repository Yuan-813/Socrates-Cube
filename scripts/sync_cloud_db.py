#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_cloud_db.py
把知识图谱 (data/knowledge_graph.json) 中 20 个 kp_xxx 节点完整同步到云端数据库，
同时补全 3 个演示账号的 mastery_map / 学习路径 / 评估记录 / 误区记录。

运行：
    .venv/Scripts/python.exe scripts/sync_cloud_db.py
"""
from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.loopse.db.connection import SessionLocal, init_db
from src.loopse.db.models import (
    AgentLog, AssessmentRecord, ChatSession,
    KnowledgeNodeRecord, LearningPath, LearningPathNode,
    MisconceptionRecord, StudentProfile, User,
)

# ─────────────────────────────────────────────────────────
# 0. 工具函数
# ─────────────────────────────────────────────────────────
def _now(offset_days: int = 0) -> datetime:
    return datetime.now() + timedelta(days=offset_days)


# ─────────────────────────────────────────────────────────
# 1. 从知识图谱同步 kp_xxx 节点（20 个）
# ─────────────────────────────────────────────────────────
def sync_knowledge_nodes(session) -> int:
    kg_path = ROOT / "data" / "knowledge_graph.json"
    kg = json.loads(kg_path.read_text(encoding="utf-8"))

    # 构建前置依赖映射
    predecessors: dict[str, list[str]] = {}
    for edge in kg.get("edges", []):
        if edge.get("relation") == "prerequisite":
            predecessors.setdefault(edge["to"], []).append(edge["from"])

    count = 0
    for node in kg["nodes"]:
        obj = KnowledgeNodeRecord(
            node_id=node["id"],
            name=node["name"],
            chapter=node["chapter"],
            node_type=node["type"],
            difficulty=node.get("difficulty", 3),
            estimated_time=node.get("estimated_time", 30),
            keywords_json=json.dumps(node.get("keywords", []), ensure_ascii=False),
            description=node.get("description", ""),
            prerequisite_ids_json=json.dumps(predecessors.get(node["id"], []), ensure_ascii=False),
        )
        session.merge(obj)
        count += 1

    session.commit()
    print(f"  knowledge_nodes: {count} 个 kp_xxx 节点已同步 [OK]")
    return count


# ─────────────────────────────────────────────────────────
# 2. 演示账号定义（profile.mastery_map 使用 kp_xxx）
# ─────────────────────────────────────────────────────────
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
            "mastery_map": {
                "kp_001": 0.60, "kp_002": 0.45, "kp_003": 0.50,
                "kp_011": 0.30, "kp_014": 0.25, "kp_015": 0.20,
            },
            "weak_points": ["kp_014", "kp_015", "kp_010"],
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
            "mastery_map": {
                "kp_001": 0.80, "kp_002": 0.75, "kp_003": 0.72,
                "kp_005": 0.68, "kp_007": 0.65, "kp_011": 0.62,
                "kp_012": 0.70, "kp_013": 0.65, "kp_014": 0.60,
                "kp_015": 0.50,
            },
            "weak_points": ["kp_015", "kp_019"],
            "strong_points": ["kp_001", "kp_003"],
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
            "mastery_map": {
                "kp_001": 0.95, "kp_002": 0.92, "kp_003": 0.90,
                "kp_005": 0.88, "kp_006": 0.85, "kp_007": 0.88,
                "kp_008": 0.82, "kp_009": 0.85, "kp_010": 0.80,
                "kp_011": 0.90, "kp_012": 0.88, "kp_013": 0.85,
                "kp_014": 0.82, "kp_015": 0.80, "kp_016": 0.78,
                "kp_017": 0.85, "kp_018": 0.83, "kp_019": 0.78,
            },
            "weak_points": [],
            "strong_points": ["kp_001", "kp_003", "kp_014", "kp_017"],
            "turn_count": 45,
            "cognitive_style": "textual",
        },
    },
]


def sync_demo_profiles(session) -> None:
    """更新 demo 账号的 student_profile（mastery_map 使用 kp_xxx）"""
    now = _now()
    for acc in DEMO_ACCOUNTS:
        # 确保 user 存在
        session.merge(User(
            id=acc["id"],
            username=acc["username"],
            create_time=_now(-30),
            update_time=now,
        ))
    session.commit()

    for acc in DEMO_ACCOUNTS:
        session.merge(StudentProfile(
            user_id=acc["id"],
            profile_json=json.dumps(acc["profile"], ensure_ascii=False),
            update_time=now,
        ))
    session.commit()
    print(f"  demo profiles: {len(DEMO_ACCOUNTS)} 个账号画像已更新（mastery_map=kp_xxx）[OK]")


# ─────────────────────────────────────────────────────────
# 3. 为 demo 账号创建学习路径
# ─────────────────────────────────────────────────────────
# 每个账号对应的推荐学习路径（节点序列，按前置依赖排序）
DEMO_PATHS = {
    "demo-student-001": {
        "title": "基础入门：网络体系结构 → 运输层",
        "description": "从网络概述出发，逐步掌握OSI、TCP/IP体系结构，再深入运输层协议",
        "nodes": ["kp_001", "kp_002", "kp_003", "kp_011", "kp_012", "kp_013", "kp_014"],
    },
    "demo-student-002": {
        "title": "进阶突破：网络层与传输层深化",
        "description": "已掌握基础，重点强化网络层路由协议、TCP流控与拥塞控制",
        "nodes": ["kp_007", "kp_008", "kp_009", "kp_010", "kp_014", "kp_015"],
    },
    "demo-student-003": {
        "title": "综合提升：应用层与网络安全",
        "description": "强化应用层协议、HTTPS/TLS安全机制及综合故障排查能力",
        "nodes": ["kp_016", "kp_017", "kp_018", "kp_019", "kp_020"],
    },
}


def sync_learning_paths(session) -> None:
    now = _now()
    total_paths = 0
    total_nodes = 0
    for user_id, path_info in DEMO_PATHS.items():
        path_id = f"demo-path-{user_id.split('-')[-1]}"
        estimated = len(path_info["nodes"]) * 40

        session.merge(LearningPath(
            path_id=path_id,
            user_id=user_id,
            title=path_info["title"],
            description=path_info["description"],
            status="active",
            total_estimated_time=estimated,
            plan_json=json.dumps({
                "nodes": path_info["nodes"],
                "source": "PathPlanner",
            }, ensure_ascii=False),
            create_time=_now(-7),
            update_time=now,
        ))
        session.commit()
        total_paths += 1

        for seq, node_id in enumerate(path_info["nodes"]):
            lpn_id = f"{path_id}_{node_id}"
            # 查询该用户对该节点的掌握度
            profile_row = session.query(StudentProfile).filter_by(user_id=user_id).first()
            mastery = 0.0
            if profile_row:
                profile = json.loads(profile_row.profile_json)
                mastery = profile.get("mastery_map", {}).get(node_id, 0.0)

            status = "completed" if mastery >= 0.75 else ("in_progress" if seq == 0 else "pending")

            session.merge(LearningPathNode(
                id=lpn_id,
                path_id=path_id,
                node_id=node_id,
                sequence=seq,
                status=status,
                current_mastery=mastery,
                recommendation_reason=f"基于认知诊断推荐，当前掌握度 {mastery:.0%}",
                create_time=_now(-7),
            ))
            total_nodes += 1

        session.commit()

    print(f"  learning_paths: {total_paths} 条，learning_path_nodes: {total_nodes} 条 [OK]")


# ─────────────────────────────────────────────────────────
# 4. 为 demo 账号创建评估记录和误区记录
# ─────────────────────────────────────────────────────────
ASSESSMENT_DATA = [
    # (user_id, node_id, q_type, score, answer_summary, diagnosis_summary)
    ("demo-student-001", "kp_001", "choice",       80.0, "网络分层的优点", "概念理解基本正确"),
    ("demo-student-001", "kp_002", "choice",       55.0, "OSI七层排序", "混淆了第5/6/7层"),
    ("demo-student-001", "kp_003", "short_answer",  65.0, "TCP/IP四层功能", "传输层功能描述不完整"),
    ("demo-student-001", "kp_014", "choice",       40.0, "三次握手目的", "误认为两次握手足够"),
    ("demo-student-001", "kp_015", "calculation",   35.0, "cwnd计算", "慢启动与拥塞避免阶段混淆"),
    ("demo-student-002", "kp_007", "choice",       75.0, "IP数据报转发", "转发表匹配规则正确"),
    ("demo-student-002", "kp_008", "calculation",   80.0, "子网划分计算", "CIDR计算正确"),
    ("demo-student-002", "kp_010", "short_answer",  70.0, "RIP vs OSPF", "BGP定位有偏差"),
    ("demo-student-002", "kp_014", "choice",       78.0, "四次挥手TIME_WAIT", "TIME_WAIT等待时间理解正确"),
    ("demo-student-002", "kp_015", "calculation",   60.0, "rwnd/cwnd取min", "流量控制与拥塞控制区分不清"),
    ("demo-student-003", "kp_014", "short_answer",  92.0, "三次握手完整分析", "SYN/ACK序号分析准确"),
    ("demo-student-003", "kp_015", "calculation",   88.0, "四阶段拥塞控制", "快恢复阶段cwnd计算正确"),
    ("demo-student-003", "kp_017", "choice",       90.0, "DNS递归vs迭代查询", "流程分析完整"),
    ("demo-student-003", "kp_018", "short_answer",  85.0, "HTTPS握手流程", "TLS证书验证步骤清晰"),
    ("demo-student-003", "kp_019", "choice",       82.0, "NAT对端到端透明性影响", "原理理解准确"),
]

MISCONCEPTION_DATA = [
    # (user_id, node_id, pattern, severity, evidence, intervention)
    ("demo-student-001", "kp_014", "握手次数混淆",
     0.75, "认为TCP两次握手即可建立可靠连接",
     "通过仿真演示历史失效连接问题，引导理解第三次ACK的必要性"),
    ("demo-student-001", "kp_015", "窗口含义混淆",
     0.70, "将滑动窗口等同于拥塞窗口，未区分rwnd和cwnd",
     "对比表格展示rwnd（接收方通告）与cwnd（发送方自适应）的职责差异"),
    ("demo-student-001", "kp_002", "层次归属错误",
     0.60, "混淆OSI第五层（会话层）和第六层（表示层）的功能",
     "通过记忆口诀和功能映射练习加深各层职责印象"),
    ("demo-student-002", "kp_015", "流控拥控概念混淆",
     0.55, "滑动窗口取min时不清楚rwnd和cwnd哪个更主要",
     "实际wireshark抓包案例分析两种控制机制的触发条件"),
    ("demo-student-002", "kp_010", "协议分类错误",
     0.45, "将BGP归类为内部网关协议（IGP）",
     "对比讲解AS（自治系统）概念，区分IGP和EGP的适用边界"),
]


def sync_assessment_and_misconceptions(session) -> None:
    now = _now()

    # 评估记录
    count_a = 0
    for user_id, node_id, q_type, score, answer, diagnosis in ASSESSMENT_DATA:
        obj = AssessmentRecord(
            assessment_id=f"demo-assess-{count_a+1:03d}",
            user_id=user_id,
            knowledge_node_id=node_id,
            question_type=q_type,
            score=score,
            max_score=100.0,
            answer_json=json.dumps({"summary": answer}, ensure_ascii=False),
            diagnosis_json=json.dumps({
                "summary": diagnosis,
                "is_correct": score >= 70,
                "confidence": round(score / 100, 2),
            }, ensure_ascii=False),
            create_time=_now(-3 + count_a % 3),
        )
        session.merge(obj)
        count_a += 1
    session.commit()
    print(f"  assessment_records: {count_a} 条 [OK]")

    # 误区记录
    count_m = 0
    for user_id, node_id, pattern, severity, evidence, intervention in MISCONCEPTION_DATA:
        mc_id = f"demo-mc-{count_m+1:03d}"
        obj = MisconceptionRecord(
            id=mc_id,
            user_id=user_id,
            knowledge_node_id=node_id,
            pattern=pattern,
            severity=severity,
            evidence=evidence,
            intervention=intervention,
            last_seen=_now(-1),
        )
        session.merge(obj)
        count_m += 1
    session.commit()
    print(f"  misconception_records: {count_m} 条 [OK]")


# ─────────────────────────────────────────────────────────
# 5. 补充演示对话（让 chat_sessions 也有 kp_xxx 上下文）
# ─────────────────────────────────────────────────────────
DEMO_SESSIONS = [
    {
        "session_id": "demo-session-001",
        "user_id": "demo-student-001",
        "messages": [
            {"role": "user",      "content": "TCP三次握手为什么不能是两次？"},
            {"role": "assistant", "content": "两次握手无法防止历史失效连接重新激活。第三次ACK让服务端确认客户端真正收到了SYN+ACK，避免资源浪费。"},
            {"role": "user",      "content": "OSI七层从下到上怎么排？"},
            {"role": "assistant", "content": "物理层→数据链路层→网络层→传输层→会话层→表示层→应用层。记忆口诀：物数网传会表应。"},
        ],
    },
    {
        "session_id": "demo-session-002",
        "user_id": "demo-student-002",
        "messages": [
            {"role": "user",      "content": "rwnd和cwnd有什么区别？"},
            {"role": "assistant", "content": "rwnd（接收窗口）由接收方通告，用于流量控制，防止发送方压垮接收方；cwnd（拥塞窗口）由发送方自行维护，用于拥塞控制，避免网络过载。实际发送量取两者最小值。"},
            {"role": "user",      "content": "BGP是内部还是外部网关协议？"},
            {"role": "assistant", "content": "BGP是外部网关协议（EGP），用于自治系统（AS）之间的路由交换。OSPF和RIP才是内部网关协议（IGP）。"},
        ],
    },
    {
        "session_id": "demo-session-003",
        "user_id": "demo-student-003",
        "messages": [
            {"role": "user",      "content": "HTTPS的握手流程是什么？"},
            {"role": "assistant", "content": "TCP三次握手建立连接→客户端发送ClientHello（支持的TLS版本/密码套件）→服务端发送ServerHello+证书→客户端验证证书→协商会话密钥→双方切换为对称加密通信。"},
            {"role": "user",      "content": "DNS用UDP还是TCP？"},
            {"role": "assistant", "content": "通常用UDP（端口53），查询和响应单包可完成。若响应超过512字节（区域传送、DNSSEC等）则切换TCP。"},
        ],
    },
]


def sync_demo_sessions(session) -> None:
    now = _now()
    for s in DEMO_SESSIONS:
        # 为消息加时间戳
        msgs = []
        for i, m in enumerate(s["messages"]):
            msgs.append({**m, "timestamp": _now(-2 + i * 0.1).isoformat()})
        session.merge(ChatSession(
            session_id=s["session_id"],
            user_id=s["user_id"],
            messages=json.dumps(msgs, ensure_ascii=False),
            create_time=_now(-5),
            update_time=now,
        ))
    session.commit()
    print(f"  chat_sessions: {len(DEMO_SESSIONS)} 条演示对话已同步 [OK]")


# ─────────────────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────────────────
def main() -> None:
    print("=== Socrates-Cube 云端数据库同步 ===")
    print("1. 确认并初始化表结构...")
    init_db()
    print("   tables ready [OK]")

    session = SessionLocal()
    try:
        print("2. 同步知识图谱节点（kp_001~kp_020）...")
        sync_knowledge_nodes(session)

        print("3. 更新演示账号画像（mastery_map=kp_xxx）...")
        sync_demo_profiles(session)

        print("4. 创建演示学习路径...")
        sync_learning_paths(session)

        print("5. 创建评估记录与误区记录...")
        sync_assessment_and_misconceptions(session)

        print("6. 同步演示对话记录...")
        sync_demo_sessions(session)

        # 最终统计
        from src.loopse.db.models import AssessmentRecord as AR, MisconceptionRecord as MR
        from sqlalchemy import func
        print("\n=== 同步完成，云端数据统计 ===")
        for model, name in [
            (KnowledgeNodeRecord, "knowledge_nodes"),
            (User, "users"),
            (StudentProfile, "student_profiles"),
            (ChatSession, "chat_sessions"),
            (LearningPath, "learning_paths"),
            (LearningPathNode, "learning_path_nodes"),
            (AR, "assessment_records"),
            (MR, "misconception_records"),
        ]:
            print(f"  {name}: {session.query(model).count()}")

    except Exception as e:
        session.rollback()
        print(f"[ERROR] {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
