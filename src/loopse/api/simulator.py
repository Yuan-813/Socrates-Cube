"""Simulator scenario routes."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/simulator", tags=["simulator"])

# 仿真场景定义（与前端 SimulatorPlayer.vue 保持一致）
SCENARIOS = {
    "three_way_handshake": {
        "label": "TCP 三次握手",
        "desc": "建立 TCP 连接的标准流程",
        "steps": [
            {"from": "client", "to": "server", "flags": ["SYN"], "seq": 100, "ack": 0,
             "clientState": "SYN_SENT", "serverState": "LISTEN",
             "desc": "客户端发送同步请求，初始序列号 ISN=100"},
            {"from": "server", "to": "client", "flags": ["SYN", "ACK"], "seq": 200, "ack": 101,
             "clientState": "SYN_SENT", "serverState": "SYN_RCVD",
             "desc": "服务端确认并同步，分配初始序列号 ISN=200"},
            {"from": "client", "to": "server", "flags": ["ACK"], "seq": 101, "ack": 201,
             "clientState": "ESTABLISHED", "serverState": "ESTABLISHED",
             "desc": "客户端确认，双方进入 ESTABLISHED 状态"},
        ],
    },
    "four_way_wavehand": {
        "label": "TCP 四次挥手",
        "desc": "优雅关闭 TCP 连接",
        "steps": [
            {"from": "client", "to": "server", "flags": ["FIN", "ACK"], "seq": 500, "ack": 400,
             "clientState": "FIN_WAIT_1", "serverState": "ESTABLISHED",
             "desc": "客户端发起关闭请求"},
            {"from": "server", "to": "client", "flags": ["ACK"], "seq": 400, "ack": 501,
             "clientState": "FIN_WAIT_2", "serverState": "CLOSE_WAIT",
             "desc": "服务端确认收到 FIN"},
            {"from": "server", "to": "client", "flags": ["FIN", "ACK"], "seq": 401, "ack": 501,
             "clientState": "TIME_WAIT", "serverState": "LAST_ACK",
             "desc": "服务端发送 FIN"},
            {"from": "client", "to": "server", "flags": ["ACK"], "seq": 501, "ack": 402,
             "clientState": "CLOSED", "serverState": "CLOSED",
             "desc": "客户端最后确认，等待 2MSL 后关闭"},
        ],
    },
    "sliding_window": {
        "label": "TCP 滑动窗口",
        "desc": "连续数据传输与流量控制",
        "steps": [
            {"from": "client", "to": "server", "flags": ["ACK"], "seq": 1000, "ack": 1,
             "clientState": "ESTABLISHED", "serverState": "ESTABLISHED",
             "desc": "ACK 确认，窗口大小通告 win=4096", "dataLen": 0},
            {"from": "client", "to": "server", "flags": ["PSH", "ACK"], "seq": 1000, "ack": 1,
             "clientState": "ESTABLISHED", "serverState": "ESTABLISHED",
             "desc": "发送数据段 #1，1024字节", "dataLen": 1024},
            {"from": "client", "to": "server", "flags": ["PSH", "ACK"], "seq": 2024, "ack": 1,
             "clientState": "ESTABLISHED", "serverState": "ESTABLISHED",
             "desc": "发送数据段 #2，1024字节", "dataLen": 1024},
            {"from": "server", "to": "client", "flags": ["ACK"], "seq": 1, "ack": 2024,
             "clientState": "ESTABLISHED", "serverState": "ESTABLISHED",
             "desc": "累积确认，窗口减小", "dataLen": 0},
            {"from": "client", "to": "server", "flags": ["PSH", "ACK"], "seq": 3048, "ack": 1,
             "clientState": "ESTABLISHED", "serverState": "ESTABLISHED",
             "desc": "发送数据段 #3，1024字节", "dataLen": 1024},
            {"from": "server", "to": "client", "flags": ["ACK"], "seq": 1, "ack": 4072,
             "clientState": "ESTABLISHED", "serverState": "ESTABLISHED",
             "desc": "确认所有数据，窗口 win=2048", "dataLen": 0},
        ],
    },
    "http_request": {
        "label": "HTTP 请求响应",
        "desc": "应用层请求与响应过程",
        "steps": [
            {"from": "client", "to": "server", "flags": ["SYN"], "seq": 100, "ack": 0,
             "clientState": "SYN_SENT", "serverState": "LISTEN",
             "desc": "Step 1: 建立 TCP 连接 — SYN"},
            {"from": "server", "to": "client", "flags": ["SYN", "ACK"], "seq": 200, "ack": 101,
             "clientState": "SYN_SENT", "serverState": "SYN_RCVD",
             "desc": "Step 2: SYN+ACK"},
            {"from": "client", "to": "server", "flags": ["ACK"], "seq": 101, "ack": 201,
             "clientState": "ESTABLISHED", "serverState": "ESTABLISHED",
             "desc": "Step 3: TCP 连接建立"},
            {"from": "client", "to": "server", "flags": ["PSH", "ACK"], "seq": 101, "ack": 201,
             "clientState": "ESTABLISHED", "serverState": "ESTABLISHED",
             "desc": "Step 4: HTTP GET 请求", "dataLen": 128},
            {"from": "server", "to": "client", "flags": ["ACK"], "seq": 201, "ack": 229,
             "clientState": "ESTABLISHED", "serverState": "ESTABLISHED",
             "desc": "Step 5: 确认收到请求", "dataLen": 0},
            {"from": "server", "to": "client", "flags": ["PSH", "ACK"], "seq": 201, "ack": 229,
             "clientState": "ESTABLISHED", "serverState": "ESTABLISHED",
             "desc": "Step 6: HTTP 200 OK 响应", "dataLen": 2048},
            {"from": "client", "to": "server", "flags": ["ACK"], "seq": 229, "ack": 2249,
             "clientState": "ESTABLISHED", "serverState": "ESTABLISHED",
             "desc": "Step 7: 确认收到响应", "dataLen": 0},
        ],
    },
    "http_encapsulation": {
        "label": "HTTP 分层封装",
        "desc": "数据从上到下逐层封装过程",
        "steps": [
            {"from": "client", "to": "server", "flags": ["APP"], "seq": 0, "ack": 0,
             "clientState": "应用层", "serverState": "应用层",
             "desc": "应用层：生成 HTTP 请求报文（Method + URL + Headers + Body）"},
            {"from": "client", "to": "server", "flags": ["TCP"], "seq": 0, "ack": 0,
             "clientState": "传输层", "serverState": "传输层",
             "desc": "传输层：添加 TCP 头部（源端口:49152 → 目的端口:80，序列号，校验和）"},
            {"from": "client", "to": "server", "flags": ["IP"], "seq": 0, "ack": 0,
             "clientState": "网络层", "serverState": "网络层",
             "desc": "网络层：添加 IP 头部（源IP:192.168.1.100 → 目的IP:93.184.216.34，TTL=64）"},
            {"from": "client", "to": "server", "flags": ["ETH"], "seq": 0, "ack": 0,
             "clientState": "数据链路层", "serverState": "数据链路层",
             "desc": "数据链路层：添加以太网帧头（源MAC → 目的MAC，EtherType=0x0800）"},
            {"from": "client", "to": "server", "flags": ["PHY"], "seq": 0, "ack": 0,
             "clientState": "物理层", "serverState": "物理层",
             "desc": "物理层：转换为比特流在物理介质上传输"},
            {"from": "server", "to": "client", "flags": ["DE-CAP"], "seq": 0, "ack": 0,
             "clientState": "物理层→应用层", "serverState": "接收完成",
             "desc": "服务端逐层解封装：物理层→数据链路层→网络层→传输层→应用层"},
        ],
    },
    "dns_resolution": {
        "label": "DNS 解析",
        "desc": "域名到IP地址的解析过程",
        "steps": [
            {"from": "client", "to": "server", "flags": ["QUERY"], "seq": 1, "ack": 0,
             "clientState": "发起查询", "serverState": "本地DNS",
             "desc": "客户端向本地 DNS 服务器发起递归查询：www.example.com → ?"},
            {"from": "server", "to": "client", "flags": ["ITER"], "seq": 2, "ack": 1,
             "clientState": "等待", "serverState": "根服务器",
             "desc": "本地 DNS 向根服务器发起迭代查询，根服务器返回 .com TLD 地址"},
            {"from": "server", "to": "client", "flags": ["ITER"], "seq": 3, "ack": 2,
             "clientState": "等待", "serverState": "TLD服务器",
             "desc": "本地 DNS 向 .com TLD 服务器查询，返回 example.com 权威 DNS 地址"},
            {"from": "server", "to": "client", "flags": ["ITER"], "seq": 4, "ack": 3,
             "clientState": "等待", "serverState": "权威DNS",
             "desc": "本地 DNS 向权威 DNS 查询 www.example.com，获得 IP: 93.184.216.34"},
            {"from": "server", "to": "client", "flags": ["RESP"], "seq": 5, "ack": 4,
             "clientState": "解析完成", "serverState": "本地DNS",
             "desc": "本地 DNS 将结果返回客户端：www.example.com → 93.184.216.34（缓存TTL=3600s）"},
        ],
    },
    "congestion_control_basic": {
        "label": "拥塞控制（基础版）",
        "desc": "TCP 拥塞窗口变化过程",
        "steps": [
            {"from": "client", "to": "server", "flags": ["SS"], "seq": 1, "ack": 0,
             "clientState": "慢启动 cwnd=1", "serverState": "等待",
             "desc": "慢启动阶段：cwnd=1 MSS，发送1个报文段"},
            {"from": "server", "to": "client", "flags": ["ACK"], "seq": 1, "ack": 1,
             "clientState": "慢启动 cwnd=2", "serverState": "确认",
             "desc": "收到ACK，cwnd翻倍：1→2 MSS（指数增长）"},
            {"from": "client", "to": "server", "flags": ["SS"], "seq": 2, "ack": 0,
             "clientState": "慢启动 cwnd=4", "serverState": "等待",
             "desc": "发送2个段，收到ACK后 cwnd→4 MSS"},
            {"from": "client", "to": "server", "flags": ["CA"], "seq": 4, "ack": 0,
             "clientState": "拥塞避免 cwnd=5", "serverState": "等待",
             "desc": "达到ssthresh，进入拥塞避免：cwnd线性增长 +1/RTT"},
            {"from": "server", "to": "client", "flags": ["LOSS"], "seq": 5, "ack": 0,
             "clientState": "丢包！cwnd减半", "serverState": "丢包检测",
             "desc": "检测到丢包！ssthresh=cwnd/2，cwnd=ssthresh（快重传/快恢复）"},
            {"from": "client", "to": "server", "flags": ["CA"], "seq": 6, "ack": 0,
             "clientState": "拥塞避免 线性增长", "serverState": "恢复",
             "desc": "重新进入拥塞避免阶段，cwnd继续线性增长"},
        ],
    },
}


@router.get("/scenarios")
def list_scenarios():
    """获取所有仿真场景列表。"""
    return {
        "scenarios": [
            {"value": key, "label": val["label"], "desc": val["desc"], "step_count": len(val["steps"])}
            for key, val in SCENARIOS.items()
        ]
    }


@router.get("/scenarios/{scenario_id}")
def get_scenario(scenario_id: str):
    """获取指定场景的完整步骤数据。"""
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail=f"场景 {scenario_id} 不存在")
    return SCENARIOS[scenario_id]


@router.post("/run")
def run_simulation(scenario_id: str):
    """运行仿真（返回完整步骤序列）。"""
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail=f"场景 {scenario_id} 不存在")
    scenario = SCENARIOS[scenario_id]
    return {
        "scenario_id": scenario_id,
        "label": scenario["label"],
        "steps": scenario["steps"],
        "total_steps": len(scenario["steps"]),
    }
