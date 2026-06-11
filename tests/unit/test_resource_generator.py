"""资源生成 Agent 单元测试 - 三类资源生成验证"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest
from unittest.mock import MagicMock


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #
DOC_MOCK = "## TCP 三次握手\n三次握手是指..."
EXERCISE_MOCK = "**题目：** TCP 握手过程中，第二次握手由谁发起？\n\n**答案：** 服务端"
CODE_MOCK = "```python\nimport socket\nclient = socket.socket()\nclient.connect(('127.0.0.1', 8080))\n```"


@pytest.fixture()
def resource_agent():
    from loopse.agents.resource_generator import ResourceGeneratorAgent

    agent = ResourceGeneratorAgent.__new__(ResourceGeneratorAgent)
    agent.llm = MagicMock()

    def _mock_chat(prompt: str, **kwargs):
        if "代码" in prompt or "code" in prompt.lower():
            return CODE_MOCK
        if "练习" in prompt or "exercise" in prompt.lower():
            return EXERCISE_MOCK
        return DOC_MOCK

    agent.llm.chat = MagicMock(side_effect=_mock_chat)
    agent.retriever = MagicMock()
    agent.retriever.search_knowledge = MagicMock(return_value={
        "docs": [{"content": "TCP三次握手建立连接", "source": "ch05"}],
        "graph_nodes": []
    })
    return agent


# ------------------------------------------------------------------ #
# 文档类资源
# ------------------------------------------------------------------ #
@pytest.mark.asyncio
async def test_generate_doc(resource_agent):
    result = await resource_agent.generate(
        knowledge_point="TCP 三次握手",
        resource_type="doc",
        difficulty=3
    )
    assert result["resource_type"] == "doc"
    assert result["knowledge_point"] == "TCP 三次握手"
    assert len(result["content"]) > 0
    assert "resource_id" in result
    assert "created_at" in result


# ------------------------------------------------------------------ #
# 练习题类资源
# ------------------------------------------------------------------ #
@pytest.mark.asyncio
async def test_generate_exercise(resource_agent):
    result = await resource_agent.generate(
        knowledge_point="TCP 三次握手",
        resource_type="exercise",
        difficulty=3
    )
    assert result["resource_type"] == "exercise"
    assert len(result["content"]) > 0


# ------------------------------------------------------------------ #
# 代码示例类资源
# ------------------------------------------------------------------ #
@pytest.mark.asyncio
async def test_generate_code(resource_agent):
    result = await resource_agent.generate(
        knowledge_point="TCP Socket 编程",
        resource_type="code",
        difficulty=3
    )
    assert result["resource_type"] == "code"
    assert len(result["content"]) > 0


# ------------------------------------------------------------------ #
# 返回结构完整性检查
# ------------------------------------------------------------------ #
@pytest.mark.asyncio
async def test_result_schema(resource_agent):
    result = await resource_agent.generate(
        knowledge_point="OSI模型",
        resource_type="doc",
        difficulty=2
    )
    required_keys = {"resource_id", "resource_type", "knowledge_point", "title", "content", "metadata", "created_at"}
    assert required_keys.issubset(result.keys()), f"缺少字段: {required_keys - result.keys()}"
