"""生成 Socrates-Cube 演示数据库数据（完整版）。

数据规模（可调整 SCALE 参数）：
  SCALE=1 → users:200 / profiles:200 / sessions:600 / agent_logs:3000
           learning_resources:200 / paths:400 / assessments:2000
           misconceptions:1000 / memory_records:400
"""
from __future__ import annotations

import json
import os
import random
import sys
import io
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# 将项目根加入 sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ.setdefault("DATABASE_URL", f"sqlite:///{ROOT}/data/socrates_cube.db")

from src.loopse.db.connection import SessionLocal, init_db
from src.loopse.db.models import (
    AgentLog, AssessmentRecord, Bookmark, ChatSession,
    KnowledgeNodeRecord, LearningPath, LearningPathNode,
    LearningResource, MemoryRecord, MisconceptionRecord,
    StudentProfile, User,
)

SCALE = 1
random.seed(42)


# ─── 工具函数 ──────────────────────────────────────────────────────────────────

def uid() -> str:
    return uuid.uuid4().hex

def rand_dt(days_ago_max=180) -> datetime:
    return datetime.now() - timedelta(
        days=random.randint(0, days_ago_max),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )


# ─── 数据字典 ──────────────────────────────────────────────────────────────────

ROLE_TYPES   = ["student", "student", "student", "professional", "self_learner", "job_seeker"]
MAJOR_FIELDS = ["计算机科学", "软件工程", "网络工程", "信息安全", "电子工程", "数据科学"]
UNIV_NAMES   = ["清华大学", "北京大学", "浙江大学", "复旦大学", "上海交通大学",
                "华中科技大学", "西安交通大学", "哈尔滨工业大学", "中山大学", "同济大学",
                "武汉大学", "南京大学", "四川大学", "东南大学", "北京航空航天大学"]
TARGET_JOBS  = ["网络工程师", "云计算工程师", "网络安全工程师", "DevOps工程师", "后端开发工程师"]
COG_STYLES   = ["visual", "practical", "textual", "analogical"]
WEAK_KPS     = [
    ["kp_013", "kp_014"], ["kp_010", "kp_011"], ["kp_006", "kp_007"],
    ["kp_015", "kp_016"], ["kp_018", "kp_019"], ["kp_008", "kp_012"],
]
AGENT_NAMES  = ["OrchestratorAgent", "DiagnosisAgent", "ProfilerAgent",
                "PathPlannerAgent", "ResourceAgent", "ChallengerAgent",
                "RetrieverAgent", "SimulatorAgent", "CareerNavigatorAgent"]
ACTIONS      = ["dispatch", "diagnose", "extract_profile", "plan",
                "generate_resource", "challenge", "retrieve", "simulate", "gap_analysis"]
PERSONAS     = ["professor", "engineer", "peer", "interviewer"]
RESOURCE_TYPES = ["doc", "exercise", "code", "mindmap", "script"]
MISCONCEPTION_PATTERNS = [
    "flow_omission", "algorithm_confusion", "metric_confusion",
    "layer_confusion", "scope_error", "direction_reversal", "overgeneralization"
]

# 加载知识图谱节点
_kg_path = ROOT / "data" / "knowledge_graph.json"
KG_NODES = []
if _kg_path.exists():
    _kg = json.loads(_kg_path.read_text(encoding="utf-8"))
    KG_NODES = [n for n in _kg.get("nodes", []) if n["id"].startswith("kp_")]


# ─── 1. 生成用户 + 画像 ────────────────────────────────────────────────────────

def gen_users(n: int) -> list[User]:
    users = []
    for i in range(1, n + 1):
        role = random.choice(ROLE_TYPES)
        uid_str = f"user_{i:04d}"
        meta = {
            "university": random.choice(UNIV_NAMES) if role == "student" else None,
            "major": random.choice(MAJOR_FIELDS),
            "grade": random.randint(1, 4) if role == "student" else None,
        }
        users.append(User(
            id=uid_str,
            username=f"learner_{i:04d}",
            email=f"user{i:04d}@socrates.edu",
            role_type=role,
            meta_json=json.dumps(meta, ensure_ascii=False),
            is_first_login=0,
            onboarded=True,
            create_time=rand_dt(180),
        ))
    return users


