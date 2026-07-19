#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_resource_node_id.py
将 learning_resources 表中所有 knowledge_node_id=NULL 的记录，
根据 knowledge_point 文本字段映射到正确的 kp_xxx 节点 ID 并更新。

运行：
    .venv/Scripts/python.exe scripts/fix_resource_node_id.py
"""
import os, sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv; load_dotenv()
import pymysql

# ─────────────────────────────────────────────────────────
# 1. 连接配置
# ─────────────────────────────────────────────────────────
url = os.getenv("DATABASE_URL", "")
rest = url.split("://", 1)[1].split("?")[0]
userpass, hostpart = rest.rsplit("@", 1)
user, password = userpass.split(":", 1)
hostport, dbname = hostpart.rsplit("/", 1)
host, port = hostport.rsplit(":", 1)

conn = pymysql.connect(
    host=host, port=int(port), user=user, password=password,
    db=dbname, charset="utf8mb4", connect_timeout=20
)
cur = conn.cursor()

# ─────────────────────────────────────────────────────────
# 2. 查出所有不同的 knowledge_point 值
# ─────────────────────────────────────────────────────────
cur.execute("SELECT DISTINCT knowledge_point FROM learning_resources ORDER BY knowledge_point")
kp_values = [row[0] for row in cur.fetchall()]
print("=== 现有 knowledge_point 值 ===")
for v in kp_values:
    print(f"  '{v}'")

# ─────────────────────────────────────────────────────────
# 3. 手工映射表：knowledge_point 文本 → kp_xxx ID
#    规则：按语义最近的课程节点对应
# ─────────────────────────────────────────────────────────
KP_MAP = {
    # 第1章：网络概述 / OSI / TCP-IP
    "计算机网络概述":       "kp_001",
    "OSI七层模型":          "kp_002",
    "OSI模型":              "kp_002",
    "TCP/IP体系结构":       "kp_003",
    "TCP/IP分层模型":       "kp_003",
    "PDU协议数据单元":      "kp_002",   # 分层封装概念属第1章OSI
    "协议数据单元PDU":      "kp_002",

    # 第2章：物理层
    "物理层基本概念":       "kp_004",
    "物理层":               "kp_004",

    # 第3章：数据链路层 / 局域网
    "数据链路层基本概念":   "kp_005",
    "数据链路层":           "kp_005",
    "局域网技术":           "kp_006",
    "以太网交换机原理":     "kp_006",
    "以太网帧格式":         "kp_006",
    "以太网帧格式&数据转发路径": "kp_006",
    "CSMA/CD":              "kp_006",
    "CSMA/CD 碰撞检测":     "kp_006",

    # 第4章：网络层
    "网络层基本概念":       "kp_007",
    "网络层":               "kp_007",
    "ICMP协议":             "kp_007",   # ICMP属于网络层
    "IP地址与子网划分":     "kp_008",
    "IP地址":               "kp_008",
    "子网划分":             "kp_008",
    "ARP协议":              "kp_009",
    "路由选择协议":         "kp_010",
    "路由算法":             "kp_010",
    "路由选择基础":         "kp_010",
    "路由算法&动态路由协议": "kp_010",

    # 第5章：传输层
    "运输层基本概念":       "kp_011",
    "传输层基本概念":       "kp_011",
    "传输层概念":           "kp_011",
    "UDP协议":              "kp_012",
    "TCP协议基础":          "kp_013",
    "TCP可靠传输":          "kp_013",
    "TCP三次握手与四次挥手": "kp_014",
    "TCP三次握手":          "kp_014",
    "TCP四次挥手":          "kp_014",
    "TCP握手与挥手":        "kp_014",
    "TCP流量控制与拥塞控制": "kp_015",
    "TCP流量控制":          "kp_015",
    "TCP拥塞控制":          "kp_015",
    "TCP流控与拥塞":        "kp_015",
    "TCP流控&滑动窗口":     "kp_015",
    "TCP流量控制&拥塞控制": "kp_015",

    # 第6章：应用层
    "应用层基本概念":       "kp_016",
    "应用层":               "kp_016",
    "DNS协议":              "kp_017",
    "DNS解析流程":          "kp_017",
    "HTTP协议":             "kp_018",
    "HTTP与HTTPS":          "kp_018",
    "HTTPS&TLS":            "kp_018",
    "HTTPS/TLS":            "kp_018",
    "HTTP&HTTPS":           "kp_018",

    # 第7章：网络安全
    "网络安全基础":         "kp_019",
    "网络安全":             "kp_019",
    "TLS安全":              "kp_019",

    # 综合
    "综合应用与故障排查":   "kp_020",
    "故障排查":             "kp_020",
    "综合":                 "kp_020",
}

# ─────────────────────────────────────────────────────────
# 4. 对每个 knowledge_point 值做模糊匹配兜底
# ─────────────────────────────────────────────────────────
KEYWORD_FALLBACK = [
    (["ARP"],                           "kp_009"),
    (["DNS"],                           "kp_017"),
    (["HTTPS", "TLS", "SSL"],           "kp_018"),
    (["HTTP"],                          "kp_018"),
    (["ICMP", "ping", "traceroute"],    "kp_007"),
    (["UDP"],                           "kp_012"),
    (["TCP三次握手", "握手", "挥手", "SYN", "FIN"], "kp_014"),
    (["拥塞", "cwnd", "慢启动"],        "kp_015"),
    (["流量控制", "滑动窗口", "rwnd"],  "kp_015"),
    (["TCP"],                           "kp_013"),
    (["CSMA", "以太网", "交换机", "局域网", "MAC"], "kp_006"),
    (["路由", "BGP", "OSPF", "RIP"],    "kp_010"),
    (["子网", "IP地址", "CIDR"],        "kp_008"),
    (["IP", "网络层", "数据报"],        "kp_007"),
    (["传输层", "运输层", "端口"],      "kp_011"),
    (["TCP/IP", "分层"],                "kp_003"),
    (["OSI"],                           "kp_002"),
    (["物理层"],                        "kp_004"),
    (["数据链路", "帧"],                "kp_005"),
    (["应用层", "P2P", "C/S"],          "kp_016"),
    (["安全", "防火墙", "加密"],        "kp_019"),
    (["故障", "综合"],                  "kp_020"),
    (["PDU", "封装"],                   "kp_002"),
]


def resolve_node_id(knowledge_point: str) -> str | None:
    kp = (knowledge_point or "").strip()
    # 精确匹配
    if kp in KP_MAP:
        return KP_MAP[kp]
    # 模糊关键词匹配
    for keywords, node_id in KEYWORD_FALLBACK:
        for kw in keywords:
            if kw in kp:
                return node_id
    return None


# ─────────────────────────────────────────────────────────
# 5. 查出所有资源，逐条更新
# ─────────────────────────────────────────────────────────
cur.execute("SELECT resource_id, knowledge_point, knowledge_node_id FROM learning_resources")
rows = cur.fetchall()

updated = 0
skipped = 0
unmapped = []

for resource_id, knowledge_point, knowledge_node_id in rows:
    if knowledge_node_id:
        skipped += 1
        continue
    node_id = resolve_node_id(knowledge_point)
    if node_id:
        cur.execute(
            "UPDATE learning_resources SET knowledge_node_id=%s WHERE resource_id=%s",
            (node_id, resource_id)
        )
        updated += 1
    else:
        unmapped.append((resource_id, knowledge_point))

conn.commit()

print(f"\n=== 更新结果 ===")
print(f"  已更新: {updated} 条")
print(f"  已有node_id跳过: {skipped} 条")
print(f"  未能映射: {len(unmapped)} 条")
if unmapped:
    print("  未映射列表：")
    for rid, kp in unmapped:
        print(f"    {rid[:20]}... knowledge_point='{kp}'")

# ─────────────────────────────────────────────────────────
# 6. 验证：统计每个 kp_xxx 节点挂载了多少资源
# ─────────────────────────────────────────────────────────
cur.execute("""
    SELECT knowledge_node_id, resource_type, COUNT(*) as cnt
    FROM learning_resources
    WHERE knowledge_node_id IS NOT NULL
    GROUP BY knowledge_node_id, resource_type
    ORDER BY knowledge_node_id, resource_type
""")
print("\n=== 各节点资源分布 ===")
current_node = None
for node_id, rtype, cnt in cur.fetchall():
    if node_id != current_node:
        print(f"  {node_id}:")
        current_node = node_id
    print(f"    {rtype}: {cnt}")

cur.execute("SELECT COUNT(*) FROM learning_resources WHERE knowledge_node_id IS NULL")
null_cnt = cur.fetchone()[0]
print(f"\n  仍为NULL的资源: {null_cnt} 条")

conn.close()
print("\n完成。")
