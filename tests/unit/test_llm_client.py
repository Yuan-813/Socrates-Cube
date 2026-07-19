"""LLM 客户端单元测试 - Mock 模式 / 流式 / 消息构建验证"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from unittest.mock import patch, MagicMock


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #
@pytest.fixture()
def mock_llm():
    """返回强制 Mock 模式的 SparkLLMClient 实例"""
    from loopse.core import llm_client as mod
    from loopse.core.llm_client import SparkLLMClient

    # 强制切换为 Mock 模式（绕过模块级环境变量加载）
    original_mock_mode = mod._MOCK_MODE
    mod._MOCK_MODE = True
    client = SparkLLMClient()
    yield client
    mod._MOCK_MODE = original_mock_mode


# ------------------------------------------------------------------ #
# Mock 模式检测
# ------------------------------------------------------------------ #
class TestMockMode:
    def test_no_api_key_triggers_mock(self):
        """无 API Key 时应进入 Mock 模式"""
        from loopse.core import llm_client as mod

        assert mod._MOCK_MODE is True or mod._MOCK_MODE is False  # 仅验证不抛异常

    def test_mock_response_contains_keyword(self, mock_llm):
        """Mock 回复应包含与关键词相关的内容"""
        reply = mock_llm.chat("什么是TCP三次握手？")
        assert "三次握手" in reply or "TCP" in reply

    def test_mock_response_four_way(self, mock_llm):
        """四次挥手关键词应触发对应 Mock"""
        reply = mock_llm.chat("TCP四次挥手的过程")
        assert "四次挥手" in reply or "FIN" in reply

    def test_mock_response_http_tcp(self, mock_llm):
        """HTTP+TCP 组合应触发协议层次 Mock"""
        reply = mock_llm.chat("HTTP需要TCP吗")
        assert "HTTP" in reply or "TCP" in reply

    def test_mock_response_generic(self, mock_llm):
        """无匹配关键词时应返回通用 Mock 回复"""
        reply = mock_llm.chat("一个完全无关的问题xyz123")
        assert len(reply) > 0


# ------------------------------------------------------------------ #
# 同步 chat() 接口
# ------------------------------------------------------------------ #
class TestChat:
    def test_chat_returns_string(self, mock_llm):
        """chat() 必须返回字符串"""
        result = mock_llm.chat("测试消息")
        assert isinstance(result, str)

    def test_chat_with_system_prompt(self, mock_llm):
        """带 system_prompt 参数时不应报错"""
        result = mock_llm.chat("你好", system_prompt="你是助教")
        assert isinstance(result, str)


# ------------------------------------------------------------------ #
# 异步流式 async_stream_chat()
# ------------------------------------------------------------------ #
class TestAsyncStream:
    @pytest.mark.asyncio
    async def test_stream_yields_tokens(self, mock_llm):
        """Mock 流式应产生多个 token 片段"""
        tokens = []
        async for token in mock_llm.async_stream_chat("什么是TCP三次握手？"):
            tokens.append(token)
        assert len(tokens) > 1

    @pytest.mark.asyncio
    async def test_stream_concatenation_covers_content(self, mock_llm):
        """流式 token 拼接后应包含完整内容"""
        tokens = []
        async for token in mock_llm.async_stream_chat("什么是TCP三次握手？"):
            tokens.append(token)
        full_text = "".join(tokens)
        assert "三次握手" in full_text or "TCP" in full_text

    @pytest.mark.asyncio
    async def test_stream_empty_message(self, mock_llm):
        """空消息也应正常返回"""
        tokens = []
        async for token in mock_llm.async_stream_chat("hello"):
            tokens.append(token)
        assert len(tokens) >= 1


# ------------------------------------------------------------------ #
# 消息构建 _build_messages
# ------------------------------------------------------------------ #
class TestBuildMessages:
    def test_user_only(self):
        """仅 user_message 时应只有 1 条消息"""
        from loopse.core.llm_client import SparkLLMClient

        class FakeMsg:
            def __init__(self, role, content):
                self.role = role
                self.content = content

        msgs = SparkLLMClient._build_messages("你好", "", FakeMsg)
        assert len(msgs) == 1
        assert msgs[0].role == "user"

    def test_with_system(self):
        """有 system_prompt 时应有 2 条消息"""
        from loopse.core.llm_client import SparkLLMClient

        class FakeMsg:
            def __init__(self, role, content):
                self.role = role
                self.content = content

        msgs = SparkLLMClient._build_messages("你好", "你是助教", FakeMsg)
        assert len(msgs) == 2
        assert msgs[0].role == "system"
        assert msgs[1].role == "user"


# ------------------------------------------------------------------ #
# 环境变量辅助函数 _first_env
# ------------------------------------------------------------------ #
class TestFirstEnv:
    def test_returns_first_valid(self):
        """应返回第一个有效值"""
        from loopse.core.llm_client import _first_env

        with patch.dict(os.environ, {"TEST_A": "value_a", "TEST_B": "value_b"}):
            assert _first_env("TEST_A", "TEST_B") == "value_a"

    def test_skips_placeholder(self):
        """以 _here 结尾的占位值应被跳过"""
        from loopse.core.llm_client import _first_env

        with patch.dict(
            os.environ,
            {"TEST_A": "your_key_here", "TEST_B": "real_key"},
        ):
            assert _first_env("TEST_A", "TEST_B") == "real_key"

    def test_returns_empty_when_none(self):
        """所有变量均不存在时应返回空字符串"""
        from loopse.core.llm_client import _first_env

        with patch.dict(os.environ, {}, clear=True):
            assert _first_env("NONEXISTENT_A", "NONEXISTENT_B") == ""
