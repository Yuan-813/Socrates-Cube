"""AI 欢迎中心 / 冷启动画像引导 API。

新用户首次进入时，通过多步引导收集背景信息，调用 ProfilerAgent.extract_profile
生成初始8维画像，并标记 onboarded=True。
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..agent.profiler import ProfilerAgent
from ..core.llm_client import llm_client
from ..db.repositories import ProfileRepository, UserRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])

_profiler = ProfilerAgent()
_ONBOARDING_PROMPT_PATH = Path("config/prompts/profiler/onboarding.txt")

_ONBOARDING_QUESTIONS = [
    {
        "id": "identity",
        "question": "你的身份是？",
        "type": "single_choice",
        "options": [
            {"value": "student_undergrad", "label": "在校本科生", "icon": "🎓"},
            {"value": "student_grad", "label": "在校研究生", "icon": "📚"},
            {"value": "self_learner", "label": "自学备考", "icon": "💡"},
            {"value": "professional", "label": "在职工程师", "icon": "💼"},
        ],
    },
    {
        "id": "goal",
        "question": "你的学习目标是？",
        "type": "multi_choice",
        "options": [
            {"value": "exam", "label": "期末考试", "icon": "📝"},
            {"value": "hcia", "label": "华为HCIA认证", "icon": "🏅"},
            {"value": "ccna", "label": "思科CCNA认证", "icon": "🌐"},
            {"value": "job", "label": "求职备战", "icon": "🏢"},
            {"value": "interest", "label": "兴趣学习", "icon": "🔍"},
        ],
    },
    {
        "id": "level",
        "question": "你目前的网络基础如何？",
        "type": "single_choice",
        "options": [
            {"value": "zero", "label": "零基础，完全新手", "icon": "🌱"},
            {"value": "basic", "label": "了解一些基础概念", "icon": "🌿"},
            {"value": "intermediate", "label": "学过但不够深入", "icon": "🌳"},
            {"value": "advanced", "label": "有实际工作经验", "icon": "🌲"},
        ],
    },
    {
        "id": "target_job",
        "question": "你希望从事或提升哪个方向？",
        "type": "single_choice",
        "options": [
            {"value": "network_engineer", "label": "网络工程师", "icon": "🔌"},
            {"value": "cloud_engineer", "label": "云计算工程师", "icon": "☁️"},
            {"value": "security_engineer", "label": "网络安全工程师", "icon": "🛡️"},
            {"value": "developer", "label": "后端/全栈开发", "icon": "💻"},
            {"value": "other", "label": "其他/暂未确定", "icon": "🎯"},
        ],
    },
    {
        "id": "learning_style",
        "question": "你更喜欢哪种学习方式？",
        "type": "single_choice",
        "options": [
            {"value": "visual", "label": "图表、动画和视频", "icon": "🎬"},
            {"value": "practical", "label": "动手实验和代码", "icon": "⌨️"},
            {"value": "textual", "label": "文字讲解和书本", "icon": "📖"},
            {"value": "mixed", "label": "多种方式结合", "icon": "🔀"},
        ],
    },
]


class OnboardingSubmitRequest(BaseModel):
    user_id: str = Field(default="student-001")
    answers: dict = Field(..., description="问卷答案字典，key=问题ID，value=选项value")


@router.get("/questions")
def get_onboarding_questions():
    """获取引导问卷题目列表。"""
    return {
        "questions": _ONBOARDING_QUESTIONS,
        "total": len(_ONBOARDING_QUESTIONS),
    }


@router.get("/status/{user_id}")
def get_onboarding_status(user_id: str):
    """查询用户是否已完成引导。"""
    profile = ProfileRepository.get(user_id) or {}
    onboarded = profile.get("onboarded", False)
    return {
        "user_id": user_id,
        "onboarded": onboarded,
        "persona_id": profile.get("persona_id", "professor"),
    }


# 差异化摸底题库（按角色分组）
_ROLE_QUESTIONS: dict[str, list[dict]] = {
    "student": [
        {
            "id": "q1",
            "question": "TCP的三次握手过程中，客户端首先发送的是？",
            "type": "choice",
            "options": [{"value": "A", "label": "SYN"}, {"value": "B", "label": "ACK"}, {"value": "C", "label": "FIN"}, {"value": "D", "label": "RST"}],
            "correct": "A",
            "knowledge_node": "kp_014",
        },
        {
            "id": "q2",
            "question": "OSI模型中，负责路由选择的层是？",
            "type": "choice",
            "options": [{"value": "A", "label": "物理层"}, {"value": "B", "label": "数据链路层"}, {"value": "C", "label": "网络层"}, {"value": "D", "label": "传输层"}],
            "correct": "C",
            "knowledge_node": "kp_007",
        },
        {
            "id": "q3",
            "question": "IP地址192.168.1.0/24的子网掩码是？",
            "type": "choice",
            "options": [{"value": "A", "label": "255.255.255.0"}, {"value": "B", "label": "255.255.0.0"}, {"value": "C", "label": "255.0.0.0"}, {"value": "D", "label": "255.255.255.128"}],
            "correct": "A",
            "knowledge_node": "kp_008",
        },
    ],
    "professional": [
        {
            "id": "q1",
            "question": "OSPF协议中，DR（指定路由器）的选举依据是？",
            "type": "choice",
            "options": [{"value": "A", "label": "路由器ID最大"}, {"value": "B", "label": "接口优先级最高（相同时比Route-ID）"}, {"value": "C", "label": "跟计数最小"}, {"value": "D", "label": "启动时间最早"}],
            "correct": "B",
            "knowledge_node": "kp_010",
        },
        {
            "id": "q2",
            "question": "TCP拥塑控制中，收到三个重复ACK时触发？",
            "type": "choice",
            "options": [{"value": "A", "label": "慢启动"}, {"value": "B", "label": "拥塑避免"}, {"value": "C", "label": "快递重传+快速恢复"}, {"value": "D", "label": "超时重传"}],
            "correct": "C",
            "knowledge_node": "kp_015",
        },
        {
            "id": "q3",
            "question": "BGP使用哪个传输层协议？",
            "type": "choice",
            "options": [{"value": "A", "label": "UDP 179"}, {"value": "B", "label": "TCP 179"}, {"value": "C", "label": "UDP 520"}, {"value": "D", "label": "TCP 520"}],
            "correct": "B",
            "knowledge_node": "kp_010",
        },
    ],
    "self_learner": [
        {
            "id": "q1",
            "question": "HTTP和HTTPS的主要区别是？",
            "type": "choice",
            "options": [{"value": "A", "label": "HTTPS通过TLS加密"}, {"value": "B", "label": "HTTPS速度更快"}, {"value": "C", "label": "HTTP已被废弃"}, {"value": "D", "label": "二者没有区别"}],
            "correct": "A",
            "knowledge_node": "kp_018",
        },
        {
            "id": "q2",
            "question": "DNS的主要作用是？",
            "type": "choice",
            "options": [{"value": "A", "label": "加密数据"}, {"value": "B", "label": "将域名解析为IP地址"}, {"value": "C", "label": "路由选择"}, {"value": "D", "label": "流量控制"}],
            "correct": "B",
            "knowledge_node": "kp_017",
        },
        {
            "id": "q3",
            "question": "TCP和UDP最主要的区别是？",
            "type": "choice",
            "options": [{"value": "A", "label": "TCP通信速度更快"}, {"value": "B", "label": "TCP提供可靠传输，UDP不可靠"}, {"value": "C", "label": "UDP优先于文件传输"}, {"value": "D", "label": "二者使用不同的IP版本"}],
            "correct": "B",
            "knowledge_node": "kp_012",
        },
    ],
    "teacher": [
        {
            "id": "q1",
            "question": "TCP拥塑控制的四个阶段是？",
            "type": "short_answer",
            "sample_answer": "慢启动、拥塑避免、快重传、快速恢复",
            "knowledge_node": "kp_015",
        },
        {
            "id": "q2",
            "question": "请解释CIDR表示法中/26表示可用主机数量。",
            "type": "short_answer",
            "sample_answer": "/26表示剤26位网络位，6位主机位，可用主机数=2^6-2=62",
            "knowledge_node": "kp_008",
        },
        {
            "id": "q3",
            "question": "ARP和DNS各在哪个层工作？各负责什么？",
            "type": "short_answer",
            "sample_answer": "ARP在网络层，将IP解析为MAC地址。DNS在应用层，将域名解析为IP地址。",
            "knowledge_node": "kp_009",
        },
    ],
}


@router.post("/submit/{user_id}")
def submit_onboarding(user_id: str, req: OnboardingSubmitRequest):
    """提交引导问卷，生成初始化8维画像。

    1. 将答案转换为自然语言描述
    2. 调用 onboarding.txt prompt 生成初始画像
    3. 标记 onboarded=True
    4. 返回初始画像和推荐起始节点
    """
    # 构建用户信息描述
    answers = req.answers
    identity_map = {
        "student_undergrad": "在校本科生",
        "student_grad": "在校研究生",
        "self_learner": "自学备考者",
        "professional": "在职工程师",
    }
    level_map = {
        "zero": "零基础，完全新手",
        "basic": "了解基础概念",
        "intermediate": "学过但不够深入",
        "advanced": "有实际工作经验",
    }
    job_map = {
        "network_engineer": "网络工程师",
        "cloud_engineer": "云计算工程师",
        "security_engineer": "网络安全工程师",
        "developer": "后端/全栈开发者",
        "other": "未确定方向",
    }
    style_map = {
        "visual": "视觉型（喜欢图表和视频）",
        "practical": "实践型（喜欢动手实验）",
        "textual": "文本型（喜欢文字讲解）",
        "mixed": "混合型",
    }
    goal_labels = {
        "exam": "期末考试",
        "hcia": "华为HCIA认证",
        "ccna": "思科CCNA认证",
        "job": "求职备战",
        "interest": "兴趣学习",
    }

    identity = identity_map.get(answers.get("identity", ""), answers.get("identity", ""))
    level = level_map.get(answers.get("level", ""), answers.get("level", ""))
    target_job = job_map.get(answers.get("target_job", ""), answers.get("target_job", ""))
    style = style_map.get(answers.get("learning_style", ""), answers.get("learning_style", ""))

    raw_goals = answers.get("goal", [])
    if isinstance(raw_goals, str):
        raw_goals = [raw_goals]
    goals_text = "、".join(goal_labels.get(g, g) for g in raw_goals) or "未指定"

    user_info = (
        f"身份：{identity}\n"
        f"网络基础：{level}\n"
        f"目标：{goals_text}\n"
        f"目标岗位：{target_job}\n"
        f"学习风格：{style}"
    )

    # 调用 LLM 生成初始画像
    prompt_template = ""
    if _ONBOARDING_PROMPT_PATH.exists():
        prompt_template = _ONBOARDING_PROMPT_PATH.read_text(encoding="utf-8")

    if prompt_template:
        prompt = prompt_template.replace("{user_info}", user_info)
    else:
        prompt = (
            f"请根据以下用户信息，生成计算机网络学习的8维初始画像JSON：\n{user_info}\n"
            "返回JSON含维度分数(0.1-1.0)、cognitive_style、learning_goals、target_job、recommended_start_nodes"
        )

    initial_profile: dict = {}
    try:
        raw = llm_client.chat(prompt, max_tokens=600)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            initial_profile = json.loads(raw[start:end])
    except Exception as exc:
        logger.warning("[Onboarding] LLM profile generation failed: %s", exc)

    # 确保基础字段存在
    dimensions = [
        "conceptual_understanding", "protocol_analysis", "calculation_ability",
        "error_diagnosis", "system_design", "knowledge_connection",
        "expression_clarity", "self_correction",
    ]
    level_scores = {"zero": 0.25, "basic": 0.4, "intermediate": 0.55, "advanced": 0.7}
    default_score = level_scores.get(answers.get("level", "basic"), 0.4)
    for dim in dimensions:
        if dim not in initial_profile or not isinstance(initial_profile.get(dim), (int, float)):
            initial_profile[dim] = default_score

    if "cognitive_style" not in initial_profile:
        style_value = answers.get("learning_style", "textual")
        initial_profile["cognitive_style"] = style_value if style_value != "mixed" else "textual"

    initial_profile["onboarded"] = True
    initial_profile["target_job"] = target_job
    initial_profile["learning_goals"] = raw_goals
    initial_profile["mastery_map"] = {}
    initial_profile["weak_points"] = []
    initial_profile["strong_points"] = []
    initial_profile["turn_count"] = 0

    # 确保用户存在并保存画像
    try:
        UserRepository.get_or_create(user_id)
    except Exception:
        pass
    ProfileRepository.upsert(user_id, initial_profile)

    logger.info("[Onboarding] 用户 %s 完成引导初始化", user_id)
    return {
        "status": "ok",
        "user_id": user_id,
        "onboarded": True,
        "initial_profile": {dim: initial_profile.get(dim, default_score) for dim in dimensions},
        "cognitive_style": initial_profile.get("cognitive_style", "textual"),
        "target_job": target_job,
        "recommended_start_nodes": initial_profile.get("recommended_start_nodes", ["kp_001", "kp_002"]),
        "message": f"欢迎！已为你生成专属的计算机网络学习画像，推荐从基础概念开始学习。",
    }


@router.get("/role-questions")
def get_role_questions(role: str = "student"):
    """按角色返回差异化摸底题。

    role 将 identity 类型映射：
    - student_undergrad / student_grad → student 题库
    - professional → professional 题库
    - self_learner → self_learner 题库
    - teacher → teacher 题库
    """
    # 映射 identity 到题库键
    role_key_map = {
        "student_undergrad": "student",
        "student_grad": "student",
        "student": "student",
        "professional": "professional",
        "self_learner": "self_learner",
        "teacher": "teacher",
    }
    key = role_key_map.get(role, "student")
    questions = _ROLE_QUESTIONS.get(key, _ROLE_QUESTIONS["student"])
    # 返回不含答案的题目（压隙 correct/sample_answer 字段）
    public_questions = []
    for q in questions:
        pq = {k: v for k, v in q.items() if k not in ("correct", "sample_answer")}
        public_questions.append(pq)
    return {
        "role": role,
        "role_key": key,
        "total": len(public_questions),
        "questions": public_questions,
    }


@router.post("/role-questions/submit")
def submit_role_questions(role: str, answers: dict):
    """提交摸底题答案，返回评分和和初始知识层次评估。"""
    role_key_map = {
        "student_undergrad": "student", "student_grad": "student", "student": "student",
        "professional": "professional", "self_learner": "self_learner", "teacher": "teacher",
    }
    key = role_key_map.get(role, "student")
    questions = _ROLE_QUESTIONS.get(key, [])

    correct_count = 0
    result_items = []
    for q in questions:
        q_id = q["id"]
        user_ans = str(answers.get(q_id, "")).strip().upper()
        correct_ans = str(q.get("correct", "")).strip().upper()
        is_correct = user_ans == correct_ans if q.get("type") == "choice" else None
        if is_correct:
            correct_count += 1
        result_items.append({
            "id": q_id,
            "is_correct": is_correct,
            "correct_answer": correct_ans or q.get("sample_answer", ""),
            "knowledge_node": q.get("knowledge_node", ""),
        })

    total_choice = sum(1 for q in questions if q.get("type") == "choice")
    score = round(correct_count / max(total_choice, 1) * 100, 1)

    # 根据得分推断知识层次
    if score >= 80:
        estimated_level = "intermediate"
        msg = "基础把握较好，建议直接从进阶内容开始"
    elif score >= 50:
        estimated_level = "basic"
        msg = "有一定基础，建议系统学习详细原理"
    else:
        estimated_level = "zero"
        msg = "建议从基础概念开始学习"

    return {
        "role": role,
        "score": score,
        "correct_count": correct_count,
        "total_questions": total_choice,
        "estimated_level": estimated_level,
        "message": msg,
        "results": result_items,
    }
