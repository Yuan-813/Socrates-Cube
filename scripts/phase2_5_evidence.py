"""
Phase 2.5 认知图谱硬证据验收
产出五项可复现的运行日志
"""
import sys, json, io
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import os
os.chdir(ROOT)

# 解决 Windows GBK 编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from loopse.kb.knowledge_graph import KnowledgeGraph, knowledge_graph
from loopse.kb.misconception_registry import MisconceptionRegistry
from loopse.agent.path_planner import PathPlannerAgent

print("=" * 60)
print("Phase 2.5 认知图谱验收 - 原始运行日志")
print("=" * 60)

kg = knowledge_graph  # 使用模块级单例（已加载 data/knowledge_graph.json）

# ===== 验收1：节点统计 =====
print("\n" + "=" * 60)
print("验收1：节点统计")
print("=" * 60)
all_nodes = list(kg._nodes.keys())
kp_nodes = [n for n in all_nodes if n.startswith("kp_")]
acu_nodes = [n for n in all_nodes if n.startswith("acu_")]
print(f"len(kg._nodes) = {len(kg._nodes)}")
print(f"  kp_* 节点: {len(kp_nodes)}")
print(f"  acu_* 节点: {len(acu_nodes)}")
print(f"\nkp_* 列表: {sorted(kp_nodes)}")
print(f"\nacu_* 列表: {sorted(acu_nodes)}")

# ===== 验收2：边统计 =====
print("\n" + "=" * 60)
print("验收2：边统计（prerequisite edges）")
print("=" * 60)
total_edges = sum(len(targets) for targets in kg._successors.values())
# 分类统计：kp→kp, acu→acu, kp→acu, acu→kp
kp_to_kp = 0
acu_to_acu = 0
cross_edges = 0
for src, targets in kg._successors.items():
    for dst in targets:
        if src.startswith("kp_") and dst.startswith("kp_"):
            kp_to_kp += 1
        elif src.startswith("acu_") and dst.startswith("acu_"):
            acu_to_acu += 1
        else:
            cross_edges += 1
print(f"总 prerequisite 边数: {total_edges}")
print(f"  kp→kp: {kp_to_kp}")
print(f"  acu→acu: {acu_to_acu}")
print(f"  跨层边: {cross_edges}")
print(f"\nACU层边列表:")
for src, targets in sorted(kg._successors.items()):
    for dst in sorted(targets):
        if src.startswith("acu_") and dst.startswith("acu_"):
            print(f"  {src} -> {dst}")

# ===== 验收3：依赖链 =====
print("\n" + "=" * 60)
print("验收3：依赖链 - get_all_prerequisites('acu_025')")
print("=" * 60)

prereqs_025 = kg.get_all_prerequisites("acu_025")
direct_025 = kg.get_prerequisites("acu_025")
print(f"acu_025 的直接前置: {sorted([n.id for n in direct_025])}")
print(f"acu_025 的全部前置（递归）: {sorted([n.id for n in prereqs_025])}")

# 也测试 acu_027 和 acu_029
prereqs_027 = kg.get_all_prerequisites("acu_027")
direct_027 = kg.get_prerequisites("acu_027")
print(f"\nacu_027 的直接前置: {sorted([n.id for n in direct_027])}")
print(f"acu_027 的全部前置（递归）: {sorted([n.id for n in prereqs_027])}")

prereqs_029 = kg.get_all_prerequisites("acu_029")
direct_029 = kg.get_prerequisites("acu_029")
print(f"\nacu_029 的直接前置: {sorted([n.id for n in direct_029])}")
print(f"acu_029 的全部前置（递归）: {sorted([n.id for n in prereqs_029])}")

# ===== 验收4：路径规划 =====
print("\n" + "=" * 60)
print("验收4：PathPlanner 路径规划 - target_node_ids=['acu_025']")
print("=" * 60)

# 构造 mastery_map：acu_025 掌握度低
mastery_map = {}
for nid in kg._nodes:
    mastery_map[nid] = 0.8  # 默认都已掌握
mastery_map["acu_025"] = 0.3  # acu_025 薄弱
# 也让前置节点稍弱
for p in kg._predecessors.get("acu_025", set()):
    mastery_map[p] = 0.4

planner = PathPlannerAgent()

# 构造 profile 字典
profile1 = {
    "mastery_map": mastery_map,
    "weak_points": ["acu_025"],
    "strong_points": [nid for nid, s in mastery_map.items() if s >= 0.8],
    "conceptual_understanding": 0.5,
    "protocol_analysis": 0.5,
    "calculation_ability": 0.5,
    "cognitive_style": "textual",
}

