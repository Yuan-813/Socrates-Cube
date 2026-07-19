"""扩展 knowledge_graph.json：新增技能/认证/岗位节点及连边。"""
import json
from pathlib import Path

fpath = Path("data/knowledge_graph.json")
data = json.loads(fpath.read_text(encoding="utf-8"))

# === 新增技能实践节点 ===
new_skill_nodes = [
    {
        "id": "skill_001", "name": "Wireshark抓包分析",
        "chapter": "实践技能", "type": "skill", "difficulty": 3,
        "estimated_time": 45,
        "keywords": ["Wireshark", "抓包", "报文分析", "协议解析"],
        "description": "掌握使用Wireshark进行网络报文捕获与协议分析的核心技能。"
    },
    {
        "id": "skill_002", "name": "路由器基础配置",
        "chapter": "实践技能", "type": "skill", "difficulty": 3,
        "estimated_time": 60,
        "keywords": ["路由器", "配置", "静态路由", "动态路由", "CLI"],
        "description": "掌握路由器基础配置，包括静态路由和动态路由协议配置。"
    },
    {
        "id": "skill_003", "name": "交换机VLAN配置",
        "chapter": "实践技能", "type": "skill", "difficulty": 3,
        "estimated_time": 50,
        "keywords": ["交换机", "VLAN", "Trunk", "Access", "配置"],
        "description": "掌握交换机VLAN划分、Trunk口和Access口的配置方法。"
    },
    {
        "id": "skill_004", "name": "防火墙策略配置",
        "chapter": "实践技能", "type": "skill", "difficulty": 4,
        "estimated_time": 60,
        "keywords": ["防火墙", "ACL", "访问控制", "安全策略"],
        "description": "掌握防火墙基本策略配置，包括ACL和安全区域划分。"
    },
    {
        "id": "skill_005", "name": "Linux网络配置",
        "chapter": "实践技能", "type": "skill", "difficulty": 3,
        "estimated_time": 45,
        "keywords": ["Linux", "ip命令", "ifconfig", "网络配置", "iptables"],
        "description": "掌握Linux系统下的网络接口配置、路由管理和防火墙设置。"
    },
    {
        "id": "skill_006", "name": "OSPF协议配置",
        "chapter": "实践技能", "type": "skill", "difficulty": 4,
        "estimated_time": 70,
        "keywords": ["OSPF", "链路状态", "区域", "DR/BDR", "配置"],
        "description": "掌握OSPF协议的配置与调试，包括多区域划分和路由汇总。"
    },
    {
        "id": "skill_007", "name": "网络故障排查",
        "chapter": "实践技能", "type": "skill", "difficulty": 4,
        "estimated_time": 60,
        "keywords": ["故障排查", "ping", "traceroute", "telnet", "诊断"],
        "description": "掌握系统化的网络故障排查方法，从物理层到应用层逐层定位问题。"
    },
    {
        "id": "skill_008", "name": "VPN与隧道技术",
        "chapter": "实践技能", "type": "skill", "difficulty": 4,
        "estimated_time": 55,
        "keywords": ["VPN", "IPSec", "GRE", "隧道", "加密"],
        "description": "了解VPN的工作原理，掌握IPSec和GRE隧道的基本配置。"
    },
    {
        "id": "skill_009", "name": "容器网络基础",
        "chapter": "实践技能", "type": "skill", "difficulty": 4,
        "estimated_time": 60,
        "keywords": ["Docker", "Kubernetes", "CNI", "容器网络", "overlay"],
        "description": "理解容器网络模型，掌握Docker网络和Kubernetes CNI基础知识。"
    },
    {
        "id": "skill_010", "name": "网络性能调优",
        "chapter": "实践技能", "type": "skill", "difficulty": 5,
        "estimated_time": 75,
        "keywords": ["性能", "调优", "带宽", "延迟", "TCP优化"],
        "description": "掌握网络性能分析方法，能够对TCP参数和网络配置进行调优。"
    },
]

# === 新增认证节点 ===
new_cert_nodes = [
    {
        "id": "cert_001", "name": "华为HCIA-Datacom认证",
        "chapter": "职业认证", "type": "certification", "difficulty": 4,
        "estimated_time": 120,
        "keywords": ["HCIA", "华为", "Datacom", "认证", "数据通信"],
        "description": "华为认证网络工程师（HCIA-Datacom），覆盖路由交换、IP基础和网络安全入门。"
    },
    {
        "id": "cert_002", "name": "华为HCIP-Datacom认证",
        "chapter": "职业认证", "type": "certification", "difficulty": 5,
        "estimated_time": 180,
        "keywords": ["HCIP", "华为", "高级认证", "OSPF", "BGP"],
        "description": "华为高级认证网络工程师（HCIP-Datacom），深入掌握企业网络规划与运维。"
    },
    {
        "id": "cert_003", "name": "思科CCNA认证",
        "chapter": "职业认证", "type": "certification", "difficulty": 4,
        "estimated_time": 120,
        "keywords": ["CCNA", "思科", "Cisco", "认证", "路由交换"],
        "description": "思科认证网络工程师（CCNA），国际认可的入门级网络认证。"
    },
    {
        "id": "cert_004", "name": "思科CCNP Enterprise认证",
        "chapter": "职业认证", "type": "certification", "difficulty": 5,
        "estimated_time": 200,
        "keywords": ["CCNP", "思科", "高级认证", "企业网络"],
        "description": "思科专业级认证（CCNP Enterprise），专注于企业网络解决方案。"
    },
    {
        "id": "cert_005", "name": "计算机网络技术高级证书",
        "chapter": "职业认证", "type": "certification", "difficulty": 3,
        "estimated_time": 90,
        "keywords": ["网络技术", "高级", "证书", "软件水平"],
        "description": "国内计算机网络相关高级专业技术认证，适合国内就业市场。"
    },
]

