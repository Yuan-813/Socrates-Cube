"""误解对抗检验 Agent（Challenger）。

根据三层诊断结果生成针对性检验题，支持自适应多轮追问：
- 答对 → 提升难度或结束并给出理解评估
- 答错 → 降维引导并继续追问（最多 5 轮，至少 2 轮）
"""
from __future__ import annotations

import json
import logging
import random
import re
from pathlib import Path
from typing import Any, Optional

from ..core.llm_client import llm_client
from .cognitive_engine import AwaitableDict, CognitiveAgentMixin

logger = logging.getLogger(__name__)
_PROMPT_DIR = Path("config/prompts/challenger")

# 内置检验题库（LLM 不可用时的兜底）
_FALLBACK_CHALLENGES = [
    {
        "question": "TCP 三次握手中，如果第三次 ACK 丢失，会发生什么？",
        "question_type": "scenario",
        "correct_answer": "服务端会重传 SYN+ACK，客户端仍处于 SYN_SENT，连接未完全建立",
        "distractor_explanation": "误认为服务端发出 SYN+ACK 即算连接建立，忽略了全双工确认",
        "topic": "TCP 三次握手",
    },
    {
        "question": "为什么说「UDP 比 TCP 快」不能仅归因于头部更小？",
        "question_type": "concept",
        "correct_answer": "UDP 无连接、无握手、无拥塞控制与重传，减少状态维护与等待",
        "distractor_explanation": "将速度差异完全归因于头部大小，忽略机制差异",
        "topic": "UDP vs TCP",
    },
    {
        "question": "HTTP 请求在局域网内转发时，数据链路层依据什么地址寻址？",
        "question_type": "analysis",
        "correct_answer": "MAC 地址；需通过 ARP 将目的 IP 解析为 MAC",
        "distractor_explanation": "混淆网络层 IP 寻址与数据链路层 MAC 寻址",
        "topic": "ARP 与 MAC",
    },
]


def _load_prompt(name: str) -> str:
    path = _PROMPT_DIR / name
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


