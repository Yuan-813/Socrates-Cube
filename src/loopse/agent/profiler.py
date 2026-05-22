"""
Profiler Agent — 学生8维画像构建与增量更新
维度：network_layer_cognition, protocol_flow_memory, packet_format_understanding,
      protocol_relationship, fault_diagnosis_logic, hands_on_ability,
      cognitive_style, misconception_patterns
"""
import json
from pathlib import Path
from typing import Optional

from src.loopse.core.llm_client import llm_client
from src.loopse.db.repositories import ProfileRepository

UPDATE_PROMPT_PATH = Path("config/prompts/profiler/update_profile.txt")


class ProfilerAgent:

    def __init__(self):
        self.update_prompt = ""
        if UPDATE_PROMPT_PATH.exists():
            self.update_prompt = UPDATE_PROMPT_PATH.read_text(encoding="utf-8")

    def update_profile(
        self,
        user_id: str,
        new_dialogue: str,
        current_profile: Optional[dict] = None,
    ) -> dict:
        """基于新对话内容增量更新画像"""
        if not current_profile:
            current_profile = ProfileRepository.get(user_id) or self._default_profile()

        if not self.update_prompt:
            return current_profile

        prompt = self.update_prompt.replace(
            "{current_profile_json}", json.dumps(current_profile, ensure_ascii=False)
        ).replace("{new_dialogue}", new_dialogue)

        result = llm_client.chat(user_message=prompt)
        try:
            clean = result.strip().strip("```json").strip("```").strip()
            updates = json.loads(clean)
            # 合并更新：只更新非null的字段
            for key, value in updates.items():
                if value is not None and key in current_profile:
                    current_profile[key] = value
        except Exception:
            pass

        # 写回DB
        ProfileRepository.upsert(user_id, current_profile)
        return current_profile

    def _default_profile(self) -> dict:
        return {
            "network_layer_cognition": None,
            "protocol_flow_memory": None,
            "packet_format_understanding": None,
            "protocol_relationship": None,
            "fault_diagnosis_logic": None,
            "hands_on_ability": None,
            "cognitive_style": None,
            "misconception_patterns": None,
        }


profiler_agent = ProfilerAgent()
