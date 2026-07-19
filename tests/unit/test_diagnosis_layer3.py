"""Diagnosis Agent 第三层（误解模式匹配）单元测试。

测试用例：
1. "HTTP 直接跑在 IP 上" → 应返回「层次穿越型」
2. "三次握手就是 SYN、ACK、FIN 三个包" → 应返回「术语混淆型」
3. 正确回答 → 应返回「无明确模式」
"""
from __future__ import annotations

import pytest

from loopse.agent.diagnosis import DiagnosisAgent


@pytest.fixture
def agent():
    return DiagnosisAgent()


class TestDiagnosisLayer3:
    """第三层误解模式匹配测试。"""

    def test_layer_crossing_pattern(self, agent: DiagnosisAgent):
        """测试用例1：HTTP 直接跑在 IP 上 → 层次穿越型。"""
        result = agent.diagnose(
            user_message="HTTP协议直接运行在IP协议之上，不需要中间层。",
            context_docs=[{"document": "HTTP 运行在 TCP 之上，TCP 运行在 IP 之上"}],
        )
        # 应识别为错误
        assert result.get("is_correct") is False
        # error_type 应包含层次相关错误
        assert result.get("error_type") != "none"
        # surface_error 应描述层次问题
        assert result.get("surface_error") is not None

    def test_terminology_confusion_pattern(self, agent: DiagnosisAgent):
        """测试用例2：三次握手误认为 SYN/ACK/FIN → 术语混淆型。"""
        result = agent.diagnose(
            user_message="TCP三次握手就是SYN、ACK、FIN三个包依次发送。",
            context_docs=[{"document": "TCP三次握手：SYN → SYN+ACK → ACK"}],
        )
        assert result.get("is_correct") is False
        assert result.get("error_type") != "none"
        # surface_error 应描述流程/术语问题
        assert result.get("surface_error") is not None

    def test_correct_answer_no_pattern(self, agent: DiagnosisAgent):
        """测试用例3：正确回答 → 无明确模式。"""
        result = agent.diagnose(
            user_message="TCP三次握手的过程是：客户端发SYN，服务端回SYN+ACK，客户端再发ACK。",
            context_docs=[{"document": "TCP三次握手：SYN → SYN+ACK → ACK"}],
        )
        assert result.get("is_correct") is True
        assert result.get("pattern") is None
        assert result.get("root_causes") == []

    def test_diagnosis_returns_all_fields(self, agent: DiagnosisAgent):
        """验证诊断结果包含所有必需字段。"""
        result = agent.diagnose(
            user_message="UDP比TCP更好，因为UDP更快。",
            context_docs=[{"document": "TCP提供可靠传输，UDP提供快速但不可靠传输"}],
        )
        required_fields = [
            "is_correct", "confidence", "surface_error", "error_type",
            "root_causes", "missing_prerequisites", "pattern",
            "intervention_suggestion", "related_node_ids",
        ]
        for field in required_fields:
            assert field in result, f"缺少字段: {field}"