# === 新增岗位节点（叶节点，仅作目标，不作prerequisite源） ===
new_job_nodes = [
    {
        "id": "job_001", "name": "网络工程师",
        "chapter": "职业方向", "type": "career_target", "difficulty": 4,
        "estimated_time": 0,
        "keywords": ["网络工程师", "运维", "路由交换", "网络规划"],
        "description": "负责企业网络基础设施的规划、部署和运维，需熟练掌握路由交换技术。"
    },
    {
        "id": "job_002", "name": "云计算网络工程师",
        "chapter": "职业方向", "type": "career_target", "difficulty": 5,
        "estimated_time": 0,
        "keywords": ["云计算", "SDN", "云网络", "Overlay"],
        "description": "专注于云平台的网络架构设计，需掌握SDN、Overlay网络和容器网络技术。"
    },
    {
        "id": "job_003", "name": "网络安全工程师",
        "chapter": "职业方向", "type": "career_target", "difficulty": 4,
        "estimated_time": 0,
        "keywords": ["网络安全", "防火墙", "渗透测试", "安全运营"],
        "description": "负责企业网络安全防护，包括防火墙管理、安全审计和应急响应。"
    },
    {
        "id": "job_004", "name": "DevOps工程师",
        "chapter": "职业方向", "type": "career_target", "difficulty": 4,
        "estimated_time": 0,
        "keywords": ["DevOps", "CI/CD", "容器", "自动化", "网络"],
        "description": "负责软件交付流程中的基础设施与网络自动化，需了解容器网络和微服务。"
    },
    {
        "id": "job_005", "name": "后端开发工程师",
        "chapter": "职业方向", "type": "career_target", "difficulty": 3,
        "estimated_time": 0,
        "keywords": ["后端", "API", "HTTP", "TCP", "服务端"],
        "description": "开发高性能后端服务，需深刻理解TCP/IP和HTTP协议的工作机制。"
    },
]

# 追加所有新节点
data["nodes"].extend(new_skill_nodes)
data["nodes"].extend(new_cert_nodes)
data["nodes"].extend(new_job_nodes)

# === 新增连边（leads_to：KP→skill→cert→job） ===
new_edges = [
    # KP → 技能节点（prerequisite关系）
    {"from": "kp_020", "to": "skill_001", "relation": "leads_to"},
    {"from": "kp_010", "to": "skill_002", "relation": "leads_to"},
    {"from": "kp_006", "to": "skill_003", "relation": "leads_to"},
    {"from": "kp_019", "to": "skill_004", "relation": "leads_to"},
    {"from": "kp_007", "to": "skill_005", "relation": "leads_to"},
    {"from": "kp_010", "to": "skill_006", "relation": "leads_to"},
    {"from": "kp_020", "to": "skill_007", "relation": "leads_to"},
    {"from": "kp_019", "to": "skill_008", "relation": "leads_to"},
    {"from": "kp_019", "to": "skill_009", "relation": "leads_to"},
    {"from": "kp_015", "to": "skill_010", "relation": "leads_to"},
    # 技能 → 认证
    {"from": "skill_001", "to": "cert_001", "relation": "leads_to"},
    {"from": "skill_002", "to": "cert_001", "relation": "leads_to"},
    {"from": "skill_003", "to": "cert_001", "relation": "leads_to"},
    {"from": "cert_001", "to": "cert_002", "relation": "leads_to"},
    {"from": "skill_002", "to": "cert_003", "relation": "leads_to"},
    {"from": "skill_006", "to": "cert_003", "relation": "leads_to"},
    {"from": "cert_003", "to": "cert_004", "relation": "leads_to"},
    # 认证 → 岗位
    {"from": "cert_001", "to": "job_001", "relation": "leads_to"},
    {"from": "cert_002", "to": "job_001", "relation": "leads_to"},
    {"from": "cert_003", "to": "job_001", "relation": "leads_to"},
    {"from": "cert_004", "to": "job_001", "relation": "leads_to"},
    {"from": "cert_002", "to": "job_002", "relation": "leads_to"},
    {"from": "skill_009", "to": "job_002", "relation": "leads_to"},
    {"from": "skill_004", "to": "job_003", "relation": "leads_to"},
    {"from": "cert_003", "to": "job_003", "relation": "leads_to"},
    {"from": "skill_009", "to": "job_004", "relation": "leads_to"},
    {"from": "skill_005", "to": "job_004", "relation": "leads_to"},
    {"from": "kp_018", "to": "job_005", "relation": "leads_to"},
    {"from": "kp_015", "to": "job_005", "relation": "leads_to"},
    # KP直接 → 岗位（辅助）
    {"from": "kp_019", "to": "job_003", "relation": "leads_to"},
]

data["edges"].extend(new_edges)

fpath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
total_nodes = len(data["nodes"])
total_edges = len(data["edges"])
print(f"Done! Total nodes: {total_nodes}, edges: {total_edges}")
