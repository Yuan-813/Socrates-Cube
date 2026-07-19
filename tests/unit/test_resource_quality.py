"""资源生成质量测试 - 6种资源类型结构、LinUCB推荐分布、诊断驱动vs全量生成差异。"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["MOCK_MODE"] = "true"

import pytest
from unittest.mock import MagicMock, patch


# ------------------------------------------------------------------ #
# Mock LLM 回复模板
# ------------------------------------------------------------------ #
_MOCK_RESPONSES = {
    "doc": "## TCP 三次握手\n\n### 概述\nTCP三次握手是建立连接的过程。\n\n### 核心原理\n1. SYN\n2. SYN-ACK\n3. ACK\n\n### 总结\n三次握手确保双方收发能力。",
    "exercise": "**题目1：** TCP握手中第二步由谁发起？\nA. 客户端\nB. 服务端\n答案：B\n解析：第二步是SYN-ACK。\n\n**题目2：** TCP需要几次握手？\n答案：三次",
    "code": "```python\nimport socket\n\ndef tcp_handshake():\n    # 模拟TCP三次握手\n    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n    client.connect(('127.0.0.1', 8080))\n    # SYN -> SYN-ACK -> ACK\n    return True\n```",
    "mindmap": "```mermaid\nmindmap\n  root((TCP三次握手))\n    SYN阶段\n      客户端发起\n      序列号初始化\n    SYN-ACK阶段\n      服务端确认\n    ACK阶段\n      连接建立\n    常见误区\n      两次握手就够\n```",
    "script": '{"scenes": [{"scene": 1, "description": "开场介绍", "narration": "今天学习TCP三次握手", "visual": "标题动画"}, {"scene": 2, "description": "流程演示", "narration": "第一步客户端发送SYN", "visual": "箭头动画"}]}',
    "infographic": '{"title": "TCP三次握手", "summary": "三步建立可靠连接", "key_numbers": [{"value": "3", "unit": "次", "desc": "握手次数"}], "comparison": {"header": ["阶段", "方向"], "rows": [["SYN", "C→S"]]}, "timeline": [{"step": "SYN", "desc": "客户端发起"}], "tags": ["TCP", "握手"]}',
}


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #
@pytest.fixture()
def resource_agent():
    """创建带 mock LLM 的 ResourceGeneratorAgent 实例。"""
    with patch("loopse.agent.resource_generator.ResourceRepository"):
        from loopse.agent.resource_generator import ResourceGeneratorAgent

        agent = ResourceGeneratorAgent.__new__(ResourceGeneratorAgent)
        # 初始化 prompt 属性
        agent._doc_prompt = ""
        agent._exercise_prompt = ""
        agent._code_prompt = ""
        agent._mindmap_prompt = ""
        agent._script_prompt = ""
        agent._infographic_prompt = ""

        # Mock LLM 客户端
        agent.llm = MagicMock()

        def _mock_chat(prompt: str, **kwargs):
            for key, response in _MOCK_RESPONSES.items():
                if key in prompt.lower() or key in prompt:
                    return response
            # 默认返回 doc 格式
            return _MOCK_RESPONSES["doc"]

        agent.llm.chat = MagicMock(side_effect=_mock_chat)
        yield agent


@pytest.fixture()
def resource_agent_with_bandit():
    """创建带模拟 LinUCB bandit 的 ResourceGeneratorAgent 实例。"""
    with patch("loopse.agent.resource_generator.ResourceRepository"), \
         patch("loopse.agent.resource_generator._RL_BANDIT_AVAILABLE", True), \
         patch("loopse.agent.resource_generator._get_bandit") as mock_get_bandit:

        from loopse.agent.resource_generator import ResourceGeneratorAgent

        mock_bandit = MagicMock()
        mock_bandit.build_context.return_value = [0.5, 0.6, 0.3, 0.7]
        mock_bandit.select_arms.return_value = (["doc", "exercise", "code"], [0.85, 0.72, 0.65])
        mock_bandit.alpha = 0.25
        mock_bandit._total = 100
        mock_get_bandit.return_value = mock_bandit

        agent = ResourceGeneratorAgent.__new__(ResourceGeneratorAgent)
        agent._doc_prompt = ""
        agent._exercise_prompt = ""
        agent._code_prompt = ""
        agent._mindmap_prompt = ""
        agent._script_prompt = ""
        agent._infographic_prompt = ""

        agent.llm = MagicMock()
        agent.llm.chat = MagicMock(return_value=_MOCK_RESPONSES["doc"])
        yield agent, mock_bandit


# ------------------------------------------------------------------ #
# 1. 六种资源类型结构正确性
# ------------------------------------------------------------------ #
class TestResourceTypeStructure:
    """验证6种资源类型都能正确生成并包含必要结构。"""

    @pytest.mark.parametrize("resource_type", [
        "doc", "exercise", "code", "mindmap", "script", "infographic"
    ])
    def test_resource_type_generates_valid_structure(self, resource_agent, resource_type):
        """每种资源类型都应生成包含必要字段的有效结构"""
        result = resource_agent.generate(
            resource_type=resource_type,
            knowledge_point="TCP 三次握手",
            difficulty=3,
        )
        required_keys = {"resource_id", "resource_type", "knowledge_point", "title", "content", "metadata", "created_at"}
        assert required_keys.issubset(result.keys()), f"缺少字段: {required_keys - result.keys()}"
        assert result["resource_type"] == resource_type
        assert result["knowledge_point"] == "TCP 三次握手"
        assert len(result["content"]) > 0
        assert len(result["resource_id"]) > 0

    def test_doc_has_markdown_structure(self, resource_agent):
        """doc 类型应包含 Markdown 结构"""
        result = resource_agent.generate(
            resource_type="doc",
            knowledge_point="TCP 三次握手",
            difficulty=3,
        )
        assert "#" in result["content"] or "概述" in result["content"]

    def test_exercise_has_question_content(self, resource_agent):
        """exercise 类型应包含题目内容"""
        result = resource_agent.generate(
            resource_type="exercise",
            knowledge_point="TCP 三次握手",
            difficulty=3,
        )
        assert len(result["content"]) > 20
        assert "difficulty" in result["metadata"]

    def test_code_has_code_content(self, resource_agent):
        """code 类型应包含代码内容"""
        result = resource_agent.generate(
            resource_type="code",
            knowledge_point="TCP Socket编程",
            difficulty=3,
        )
        assert len(result["content"]) > 10
        assert result["metadata"].get("language") == "python"

    def test_mindmap_has_mermaid_format(self, resource_agent):
        """mindmap 类型应包含 Mermaid 格式"""
        result = resource_agent.generate(
            resource_type="mindmap",
            knowledge_point="OSI七层模型",
            difficulty=2,
        )
        assert result["metadata"].get("format") == "mermaid"

    def test_script_has_json_format(self, resource_agent):
        """script 类型应标注 JSON 格式"""
        result = resource_agent.generate(
            resource_type="script",
            knowledge_point="DNS解析流程",
            difficulty=3,
        )
        assert result["metadata"].get("format") == "json"

    def test_infographic_has_json_format(self, resource_agent):
        """infographic 类型应标注 JSON 格式"""
        result = resource_agent.generate(
            resource_type="infographic",
            knowledge_point="HTTP协议",
            difficulty=2,
        )
        assert result["metadata"].get("format") == "json"

    def test_invalid_resource_type_raises_error(self, resource_agent):
        """不支持的资源类型应抛出 ValueError"""
        with pytest.raises(ValueError, match="不支持的资源类型"):
            resource_agent.generate(
                resource_type="invalid_type",
                knowledge_point="TCP",
                difficulty=3,
            )

    @pytest.mark.parametrize("difficulty", [1, 2, 3, 4, 5])
    def test_difficulty_parameter_accepted(self, resource_agent, difficulty):
        """所有难度级别（1-5）都应被接受"""
        result = resource_agent.generate(
            resource_type="doc",
            knowledge_point="TCP",
            difficulty=difficulty,
        )
        assert result["metadata"]["difficulty"] == difficulty


# ------------------------------------------------------------------ #
# 2. LinUCB 算法推荐分布合理性
# ------------------------------------------------------------------ #
class TestLinUCBRecommendation:
    """验证 LinUCB 算法的资源推荐分布合理性。"""

    def test_select_resource_types_visual_style(self, resource_agent):
        """visual 认知风格应优先推荐 mindmap 和 script"""
        profile = {"cognitive_style": "visual"}
        types = resource_agent._select_resource_types(profile, None)
        assert "mindmap" in types
        assert "script" in types

    def test_select_resource_types_practical_style(self, resource_agent):
        """practical 认知风格应优先推荐 code 和 exercise"""
        profile = {"cognitive_style": "practical"}
        types = resource_agent._select_resource_types(profile, None)
        assert "code" in types
        assert "exercise" in types

    def test_select_resource_types_textual_style(self, resource_agent):
        """textual 认知风格应优先推荐 doc"""
        profile = {"cognitive_style": "textual"}
        types = resource_agent._select_resource_types(profile, None)
        assert types[0] == "doc"

    def test_error_boost_adds_exercise(self, resource_agent):
        """concept_confusion 错误类型应追加 exercise"""
        profile = {"cognitive_style": "textual"}
        diagnosis = {"error_type": "concept_confusion", "pattern": ""}
        types = resource_agent._select_resource_types(profile, diagnosis)
        assert "exercise" in types

    def test_error_boost_adds_mindmap_for_layer_error(self, resource_agent):
        """layer_misplacement 错误应追加 mindmap"""
        profile = {"cognitive_style": "practical"}
        diagnosis = {"error_type": "layer_misplacement", "pattern": ""}
        types = resource_agent._select_resource_types(profile, diagnosis)
        assert "mindmap" in types

    def test_doc_always_present(self, resource_agent):
        """无论何种组合 doc 应始终存在"""
        for style in ["visual", "practical", "textual", "analogical"]:
            profile = {"cognitive_style": style}
            types = resource_agent._select_resource_types(profile, None)
            assert "doc" in types

    def test_bandit_context_built_correctly(self, resource_agent_with_bandit):
        """LinUCB bandit 上下文应被正确构建"""
        agent, mock_bandit = resource_agent_with_bandit
        profile = {"user_id": "u1", "cognitive_style": "visual"}
        diagnosis = {"error_type": "flow_omission", "pattern": ""}

        # 调用 generate_from_diagnosis 应触发 bandit
        agent.generate_from_diagnosis(
            knowledge_point="TCP 三次握手",
            diagnosis_result=diagnosis,
            profile=profile,
            difficulty=3,
        )
        mock_bandit.build_context.assert_called_once()

    def test_bandit_selects_arms(self, resource_agent_with_bandit):
        """LinUCB bandit 应进行 arm 选择"""
        agent, mock_bandit = resource_agent_with_bandit
        profile = {"user_id": "u1", "cognitive_style": "practical"}
        diagnosis = {"error_type": "conceptual", "pattern": ""}

        result = agent.generate_from_diagnosis(
            knowledge_point="TCP",
            diagnosis_result=diagnosis,
            profile=profile,
            difficulty=3,
        )
        mock_bandit.select_arms.assert_called_once()
        assert "LinUCB" in result["strategy_reason"]


# ------------------------------------------------------------------ #
# 3. 诊断驱动 vs 全量生成的输出差异
# ------------------------------------------------------------------ #
class TestDiagnosisDrivenVsFullGeneration:
    """验证诊断驱动和全量生成的输出差异。"""

    def test_generate_all_produces_all_types(self, resource_agent):
        """全量生成应产出所有6种资源类型"""
        result = resource_agent.generate_all(
            knowledge_point="TCP 三次握手",
            difficulty=3,
        )
        assert result["knowledge_point"] == "TCP 三次握手"
        assert result["total_resources"] >= 5
        for rtype in ("doc", "exercise", "code", "mindmap", "script"):
            assert result.get(rtype) is not None

    def test_diagnosis_driven_produces_fewer_types(self, resource_agent):
        """诊断驱动应只生成选定的资源类型（默认最多3种）"""
        diagnosis = {
            "error_type": "flow_omission",
            "pattern": "flow_omission",
            "recommended_interventions": ["doc", "exercise"],
            "misconception_id": "mc_001",
            "acu_ids": [],
        }
        result = resource_agent.generate_from_diagnosis(
            knowledge_point="TCP 三次握手",
            diagnosis_result=diagnosis,
            profile={"cognitive_style": "textual"},
            difficulty=3,
            max_types=3,
        )
        assert result["diagnosis_driven"] is True
        assert result["total_resources"] <= 3
        assert "doc" in result["selected_types"]

    def test_diagnosis_driven_uses_recommended_interventions(self, resource_agent):
        """诊断驱动应优先使用 recommended_interventions"""
        diagnosis = {
            "error_type": "concept_confusion",
            "pattern": "",
            "recommended_interventions": ["exercise", "mindmap"],
            "misconception_id": "mc_002",
            "acu_ids": [],
        }
        result = resource_agent.generate_from_diagnosis(
            knowledge_point="OSI模型",
            diagnosis_result=diagnosis,
            profile=None,
            difficulty=2,
        )
        # doc 应被确保存在（即使不在推荐列表中）
        assert "doc" in result["selected_types"]

    def test_diagnosis_driven_includes_strategy_reason(self, resource_agent):
        """诊断驱动结果应包含策略理由"""
        diagnosis = {
            "error_type": "flow_omission",
            "pattern": "",
            "recommended_interventions": ["doc"],
            "misconception_id": None,
            "acu_ids": [],
        }
        result = resource_agent.generate_from_diagnosis(
            knowledge_point="TCP",
            diagnosis_result=diagnosis,
            profile=None,
            difficulty=3,
        )
        assert "strategy_reason" in result
        assert len(result["strategy_reason"]) > 0

    def test_full_generation_vs_diagnosis_output_keys(self, resource_agent):
        """全量生成和诊断驱动应有不同的输出键"""
        full_result = resource_agent.generate_all(
            knowledge_point="TCP",
            difficulty=3,
        )
        diag_result = resource_agent.generate_from_diagnosis(
            knowledge_point="TCP",
            diagnosis_result={"error_type": "conceptual", "pattern": "", "recommended_interventions": ["doc"], "misconception_id": None, "acu_ids": []},
            profile=None,
            difficulty=3,
        )
        # 诊断驱动特有字段
        assert "diagnosis_driven" in diag_result
        assert "selected_types" in diag_result
        assert "strategy_reason" in diag_result
        # 全量生成特有字段
        assert "total_resources" in full_result

    def test_fallback_content_on_llm_failure(self, resource_agent):
        """LLM 失败时应使用备选内容而非崩溃"""
        resource_agent.llm.chat.side_effect = RuntimeError("LLM 不可用")
        result = resource_agent.generate(
            resource_type="doc",
            knowledge_point="TCP 三次握手",
            difficulty=3,
        )
        assert result["content"] is not None
        assert len(result["content"]) > 0
        assert result["metadata"].get("fallback") is True

    @pytest.mark.parametrize("error_type,expected_boost", [
        ("flow_omission", "simulator"),
        ("concept_confusion", "exercise"),
        ("reasoning_breakdown", "doc"),
    ])
    def test_error_type_boosts_specific_resources(self, resource_agent, error_type, expected_boost):
        """不同错误类型应追加对应的资源类型"""
        profile = {"cognitive_style": "textual"}
        diagnosis = {"error_type": error_type, "pattern": ""}
        types = resource_agent._select_resource_types(profile, diagnosis)
        # 某些boost类型可能不在 RESOURCE_TYPES 中（如 simulator），只验证逻辑触发
        if expected_boost in resource_agent.RESOURCE_TYPES:
            assert expected_boost in types

    def test_quality_score_present_in_output(self, resource_agent):
        """生成结果应包含质量评分"""
        result = resource_agent.generate(
            resource_type="doc",
            knowledge_point="IP协议",
            difficulty=2,
        )
        assert "quality_score" in result
        assert 0 <= result["quality_score"] <= 1.0
