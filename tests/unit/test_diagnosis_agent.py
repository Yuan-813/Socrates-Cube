"""
单元测试：Diagnosis Agent（mock模式）
验证三层诊断结构完整性
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import unittest
from unittest.mock import patch, MagicMock
from src.loopse.agent.diagnosis import DiagnosisAgent, ErrorType


class TestDiagnosisAgent(unittest.TestCase):

    def setUp(self):
        self.agent = DiagnosisAgent()

    @patch("src.loopse.agent.diagnosis.llm_client.chat")
    def test_detect_surface_error_layer_misplacement(self, mock_chat):
        """测试：识别 layer_misplacement 错误"""
        mock_chat.return_value = '{"error_type": "layer_misplacement", "error_description": "把HTTP放在IP层", "evidence": "HTTP不需要TCP", "confidence": 0.92}'

        result = self.agent._detect_surface_error("HTTP直接用IP就行", "HTTP基于TCP")
        assert result["error_type"] == ErrorType.LAYER_MISPLACEMENT
        assert result["confidence"] >= 0.9

    @patch("src.loopse.agent.diagnosis.llm_client.chat")
    def test_detect_surface_error_correct(self, mock_chat):
        """测试：回答正确时返回 correct"""
        mock_chat.return_value = '{"error_type": "correct", "error_description": "", "evidence": "", "confidence": 1.0}'

        result = self.agent._detect_surface_error("TCP是面向连接的可靠传输协议", "TCP提供可靠传输")
        assert result["error_type"] == ErrorType.CORRECT

    @patch("src.loopse.agent.diagnosis.llm_client.chat")
    def test_diagnose_returns_three_layers(self, mock_chat):
        """测试：完整诊断返回三层结构"""
        mock_chat.side_effect = [
            # Layer 1: surface error
            '{"error_type": "concept_confusion", "error_description": "混淆SYN和ACK", "evidence": "SYN就是ACK", "confidence": 0.85}',
            # Layer 2: root causes
            '[{"knowledge_node_id": "kn_007", "knowledge_node_name": "TCP报文格式", "current_mastery": 0.3, "required_mastery": 0.8, "reason": "不了解控制位含义", "evidence_from_profile": "packet_format_understanding为2分"}]',
            # Layer 3: pattern match
            '{"pattern": "术语混淆型", "pattern_explanation": "把相似术语混用", "intervention_suggestion": "用对比表区分术语"}',
        ]

        result = self.agent.diagnose("SYN就是ACK对吧", "SYN用于请求，ACK用于确认")

        assert result["is_correct"] is False
        # Layer 1
        assert "surface_error" in result
        assert result["surface_error"]["error_type"] == ErrorType.CONCEPT_CONFUSION
        # Layer 2
        assert "root_causes" in result
        assert len(result["root_causes"]) >= 1
        assert result["root_causes"][0]["knowledge_node_id"].startswith("kn_")
        # Layer 3
        assert "pattern" in result
        assert result["pattern"]["pattern"] == "术语混淆型"
        assert "intervention_suggestion" in result

    @patch("src.loopse.agent.diagnosis.llm_client.chat")
    def test_diagnose_correct_answer_short_circuits(self, mock_chat):
        """测试：正确回答时跳过后续层"""
        mock_chat.return_value = '{"error_type": "correct", "error_description": "", "evidence": "", "confidence": 1.0}'

        result = self.agent.diagnose("TCP三次握手需要三步", "")

        assert result["is_correct"] is True
        assert result["root_causes"] == []
        assert result["pattern"] == "无明确模式"

    def test_all_error_types_defined(self):
        """测试：所有错误类型枚举值存在"""
        assert ErrorType.CONCEPT_CONFUSION == "concept_confusion"
        assert ErrorType.FLOW_OMISSION == "flow_omission"
        assert ErrorType.FIELD_MISUNDERSTANDING == "field_misunderstanding"
        assert ErrorType.LAYER_MISPLACEMENT == "layer_misplacement"
        assert ErrorType.REASONING_BREAKDOWN == "reasoning_breakdown"
        assert ErrorType.CALCULATION_ERROR == "calculation_error"
        assert ErrorType.CORRECT == "correct"

    @patch("src.loopse.agent.diagnosis.llm_client.chat")
    def test_malformed_llm_response_fallback(self, mock_chat):
        """测试：LLM返回非法JSON时有fallback"""
        mock_chat.return_value = "不是JSON"

        result = self.agent._detect_surface_error("任何输入", "")
        assert "error_type" in result
        assert result["confidence"] >= 0.0


if __name__ == "__main__":
    unittest.main(verbosity=2)
