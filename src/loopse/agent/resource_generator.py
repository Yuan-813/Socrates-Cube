"""
Resource Generator Agent — 3类多表征资源生成
doc: 讲解文档（Markdown）
exercise: 练习题（JSON结构）
code: 代码实操案例（JSON结构）
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.loopse.core.llm_client import llm_client


class ResourceGeneratorAgent:
    PROMPT_DIR = Path("config/prompts/resource_generator")

    def __init__(self):
        self.prompts = {
            "doc": self._load("generate_doc.txt"),
            "exercise": self._load("generate_exercise.txt"),
            "code": self._load("generate_code.txt"),
        }

    def _load(self, filename: str) -> str:
        p = self.PROMPT_DIR / filename
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def generate(
        self,
        knowledge_point: str,
        resource_types: List[str],
        cognitive_style: str = "textual",
        error_type: str = "",
        reference_content: str = "",
        source_chapter: str = "",
        weakness_summary: str = "",
    ) -> List[dict]:
        results = []
        for rtype in resource_types:
            generator = getattr(self, f"_generate_{rtype}", None)
            if generator:
                resource = generator(
                    knowledge_point=knowledge_point,
                    cognitive_style=cognitive_style,
                    error_type=error_type,
                    reference_content=reference_content,
                    source_chapter=source_chapter,
                    weakness_summary=weakness_summary,
                )
                if resource:
                    results.append(resource)
        return results

    def _generate_doc(self, knowledge_point: str, cognitive_style: str,
                      reference_content: str, source_chapter: str,
                      weakness_summary: str, **kwargs) -> Optional[dict]:
        prompt = self.prompts["doc"] \
            .replace("{knowledge_point}", knowledge_point) \
            .replace("{cognitive_style}", cognitive_style) \
            .replace("{reference_content}", reference_content[:1500]) \
            .replace("{source_chapter}", source_chapter) \
            .replace("{weakness_summary}", weakness_summary or "暂无")

        content = llm_client.chat(user_message=prompt)
        return {
            "resource_id": str(uuid.uuid4()),
            "resource_type": "doc",
            "knowledge_point": knowledge_point,
            "title": f"【讲解】{knowledge_point}",
            "content": content,
            "cognitive_style_target": cognitive_style,
            "source_references": [source_chapter] if source_chapter else [],
            "generated_at": datetime.now().isoformat(),
            "reading_time": max(3, len(content) // 300),
        }

    def _generate_exercise(self, knowledge_point: str, error_type: str,
                            reference_content: str, **kwargs) -> Optional[dict]:
        type_map = {
            "concept_confusion": "choice",
            "flow_omission": "scenario",
            "layer_misplacement": "choice",
            "field_misunderstanding": "fill_blank",
            "": "choice",
        }
        exercise_type = type_map.get(error_type, "choice")

        prompt = self.prompts["exercise"] \
            .replace("{knowledge_point}", knowledge_point) \
            .replace("{error_type}", error_type or "general") \
            .replace("{exercise_type}", exercise_type) \
            .replace("{reference_content}", reference_content[:1000])

        result_str = llm_client.chat(user_message=prompt)
        try:
            clean = result_str.strip().strip("```json").strip("```").strip()
            exercise_data = json.loads(clean)
        except Exception:
            exercise_data = {
                "question": f"关于{knowledge_point}，以下说法正确的是？",
                "options": [{"label": "A", "text": "（题目生成失败，请重试）", "is_distractor": False}],
                "correct_answer": "A",
                "explanation": "解析生成失败",
                "targeted_misconception": error_type,
            }

        return {
            "resource_id": str(uuid.uuid4()),
            "resource_type": "exercise",
            "knowledge_point": knowledge_point,
            "title": f"【练习】{knowledge_point}",
            "exercise_type": exercise_type,
            "generated_at": datetime.now().isoformat(),
            **exercise_data,
        }

    def _generate_code(self, knowledge_point: str, reference_content: str,
                       **kwargs) -> Optional[dict]:
        prompt = self.prompts["code"] \
            .replace("{knowledge_point}", knowledge_point) \
            .replace("{reference_content}", reference_content[:1000])

        result_str = llm_client.chat(user_message=prompt)
        try:
            clean = result_str.strip().strip("```json").strip("```").strip()
            code_data = json.loads(clean)
        except Exception:
            code_data = {
                "title": f"{knowledge_point} 代码示例",
                "language": "python",
                "code": f"# {knowledge_point} 代码生成失败\nprint('Hello, TCP!')",
                "explanation": "代码解析失败",
                "expected_output": "",
                "wireshark_filter": "",
                "think_question": "",
            }

        return {
            "resource_id": str(uuid.uuid4()),
            "resource_type": "code",
            "knowledge_point": knowledge_point,
            "title": code_data.get("title", f"【代码】{knowledge_point}"),
            "generated_at": datetime.now().isoformat(),
            **code_data,
        }


resource_generator = ResourceGeneratorAgent()
