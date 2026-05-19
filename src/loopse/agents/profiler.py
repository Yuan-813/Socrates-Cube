import json
from pathlib import Path
from typing import Optional
from src.loopse.core.llm_client import llm_client

class ProfilerAgent:
    """对话式8维协议能力画像构建Agent"""
    
    PROMPT_DIR = Path("config/prompts/profiler")
    
    def __init__(self):
        self.extract_prompt = self._load_prompt("extract_profile.txt")
        self.update_prompt = self._load_prompt("update_profile.txt")
    
    def _load_prompt(self, filename: str) -> str:
        prompt_path = self.PROMPT_DIR / filename
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        return ""
    
    def extract_profile(self, dialogue: str) -> dict:
        """从对话中提取8维画像JSON"""
        if not self.extract_prompt:
            return self._empty_profile()

        result = llm_client.chat(
            user_message=f"学生对话：\n{dialogue}",
            system_prompt=self.extract_prompt.replace("{dialogue}", dialogue)
        )
        
        try:
            clean_result = result.strip().strip('```json').strip('```').strip()
            return json.loads(clean_result)
        except json.JSONDecodeError:
            return self._empty_profile()
    
    def _empty_profile(self) -> dict:
        return {
            "network_layer_cognition": None,
            "protocol_flow_memory": None,
            "packet_format_understanding": None,
            "protocol_relationship": None,
            "fault_diagnosis_logic": None,
            "hands_on_ability": None,
            "cognitive_style": "textual",
            "misconception_patterns": []
        }

profiler_agent = ProfilerAgent()
