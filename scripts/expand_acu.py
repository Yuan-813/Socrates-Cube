"""扩展 knowledge_graph.json 中的 cognitive_nodes，从 48 个 ACU 扩展到 60 个。

新增12个 ACU：
- kp_004（物理层）：3个 → 信号调制/复用技术/传输媒体
- kp_020（综合应用）：3个 → Wireshark使用/traceroute解读/故障排查流程
- kp_018（HTTP/应用层）：2个 → HTTP缓存机制/Cookie会话管理
- kp_019（网络安全）：2个 → TLS握手流程/防火墙策略配置
- kp_006（数据链路层/VLAN）：2个 → VLAN跨交换机/STP收敛过程
"""
import json
from pathlib import Path

fpath = Path("data/knowledge_graph.json")
data = json.loads(fpath.read_text(encoding="utf-8"))

new_acu = [
    # ── kp_004 物理层（3个）──────────────────────────────────
    {
        "id": "acu_049",
        "name": "signal_modulation_basics",
        "label": "信号调制与解调基本原理",
        "parent_curriculum_node": "kp_004",
        "related_misconceptions": [],
        "repair_strategies": [
            "animation:signal_modulation_demo",
            "exercise:modulation_type_identification"
        ]
    },
    {
        "id": "acu_050",
        "name": "channel_multiplexing_techniques",
        "label": "信道复用技术对比（FDM/TDM/CDMA/WDM）",
        "parent_curriculum_node": "kp_004",
        "related_misconceptions": [],
        "repair_strategies": [
            "contrast_table:multiplexing_comparison",
            "exercise:multiplexing_scenario"
        ]
    },
    {
        "id": "acu_051",
        "name": "transmission_media_types",
        "label": "传输媒体类型与特性对比",
        "parent_curriculum_node": "kp_004",
        "related_misconceptions": [],
        "repair_strategies": [
            "contrast_table:media_comparison",
            "exercise:media_selection"
        ]
    },

    # ── kp_020 综合应用（3个）──────────────────────────────────
    {
        "id": "acu_052",
        "name": "wireshark_packet_analysis",
        "label": "Wireshark抓包分析与协议解读",
        "parent_curriculum_node": "kp_020",
        "related_misconceptions": [],
        "repair_strategies": [
            "simulation:wireshark_lab",
            "exercise:packet_decode"
        ]
    },
    {
        "id": "acu_053",
        "name": "traceroute_interpretation",
        "label": "traceroute/tracert 输出解读与 TTL 机制",
        "parent_curriculum_node": "kp_020",
        "related_misconceptions": [],
        "repair_strategies": [
            "simulation:traceroute_demo",
            "exercise:hop_analysis"
        ]
    },
    {
        "id": "acu_054",
        "name": "network_troubleshooting_methodology",
        "label": "网络故障排查方法论（分层诊断流程）",
        "parent_curriculum_node": "kp_020",
        "related_misconceptions": [],
        "repair_strategies": [
            "checklist:troubleshooting_steps",
            "simulation:fault_scenario"
        ]
    },

    # ── kp_018 HTTP/应用层（2个）──────────────────────────────
    {
        "id": "acu_055",
        "name": "http_cache_mechanisms",
        "label": "HTTP 缓存机制（强缓存/协商缓存/Cache-Control）",
        "parent_curriculum_node": "kp_018",
        "related_misconceptions": [],
        "repair_strategies": [
            "contrast_table:cache_type_comparison",
            "exercise:cache_header_analysis"
        ]
    },
    {
        "id": "acu_056",
        "name": "cookie_session_management",
        "label": "Cookie 与 Session 会话管理机制",
        "parent_curriculum_node": "kp_018",
        "related_misconceptions": ["mc_115"],
        "repair_strategies": [
            "simulation:login_session_demo",
            "exercise:stateless_vs_stateful"
        ]
    },

    # ── kp_019 网络安全（2个）──────────────────────────────────
    {
        "id": "acu_057",
        "name": "tls_handshake_process",
        "label": "TLS 握手完整流程（证书验证/密钥协商）",
        "parent_curriculum_node": "kp_019",
        "related_misconceptions": ["mc_121", "mc_124"],
        "repair_strategies": [
            "simulation:tls_handshake_animation",
            "exercise:tls_step_ordering"
        ]
    },
    {
        "id": "acu_058",
        "name": "firewall_acl_configuration",
        "label": "防火墙策略与 ACL 配置逻辑",
        "parent_curriculum_node": "kp_019",
        "related_misconceptions": ["mc_122", "mc_128"],
        "repair_strategies": [
            "exercise:acl_rule_writing",
            "simulation:firewall_policy_demo"
        ]
    },

    # ── kp_006 数据链路层/VLAN（2个）──────────────────────────
    {
        "id": "acu_059",
        "name": "inter_vlan_routing_methods",
        "label": "跨 VLAN 路由实现方式（Router-on-a-stick / 三层交换）",
        "parent_curriculum_node": "kp_006",
        "related_misconceptions": ["mc_141"],
        "repair_strategies": [
            "simulation:vlan_routing_lab",
            "contrast_table:vlan_routing_methods"
        ]
    },
    {
        "id": "acu_060",
        "name": "stp_convergence_process",
        "label": "STP 收敛过程与端口状态迁移",
        "parent_curriculum_node": "kp_006",
        "related_misconceptions": ["mc_143", "mc_144", "mc_149"],
        "repair_strategies": [
            "simulation:stp_election_demo",
            "exercise:port_state_identification"
        ]
    },
]

# 追加到 cognitive_nodes
data["cognitive_nodes"].extend(new_acu)

fpath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
total_acu = len(data["cognitive_nodes"])
print(f"Done! Total ACU: {total_acu}")