path_result = planner.plan(
    user_id="test_user",
    profile=profile1,
    target_node_ids=["acu_025"],
    max_nodes=10,
)
print(f"输入 target_node_ids: ['acu_025']")
print(f"PathPlanner 输出路径:")
# 打印精简版（不含 agent_trace）
path_output = {k: v for k, v in path_result.items() if k != "agent_trace"}
print(json.dumps(path_output, indent=2, ensure_ascii=False))

# 再测一个：acu_028
print(f"\n{'─' * 40}")
mastery_map2 = {nid: 0.8 for nid in kg._nodes}
mastery_map2["acu_028"] = 0.25
for p in kg._predecessors.get("acu_028", set()):
    mastery_map2[p] = 0.4

profile2 = {
    "mastery_map": mastery_map2,
    "weak_points": ["acu_028"],
    "strong_points": [nid for nid, s in mastery_map2.items() if s >= 0.8],
    "conceptual_understanding": 0.5,
    "protocol_analysis": 0.5,
    "calculation_ability": 0.5,
    "cognitive_style": "textual",
}

path_result2 = planner.plan(
    user_id="test_user",
    profile=profile2,
    target_node_ids=["acu_028"],
    max_nodes=10,
)
print(f"\n输入 target_node_ids: ['acu_028']")
print(f"PathPlanner 输出路径:")
path_output2 = {k: v for k, v in path_result2.items() if k != "agent_trace"}
print(json.dumps(path_output2, indent=2, ensure_ascii=False))

# ===== 验收5：完整诊断链路 =====
print("\n" + "=" * 60)
print("验收5：完整诊断链路追踪")
print("=" * 60)
print("输入: '两次握手就够了' → error_type='flow_omission', knowledge_point='TCP 三次握手'")
print("-" * 40)

registry = MisconceptionRegistry()

# Step 1: 误解库匹配（使用实际接口：error_type + knowledge_point）
print("\nStep 1: MisconceptionRegistry.match_from_diagnosis()")
matched = registry.match_from_diagnosis("flow_omission", "TCP 三次握手")
if matched:
    print(f"  命中误解: {matched.get('id')}")
    print(f"  misconception: {matched.get('misconception')}")
    print(f"  knowledge_node_ids: {matched.get('knowledge_node_ids')}")
    print(f"  error_type: {matched.get('error_type')}")
    print(f"  knowledge_point: {matched.get('knowledge_point')}")
else:
    # fallback: 手动查找 mc_001
    print("  match_from_diagnosis 未命中，尝试 get_by_id('mc_001')...")
    mc_001 = registry.get_by_id("mc_001")
    if mc_001:
        matched = mc_001
        print(f"  手动查找 mc_001: {mc_001.get('misconception')}")
        print(f"  knowledge_node_ids: {mc_001.get('knowledge_node_ids')}")

# Step 2: 提取节点
if matched:
    node_ids = matched.get("knowledge_node_ids", [])
    print(f"\nStep 2: 提取 knowledge_node_ids = {node_ids}")

    # Step 3: Profiler mastery 更新模拟
    print(f"\nStep 3: Profiler mastery_map 更新模拟")
    test_mastery = {nid: 0.5 for nid in kg._nodes}
    print(f"  更新前: ", end="")
    for nid in node_ids:
        print(f"{nid}={test_mastery.get(nid, 'N/A')}", end=" ")
    print()

    # 模拟诊断失败导致分数下降
    for nid in node_ids:
        old = test_mastery.get(nid, 0.5)
        test_mastery[nid] = round(max(0.0, old - 0.07), 3)

    print(f"  更新后: ", end="")
    for nid in node_ids:
        print(f"{nid}={test_mastery.get(nid, 'N/A')}", end=" ")
    print()

    # Step 4: PathPlanner
    print(f"\nStep 4: PathPlanner 路径规划")
    for nid in node_ids:
        test_mastery[nid] = 0.3
    for nid in node_ids:
        for p in kg._predecessors.get(nid, set()):
            test_mastery[p] = 0.4

    profile_final = {
        "mastery_map": test_mastery,
        "weak_points": node_ids,
        "strong_points": [nid for nid, s in test_mastery.items() if s >= 0.8],
        "conceptual_understanding": 0.5,
        "protocol_analysis": 0.5,
        "calculation_ability": 0.5,
        "cognitive_style": "textual",
    }

    path_final = planner.plan(
        user_id="test_user",
        profile=profile_final,
        target_node_ids=node_ids,
        max_nodes=10,
    )
    print(f"  输入 target_node_ids: {node_ids}")
    print(f"  PathPlanner 输出:")
    path_final_output = {k: v for k, v in path_final.items() if k != "agent_trace"}
    print(f"  {json.dumps(path_final_output, indent=4, ensure_ascii=False)}")

print("\n" + "=" * 60)
print("Phase 2.5 验收完成")
print("=" * 60)