class ChallengerAgent(CognitiveAgentMixin):
    """自适应误解对抗检验 Agent。"""

    MIN_ROUNDS = 2
    MAX_ROUNDS = 5

    def __init__(self):
        self._prompt = _load_prompt("challenge.txt")
        self._sessions: dict[str, dict[str, Any]] = {}

    def should_challenge(
        self,
        diagnosis: dict[str, Any],
        learning_turns: int = 0,
        force: bool = False,
    ) -> bool:
        if force:
            return True
        if not diagnosis.get("is_correct", True):
            return True
        return learning_turns >= 5

    def start_session(
        self,
        session_id: str,
        diagnosis: dict[str, Any],
        profile: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        profile = profile or {}
        challenge = self._generate_challenge(diagnosis, profile, round_num=1)
        state = {
            "round": 1,
            "score": 0,
            "consecutive_correct": 0,
            "history": [],
            "current_challenge": challenge,
            "diagnosis": diagnosis,
            "profile": profile,
            "status": "active",
        }
        self._sessions[session_id] = state
        return self._build_round_payload(session_id, challenge, round_num=1, is_start=True)

    def evaluate_answer(
        self,
        session_id: str,
        user_answer: str,
    ) -> dict[str, Any]:
        state = self._sessions.get(session_id)
        if not state:
            return {"status": "inactive", "message": "当前会话没有进行中的 Challenger 检验"}

        challenge = state["current_challenge"]
        evaluation = self._evaluate_response(challenge, user_answer)
        round_num = state["round"]
        state["history"].append({
            "round": round_num,
            "question": challenge.get("question"),
            "user_answer": user_answer,
            "is_correct": evaluation["is_correct"],
            "feedback": evaluation["feedback"],
        })

        if evaluation["is_correct"]:
            state["score"] += 1
            state["consecutive_correct"] += 1
        else:
            state["consecutive_correct"] = 0

        should_end = self._should_end(state, evaluation["is_correct"])
        if should_end:
            assessment = self._build_assessment(state)
            state["status"] = "completed"
            return {
                "status": "completed",
                "round": round_num,
                "is_correct": evaluation["is_correct"],
                "feedback": evaluation["feedback"],
                "understanding_level": assessment["understanding_level"],
                "understanding_score": assessment["understanding_score"],
                "suggestions": assessment["suggestions"],
                "total_rounds": round_num,
                "correct_count": state["score"],
                "history": state["history"],
            }

        next_round = round_num + 1
        next_challenge = self._generate_challenge(
            state["diagnosis"],
            state["profile"],
            round_num=next_round,
            previous_correct=evaluation["is_correct"],
        )
        state["round"] = next_round
        state["current_challenge"] = next_challenge
        payload = self._build_round_payload(session_id, next_challenge, round_num=next_round)
        payload.update({
            "status": "continue",
            "is_correct": evaluation["is_correct"],
            "feedback": evaluation["feedback"],
            "previous_round": round_num,
        })
        return payload

    def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        return self._sessions.get(session_id)

    def _generate_challenge(
        self,
        diagnosis: dict[str, Any],
        profile: dict[str, Any],
        round_num: int = 1,
        previous_correct: bool = True,
    ) -> dict[str, Any]:
        misconception = diagnosis.get("surface_error") or diagnosis.get("pattern") or "计算机网络概念"
        correct = diagnosis.get("intervention_suggestion") or "参考课程讲义与图谱节点"
        cognitive_style = profile.get("cognitive_style", "textual")

        prompt = self._format_prompt(
            self._prompt,
            {
                "misconception_description": misconception,
                "correct_understanding": correct,
                "cognitive_style": cognitive_style,
                "round_num": str(round_num),
                "difficulty_hint": "提高难度" if previous_correct and round_num > 1 else "基础检验",
            },
            (
                f"针对误解「{misconception}」设计第 {round_num} 轮检验题。"
                f"认知风格：{cognitive_style}。返回 JSON 含 question/question_type/correct_answer/distractor_explanation。"
            ),
        )
        try:
            raw = llm_client.chat(prompt, max_tokens=400)
            data = self._parse_json(raw, {})
            if data.get("question"):
                data.setdefault("topic", diagnosis.get("pattern") or "计算机网络")
                return data
        except Exception as exc:
            logger.warning("[Challenger] LLM challenge generation failed: %s", exc)

        idx = (round_num - 1) % len(_FALLBACK_CHALLENGES)
        fallback = dict(_FALLBACK_CHALLENGES[idx])
        if not previous_correct and round_num > 1:
            fallback["question"] = f"（引导题）{fallback['question']}"
        return fallback

    def _evaluate_response(self, challenge: dict[str, Any], user_answer: str) -> dict[str, Any]:
        answer = (user_answer or "").strip()
        if not answer:
            return {
                "is_correct": False,
                "feedback": "请先给出你的判断或解释，才能评估理解程度。",
            }

        correct_ref = challenge.get("correct_answer", "")
        distractor = challenge.get("distractor_explanation", "")

        # 关键词重叠快速判断
        keywords = [w for w in re.split(r"[\s，。；、]+", correct_ref) if len(w) >= 2]
        hits = sum(1 for kw in keywords[:8] if kw in answer)
        quick_correct = hits >= max(2, len(keywords[:8]) // 3)

        prompt = (
            "你是计算机网络助教，判断学生是否理解了检验题要点。\n"
            f"题目：{challenge.get('question', '')}\n"
            f"参考答案要点：{correct_ref}\n"
            f"常见错误：{distractor}\n"
            f"学生回答：{answer}\n"
            '返回 JSON：{"is_correct": true/false, "feedback": "简短反馈"}'
        )
        try:
            raw = llm_client.chat(prompt, max_tokens=200)
            data = self._parse_json(raw, {})
            if "is_correct" in data:
                return {
                    "is_correct": bool(data["is_correct"]),
                    "feedback": data.get("feedback", "已记录你的回答。"),
                }
        except Exception as exc:
            logger.warning("[Challenger] LLM evaluation failed: %s", exc)

        return {
            "is_correct": quick_correct,
            "feedback": (
                "回答抓住了关键要点，理解较好。"
                if quick_correct
                else f"尚未完全纠正误解。参考：{correct_ref[:120]}"
            ),
        }

    def _should_end(self, state: dict[str, Any], last_correct: bool) -> bool:
        round_num = state["round"]
        if round_num >= self.MAX_ROUNDS:
            return True
        if round_num < self.MIN_ROUNDS:
            return False
        if state["consecutive_correct"] >= 2:
            return True
        if not last_correct and round_num >= 3 and state["score"] == 0:
            return True
        return False

    def _build_assessment(self, state: dict[str, Any]) -> dict[str, Any]:
        total = state["round"]
        score = state["score"]
        ratio = score / max(total, 1)
        if ratio >= 0.8:
            level, suggestions = "良好", ["可以进入变式题或仿真场景巩固", "尝试向同学讲解一次三次握手"]
        elif ratio >= 0.5:
            level, suggestions = "部分理解", ["建议回看诊断指出的根因节点", "用对比表区分易混概念"]
        else:
            level, suggestions = "需加强", [
                "先完成推荐文档与思维导图",
                "通过协议仿真逐步建立流程直觉",
            ]
        return {
            "understanding_level": level,
            "understanding_score": round(ratio * 100),
            "suggestions": suggestions,
        }

    @staticmethod
    def _build_round_payload(
        session_id: str,
        challenge: dict[str, Any],
        round_num: int,
        is_start: bool = False,
    ) -> dict[str, Any]:
        return {
            "status": "active" if is_start else "continue",
            "session_id": session_id,
            "round": round_num,
            "max_rounds": ChallengerAgent.MAX_ROUNDS,
            "question": challenge.get("question", ""),
            "question_type": challenge.get("question_type", "concept"),
            "topic": challenge.get("topic", "计算机网络"),
            "correct_answer_hint": challenge.get("correct_answer", ""),
            "distractor_explanation": challenge.get("distractor_explanation", ""),
        }

    @staticmethod
    def _format_prompt(template: str, mapping: dict[str, str], fallback: str) -> str:
        if not template:
            return fallback
        prompt = template
        for key, value in mapping.items():
            prompt = prompt.replace("{" + key + "}", value)
        return prompt

    @staticmethod
    def _parse_json(raw: str, default: dict[str, Any]) -> dict[str, Any]:
        try:
            text = raw.strip()
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                text = text[start : end + 1]
            return json.loads(text)
        except Exception:
            return default


challenger_agent = ChallengerAgent()


# ─────────────────────────────────────────────────────────────────────────────
# 考试模式（Exam Mode）：基于题库的客观评分
# ─────────────────────────────────────────────────────────────────────────────

_EXAM_DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "certificate_exams.json"
_exam_data: dict = {}


def _load_exam_data() -> dict:
    global _exam_data
    if not _exam_data:
        try:
            _exam_data = json.loads(_EXAM_DATA_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("[ExamMode] 题库加载失败: %s", exc)
            _exam_data = {"exams": {}}
    return _exam_data


def list_exams() -> list[dict]:
    """Returns available exam list."""
    data = _load_exam_data()
    return [
        {
            "exam_id": eid,
            "name": edata["name"],
            "description": edata.get("description", ""),
            "question_count": edata["question_count"],
            "time_limit_minutes": edata.get("time_limit_minutes", 90),
            "pass_score": edata.get("pass_score", 70),
            "cert_node_id": edata.get("cert_node_id"),
        }
        for eid, edata in data.get("exams", {}).items()
    ]


def start_exam_session(
    user_id: str,
    exam_id: str,
    question_count: int = 20,
    weak_kp_ids: list[str] | None = None,
) -> dict:
    """从题库抽取题目并创建考试会话。

    支持基于薄弱点加权抽题。
    """
    data = _load_exam_data()
    exam = data.get("exams", {}).get(exam_id)
    if not exam:
        return {"error": f"未知考试 ID: {exam_id}"}

    all_questions = exam["questions"]
    question_count = min(question_count, len(all_questions))

    # 加权抽题：薄弱知识点对应题目权重 x2
    if weak_kp_ids:
        weighted = []
        for q in all_questions:
            weight = 2 if q.get("kp_node_id") in weak_kp_ids else 1
            weighted.extend([q] * weight)
        selected = random.sample(weighted, min(question_count, len(weighted)))
        # 去重，保持题目无重复
        seen_ids = set()
        questions = []
        for q in selected:
            if q["id"] not in seen_ids:
                seen_ids.add(q["id"])
                questions.append(q)
        if len(questions) < question_count:
            extra = [q for q in all_questions if q["id"] not in seen_ids]
            questions.extend(random.sample(extra, min(question_count - len(questions), len(extra))))
    else:
        questions = random.sample(all_questions, question_count)

    # 存入会话，使用 challenger_agent._sessions 统一管理
    import uuid
    session_id = f"exam_{uuid.uuid4().hex[:12]}"
    exam_state = {
        "session_id": session_id,
        "exam_id": exam_id,
        "exam_name": exam["name"],
        "user_id": user_id,
        "questions": questions,
        "answers": {},
        "status": "active",
        "time_limit_minutes": exam.get("time_limit_minutes", 90),
        "pass_score": exam.get("pass_score", 70),
    }
    challenger_agent._sessions[session_id] = exam_state

    # 返回题目列表（不含答案）
    public_questions = []
    for i, q in enumerate(questions, 1):
        pq = {
            "index": i,
            "id": q["id"],
            "type": q["type"],
            "question": q["question"],
            "options": q.get("options", {}),
            "knowledge_point": q.get("knowledge_point", ""),
        }
        public_questions.append(pq)

    logger.info("[ExamMode] 考试会话创建 session=%s exam=%s user=%s count=%d",
                session_id, exam_id, user_id, len(questions))
    return {
        "session_id": session_id,
        "exam_id": exam_id,
        "exam_name": exam["name"],
        "question_count": len(questions),
        "time_limit_minutes": exam.get("time_limit_minutes", 90),
        "questions": public_questions,
    }


def submit_exam(session_id: str, answers: dict[str, str]) -> dict:
    """批量评分并生成考试报告。

    Args:
        session_id: 考试会话 ID
        answers: {question_id: answer_str} 映射

    Returns:
        考试报告：分数/错题诊断/薄弱知识点
    """
    state = challenger_agent._sessions.get(session_id)
    if not state or "questions" not in state:
        return {"error": "会话不存在或已过期"}

    questions = state["questions"]
    pass_score = state.get("pass_score", 70)
    correct_count = 0
    wrong_items = []
    weak_kp_ids = set()

    for q in questions:
        qid = q["id"]
        user_ans = (answers.get(qid) or "").strip().upper()
        correct_ans = q["answer"].strip().upper()
        is_correct = user_ans == correct_ans
        if is_correct:
            correct_count += 1
        else:
            weak_kp_ids.add(q.get("kp_node_id", ""))
            wrong_items.append({
                "question_id": qid,
                "question": q["question"],
                "user_answer": user_ans or "(未作答)",
                "correct_answer": correct_ans,
                "explanation": q.get("explanation", ""),
                "knowledge_point": q.get("knowledge_point", ""),
                "kp_node_id": q.get("kp_node_id", ""),
            })

    total = len(questions)
    score = round(correct_count / total * 100, 1) if total > 0 else 0
    passed = score >= pass_score

    state["status"] = "completed"
    state["score"] = score
    state["answers"] = answers

    logger.info("[ExamMode] 考试提交 session=%s score=%.1f passed=%s wrong=%d",
                session_id, score, passed, len(wrong_items))

    return {
        "session_id": session_id,
        "exam_name": state.get("exam_name", ""),
        "total_questions": total,
        "correct_count": correct_count,
        "score": score,
        "passed": passed,
        "pass_score": pass_score,
        "wrong_count": len(wrong_items),
        "weak_kp_ids": list(weak_kp_ids - {""}),
        "wrong_items": wrong_items,
        "grade": _score_grade(score),
    }


def get_exam_session(session_id: str) -> dict | None:
    """Get exam session state."""
    return challenger_agent._sessions.get(session_id)


def _score_grade(score: float) -> str:
    if score >= 90: return "优秀（A）"
    elif score >= 80: return "良好（B）"
    elif score >= 70: return "中等（C）"
    elif score >= 60: return "及格（D）"
    else: return "不及格（F）"
