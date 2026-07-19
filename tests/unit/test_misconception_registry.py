"""MisconceptionRegistry 单元测试"""
import json
from pathlib import Path
import pytest

# 参考已有测试的 import 方式（tests/conftest.py 已将 src 加入路径）
from loopse.kb.misconception_registry import MisconceptionRegistry


class TestMisconceptionRegistryLoad:
    """加载与初始化测试"""

    def test_load_success(self):
        """验证能成功加载 misconceptions.json"""
        registry = MisconceptionRegistry()
        assert registry.count >= 50

    def test_load_invalid_path_no_crash(self):
        """无效路径不应崩溃，count 为 0"""
        registry = MisconceptionRegistry(json_path="nonexistent.json")
        assert registry.count == 0


class TestGetById:
    """按 ID 查询测试"""

    def test_get_existing_id(self):
        registry = MisconceptionRegistry()
        mc = registry.get_by_id("mc_001")
        assert mc is not None
        assert mc["id"] == "mc_001"
        assert mc["knowledge_point"] == "TCP 三次握手"

    def test_get_nonexistent_id(self):
        registry = MisconceptionRegistry()
        assert registry.get_by_id("mc_999") is None


class TestFindByNode:
    """按知识节点反向查询"""

    def test_find_existing_node(self):
        registry = MisconceptionRegistry()
        # find_by_node 索引基于 knowledge_node_ids 字段（acu_* 格式）
        results = registry.find_by_node("acu_025")
        assert len(results) > 0
        # acu_025 是 TCP 三次握手节点
        assert any(mc["id"] == "mc_001" for mc in results)

    def test_find_nonexistent_node(self):
        registry = MisconceptionRegistry()
        results = registry.find_by_node("kp_999")
        assert results == []


class TestFindByErrorType:
    """按错误类型查询"""

    def test_find_flow_omission(self):
        registry = MisconceptionRegistry()
        results = registry.find_by_error_type("flow_omission")
        assert len(results) > 0
        assert all(mc["error_type"] == "flow_omission" for mc in results)

    def test_find_nonexistent_type(self):
        registry = MisconceptionRegistry()
        results = registry.find_by_error_type("nonexistent_type")
        assert results == []


class TestMatchFromDiagnosis:
    """诊断匹配测试"""

    def test_exact_match(self):
        registry = MisconceptionRegistry()
        mc = registry.match_from_diagnosis("flow_omission", "TCP 三次握手")
        assert mc is not None
        assert mc["id"] == "mc_001"

    def test_partial_match(self):
        registry = MisconceptionRegistry()
        mc = registry.match_from_diagnosis("flow_omission", "三次握手")
        assert mc is not None
        assert "三次握手" in mc["knowledge_point"]

    def test_fallback_to_error_type(self):
        """无关键词匹配时，应返回同 error_type 的第一条"""
        registry = MisconceptionRegistry()
        mc = registry.match_from_diagnosis("flow_omission", "完全不相关的内容xyz")
        # 应该返回 flow_omission 类型的某条记录
        assert mc is not None
        assert mc["error_type"] == "flow_omission"

    def test_empty_knowledge_point(self):
        registry = MisconceptionRegistry()
        mc = registry.match_from_diagnosis("concept_confusion", "")
        assert mc is not None


class TestDataConsistency:
    """数据一致性校验"""

    def test_all_records_have_required_fields(self):
        """所有记录都应有新增的三个字段"""
        registry = MisconceptionRegistry()
        for mc in registry.all_misconceptions:
            assert "knowledge_node_ids" in mc, f"{mc['id']} 缺少 knowledge_node_ids"
            assert "weak_prerequisites" in mc, f"{mc['id']} 缺少 weak_prerequisites"
            assert "interventions" in mc, f"{mc['id']} 缺少 interventions"
            assert isinstance(mc["knowledge_node_ids"], list)
            assert isinstance(mc["interventions"], list)

    def test_knowledge_node_ids_valid(self):
        """所有 knowledge_node_ids 必须是有效的图谱节点或合法ACU格式"""
        import re
        # 加载知识图谱获取有效 ID
        kg_path = Path(__file__).resolve().parents[2] / "data" / "knowledge_graph.json"
        if not kg_path.exists():
            pytest.skip("knowledge_graph.json not found")

        kg_data = json.loads(kg_path.read_text(encoding="utf-8"))
        valid_ids = {node["id"] for node in kg_data.get("nodes", [])}
        # ACU节点由独立认知单元系统管理，接受 acu_NNN 格式
        acu_pattern = re.compile(r"^acu_\d{3}$")

        registry = MisconceptionRegistry()
        for mc in registry.all_misconceptions:
            for node_id in mc.get("knowledge_node_ids", []):
                assert node_id in valid_ids or acu_pattern.match(node_id), \
                    f"{mc['id']} 的 knowledge_node_ids 包含无效ID: {node_id}"

    def test_interventions_valid_types(self):
        """interventions 值只能是预定义的干预类型字符串"""
        valid_types = {"simulation", "exercise", "challenge", "doc",
                       "follow_up_question", "comparison_table", "contrast_table"}
        registry = MisconceptionRegistry()
        for mc in registry.all_misconceptions:
            for intervention in mc.get("interventions", []):
                assert intervention in valid_types, \
                    f"{mc['id']} 的 intervention 无效: {intervention}"
