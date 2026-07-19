"""Patch orchestrator.py to add persona_id support."""
import re

fpath = "src/loopse/agent/orchestrator.py"
content = open(fpath, encoding="utf-8").read()

# 1. Insert persona loading after history_text line
old1 = "            history_text = self._get_history(session_id)\n"
new1 = (
    "            history_text = self._get_history(session_id)\n"
    "\n"
    "            # 获取当前会话的 persona_id\n"
    "            sess_state_for_persona = self._get_session_state(session_id)\n"
    '            current_persona_id = sess_state_for_persona.get("persona_id", "professor")\n'
    "\n"
)
if old1 in content:
    content = content.replace(old1, new1, 1)
    print("Patch 1 applied: persona_id loading")
else:
    print("Patch 1 FAILED: could not find history_text line")

# 2. Patch the _build_reply_prompt call to pass persona_id
old2 = "            prompt = self._build_reply_prompt(user_message, retrieval, diag_result, history_text, trace.to_dict())"
new2 = (
    "            prompt = self._build_reply_prompt(\n"
    "                user_message, retrieval, diag_result, history_text, trace.to_dict(),\n"
    "                persona_id=current_persona_id,\n"
    "            )"
)
if old2 in content:
    content = content.replace(old2, new2, 1)
    print("Patch 2 applied: _build_reply_prompt call")
else:
    print("Patch 2 FAILED")

# 3. Replace _build_reply_prompt signature and body
old3 = (
    '    @staticmethod\n'
    '    def _build_reply_prompt(\n'
    '        user_message: str,\n'
    '        retrieval: dict,\n'
    '        diag: dict,\n'
    '        history: str,\n'
    '        trace: dict,\n'
    '    ) -> str:\n'
)
new3 = (
    '    @staticmethod\n'
    '    def _build_reply_prompt(\n'
    '        user_message: str,\n'
    '        retrieval: dict,\n'
    '        diag: dict,\n'
    '        history: str,\n'
    '        trace: dict,\n'
    '        persona_id: str = "professor",\n'
    '    ) -> str:\n'
)
if old3 in content:
    content = content.replace(old3, new3, 1)
    print("Patch 3 applied: _build_reply_prompt signature")
else:
    print("Patch 3 FAILED: could not find _build_reply_prompt signature")

# 4. Update the return statement in _build_reply_prompt to inject persona prefix
old4 = (
    '        return (\n'
    '            "你是一个高级苏格拉底式计算机网络助教智能体。"\n'
    '            "你需要结合检索证据、错误诊断、学习画像和自己的推理轨迹来回答。"\n'
    '            "回答时先给学生可操作的理解框架，再用一到两个追问推动思考，避免只甩结论。\\n\\n"\n'
)
new4 = (
    '        # 人格化系统提示词\n'
    '        persona = _PERSONAS.get(persona_id, _PERSONAS.get("professor", {}))\n'
    '        persona_prefix = persona.get("prompt_prefix", "")\n'
    '        if persona_prefix:\n'
    '            persona_prefix = persona_prefix + "\\n\\n"\n'
    '        else:\n'
    '            persona_prefix = "你是一个高级苏格拉底式计算机网络助教智能体。\\n\\n"\n'
    '        return (\n'
    '            persona_prefix\n'
    '            + "你需要结合检索证据、错误诊断、学习画像和自己的推理轨迹来回答。"\n'
    '            "回答时先给学生可操作的理解框架，再用一到两个追问推动思考，避免只甩结论。\\n\\n"\n'
)
if old4 in content:
    content = content.replace(old4, new4, 1)
    print("Patch 4 applied: persona prefix injection")
else:
    print("Patch 4 FAILED: could not find return statement")

open(fpath, "w", encoding="utf-8").write(content)
print("Done writing file.")