def gen_profile(user_id: str) -> StudentProfile:
    kp_ids = [n["id"] for n in KG_NODES] if KG_NODES else [f"kp_{i:03d}" for i in range(1, 21)]
    mastery = {kid: round(random.uniform(0.2, 0.95), 2) for kid in kp_ids}
    weak_kps = random.choice(WEAK_KPS)
    for kp in weak_kps:
        mastery[kp] = round(random.uniform(0.1, 0.35), 2)

    profile = {
        "user_id": user_id,
        "learning_style": random.choice(["deep", "strategic", "surface"]),
        "cognitive_style": random.choice(COG_STYLES),
        "knowledge_level": round(random.uniform(0.3, 0.85), 2),
        "mastery_map": mastery,
        "weak_points": weak_kps,
        "target_job": random.choice(TARGET_JOBS),
        "current_persona": random.choice(PERSONAS),
        "total_study_hours": round(random.uniform(10, 300), 1),
        "streak_days": random.randint(0, 60),
    }
    return StudentProfile(
        user_id=user_id,
        profile_json=json.dumps(profile, ensure_ascii=False),
        update_time=rand_dt(30),
    )


# ─── 2. Chat Sessions ──────────────────────────────────────────────────────────

SAMPLE_MESSAGES = [
    {"role": "user", "content": "TCP三次握手为什么不能是两次？"},
    {"role": "assistant", "content": "两次握手无法防止历史失效的SYN请求建立无效连接..."},
    {"role": "user", "content": "那TIME_WAIT状态的意义是什么？"},
    {"role": "assistant", "content": "TIME_WAIT等待2MSL，确保最后一个ACK到达并等待旧连接报文消失..."},
]

def gen_sessions(user_ids: list[str], sessions_per_user: int = 3) -> list[ChatSession]:
    sessions = []
    for uid in user_ids:
        for _ in range(sessions_per_user):
            msg_count = random.randint(4, 16)
            msgs = random.choices(SAMPLE_MESSAGES, k=msg_count)
            sessions.append(ChatSession(
                session_id=uid16(),
                user_id=uid,
                messages=json.dumps(msgs, ensure_ascii=False),
                create_time=rand_dt(60),
            ))
    return sessions


def uid16() -> str:
    return uuid.uuid4().hex[:16]


# ─── 3. Agent Logs ────────────────────────────────────────────────────────────

def gen_agent_logs(session_ids: list[str], logs_per_session: int = 5) -> list[AgentLog]:
    logs = []
    for sid in session_ids:
        for _ in range(logs_per_session):
            agent = random.choice(AGENT_NAMES)
            action = random.choice(ACTIONS)
            logs.append(AgentLog(
                log_id=uid16(),
                session_id=sid,
                agent_name=agent,
                action=action,
                state=json.dumps({"intent": random.choice(["explain", "diagnose", "challenge", "plan"])}, ensure_ascii=False),
                timestamp=rand_dt(60),
                result=json.dumps({"status": "success", "latency_ms": random.randint(50, 800)}, ensure_ascii=False),
            ))
    return logs


# ─── 4. Knowledge Nodes ───────────────────────────────────────────────────────

def gen_knowledge_nodes() -> list[KnowledgeNodeRecord]:
    if not KG_NODES:
        return []
    records = []
    for node in KG_NODES:
        records.append(KnowledgeNodeRecord(
            node_id=node["id"],
            name=node["name"],
            chapter=node.get("chapter", "未分类"),
            node_type=node.get("type", "concept"),
            difficulty=node.get("difficulty", 3),
            estimated_time=node.get("estimated_time", 30),
            keywords_json=json.dumps(node.get("keywords", []), ensure_ascii=False),
            description=node.get("description", ""),
            prerequisite_ids_json=json.dumps([], ensure_ascii=False),
            create_time=datetime.now(),
        ))
    return records


# ─── 5. Learning Resources ────────────────────────────────────────────────────

RESOURCE_TITLES = {
    "doc": ["{}原理详解", "{}深度解析", "{}完全指南", "{}从入门到精通"],
    "exercise": ["{}经典习题集", "{}综合练习", "{}强化训练", "{}考点精练"],
    "code": ["{}代码实现", "{}编程实战", "{}实验代码", "{}动手实践"],
    "mindmap": ["{}知识图谱", "{}思维导图", "{}概念网络", "{}知识框架"],
    "script": ["{}视频讲解脚本", "{}教学视频大纲", "{}动画演示脚本", "{}课程录制稿"],
}

KP_NAMES = [n["name"] for n in KG_NODES] if KG_NODES else ["TCP协议", "HTTP协议", "OSPF路由", "VLAN技术"]

