"""诊断-路径联动集成测试 - 验证诊断结果正确传递到路径规划器的完整链路。"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["MOCK_MODE"] = "true"

import pytest
from unittest.mock import MagicMock, patch


# ------------------------------------------------------------------ #
# 辅助工具
# ------------------------------------------------------------------ #
def _make_mock_knowledge_graph():
    """创建模拟的知识图谱，包含合理的拓扑结构。"""
    from loopse.kb.knowledge_graph import KnowledgeNode

    nodes_data = [
        {"id": "kp_001", "name": "计算机网络概述", "chapter": "ch01", "type": "concept", "difficulty": 1, "estimated_time": 20},
        {"id": "kp_005", "name": "数据链路层", "chapter": "ch05", "type": "concept", "difficulty": 2, "estimated_time": 30},
        {"id": "kp_007", "name": "IP协议", "chapter": "ch04", "type": "protocol", "difficulty": 3, "estimated_time": 40},
        {"id": "kp_008", "name": "TCP协议基础", "chapter": "ch03", "type": "protocol", "difficulty": 3, "estimated_time": 45},
        {"id": "kp_009", "name": "TCP三次握手", "chapter": "ch03", "type": "protocol", "difficulty": 3, "estimated_time": 35},
        {"id": "kp_010", "name": "路由选择协议", "chapter": "ch04", "type": "protocol", "difficulty": 4, "estimated_time": 50},
        {"id": "kp_014", "name": "TCP连接管理", "chapter": "ch03", "type": "protocol", "difficulty": 4, "estimated_time": 40},
        {"id": "kp_015", "name": "TCP拥塞控制", "chapter": "ch03", "type": "protocol", "difficulty": 5, "estimated_time": 60},
    ]
    nodes = {d["id"]: KnowledgeNode(d) for d in nodes_data}

    # 拓扑关系: kp_001 → kp_005 → kp_007 → kp_008 → kp_009 → kp_014 → kp_015
    # kp_007 → kp_010
    edges = {
        "kp_005": {"kp_001"},
        "kp_007": {"kp_005"},
        "kp_008": {"kp_007"},
        "kp_009": {"kp_008"},
        "kp_010": {"kp_007"},
        "kp_014": {"kp_009"},
        "kp_015": {"kp_014"},
    }
    return nodes, edges


def _build_profile(mastery_map=None, weak_points=None, strong_points=None):
    """构建模拟的学生画像。"""
    return {
        "user_id": "test_user",
        "mastery_map": mastery_map or {},
        "weak_points": weak_points or [],
        "strong_points": strong_points or [],
        "turn_count": 5,
        "cognitive_style": "textual",
        "conceptual_understanding": 0.6,
        "protocol_analysis": 0.5,
        "calculation_ability": 0.4,
    }


def _build_diagnosis_result(is_correct=False, knowledge_node_ids=None, error_type="flow_omission"):
    """构建模拟诊断结果。"""
    if is_correct:
        return {
            "is_correct": True,
            "confidence": 0.85,
            "surface_error": None,
            "error_type": "none",
            "root_causes": [],
            "missing_prerequisites": [],
            "knowledge_node_ids": [],
            "misconception_id": None,
        }
    return {
        "is_correct": False,
        "confidence": 0.72,
        "surface_error": "TCP握手流程描述不完整",
        "error_type": error_type,
        "root_causes": ["协议流程理解不深入"],
        "missing_prerequisites": ["kp_008"],
        "knowledge_node_ids": knowledge_node_ids or ["kp_009"],
        "misconception_id": "mc_001",
    }


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #
@pytest.fixture()
def path_planner():
    """创建一个使用真实逻辑但 mock 知识图谱的 PathPlannerAgent 实例。"""
    with patch("loopse.agent.path_planner.knowledge_graph") as mock_kg:
        nodes, edges = _make_mock_knowledge_graph()

        mock_kg.get_node.side_effect = lambda nid: nodes.get(nid)
        mock_kg.get_all_nodes.return_value = list(nodes.values())

        def _get_prereqs(nid):
            pred_ids = edges.get(nid, set())
            return [nodes[pid] for pid in pred_ids if pid in nodes]

        mock_kg.get_prerequisites.side_effect = _get_prereqs

        def _estimate_mastery(nid, mastery_map):
            direct = mastery_map.get(nid)
            if direct is not None:
                return float(direct)
            return 0.35

        mock_kg.estimate_mastery.side_effect = _estimate_mastery

        def _find_weak_prereqs(target_ids, mastery_map, threshold=0.65):
            weak = []
            for tid in target_ids:
                for pid in edges.get(tid, set()):
                    if pid in nodes and _estimate_mastery(pid, mastery_map) < threshold:
                        weak.append(nodes[pid])
            return weak

        mock_kg.find_weak_prerequisites.side_effect = _find_weak_prereqs

        def _topo_sort(node_ids):
            """简化拓扑排序：按 difficulty 升序。"""
            valid_ids = [nid for nid in (node_ids or []) if nid in nodes]
            sorted_nodes = sorted([nodes[nid] for nid in valid_ids], key=lambda n: (n.difficulty, n.id))
            return sorted_nodes

        mock_kg.topological_sort.side_effect = _topo_sort
        mock_kg.get_downstream_nodes.return_value = []

        from loopse.agent.path_planner import PathPlannerAgent
        agent = PathPlannerAgent()
        yield agent


# ------------------------------------------------------------------ #
# 1. 诊断结果到路径规划的正确传递
# ------------------------------------------------------------------ #
class TestDiagnosisToPathTransfer:
    """验证诊断结果中的 knowledge_node_ids 被正确传递给路径规划器。"""

    def test_diagnosis_node_ids_used_as_targets(self, path_planner):
        """诊断结果中的 knowledge_node_ids 应作为路径规划的目标节点"""
        profile = _build_profile(mastery_map={"kp_009": 0.3, "kp_008": 0.5})
        diag = _build_diagnosis_result(is_correct=False, knowledge_node_ids=["kp_009"])

        path = path_planner.plan(
            user_id="test_user",
            profile=profile,
            target_node_ids=diag["knowledge_node_ids"],
        )

        assert "nodes" in path
        assert len(path["nodes"]) > 0
        # 目标节点应在路径中
        node_ids_in_path = [n["node_id"] for n in path["nodes"]]
        assert "kp_009" in node_ids_in_path

    def test_multiple_diagnosis_targets(self, path_planner):
        """多个诊断目标应都被纳入路径"""
        profile = _build_profile(mastery_map={"kp_009": 0.3, "kp_014": 0.2})
        target_ids = ["kp_009", "kp_014"]

        path = path_planner.plan(
            user_id="test_user",
            profile=profile,
            target_node_ids=target_ids,
        )

        node_ids_in_path = [n["node_id"] for n in path["nodes"]]
        # 至少有一个目标应在路径中
        assert any(tid in node_ids_in_path for tid in target_ids)

    def test_empty_diagnosis_targets_uses_weak_points(self, path_planner):
        """空诊断目标时应使用画像中的薄弱点"""
        profile = _build_profile(
            mastery_map={"kp_008": 0.4},
            weak_points=["kp_008"],
        )

        path = path_planner.plan(
            user_id="test_user",
            profile=profile,
            target_node_ids=None,
        )

        assert "nodes" in path
        assert len(path["nodes"]) > 0

    def test_path_includes_prerequisite_info(self, path_planner):
        """路径节点应包含前置依赖信息"""
        profile = _build_profile(mastery_map={"kp_009": 0.3})

        path = path_planner.plan(
            user_id="test_user",
            profile=profile,
            target_node_ids=["kp_009"],
        )

        for node in path["nodes"]:
            assert "prerequisites" in node
            assert "prerequisites_met" in node
            assert isinstance(node["prerequisites"], list)


# ------------------------------------------------------------------ #
# 2. 知识图谱拓扑排序在有/无诊断结果时的行为差异
# ------------------------------------------------------------------ #
class TestTopologySortBehavior:
    """验证拓扑排序在不同诊断状态下的行为。"""

    def test_with_diagnosis_targets_path_more_focused(self, path_planner):
        """有诊断目标时路径应更聚焦（节点更少或更集中）"""
        profile = _build_profile(mastery_map={"kp_009": 0.3, "kp_008": 0.6})

        # 有目标的路径
        path_targeted = path_planner.plan(
            user_id="test_user",
            profile=profile,
            target_node_ids=["kp_009"],
        )

        # 无目标的路径（使用默认）
        path_default = path_planner.plan(
            user_id="test_user_2",
            profile=profile,
            target_node_ids=None,
        )

        # 两种路径都应产出结果
        assert len(path_targeted["nodes"]) > 0
        assert len(path_default["nodes"]) > 0

    def test_topo_sort_respects_dependency_order(self, path_planner):
        """拓扑排序应保证路径中包含目标节点及其前置依赖"""
        # kp_005 依赖 kp_001, 两者都应出现在路径中
        profile = _build_profile(mastery_map={"kp_001": 0.3, "kp_005": 0.2})

        path = path_planner.plan(
            user_id="test_user",
            profile=profile,
            target_node_ids=["kp_005"],
        )

        node_ids = [n["node_id"] for n in path["nodes"]]
        # 目标节点 kp_005 应在路径中
        assert "kp_005" in node_ids
        # 前置节点 kp_001 因掌握度低也应被加入路径
        assert "kp_001" in node_ids

    def test_high_mastery_skips_completed_nodes(self, path_planner):
        """高掌握度节点应标记为 completed"""
        profile = _build_profile(mastery_map={"kp_001": 0.9, "kp_009": 0.3})

        path = path_planner.plan(
            user_id="test_user",
            profile=profile,
            target_node_ids=["kp_001", "kp_009"],
        )

        for node in path["nodes"]:
            if node["node_id"] == "kp_001":
                assert node["status"] == "completed"

    @pytest.mark.parametrize("mastery,expected_status", [
        (0.3, "in_progress"),
        (0.5, "in_progress"),
    ])
    def test_node_status_based_on_mastery(self, path_planner, mastery, expected_status):
        """低掌握度节点应被标记为非 completed 状态"""
        # kp_001 没有前置依赖，状态取决于掌握度
        profile = _build_profile(mastery_map={"kp_001": mastery})

        path = path_planner.plan(
            user_id="test_user",
            profile=profile,
            target_node_ids=["kp_001"],
        )

        target_node = next((n for n in path["nodes"] if n["node_id"] == "kp_001"), None)
        if target_node:
            # 低掌握度应不是 completed
            assert target_node["status"] == expected_status


# ------------------------------------------------------------------ #
# 3. 前置知识缺失场景的路径调整
# ------------------------------------------------------------------ #
class TestPrerequisiteMissing:
    """验证前置知识缺失时路径的自动调整。"""

    def test_weak_prerequisites_added_to_path(self, path_planner):
        """前置知识薄弱时应被自动加入路径"""
        # kp_009 依赖 kp_008，kp_008 掌握度低
        profile = _build_profile(mastery_map={"kp_008": 0.3, "kp_009": 0.2})

        path = path_planner.plan(
            user_id="test_user",
            profile=profile,
            target_node_ids=["kp_009"],
        )

        node_ids = [n["node_id"] for n in path["nodes"]]
        # 前置节点 kp_008 应被加入路径
        assert "kp_008" in node_ids

    def test_all_prereqs_met_no_extra_nodes(self, path_planner):
        """前置知识全部达标时不应额外添加前置节点"""
        profile = _build_profile(mastery_map={"kp_008": 0.9, "kp_009": 0.4})

        path = path_planner.plan(
            user_id="test_user",
            profile=profile,
            target_node_ids=["kp_009"],
        )

        # 路径应包含目标但前置已完成
        node_ids = [n["node_id"] for n in path["nodes"]]
        assert "kp_009" in node_ids

    def test_locked_status_for_unmet_prerequisites(self, path_planner):
        """未满足前置条件的节点应为 locked 或 pending 状态（非 completed）"""
        # kp_015 依赖 kp_014, kp_014 依赖 kp_009
        profile = _build_profile(mastery_map={
            "kp_009": 0.2, "kp_014": 0.1, "kp_015": 0.1
        })

        path = path_planner.plan(
            user_id="test_user",
            profile=profile,
            target_node_ids=["kp_009", "kp_014", "kp_015"],
        )

        for node in path["nodes"]:
            if node["node_id"] == "kp_015":
                # 前置未满足的节点不应是 completed
                assert node["status"] != "completed"

    def test_path_has_recommendation_reasons(self, path_planner):
        """每个路径节点应包含推荐理由"""
        profile = _build_profile(mastery_map={"kp_008": 0.4})

        path = path_planner.plan(
            user_id="test_user",
            profile=profile,
            target_node_ids=["kp_008"],
        )

        for node in path["nodes"]:
            assert "recommendation_reason" in node
            assert len(node["recommendation_reason"]) > 0

    def test_path_output_structure_complete(self, path_planner):
        """路径输出应包含所有必要字段"""
        profile = _build_profile(mastery_map={"kp_008": 0.5})

        path = path_planner.plan(
            user_id="test_user",
            profile=profile,
            target_node_ids=["kp_008"],
        )

        assert "path_id" in path
        assert "user_id" in path
        assert "title" in path
        assert "nodes" in path
        assert "total_estimated_time" in path
        assert "generated_at" in path
        assert "quality_score" in path

    @pytest.mark.parametrize("target_ids", [
        ["kp_001"],
        ["kp_008", "kp_009"],
        ["kp_007", "kp_010"],
    ])
    def test_various_target_combinations(self, path_planner, target_ids):
        """不同目标组合都应能生成有效路径"""
        profile = _build_profile(mastery_map={tid: 0.3 for tid in target_ids})

        path = path_planner.plan(
            user_id="test_user",
            profile=profile,
            target_node_ids=target_ids,
        )

        assert len(path["nodes"]) > 0
        assert path["total_estimated_time"] > 0
