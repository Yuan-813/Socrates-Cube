"""Resource Generator 六类资源生成测试。

测试6种类型分别生成，返回结构符合 Schema。
"""
from __future__ import annotations

import pytest

from loopse.agent.resource_generator import ResourceGeneratorAgent


@pytest.fixture
def agent():
    return ResourceGeneratorAgent()


class TestResourceGeneratorAllTypes:
    """六类资源生成测试。"""

    def test_resource_types_constant(self, agent: ResourceGeneratorAgent):
        """验证 RESOURCE_TYPES 包含全部已知类型（包括 infographic）。"""
        assert "doc" in agent.RESOURCE_TYPES
        assert "exercise" in agent.RESOURCE_TYPES
        assert "code" in agent.RESOURCE_TYPES
        assert "mindmap" in agent.RESOURCE_TYPES
        assert "script" in agent.RESOURCE_TYPES
        assert "infographic" in agent.RESOURCE_TYPES
        # 类型总数应 ≥ 5（小项目扩展新类型后不为硬编码数字）
        assert len(agent.RESOURCE_TYPES) >= 5

    @pytest.mark.parametrize("res_type", ["doc", "exercise", "code", "mindmap", "script"])
    def test_generate_single_type(self, agent: ResourceGeneratorAgent, res_type: str):
        """测试每种类型的单独生成。"""
        result = agent.generate(
            resource_type=res_type,
            knowledge_point="TCP三次握手",
            context_docs=[{"document": "TCP三次握手过程：SYN → SYN+ACK → ACK"}],
            difficulty=3,
        )
        assert result["resource_type"] == res_type
        assert result["resource_id"]
        assert result["title"]
        assert result["content"]
        assert result["metadata"]
        assert result["created_at"]
        assert result["knowledge_point"] == "TCP三次握手"

    def test_generate_all_five_types(self, agent: ResourceGeneratorAgent):
        """测试一次性生成全部5类资源。"""
        result = agent.generate_all(
            knowledge_point="OSI七层模型",
            context_docs=[{"document": "OSI七层模型包含物理层到应用层"}],
            difficulty=2,
        )
        assert result["knowledge_point"] == "OSI七层模型"
        assert result["total_resources"] >= 1
        # 检查每种类型字段存在
        for res_type in agent.RESOURCE_TYPES:
            assert res_type in result

    def test_invalid_type_raises(self, agent: ResourceGeneratorAgent):
        """测试不支持的类型应抛出 ValueError。"""
        with pytest.raises(ValueError, match="不支持的资源类型"):
            agent.generate(
                resource_type="invalid_type",
                knowledge_point="TCP",
            )

    def test_select_resource_types_visual(self, agent: ResourceGeneratorAgent):
        """测试画像驱动选择：visual 风格。"""
        types = agent._select_resource_types(
            profile={"cognitive_style": "visual"},
            diagnosis=None,
        )
        assert "mindmap" in types
        assert "doc" in types

    def test_select_resource_types_with_diagnosis(self, agent: ResourceGeneratorAgent):
        """测试诊断叠加：flow_omission 错误应追加 simulator。"""
        types = agent._select_resource_types(
            profile={"cognitive_style": "textual"},
            diagnosis={"error_type": "flow_omission", "pattern": "流程死记型"},
        )
        assert "doc" in types

    def test_select_resource_types_default(self, agent: ResourceGeneratorAgent):
        """测试无画像时使用默认选择。"""
        types = agent._select_resource_types(profile=None, diagnosis=None)
        assert "doc" in types
        assert len(types) >= 2

    def test_generate_mindmap_has_mermaid(self, agent: ResourceGeneratorAgent):
        """测试思维导图生成返回 Mermaid 内容。"""
        result = agent.generate(
            resource_type="mindmap",
            knowledge_point="TCP三次握手",
            context_docs=[{"document": "TCP三次握手流程"}],
        )
        assert result["resource_type"] == "mindmap"
        assert result["metadata"].get("format") == "mermaid"

    def test_generate_script_has_duration(self, agent: ResourceGeneratorAgent):
        """测试视频脚本生成返回时长信息。"""
        result = agent.generate(
            resource_type="script",
            knowledge_point="DNS解析",
            context_docs=[{"document": "DNS递归查询和迭代查询"}],
        )
        assert result["resource_type"] == "script"
        assert result["metadata"].get("format") == "json"