def gen_resources(n: int = 200) -> list[LearningResource]:
    resources = []
    for _ in range(n):
        rtype = random.choice(RESOURCE_TYPES)
        kp_name = random.choice(KP_NAMES)
        title_tpl = random.choice(RESOURCE_TITLES.get(rtype, ["{}教程"]))
        title = title_tpl.format(kp_name)
        node = random.choice(KG_NODES) if KG_NODES else None
        resources.append(LearningResource(
            resource_id=uid16(),
            knowledge_node_id=node["id"] if node else None,
            knowledge_point=kp_name,
            resource_type=rtype,
            difficulty=random.randint(1, 5),
            title=title,
            content=f"本资源围绕{kp_name}展开，涵盖核心概念、工作原理与常见误解纠正。",
            metadata_json=json.dumps({"source": "AI生成", "version": "2.0"}, ensure_ascii=False),
            quality_score=round(random.uniform(0.65, 0.98), 2),
            create_time=rand_dt(90),
        ))
    return resources


# ─── 6. Learning Paths ────────────────────────────────────────────────────────

def gen_paths(user_ids: list[str], paths_per_user: int = 2) -> tuple[list[LearningPath], list[LearningPathNode]]:
    paths, nodes = [], []
    kp_ids = [n["id"] for n in KG_NODES] if KG_NODES else [f"kp_{i:03d}" for i in range(1, 10)]
    for uid in user_ids:
        for k in range(paths_per_user):
            pid = uid16()
            target = random.choice(TARGET_JOBS)
            path = LearningPath(
                path_id=pid,
                user_id=uid,
                title=f"{target}成长路径 #{k+1}",
                description=f"为{target}方向定制的个性化学习路径",
                status=random.choice(["active", "active", "completed", "paused"]),
                total_estimated_time=random.randint(600, 3600),
                plan_json=json.dumps({"target_job": target}, ensure_ascii=False),
                create_time=rand_dt(90),
            )
            paths.append(path)
            # 路径节点（每条路径4-8个节点）
            selected_kps = random.sample(kp_ids, min(random.randint(4, 8), len(kp_ids)))
            for seq, kp in enumerate(selected_kps):
                nodes.append(LearningPathNode(
                    id=f"{pid}_{seq}",
                    path_id=pid,
                    node_id=kp,
                    sequence=seq,
                    status=random.choice(["completed", "in_progress", "pending"]),
                    current_mastery=round(random.uniform(0.1, 0.95), 2),
                    recommendation_reason="基于GAP分析与个人画像推荐",
                    create_time=rand_dt(90),
                ))
    return paths, nodes


# ─── 7. Assessment Records ────────────────────────────────────────────────────

QUESTION_TYPES = ["single_choice", "multi_choice", "open_question", "true_false"]

def gen_assessments(user_ids: list[str], count_per_user: int = 10) -> list[AssessmentRecord]:
    records = []
    kp_ids = [n["id"] for n in KG_NODES] if KG_NODES else [f"kp_{i:03d}" for i in range(1, 21)]
    for uid in user_ids:
        for _ in range(count_per_user):
            score = round(random.uniform(30, 100), 1)
            records.append(AssessmentRecord(
                assessment_id=uid16(),
                user_id=uid,
                knowledge_node_id=random.choice(kp_ids),
                question_type=random.choice(QUESTION_TYPES),
                score=score,
                max_score=100.0,
                answer_json=json.dumps({"answer": "用户回答内容"}, ensure_ascii=False),
                diagnosis_json=json.dumps({
                    "is_correct": score >= 60,
                    "pattern": random.choice(MISCONCEPTION_PATTERNS),
                }, ensure_ascii=False),
                create_time=rand_dt(120),
            ))
    return records


# ─── 8. Misconception Records ──────────────────────────────────────────────────

def gen_misconceptions(user_ids: list[str], count_per_user: int = 5) -> list[MisconceptionRecord]:
    records = []
    kp_ids = [n["id"] for n in KG_NODES] if KG_NODES else [f"kp_{i:03d}" for i in range(1, 21)]
    seen = set()
    for uid in user_ids:
        user_kps = random.sample(kp_ids, min(count_per_user, len(kp_ids)))
        for kp in user_kps:
            pattern = random.choice(MISCONCEPTION_PATTERNS)
            key = (uid, kp, pattern)
            if key in seen:
                continue
            seen.add(key)
            records.append(MisconceptionRecord(
                id=uid16(),
                user_id=uid,
                knowledge_node_id=kp,
                pattern=pattern,
                severity=round(random.uniform(0.2, 0.9), 2),
                evidence="基于多轮对话诊断记录",
                intervention=f"建议通过仿真场景与对比练习纠正{pattern}类误解",
                last_seen=rand_dt(30),
            ))
    return records


