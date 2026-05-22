"""
Diagnosis Agent — 三层认知诊断
Layer 1: 表面错误识别（错误类型 + 置信度）
Layer 2: 根因溯源（前置知识薄弱点）
Layer 3: 误解模式匹配（5种模式）
"""
import json
from pathlib import Path
from typing import Optional

from src.loopse.core.llm_client import llm_client


class ErrorType:
    CONCEPT_CONFUSION = "concept_confusion"
    FLOW_OMISSION = "flow_omission"
    FIELD_MISUNDERSTANDING = "field_misunderstanding"
    LAYER_MISPLACEMENT = "layer_misplacement"
    REASONING_BREAKDOWN = "reasoning_breakdown"
    CALCULATION_ERROR = "calculation_error"
    CORRECT = "correct"


class DiagnosisAgent:
    PROMPT_DIR = Path("config/prompts/diagnosis")

    def __init__(self):
        self.surface_prompt = self._load("surface_error.txt")
        self.root_cause_prompt = self._load("root_cause.txt")
        self.pattern_prompt = self._load("pattern_match.txt")

    def _load(self, filename: str) -> str:
        p = self.PROMPT_DIR / filename
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def diagnose(
        self,
        student_answer: str,
        reference_content: str,
        profile: Optional[dict] = None,
        knowledge_graph_context: str = "",
    ) -> dict:
        # Layer 1：表面错误
        surface = self._detect_surface_error(student_answer, reference_content)

        if surface.get("error_type") == ErrorType.CORRECT:
            return {
                "is_correct": True,
                "surface_error": surface,
                "root_causes": [],
                "pattern": "无明确模式",
            }

        # Layer 2：根因溯源
        root_causes = self._analyze_root_cause(
            surface, profile or {}, knowledge_graph_context
        )

        # Layer 3：误解模式匹配
        pattern = self._match_pattern(surface, root_causes)

        return {
            "is_correct": False,
            "surface_error": surface,
            "root_causes": root_causes,
            "pattern": pattern,
            "intervention_suggestion": pattern.get("intervention_suggestion", ""),
        }

    def _detect_surface_error(self, student_answer: str, reference: str) -> dict:
        prompt = self.surface_prompt.replace(
            "{student_answer}", student_answer
        ).replace("{reference_content}", reference)

        result = llm_client.chat(user_message=prompt)
        try:
            clean = result.strip().strip("```json").strip("```").strip()
            return json.loads(clean)
        except Exception:
            return {
                "error_type": ErrorType.CONCEPT_CONFUSION,
                "error_description": "无法解析诊断结果",
                "evidence": student_answer[:100],
                "confidence": 0.5,
            }

    def _analyze_root_cause(
        self, surface: dict, profile: dict, kg_context: str
    ) -> list:
        prompt = self.root_cause_prompt.replace(
            "{surface_error_json}", json.dumps(surface, ensure_ascii=False)
        ).replace(
            "{profile_json}", json.dumps(profile, ensure_ascii=False)
        ).replace(
            "{knowledge_graph_context}", kg_context or "暂无知识图谱数据"
        )

        result = llm_client.chat(user_message=prompt)
        try:
            clean = result.strip().strip("```json").strip("```").strip()
            return json.loads(clean)
        except Exception:
            return []

    def _match_pattern(self, surface: dict, root_causes: list) -> dict:
        prompt = self.pattern_prompt.replace(
            "{surface_error_json}", json.dumps(surface, ensure_ascii=False)
        ).replace(
            "{root_causes_json}", json.dumps(root_causes, ensure_ascii=False)
        )

        result = llm_client.chat(user_message=prompt)
        try:
            clean = result.strip().strip("```json").strip("```").strip()
            return json.loads(clean)
        except Exception:
            return {"pattern": "无明确模式", "pattern_explanation": "", "intervention_suggestion": ""}


diagnosis_agent = DiagnosisAgent()
