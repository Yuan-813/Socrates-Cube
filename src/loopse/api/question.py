"""题目生成 API — 多类型练习题按需生成。

支持题型：选择题 / 填空题 / 简答题 / 图形判断题 / 自定义类型
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/question", tags=["question"])


# ── 题目类型定义 ────────────────────────────────────────────────────────────
QUESTION_TYPE_PROMPTS = {
    "choice": (
        "生成一道单选题，包含4个选项（A/B/C/D），明确标注正确答案和详细解析。"
        "格式：{'question':'题干','options':{'A':'...','B':'...','C':'...','D':'...'},'answer':'A','explanation':'...'}"
    ),
    "fill": (
        "生成一道填空题，用___表示空白处，给出标准答案和简要说明。"
        "格式：{'question':'题干含___','answer':'标准答案','explanation':'...'}"
    ),
    "short_answer": (
        "生成一道简答题，给出评分要点（3-5个关键点）。"
        "格式：{'question':'题目','key_points':['要点1','要点2',...],'sample_answer':'参考答案'}"
    ),
    "diagram": (
        "生成一道图形判断题，描述一个网络拓扑或协议流程图，判断其中标注是否正确。"
        "格式：{'question':'描述图形场景','diagram_desc':'图形描述','options':{'A':'正确','B':'错误','C':'部分正确'},'answer':'A/B/C','explanation':'...'}"
    ),
    "case": (
        "生成一道案例分析题，描述真实网络故障场景，要求学生分析根因并给出解决方案。"
        "格式：{'question':'案例描述','sub_questions':['问1','问2'],'sample_answer':'参考答案'}"
    ),
}

DIFFICULTY_LABELS = {1: "入门", 2: "基础", 3: "中等", 4: "进阶", 5: "专家"}


class GenerateQuestionRequest(BaseModel):
    knowledge_point: str = Field(..., min_length=1, max_length=100, description="知识点，如'TCP三次握手'")
    question_type: str = Field(default="choice", description="题型: choice/fill/short_answer/diagram/case/custom")
    difficulty: int = Field(default=3, ge=1, le=5, description="难度 1-5")
    count: int = Field(default=3, ge=1, le=10, description="生成数量")
    custom_type_desc: Optional[str] = Field(default=None, description="自定义题型说明（question_type=custom时使用）")
    context: Optional[str] = Field(default=None, description="额外背景信息")


class BatchGenerateRequest(BaseModel):
    knowledge_point: str
    types: List[str] = Field(default=["choice", "fill", "short_answer", "diagram"])
    difficulty: int = Field(default=3, ge=1, le=5)
    count_per_type: int = Field(default=2, ge=1, le=5)


# ── 题目生成核心逻辑 ────────────────────────────────────────────────────────

def _build_question_prompt(
    knowledge_point: str,
    question_type: str,
    difficulty: int,
    custom_type_desc: Optional[str] = None,
    context: Optional[str] = None,
) -> str:
    diff_label = DIFFICULTY_LABELS.get(difficulty, "中等")
    type_prompt = QUESTION_TYPE_PROMPTS.get(
        question_type,
        f"生成一道{custom_type_desc or question_type}类型的题目，包含题目、答案和解析。"
        "以JSON格式返回。"
    )
    ctx_text = f"\n参考背景：{context[:300]}" if context else ""
    return (
        f"你是一位计算机网络专业教师，请针对知识点「{knowledge_point}」"
        f"按以下要求出{diff_label}难度的题目：\n"
        f"{type_prompt}\n"
        f"{ctx_text}\n"
        "要求：题目内容严谨、准确、符合教学规范，以合法JSON格式返回，不要添加代码块标记。"
    )


def _parse_question_response(raw: str, question_type: str, knowledge_point: str) -> dict:
    """解析 LLM 返回的题目 JSON，失败时构造默认结构。"""
    import re
    # 去掉 markdown 代码块
    clean = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
    try:
        data = json.loads(clean)
        data["id"] = str(uuid.uuid4())[:8]
        data["type"] = question_type
        data["knowledge_point"] = knowledge_point
        return data
    except Exception:
        # 降级：返回原始文本作为题目
        return {
            "id": str(uuid.uuid4())[:8],
            "type": question_type,
            "knowledge_point": knowledge_point,
            "question": f"关于{knowledge_point}的{question_type}题目",
            "raw_content": raw[:500],
            "parse_error": True,
        }


# ── 路由 ──────────────────────────────────────────────────────────────────

@router.post("/generate")
async def generate_questions(req: GenerateQuestionRequest):
    """生成指定类型的练习题。"""
    from ..core.llm_client import llm_client

    questions = []
    prompt = _build_question_prompt(
        req.knowledge_point, req.question_type, req.difficulty,
        req.custom_type_desc, req.context,
    )

    # 批量生成
    batch_prompt = (
        f"{prompt}\n\n请生成 {req.count} 道题目，以JSON数组格式返回，"
        "例如：[{{题目1}}, {{题目2}}, ...]"
    )

    try:
        raw = llm_client.chat(batch_prompt, max_tokens=3000)
        # 尝试解析数组
        import re
        clean = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
        try:
            parsed = json.loads(clean)
            if isinstance(parsed, list):
                for item in parsed:
                    item["id"] = str(uuid.uuid4())[:8]
                    item["type"] = req.question_type
                    item["knowledge_point"] = req.knowledge_point
                questions = parsed
            else:
                questions = [_parse_question_response(raw, req.question_type, req.knowledge_point)]
        except Exception:
            questions = [_parse_question_response(raw, req.question_type, req.knowledge_point)]
    except Exception as exc:
        logger.error("[Question] 题目生成失败: %s", exc)
        raise HTTPException(status_code=500, detail=f"题目生成失败：{exc}")

    return {
        "knowledge_point": req.knowledge_point,
        "question_type": req.question_type,
        "difficulty": req.difficulty,
        "difficulty_label": DIFFICULTY_LABELS.get(req.difficulty, "中等"),
        "count": len(questions),
        "questions": questions,
    }


@router.post("/batch")
async def batch_generate_questions(req: BatchGenerateRequest):
    """批量生成多种类型题目（一次请求返回所有类型）。"""
    from ..core.llm_client import llm_client

    result: dict[str, list] = {}
    for q_type in req.types:
        prompt = _build_question_prompt(req.knowledge_point, q_type, req.difficulty)
        batch_prompt = (
            f"{prompt}\n\n请生成 {req.count_per_type} 道题目，"
            "以JSON数组格式返回。"
        )
        try:
            raw = llm_client.chat(batch_prompt, max_tokens=2500)
            import re
            clean = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
            try:
                parsed = json.loads(clean)
                if isinstance(parsed, list):
                    for item in parsed:
                        item["id"] = str(uuid.uuid4())[:8]
                        item["type"] = q_type
                    result[q_type] = parsed
                else:
                    result[q_type] = [_parse_question_response(raw, q_type, req.knowledge_point)]
            except Exception:
                result[q_type] = [_parse_question_response(raw, q_type, req.knowledge_point)]
        except Exception as exc:
            logger.warning("[Question] %s 类型生成失败: %s", q_type, exc)
            result[q_type] = []

    total = sum(len(v) for v in result.values())
    return {
        "knowledge_point": req.knowledge_point,
        "difficulty": req.difficulty,
        "total_count": total,
        "questions_by_type": result,
    }


@router.get("/types")
def list_question_types():
    """返回所有支持的题型说明。"""
    return {
        "types": [
            {"key": "choice",       "label": "单选题",   "desc": "4个选项，1个正确答案"},
            {"key": "fill",         "label": "填空题",   "desc": "标准答案填空，支持多空"},
            {"key": "short_answer", "label": "简答题",   "desc": "开放式问答，评分要点"},
            {"key": "diagram",      "label": "图形判断", "desc": "判断网络拓扑/协议图是否正确"},
            {"key": "case",         "label": "案例分析", "desc": "真实故障场景综合分析"},
            {"key": "custom",       "label": "自定义",   "desc": "用户描述题型，AI自动生成"},
        ]
    }