# ─── 9. Memory Records ─────────────────────────────────────────────────────────

MEMORY_CONTENTS = [
    "用户倾向于使用类比方式理解协议栈，适合用生活场景举例。",
    "用户对TCP可靠性机制理解较弱，历史诊断多次发现flow_omission误解。",
    "用户目标是华为HCIA认证，学习动力强，需要多出实际配置题。",
    "用户喜欢短问题频繁交互，不喜欢长篇文字解释。",
    "本次会话重点纠正了用户对NAT与防火墙功能混淆的误解。",
]

def gen_memory_records(user_ids: list[str], count_per_user: int = 2) -> list[MemoryRecord]:
    records = []
    for uid in user_ids:
        for _ in range(count_per_user):
            records.append(MemoryRecord(
                id=uid16(),
                user_id=uid,
                persona=random.choice(PERSONAS),
                memory_type=random.choice(["long_term", "session_summary", "preference"]),
                content=random.choice(MEMORY_CONTENTS),
                created_at=rand_dt(60),
            ))
    return records


# ─── 主程序 ────────────────────────────────────────────────────────────────────

def main():
    print("初始化数据库...")
    init_db()

    db = SessionLocal()
    try:
        n_users = 200 * SCALE

        # 检查是否已有数据
        existing = db.query(User).count()
        if existing >= n_users:
            print(f"数据库已有 {existing} 个用户，跳过生成。如需重新生成请先清空数据库。")
            return

        print(f"生成 {n_users} 个用户 + 画像...")
        users = gen_users(n_users)
        for u in users:
            db.merge(u)
        db.flush()

        profiles = [gen_profile(u.id) for u in users]
        for p in profiles:
            db.merge(p)
        db.flush()
        print(f"  ✓ {len(users)} 用户 + {len(profiles)} 画像")

        # Chat sessions
        user_ids = [u.id for u in users]
        sessions = gen_sessions(user_ids, 3)
        for s in sessions:
            db.merge(s)
        db.flush()
        print(f"  ✓ {len(sessions)} 对话会话")

        # Agent logs
        session_ids = [s.session_id for s in sessions]
        logs = gen_agent_logs(session_ids, 5)
        for l in logs:
            db.merge(l)
        db.flush()
        print(f"  ✓ {len(logs)} Agent日志")

        # Knowledge nodes
        kn_records = gen_knowledge_nodes()
        for r in kn_records:
            db.merge(r)
        db.flush()
        print(f"  ✓ {len(kn_records)} 知识节点记录")

        # Learning resources
        resources = gen_resources(200)
        for r in resources:
            db.merge(r)
        db.flush()
        print(f"  ✓ {len(resources)} 学习资源")

        # Learning paths
        paths, path_nodes = gen_paths(user_ids, 2)
        for p in paths:
            db.merge(p)
        db.flush()
        for pn in path_nodes:
            db.merge(pn)
        db.flush()
        print(f"  ✓ {len(paths)} 学习路径 + {len(path_nodes)} 路径节点")

        # Assessment records
        assessments = gen_assessments(user_ids, 10)
        for a in assessments:
            db.merge(a)
        db.flush()
        print(f"  ✓ {len(assessments)} 学习评估记录")

        # Misconception records
        misc_records = gen_misconceptions(user_ids, 5)
        for m in misc_records:
            db.merge(m)
        db.flush()
        print(f"  ✓ {len(misc_records)} 误解记录")

        # Memory records
        memory_records = gen_memory_records(user_ids, 2)
        for m in memory_records:
            db.merge(m)
        db.flush()
        print(f"  ✓ {len(memory_records)} 记忆记录")

        db.commit()
        print("\n数据生成完成！统计如下：")
        print(f"  users:              {db.query(User).count()}")
        print(f"  student_profiles:   {db.query(StudentProfile).count()}")
        print(f"  chat_sessions:      {db.query(ChatSession).count()}")
        print(f"  agent_logs:         {db.query(AgentLog).count()}")
        print(f"  knowledge_nodes:    {db.query(KnowledgeNodeRecord).count()}")
        print(f"  learning_resources: {db.query(LearningResource).count()}")
        print(f"  learning_paths:     {db.query(LearningPath).count()}")
        print(f"  assessment_records: {db.query(AssessmentRecord).count()}")
        print(f"  misconception_records: {db.query(MisconceptionRecord).count()}")
        print(f"  memory_records:     {db.query(MemoryRecord).count()}")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
