"""
单元测试：Resource Generator Agent（mock模式）
验证3类资源结构完整性
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import unittest
from unittest.mock import patch
from src.loopse.agent.resource_generator import ResourceGeneratorAgent


class TestResourceGeneratorAgent(unittest.TestCase):

    def setUp(self):
        self.agent = ResourceGeneratorAgent()

    @patch("src.loopse.agent.resource_generator.llm_client.chat")
    def test_generate_doc_structure(self, mock_chat):
        """测试：doc资源包含必要字段"""
        mock_chat.return_value = "## TCP三次握手\n\n1. 客户端发送SYN\n2. 服务端回复SYN+ACK\n\n来源章节 = 第5章"

        result = self.agent._generate_doc(
            knowledge_point="TCP三次握手",
            cognitive_style="textual",
            reference_content="TCP三次握手是...",
            source_chapter="第5章",
            weakness_summary="",
        )
        assert result["resource_type"] == "doc"
        assert result["title"] == "【讲解】TCP三次握手"
        assert "content" in result
        assert "resource_id" in result
        assert result["source_references"] == ["第5章"]
        assert "reading_time" in result

    @patch("src.loopse.agent.resource_generator.llm_client.chat")
    def test_generate_exercise_structure(self, mock_chat):
        """测试：exercise资源包含必要字段"""
        mock_chat.return_value = ('{"question": "以下关于TCP的说法正确的是？", '
                                  '"options": [{"label": "A", "text": "TCP是可靠的", "is_distractor": false}, '
                                  '{"label": "B", "text": "UDP更可靠", "is_distractor": true}], '
                                  '"correct_answer": "A", '
                                  '"explanation": "TCP提供可靠传输", '
                                  '"targeted_misconception": "概念混淆"}')

        result = self.agent._generate_exercise(
            knowledge_point="TCP特性",
            error_type="concept_confusion",
            reference_content="TCP提供可靠传输...",
        )
        assert result["resource_type"] == "exercise"
        assert "question" in result
        assert "options" in result
        assert "correct_answer" in result
        assert "explanation" in result
        assert "targeted_misconception" in result
        assert len(result["options"]) >= 2

    @patch("src.loopse.agent.resource_generator.llm_client.chat")
    def test_generate_code_structure(self, mock_chat):
        """测试：code资源包含必要字段"""
        mock_chat.return_value = ('{"title": "TCP握手模拟", "language": "python", '
                                  '"code": "import socket\\n# 代码", '
                                  '"explanation": "使用socket模拟", '
                                  '"expected_output": "连接成功", '
                                  '"wireshark_filter": "tcp.flags.syn==1", '
                                  '"think_question": "为什么需要三次？"}')

        result = self.agent._generate_code(
            knowledge_point="TCP握手",
            reference_content="TCP握手过程...",
        )
        assert result["resource_type"] == "code"
        assert "code" in result
        assert "explanation" in result
        assert "expected_output" in result
        assert "wireshark_filter" in result
        assert "think_question" in result

    @patch("src.loopse.agent.resource_generator.llm_client.chat")
    def test_generate_batch(self, mock_chat):
        """测试：批量生成3类资源"""
        mock_chat.side_effect = [
            "## doc内容\n来源章节 = 第5章",
            '{"question": "Q", "options": [{"label": "A", "text": "x", "is_distractor": false}], "correct_answer": "A", "explanation": "e", "targeted_misconception": ""}',
            '{"title": "t", "language": "python", "code": "c", "explanation": "e", "expected_output": "o", "wireshark_filter": "w", "think_question": "q"}',
        ]

        results = self.agent.generate(
            knowledge_point="TCP",
            resource_types=["doc", "exercise", "code"],
            cognitive_style="visual",
            error_type="layer_misplacement",
            reference_content="ref",
            source_chapter="第5章",
        )
        assert len(results) == 3
        types = [r["resource_type"] for r in results]
        assert "doc" in types
        assert "exercise" in types
        assert "code" in types

    @patch("src.loopse.agent.resource_generator.llm_client.chat")
    def test_malformed_json_fallback(self, mock_chat):
        """测试：LLM返回非法JSON时有fallback"""
        mock_chat.return_value = "不是JSON"

        result = self.agent._generate_exercise("知识点", "error", "ref")
        assert result["resource_type"] == "exercise"
        assert "question" in result
        assert "correct_answer" in result


if __name__ == "__main__":
    unittest.main(verbosity=2)
