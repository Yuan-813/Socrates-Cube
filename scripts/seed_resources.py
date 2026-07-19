#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Socrates-Cube 高质量学习资源种子脚本
覆盖计算机网络核心知识体系，分六阶段系统构建：
  Phase1: 网络体系结构
  Phase2: 传输层核心
  Phase3: UDP与Socket编程
  Phase4: 网络层
  Phase5: 应用层
  Phase6: 数据链路层

运行方式：python scripts/seed_resources.py
"""
import sys
import uuid
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.loopse.db.repositories import ResourceRepository

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


def R(rtype: str, kp: str, title: str, content: str,
      difficulty: int = 3, **extra) -> dict:
    """快捷构造资源字典（兼容 ResourceRepository.save 格式）。"""
    meta = {"difficulty": difficulty}
    meta.update(extra)
    return {
        "resource_id": str(uuid.uuid4()),
        "resource_type": rtype,
        "knowledge_point": kp,
        "title": title,
        "content": content,
        "metadata": meta,
        "quality_score": 0.95,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 1  网络体系结构
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PHASE1 = [

# ──────────── OSI七层模型 ────────────
R("doc", "OSI七层模型", "【知识文档】OSI七层参考模型", r"""# OSI七层参考模型

## 一、背景与意义
OSI（Open Systems Interconnection）模型由 ISO 于 1984 年提出，将网络通信划分为 7 个逻辑层次，
目标是实现不同厂商设备间的互联互通。**实际互联网使用 TCP/IP 四层模型**，OSI 是理论参考框架。

## 二、七层结构（自下而上）

| 层 | 名称 | 主要功能 | 典型协议/设备 | PDU名称 |
|----|------|---------|-------------|---------|
| 1 | 物理层 | 比特流收发，定义电气/机械/功能特性 | 双绞线、光纤、Hub | 比特（Bit） |
| 2 | 数据链路层 | 帧封装、MAC寻址、差错检测（CRC）、流量控制 | 以太网、PPP、交换机 | 帧（Frame） |
| 3 | 网络层 | 逻辑寻址（IP）、路由选择、分组转发 | IP、ARP、ICMP、路由器 | 分组/包（Packet） |
| 4 | 传输层 | 端到端可靠传输，流量控制，拥塞控制，端口复用 | TCP、UDP | 报文段（Segment） |
| 5 | 会话层 | 建立/维护/终止会话，同步（断点续传） | NetBIOS、RPC | 数据（Data） |
| 6 | 表示层 | 数据格式转换、加密/解密、压缩 | SSL/TLS、JPEG、ASCII | 数据（Data） |
| 7 | 应用层 | 为用户进程提供网络服务入口 | HTTP、FTP、SMTP、DNS | 报文（Message） |

> 记忆口诀：**物数网传会表应**（由低到高）

## 三、封装与解封装

```
发送方（自顶向下封装）:
  应用层数据
  → [传输层头|数据]          ← 段（Segment）
  → [网络层头|段]            ← 包（Packet）
  → [链路层头|包|链路层尾]   ← 帧（Frame）
  → 0101...                  ← 比特（Bit）

接收方（自底向上解封装，逆过程）
```

## 四、相邻层间通过"服务访问点"（SAP）交互
- 上层向下层发出**服务原语**，下层向上层提供**服务**
- 同层实体之间依据**协议**进行通信（虚通信）
- 实际物理通信只发生在**物理层**

## 五、与 TCP/IP 模型对比

| OSI（7层） | TCP/IP（4层） | 主要协议 |
|-----------|--------------|---------|
| 应用层/表示层/会话层 | 应用层 | HTTP、DNS、SMTP、FTP |
| 传输层 | 传输层 | TCP、UDP |
| 网络层 | 网际层 | IP、ICMP、ARP |
| 数据链路层/物理层 | 网络接口层 | 以太网、Wi-Fi |

## 六、常见误区
- ❌ OSI模型是实际使用的模型 → 实际互联网用 TCP/IP
- ❌ 传输层负责路由 → 路由是**网络层**职责
- ❌ 物理层只管线缆 → 物理层还定义信号编码、传输速率、接口规格
""", difficulty=2),

R("exercise", "OSI七层模型", "【练习题】OSI七层模型综合练习", r"""## 知识点：OSI七层参考模型

---
### 选择题

**Q1. 下列设备中，工作在数据链路层的是？（单选）**

A. 集线器（Hub）
B. 路由器
C. 交换机（Switch）
D. 中继器

**答案：C**
**解析：** 集线器工作在物理层；路由器工作在网络层；中继器工作在物理层；**交换机工作在数据链路层**，依据 MAC 地址进行帧转发。

---
**Q2. OSI 模型中，负责端到端可靠传输的是哪一层？（单选）**

A. 网络层
B. 数据链路层
C. 传输层
D. 会话层

**答案：C**
**解析：** 传输层提供端到端（进程到进程）的可靠传输，包括流量控制、拥塞控制和差错恢复。网络层只负责点到点转发（逐跳）。

---
**Q3. 以下哪个说法是正确的？（多选）**

A. 物理层的PDU是比特
B. 网络层的PDU是帧
C. 传输层的PDU是报文段
D. 数据链路层通过CRC进行差错检测

**答案：ACD**
**解析：** 网络层的PDU是**分组（Packet/包）**，不是帧；帧是数据链路层的PDU。

---
### 判断题

**Q4. OSI 七层模型是目前互联网实际使用的模型。（ ）**

**答案：错误**
**解析：** 实际互联网使用 TCP/IP 四层模型（应用层、传输层、网际层、网络接口层），OSI 七层模型是理论参考模型。

---
### 简答题

**Q5. 简述 OSI 模型中数据从发送方到接收方的封装与解封装过程。**

**参考答案：**
发送方自顶向下封装：每经过一层，添加该层的协议头部（数据链路层还添加尾部）。最终以比特流通过物理介质传输。
接收方自底向上解封装：每经过一层，去掉该层的头部（尾部），将净载荷交给上一层处理，直到应用层获得原始数据。
""", difficulty=2),

R("mindmap", "OSI七层模型", "【思维导图】OSI七层模型知识体系", r"""```mermaid
graph TD
    A[OSI七层模型] --> B[物理层 L1]
    A --> C[数据链路层 L2]
    A --> D[网络层 L3]
    A --> E[传输层 L4]
    A --> F[会话层 L5]
    A --> G[表示层 L6]
    A --> H[应用层 L7]

    B --> B1[PDU: 比特]
    B --> B2[设备: Hub/中继器]
    B --> B3[功能: 电气/机械特性]

    C --> C1[PDU: 帧]
    C --> C2[设备: 交换机]
    C --> C3[MAC寻址/CRC差错检测]

    D --> D1[PDU: 包]
    D --> D2[设备: 路由器]
    D --> D3[IP寻址/路由选择]

    E --> E1[PDU: 报文段]
    E --> E2[TCP/UDP]
    E --> E3[端到端可靠/流量/拥塞控制]

    H --> H1[HTTP/FTP/DNS/SMTP]
    H --> H2[为应用进程提供服务]

    A --> I[❌常见误区]
    I --> I1[混淆PDU名称]
    I --> I2[以为OSI是实际标准]
    I --> I3[传输层与网络层功能混淆]
```""", difficulty=2),

# ──────────── TCP/IP四层模型 ────────────
R("doc", "TCP/IP四层模型", "【知识文档】TCP/IP四层模型与协议栈", r"""# TCP/IP 四层模型与协议栈

## 一、模型概述
TCP/IP 模型（也称 DoD 模型）是实际互联网使用的协议体系结构，由 ARPA 开发，共分四层。
与 OSI 七层模型不同，TCP/IP 是先有实现（协议），后有模型，具有更强的工程实用性。

## 二、四层结构

### 第4层：应用层（Application Layer）
- 直接面向用户，提供各类网络应用服务
- 主要协议：**HTTP/HTTPS**（Web）、**DNS**（域名解析）、**FTP**（文件传输）、
  **SMTP/POP3/IMAP**（邮件）、**SSH**（远程登录）、**DHCP**（地址分配）
- PDU：**报文（Message）**

### 第3层：传输层（Transport Layer）
- 提供进程到进程的端到端通信
- **TCP**：面向连接，可靠传输，字节流，流量/拥塞控制
- **UDP**：无连接，不可靠，数据报，低延迟
- 通过**端口号**区分同一主机上的不同进程
- PDU：**报文段（Segment）**

### 第2层：网际层（Internet Layer）
- 实现主机到主机的逻辑寻址与分组转发
- **IP**（IPv4/IPv6）：核心协议，提供尽力而为（best-effort）服务
- **ARP**：IP 地址→MAC 地址映射
- **ICMP**：网络控制消息（ping/traceroute）
- **IGMP**：组播管理
- PDU：**IP数据报（Datagram）**

### 第1层：网络接口层（Network Access Layer）
- 对应 OSI 的物理层 + 数据链路层
- 负责在物理网络上发送/接收 IP 数据报
- 协议与硬件紧密相关：以太网（Ethernet）、Wi-Fi（802.11）、PPP 等

## 三、典型通信过程（HTTP 请求为例）

```
浏览器（应用层）: GET /index.html HTTP/1.1
    ↓ 封装
TCP（传输层）:  [TCP头: 源端口=54321, 目的端口=80][HTTP数据]
    ↓ 封装
IP（网际层）:   [IP头: 源IP=192.168.1.5, 目的IP=93.184.216.34][TCP段]
    ↓ 封装
以太网（接口层）:[以太网帧头][IP包][FCS尾]
    ↓
物理介质传输
```

## 四、端口号分类

| 范围 | 类型 | 说明 |
|------|------|------|
| 0 ~ 1023 | 熟知端口 | HTTP=80, HTTPS=443, FTP=21, SSH=22, DNS=53 |
| 1024 ~ 49151 | 注册端口 | 由 IANA 分配给特定应用 |
| 49152 ~ 65535 | 动态/私有端口 | 客户端临时使用 |

## 五、关键概念辨析

| 概念 | 作用域 | 标识什么 |
|------|--------|---------|
| MAC 地址 | 数据链路层（同一网段内） | 网卡硬件地址 |
| IP 地址 | 网络层（跨网段） | 主机网络位置 |
| 端口号 | 传输层 | 主机上的进程/服务 |
| Socket = IP + 端口 | 传输层 | 唯一标识一个网络进程 |
""", difficulty=2),

R("exercise", "TCP/IP四层模型", "【练习题】TCP/IP协议栈综合练习", r"""## 知识点：TCP/IP四层模型

---
### 选择题

**Q1. 在 TCP/IP 体系中，负责将域名解析为 IP 地址的协议是？（单选）**

A. ARP
B. DNS
C. DHCP
D. ICMP

**答案：B**
**解析：** DNS（Domain Name System）负责将人类可读的域名（如 www.example.com）解析为对应的 IP 地址。ARP 解析 MAC 地址；DHCP 动态分配 IP；ICMP 传递控制消息。

---
**Q2. HTTP 协议运行在 TCP/IP 的哪一层？（单选）**

A. 网络层
B. 传输层
C. 应用层
D. 网络接口层

**答案：C**
**解析：** HTTP 是应用层协议，运行在传输层（TCP）之上，默认使用 TCP 的 80 端口（HTTPS 使用 443 端口）。

---
**Q3. 下列端口号与服务对应正确的是？（多选）**

A. FTP → 21
B. SSH → 22
C. SMTP → 25
D. DNS → 53
E. HTTP → 8080

**答案：ABCD**
**解析：** HTTP 默认端口是 **80**，不是 8080（8080 是常见的备用/开发端口，非标准端口）。

---
### 判断题

**Q4. TCP/IP 模型的网际层对应 OSI 模型的网络层。（ ）**

**答案：正确**
**解析：** TCP/IP 网际层主要协议是 IP，与 OSI 网络层功能对应，负责逻辑寻址和路由选择。注意 TCP/IP 的网络接口层对应 OSI 的物理层+数据链路层。

---
### 简答题

**Q5. 一台主机发送 HTTP 请求时，数据在各层是如何被封装的？列出封装过程中添加的关键信息。**

**参考答案：**
1. **应用层**：生成 HTTP 请求报文（包含请求方法、URL、首部字段等）
2. **传输层（TCP）**：添加 TCP 首部（源端口号、目的端口=80、序列号、确认号等），形成 TCP 段
3. **网际层（IP）**：添加 IP 首部（源IP地址、目的IP地址、TTL、协议号=6表示TCP），形成 IP 数据报
4. **网络接口层（以太网）**：添加以太网帧头（源MAC、目的MAC）和帧尾（FCS校验），形成帧
5. 最终在物理介质上以**比特流**形式传输
""", difficulty=2),

R("mindmap", "TCP/IP四层模型", "【思维导图】TCP/IP协议栈全景图", r"""```mermaid
graph TD
    ROOT[TCP/IP协议栈] --> L4[应用层]
    ROOT --> L3[传输层]
    ROOT --> L2[网际层]
    ROOT --> L1[网络接口层]

    L4 --> WEB[Web: HTTP/HTTPS]
    L4 --> DNS2[DNS: 域名解析]
    L4 --> MAIL[邮件: SMTP/POP3]
    L4 --> FILE[文件: FTP/SFTP]
    L4 --> REMOTE[远程: SSH/Telnet]
    L4 --> ASSIGN[分配: DHCP]

    L3 --> TCP2[TCP: 可靠/面向连接]
    L3 --> UDP2[UDP: 快速/无连接]
    L3 --> PORT[端口号: 0-65535]

    L2 --> IP2[IP: IPv4/IPv6]
    L2 --> ARP2[ARP: IP→MAC]
    L2 --> ICMP2[ICMP: 控制消息]
    L2 --> ROUTE[路由: 转发决策]

    L1 --> ETH[以太网 Ethernet]
    L1 --> WIFI[Wi-Fi 802.11]
    L1 --> PPP2[PPP 点对点]

    ROOT --> ID[唯一标识体系]
    ID --> MAC2[MAC: 链路层]
    ID --> IP3[IP: 网络层]
    ID --> SOC[Socket=IP+端口]
```""", difficulty=2),

# ──────────── 协议数据单元PDU ────────────
R("doc", "协议数据单元PDU", "【知识文档】PDU与数据封装详解", r"""# 协议数据单元（PDU）与数据封装

## 一、什么是PDU
协议数据单元（Protocol Data Unit，PDU）是各层对等实体之间传递的数据单元，
不同层的 PDU 有不同的名称和格式。

## 二、各层PDU名称

| 层次 | PDU名称 | 主要头部字段 |
|------|---------|------------|
| 应用层 | 报文（Message） | 应用层协议特定字段 |
| 传输层 | 报文段/数据报（Segment/Datagram） | 源端口、目的端口、序号、校验和 |
| 网络层 | 分组/包（Packet） | 源IP、目的IP、TTL、协议号 |
| 数据链路层 | 帧（Frame） | 源MAC、目的MAC、类型、FCS |
| 物理层 | 比特（Bit） | 无头部，原始信号 |

## 三、封装过程详解

以用户访问网页为例，"Hello"数据的封装路径：

```
应用层:  "Hello"
         ↓ TCP封装
传输层:  [源端口:54321|目的端口:80|序号:100|确认号:0|...] + "Hello"
         ↓ IP封装
网络层:  [版本:4|TTL:64|协议:6|源IP:1.2.3.4|目的IP:5.6.7.8] + TCP段
         ↓ 以太网封装
链路层:  [目的MAC:AA:BB:...|源MAC:CC:DD:...|类型:0x0800] + IP包 + [FCS]
         ↓
物理层:  01001011 01110100 ... (比特流)
```

## 四、MTU与分片
- **MTU**（Maximum Transmission Unit，最大传输单元）：以太网默认 **1500 字节**
- 若 IP 数据报超过 MTU，需要在网络层**分片**（Fragmentation）
- IPv4 支持分片，IPv6 不支持路由器分片（源端负责）
- TCP 通过 **MSS**（Maximum Segment Size）协商避免分片，默认 MSS=MTU-40=1460 字节

## 五、SDU与PDU关系
- **SDU**（Service Data Unit）：上层传递给本层的数据（服务数据单元）
- **PDU** = 本层头部（PCI，协议控制信息）+ SDU
- 本层的 PDU 就是下层的 SDU

## 六、常见误区
- ❌ "帧"和"包"可以混用 → 帧是数据链路层PDU，包是网络层PDU，含义不同
- ❌ UDP也叫"报文段" → UDP的PDU称为**数据报（Datagram）**，TCP的称报文段（Segment）
- ❌ 分片在传输层进行 → **IP分片**发生在网络层，传输层通过MSS协商避免分片
""", difficulty=3),

]  # END PHASE1

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 2  传输层核心
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PHASE2 = [

# ──────────── TCP三次握手 ────────────
R("doc", "TCP三次握手", "【知识文档】TCP三次握手建立连接", r"""# TCP 三次握手（连接建立）

## 一、背景
TCP（Transmission Control Protocol）是面向连接的传输协议，通信前必须建立连接。
三次握手确保双方的**发送能力**和**接收能力**均正常，并同步初始序列号（ISN）。

## 二、握手过程

```
客户端                          服务端
  │                               │
  │──── SYN (seq=x) ─────────────►│  第一次握手
  │     (客户端进入 SYN_SENT)      │  (服务端进入 SYN_RCVD)
  │                               │
  │◄─── SYN+ACK (seq=y, ack=x+1) ─│  第二次握手
  │                               │
  │──── ACK (ack=y+1) ────────────►│  第三次握手
  │     (双方进入 ESTABLISHED)     │
```

**第一次握手**：客户端发送 SYN（同步）报文，携带随机初始序号 `seq=x`；客户端进入 `SYN_SENT` 状态。

**第二次握手**：服务端收到 SYN 后，发送 SYN+ACK 报文：
- `seq=y`（服务端初始序号）
- `ack=x+1`（确认收到客户端序号 x，期望下次收到 x+1）
- 服务端进入 `SYN_RCVD` 状态

**第三次握手**：客户端发送 ACK 报文，`ack=y+1`；双方进入 `ESTABLISHED` 状态，连接建立。

## 三、为什么需要三次（不能两次）

| 问题 | 说明 |
|------|------|
| 确认双向通信能力 | 两次握手只能确认客户端发送+服务端接收，无法确认**服务端发送+客户端接收** |
| 防止历史失效连接 | 若旧的 SYN 报文延迟到达服务端，两次握手会导致服务端建立无效连接；第三次握手可让客户端拒绝 |
| 同步双方ISN | 三次握手确保双方的初始序列号均被对方确认 |

## 四、SYN Flood 攻击
攻击者发送大量 SYN 而不完成第三次握手，耗尽服务端 `SYN_RCVD` 队列资源（半连接队列）。
**防御**：SYN Cookie、限速、防火墙。

## 五、TCP 头部关键标志位

| 标志 | 含义 |
|------|------|
| SYN | 请求建立连接，同步序列号 |
| ACK | 确认号字段有效 |
| FIN | 请求终止连接 |
| RST | 强制重置连接 |
| PSH | 立即将数据推送给应用层 |

## 六、连接建立后的 Socket 队列
- **半连接队列（SYN队列）**：存放 SYN_RCVD 状态的连接
- **全连接队列（Accept队列）**：存放 ESTABLISHED 但未被 accept() 的连接
- `net.ipv4.tcp_max_syn_backlog` 控制半连接队列大小
""", difficulty=3),

R("exercise", "TCP三次握手", "【练习题】TCP三次握手深度练习", r"""## 知识点：TCP 三次握手

---
### 选择题

**Q1. 在 TCP 三次握手中，第二次握手报文携带的标志位是？（单选）**

A. 仅 SYN
B. 仅 ACK
C. SYN + ACK
D. FIN + ACK

**答案：C**
**解析：** 服务端在第二次握手中同时发送 SYN（同步自己的初始序号）和 ACK（确认收到客户端的 SYN），因此标志位为 SYN+ACK。

---
**Q2. 若客户端第一次握手的 SYN 报文中 seq=1000，服务端第二次握手的 ack 应为？（单选）**

A. 1000
B. 1001
C. 999
D. 由服务端随机决定

**答案：B**
**解析：** ACK 确认号 = 收到的 seq + 1 = 1000 + 1 = **1001**，表示期望下次收到序号 1001 的数据。

---
**Q3. SYN Flood 攻击利用了 TCP 握手的哪个弱点？（单选）**

A. 第三次握手可以被伪造
B. 服务端需维护半连接队列，资源有限
C. TCP 序列号可以被预测
D. 第一次握手不需要认证

**答案：B**
**解析：** SYN Flood 发送大量 SYN 但不完成第三次握手，导致服务端半连接队列（SYN队列）耗尽，拒绝新的合法连接。SYN Cookie 技术可以缓解此问题。

---
### 判断题

**Q4. TCP 三次握手过程中，客户端在第一次握手发送 SYN 后立即进入 ESTABLISHED 状态。（ ）**

**答案：错误**
**解析：** 客户端发送第一次握手（SYN）后进入 **SYN_SENT** 状态；收到服务端的 SYN+ACK 并发送第三次握手（ACK）后，才进入 **ESTABLISHED** 状态。

---
### 简答题

**Q5. 为什么 TCP 建立连接需要三次握手而不是两次？请从两个不同角度分析。**

**参考答案：**

**角度一——确认双向通信能力：**
- 第一次握手：服务端确认客户端**发送**正常，自己**接收**正常
- 第二次握手：客户端确认服务端**发送**正常，自己**接收**正常
- 两次握手只能确认单向，客户端无法确认自己的接收是否正常（无法验证服务端发送+客户端接收）

**角度二——防止历史失效连接：**
若网络中存在延迟的旧 SYN 报文，两次握手下服务端会将其当作新连接接受，建立无效连接浪费资源。
三次握手时，客户端收到响应后会检查上下文，若发现是历史连接，会发送 RST 拒绝，保护服务端不被旧连接骚扰。
""", difficulty=3),

R("code", "TCP三次握手", "【代码示例】用Python Socket观察TCP连接建立", r"""# TCP三次握手观察实验
# 通过Python Socket API展示TCP连接建立过程
# 运行方式：先启动server.py，再运行client.py
# 可配合 Wireshark 抓包验证三次握手报文

import socket
import threading
import time


def tcp_server(host='127.0.0.1', port=9999):
    # TCP服务端：监听连接，观察握手过程
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((host, port))
    server_sock.listen(5)
    print(f"[服务端] 监听 {host}:{port}，等待三次握手...")

    conn, addr = server_sock.accept()  # 阻塞，直到完成三次握手
    print(f"[服务端] ✅ 三次握手完成，连接来自 {addr}")
    # 此时双方均处于 ESTABLISHED 状态

    data = conn.recv(1024)
    print(f"[服务端] 收到数据: {data.decode()}")
    conn.send(b"Hello from Server")
    conn.close()
    server_sock.close()


def tcp_client(host='127.0.0.1', port=9999):
    # TCP客户端：主动发起三次握手
    time.sleep(0.2)  # 等待服务端就绪
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"[客户端] 发起连接（开始三次握手）...")

    # connect() 内部完成三次握手：
    #   1. 内核发送 SYN
    #   2. 收到服务端 SYN+ACK
    #   3. 内核发送 ACK
    client_sock.connect((host, port))
    print(f"[客户端] ✅ 三次握手完成，进入 ESTABLISHED")

    client_sock.send(b"Hello from Client")
    resp = client_sock.recv(1024)
    print(f"[客户端] 收到响应: {resp.decode()}")
    client_sock.close()


# 演示TCP连接状态
def show_tcp_states():
    # TCP连接建立过程中的状态变化
    states = [
        ("CLOSED",      "初始状态，无连接"),
        ("SYN_SENT",    "客户端发送SYN，等待服务端响应"),
        ("SYN_RCVD",    "服务端收到SYN，发送SYN+ACK，等待客户端ACK"),
        ("ESTABLISHED", "三次握手完成，连接建立，可以传输数据"),
    ]
    print("\n=== TCP 三次握手状态机 ===")
    for state, desc in states:
        print(f"  {state:<15} → {desc}")


if __name__ == "__main__":
    show_tcp_states()
    print("\n=== 模拟TCP连接 ===")
    t = threading.Thread(target=tcp_server, daemon=True)
    t.start()
    tcp_client()
    t.join(timeout=3)
""", difficulty=3, language="python"),

R("mindmap", "TCP三次握手", "【思维导图】TCP三次握手全景", r"""```mermaid
graph TD
    A[TCP三次握手] --> B[第一次握手]
    A --> C[第二次握手]
    A --> D[第三次握手]
    A --> E[为什么需要三次]
    A --> F[相关安全问题]

    B --> B1[客户端发 SYN,seq=x]
    B --> B2[客户端状态: SYN_SENT]

    C --> C1[服务端发 SYN+ACK]
    C --> C2[seq=y, ack=x+1]
    C --> C3[服务端状态: SYN_RCVD]

    D --> D1[客户端发 ACK,ack=y+1]
    D --> D2[双方进入 ESTABLISHED]

    E --> E1[确认双向收发能力]
    E --> E2[防止历史失效连接]
    E --> E3[同步双方初始序号ISN]

    F --> F1[SYN Flood攻击]
    F --> F2[半连接队列耗尽]
    F --> F3[防御: SYN Cookie]
```""", difficulty=3),

# ──────────── TCP四次挥手 ────────────
R("doc", "TCP四次挥手", "【知识文档】TCP四次挥手连接释放", r"""# TCP 四次挥手（连接释放）

## 一、为什么需要四次
TCP 连接是**全双工**的（双方都可发送数据），关闭时需要各方单独关闭自己的发送方向，
因此需要四次报文交换（每个方向各一次 FIN + 一次 ACK）。

## 二、挥手过程

```
主动关闭方（通常是客户端）        被动关闭方（通常是服务端）
       │                                │
       │──── FIN (seq=u) ──────────────►│  第一次挥手
       │     (主动方进入 FIN_WAIT_1)     │  (被动方进入 CLOSE_WAIT)
       │                                │
       │◄─── ACK (ack=u+1) ─────────────│  第二次挥手
       │     (主动方进入 FIN_WAIT_2)     │  [被动方继续发送剩余数据...]
       │                                │
       │◄─── FIN (seq=v) ───────────────│  第三次挥手
       │                                │  (被动方进入 LAST_ACK)
       │                                │
       │──── ACK (ack=v+1) ────────────►│  第四次挥手
       │     (主动方进入 TIME_WAIT)      │  (被动方进入 CLOSED)
       │
       │  等待 2×MSL（约 60~120秒）
       │
       │     (主动方进入 CLOSED)
```

## 三、TIME_WAIT 状态详解

### 为什么需要 TIME_WAIT
1. **保证最后一个 ACK 能到达服务端**：若最后的 ACK 丢失，服务端会超时重传 FIN，主动方还能重新发 ACK
2. **让旧连接报文消散**：等待 2×MSL（Maximum Segment Lifetime，报文最大存活时间），确保本次连接所有报文都在网络中消失，避免影响新连接

### TIME_WAIT 持续时长
- MSL 通常为 60 秒，TIME_WAIT 持续 **2×MSL = 120 秒**
- Linux 中 `net.ipv4.tcp_fin_timeout` 可调整（默认 60s）

### TIME_WAIT 过多的影响
大量短连接服务器（如 HTTP/1.0）会积累大量 TIME_WAIT，耗尽端口资源。
**解决方案**：
- `SO_REUSEADDR`：允许复用处于 TIME_WAIT 状态的端口
- `tcp_tw_reuse`：允许将 TIME_WAIT 的连接用于新的 TCP 连接（需开启时间戳）
- 使用长连接（HTTP Keep-Alive、连接池）

## 四、CLOSE_WAIT 过多的原因
服务端大量 `CLOSE_WAIT` 意味着收到了 FIN 但**应用层没有调用 close()**，
通常是代码中连接未正确关闭（忘记调用 close 或 finally 块缺失）。

## 五、与三次握手的对比

| 阶段 | 握手 | 挥手 |
|------|------|------|
| 次数 | 3次 | 4次 |
| 原因 | SYN 和 SYN+ACK 可以合并 | FIN 和 ACK 不能合并（服务端可能还有数据要发） |
| 特殊状态 | SYN_SENT/SYN_RCVD | FIN_WAIT_1/2、CLOSE_WAIT、TIME_WAIT、LAST_ACK |
""", difficulty=3),

R("exercise", "TCP四次挥手", "【练习题】TCP四次挥手与连接状态", r"""## 知识点：TCP 四次挥手

---
### 选择题

**Q1. 主动发起关闭连接的一方，在发送第四次挥手（最后的ACK）之后，进入什么状态？（单选）**

A. CLOSED
B. FIN_WAIT_2
C. TIME_WAIT
D. LAST_ACK

**答案：C**
**解析：** 主动方发送最后的 ACK 后进入 **TIME_WAIT** 状态，需等待 2×MSL 后才真正进入 CLOSED。TIME_WAIT 的作用是确保最后一个 ACK 被对方收到，并使网络中的旧报文消散。

---
**Q2. 服务端大量处于 CLOSE_WAIT 状态，最可能的原因是？（单选）**

A. 网络延迟过高
B. 服务端代码中连接未正确关闭（未调用 close()）
C. 客户端发送了大量 FIN
D. SYN Flood 攻击

**答案：B**
**解析：** CLOSE_WAIT 表示服务端收到了客户端的 FIN 并发了 ACK，但应用层**没有调用 close()** 关闭自己这端的连接，导致连接停在 CLOSE_WAIT 状态。需检查代码是否有连接泄漏。

---
**Q3. TCP 四次挥手为什么是四次而不是三次？（单选）**

A. TCP 安全性要求更多次握手
B. 全双工连接关闭时，每个方向需独立关闭（各一次FIN+ACK）
C. 服务端需要等待 MSL 时间
D. ACK 报文不可与 FIN 合并

**答案：B**
**解析：** TCP 是全双工的，关闭连接需要两个方向分别关闭。客户端发 FIN 关闭自己到服务端的通道；服务端可能还有数据要发送，所以不能立即 FIN，先发 ACK；待数据发完再发 FIN；客户端再 ACK。故需四次。

---
### 判断题

**Q4. TIME_WAIT 状态只在服务端出现。（ ）**

**答案：错误**
**解析：** TIME_WAIT 出现在**主动关闭连接的一方**，客户端或服务端都可能是主动关闭方，HTTP 客户端通常是主动关闭方。

---
### 简答题

**Q5. 解释 TIME_WAIT 状态存在的两个原因，以及 TIME_WAIT 时长为 2×MSL 的意义。**

**参考答案：**

**原因一：保证最后 ACK 可靠到达**
最后一次 ACK（第四次挥手）可能在网络中丢失。若丢失，被动方会超时重传 FIN；
主动方处于 TIME_WAIT 状态，仍可重新发送 ACK，确保被动方能正常关闭。

**原因二：让旧报文消散，避免影响新连接**
相同四元组（srcIP、srcPort、dstIP、dstPort）的新连接建立后，若旧连接中的延迟报文到达，会干扰新连接。
等待 2×MSL 确保所有属于旧连接的报文都在网络中消失（一个MSL是报文单向最大存活时间，往返需2×MSL）。

**2×MSL 的意义：**
- 一个 MSL = 报文从源到目的的最大时间（通常60s）
- 2×MSL 覆盖了报文从主动方到被动方、再从被动方到主动方的完整往返时间
- 确保即使最坏情况下的延迟报文也已超时销毁
""", difficulty=4),

R("mindmap", "TCP四次挥手", "【思维导图】TCP四次挥手与状态机", r"""```mermaid
graph TD
    A[TCP四次挥手] --> B[第一次挥手]
    A --> C[第二次挥手]
    A --> D[第三次挥手]
    A --> E[第四次挥手]
    A --> F[关键状态]
    A --> G[TIME_WAIT详解]

    B --> B1[主动方: 发FIN,seq=u]
    B --> B2[主动方: FIN_WAIT_1]

    C --> C1[被动方: 发ACK,ack=u+1]
    C --> C2[被动方: CLOSE_WAIT]
    C --> C3[主动方: FIN_WAIT_2]

    D --> D1[被动方: 发FIN,seq=v]
    D --> D2[被动方: LAST_ACK]

    E --> E1[主动方: 发ACK,ack=v+1]
    E --> E2[主动方: TIME_WAIT]
    E --> E3[被动方: CLOSED]

    F --> F1[CLOSE_WAIT: 被动方等待应用关闭]
    F --> F2[FIN_WAIT_2: 主动方等待服务端FIN]

    G --> G1[持续 2×MSL]
    G --> G2[原因1: 保证ACK可达]
    G --> G3[原因2: 旧报文消散]
    G --> G4[TIME_WAIT过多: SO_REUSEADDR]
```""", difficulty=3),

# ──────────── TCP可靠传输 ────────────
R("doc", "TCP可靠传输", "【知识文档】TCP可靠传输机制", r"""# TCP 可靠传输机制

## 一、可靠传输概述
TCP 通过以下机制确保数据**有序、完整、不重复**地到达接收方：
序列号与确认、超时重传、校验和、流量控制、拥塞控制。

## 二、序列号与确认号

### 序列号（Sequence Number）
- TCP 将数据视为**字节流**，每个字节都有唯一的序列号
- 初始序列号（ISN）在握手时随机生成，防止历史连接报文干扰
- 序列号 = 本报文段第一个字节的序号

### 确认号（Acknowledgment Number）
- ACK 号表示"期望收到的下一个字节序号"，即已成功收到该序号**之前**的所有数据
- **累积确认**：一个 ACK 可以确认之前所有数据（不是逐包确认）

## 三、超时重传（RTO）

### 工作原理
发送方为每个已发出但未确认的报文段启动计时器。若超时未收到 ACK，则重传该报文段。

### RTO 计算（自适应）
$$RTO = SRTT + 4 \times RTTVAR$$
- **RTT**（往返时延）= ACK 到达时间 - 发送时间
- **SRTT**（平滑RTT）= (1-α)×SRTT + α×RTT，α通常为 1/8
- **RTTVAR**（RTT方差）平滑后的偏差
- RTO 初始值通常设为 1 秒，每次超时 RTO **翻倍**（指数退避）

## 四、快速重传（Fast Retransmit）
收到**3个重复ACK**（即共4个相同ACK）时，不等超时立即重传丢失的报文段。
这比超时重传更快，是检测丢包的重要手段。

## 五、选择确认（SACK）
标准的累积确认无法告知发送方哪些数据块到达了、哪些丢失了。
**SACK**（Selective ACK）扩展允许接收方明确告知已收到的不连续数据块，
发送方只需重传真正丢失的报文段，提高传输效率。

## 六、校验和（Checksum）
TCP 首部包含 16 位校验和，覆盖伪首部（源IP+目的IP+协议号+数据长度）+ TCP首部 + 数据。
用于检测传输过程中的比特错误（不能检测所有错误）。

## 七、有序交付
- 接收方按序列号**重新排序**乱序到达的报文段
- 使用**接收缓冲区**（Receive Buffer）暂存乱序数据，等缺口填补后按序交给应用层
""", difficulty=4),

R("exercise", "TCP可靠传输", "【练习题】TCP序列号与可靠传输机制", r"""## 知识点：TCP 可靠传输

---
### 选择题

**Q1. TCP 收到 3 个重复 ACK 时，会触发什么机制？（单选）**

A. 超时重传
B. 快速重传
C. SACK 重传
D. 拥塞避免

**答案：B**
**解析：** 收到 3 个重复 ACK（共 4 个相同 ACK）时，TCP 判断该 ACK 对应的下一个数据段可能已丢失，立即触发**快速重传**，无需等待 RTO 超时，大幅减少延迟。

---
**Q2. 关于TCP序列号的作用，以下说法正确的是？（多选）**

A. 标识每个字节在字节流中的位置
B. 用于接收方对乱序数据进行重排序
C. 防止历史连接报文被误认为新连接数据
D. 用于计算校验和

**答案：ABC**
**解析：** 序列号用于标识字节位置（A）、支持乱序重排（B）、防止历史连接干扰（C）。校验和的计算用的是数据内容而非序列号（D错误）。

---
**Q3. SACK（选择确认）相比累积确认的主要优势是？（单选）**

A. 减少TCP首部大小
B. 允许接收方精确告知哪些数据段已收到，避免不必要的重传
C. 完全替代超时重传机制
D. 提高三次握手速度

**答案：B**
**解析：** 传统累积ACK只能确认连续收到的最大序号，丢包时发送方不知道后续哪些已到达。SACK让接收方精确反馈已收到的不连续块，发送方只重传真正丢失的部分。

---
### 判断题

**Q4. TCP 每次超时重传后，RTO 会翻倍（指数退避）。（ ）**

**答案：正确**
**解析：** 指数退避（Exponential Backoff）是为了避免在网络拥塞时频繁重传加重拥塞。每次超时后 RTO 加倍，直到收到新的 ACK 后重新通过 RTT 计算 RTO。

---
### 简答题

**Q5. 发送方已发送序号 1~100 的数据，但只收到了对序号 1~40 的 ACK，随后连续收到 3 个 ack=41 的重复ACK。接下来会发生什么？请解释其原因。**

**参考答案：**

**发生快速重传：**
连续收到 3 个重复 ACK（ack=41）说明接收方收到了41之后的数据但等不到序号41的数据，
推断序号从41开始的报文段（第41~?字节）已经**丢失**。

发送方立即重传从序号 41 开始的报文段，无需等待 RTO 超时。

同时会触发**拥塞控制的快速恢复（Fast Recovery）**机制：
1. ssthresh = cwnd/2（将拥塞窗口减半）
2. cwnd = ssthresh + 3（膨胀窗口）
3. 进入快速恢复阶段，继续发送新数据（与慢启动后从1开始不同）
""", difficulty=4),

# ──────────── TCP流量控制 ────────────
R("doc", "TCP流量控制", "【知识文档】TCP流量控制与滑动窗口", r"""# TCP 流量控制与滑动窗口

## 一、目的
流量控制防止**发送方发送速度过快**，导致接收方缓冲区溢出，丢失数据。
机制：接收方通过通告**接收窗口（rwnd）**告知发送方自己还能接受多少数据。

## 二、滑动窗口机制

### 接收窗口（rwnd）
- 接收方在 TCP 首部中的 **Window 字段**（16位，最大65535字节，可通过窗口缩放选项扩展）
- 表示接收缓冲区的剩余空间
- 每次发送 ACK 时更新 rwnd

### 发送窗口
发送窗口 ≤ min(rwnd, cwnd)
- **rwnd**：接收方通告的接收窗口（流量控制）
- **cwnd**：拥塞窗口（拥塞控制）
- 取两者中的最小值，限制发送速率

### 窗口滑动过程
```
发送方字节缓冲区:
|  已发送已确认  |  已发送未确认  |  允许发送未发  |  不允许发送  |
               ↑                ↑               ↑
           send_base         nextseqnum    send_base+window

窗口随ACK滑动:
  收到 ACK N → send_base = N → 窗口右移 → 新的字节可被发送
```

## 三、窗口为零时的处理（Zero Window）
若接收方缓冲区满，通告 `rwnd=0`，发送方停止发送。
**解决机制**：发送方启动**坚持计时器（Persist Timer）**，定期发送探测报文（零窗口探测，Zero Window Probe），询问接收方是否有新的缓冲空间。接收方缓冲区释放后，发送**窗口更新 ACK**通知发送方。

## 四、糊涂窗口综合症（Silly Window Syndrome）
接收方每次只释放少量缓冲区（如1字节），就通告新窗口，导致大量小报文传输，效率极低。

**解决方案**：
- **接收方**：Clark算法——只有缓冲区增加到半满（或增加 MSS）才通告新窗口
- **发送方**：Nagle算法——积累数据到一个 MSS 或收到上一个报文的 ACK 才发送新数据
  - 若应用需要低延迟（如 SSH 按键），可通过 `TCP_NODELAY` 禁用 Nagle

## 五、关键参数

| 参数 | 说明 |
|------|------|
| rwnd | 接收窗口，接收方通告 |
| cwnd | 拥塞窗口，发送方维护 |
| MSS | 最大报文段长度（通常1460字节） |
| BDP | 带宽时延积 = 带宽 × RTT，理想窗口大小 |

## 六、与拥塞控制的区别

| 流量控制 | 拥塞控制 |
|---------|---------|
| 防止接收方被淹没 | 防止网络被淹没 |
| 由接收方通告rwnd | 由发送方维护cwnd |
| 端到端（点对点）问题 | 全网（全局）问题 |
""", difficulty=4),

# ──────────── TCP拥塞控制 ────────────
R("doc", "TCP拥塞控制", "【知识文档】TCP拥塞控制算法", r"""# TCP 拥塞控制

## 一、为什么需要拥塞控制
若所有发送方都全速发送，网络中间节点（路由器）的缓冲区会溢出，导致大量丢包，
丢包后所有主机又超时重传，进一步加剧拥塞——**拥塞崩溃（Congestion Collapse）**。
拥塞控制让 TCP 主动感知网络状态并调整发送速率。

## 二、拥塞检测手段
- **丢包（超时）**：最强拥塞信号，意味着路由器缓冲区已满并丢弃分组
- **3个重复ACK**：较轻拥塞信号，部分分组丢失但后续到达（快速重传触发）
- **RTT增大**：BBR 等新算法通过 RTT 变化感知拥塞

## 三、经典 TCP Reno 四阶段

### 阶段1：慢启动（Slow Start）
- 初始 cwnd = 1 MSS（或初始拥塞窗口IW）
- 每收到一个 ACK，cwnd += 1 MSS → **每个 RTT 翻倍**（指数增长）
- 持续到 cwnd ≥ ssthresh（慢启动阈值）

### 阶段2：拥塞避免（Congestion Avoidance）
- cwnd ≥ ssthresh 后进入
- 每个 RTT cwnd += 1 MSS → **线性增长**（加法增大）
- 目的：缓慢探测网络容量，避免过快触发拥塞

### 阶段3：快速重传与快速恢复（Fast Retransmit & Fast Recovery）
收到 3 个重复 ACK（**乘法减小**）：
```
ssthresh = cwnd / 2
cwnd = ssthresh + 3 MSS      ← 快速恢复起点
立即重传丢失报文段
进入快速恢复阶段：每收到一个重复ACK，cwnd += 1 MSS
直到收到新 ACK → cwnd = ssthresh，进入拥塞避免
```

### 阶段4：超时重传（最严重）
发生超时：
```
ssthresh = cwnd / 2
cwnd = 1 MSS                 ← 回到慢启动起点
重新执行慢启动
```

## 四、发展历程对比

| 算法 | 特点 |
|------|------|
| TCP Tahoe | 超时和3重复ACK都触发慢启动 |
| TCP Reno | 3重复ACK触发快速恢复，超时回到慢启动 |
| TCP CUBIC | Linux默认，用三次函数替代线性增长，适合高带宽 |
| TCP BBR | 基于带宽和RTT建模，不依赖丢包检测，Google开发 |

## 五、cwnd 变化示意图

```
cwnd
 ^
 |        /\   拥塞避免（线性）
 |      /    \
 |    /        \__  快速重传后进入快速恢复
 |  /（慢启动指数）
 |/
 +─────────────────────────────── RTT
```

## 六、AIMD（加法增大乘法减小）原则
拥塞避免时加法增大（Additive Increase），检测到拥塞时乘法减小（Multiplicative Decrease），
这是 TCP 拥塞控制收敛到公平共享带宽的数学基础。
""", difficulty=5),

R("exercise", "TCP拥塞控制", "【练习题】TCP拥塞控制算法分析", r"""## 知识点：TCP 拥塞控制

---
### 选择题

**Q1. TCP Reno 检测到3个重复ACK时，ssthresh 如何变化？（单选）**

A. ssthresh = 1 MSS
B. ssthresh = cwnd
C. ssthresh = cwnd / 2
D. ssthresh 不变

**答案：C**
**解析：** 收到3个重复ACK时，TCP Reno 触发快速重传和快速恢复：**ssthresh = cwnd / 2**（乘法减小），然后 cwnd = ssthresh + 3，进入快速恢复阶段（而非慢启动）。与超时重传不同，超时后 cwnd 归 1 MSS 重新慢启动。

---
**Q2. 下列关于慢启动的说法，正确的是？（多选）**

A. 慢启动阶段 cwnd 指数增长
B. "慢"是指初始 cwnd 很小（1 MSS），增长方式并不慢
C. 当 cwnd 达到 ssthresh 后，切换到拥塞避免
D. 慢启动只在连接建立时执行一次

**答案：ABC**
**解析：** 慢启动每收到一个ACK就将cwnd+1，每个RTT翻倍，是**指数**增长（A正确）；之所以叫"慢"是因为初始只发1个MSS，相对全速更保守（B正确）；达到ssthresh后进入拥塞避免线性增长（C正确）；超时重传也会触发慢启动（D错误）。

---
### 填空题

**Q3. 设当前 cwnd = 16 MSS，ssthresh = 8 MSS，此时发生超时重传，则超时后：**
- ssthresh = _____ MSS
- cwnd = _____ MSS
- 进入 _____ 阶段

**答案：** ssthresh = **8**，cwnd = **1**，进入**慢启动**阶段
**解析：** 超时时 ssthresh = cwnd/2 = 8，cwnd 重置为 1 MSS，从慢启动重新开始。

---
### 简答题

**Q4. 解释 TCP 拥塞控制中"AIMD"原则的含义，并说明为什么这种设计能使多个 TCP 连接公平地共享带宽。**

**参考答案：**

**AIMD（加法增大，乘法减小）：**
- **加法增大（AI）**：没有拥塞时，每个 RTT 将 cwnd 增加 1 MSS（线性增长），缓慢探测可用带宽
- **乘法减小（MD）**：检测到拥塞时，将 cwnd 减半，快速降低发送速率

**公平性证明（直觉）：**
假设两个 TCP 连接共享一条带宽为 R 的链路，理想分配是每个连接获得 R/2。
若连接 A 带宽多于 B，则两者 cwnd 都在增加（AI），但 A 占用更多，拥塞先由 A 触发，A 减半，
两者重新接近公平点。反复 AIMD 后，两者都会收敛到公平共享带宽附近。
""", difficulty=5),

R("mindmap", "TCP拥塞控制", "【思维导图】TCP拥塞控制全景", r"""```mermaid
graph TD
    A[TCP拥塞控制] --> B[慢启动 SS]
    A --> C[拥塞避免 CA]
    A --> D[快速重传+快速恢复]
    A --> E[超时重传]
    A --> F[现代算法]

    B --> B1[初始 cwnd=1MSS]
    B --> B2[每收到ACK: cwnd+1]
    B --> B3[指数增长]
    B --> B4[到达ssthresh→进CA]

    C --> C1[每个RTT: cwnd+1MSS]
    C --> C2[线性增长 AIMD]
    C --> C3[直到检测到拥塞]

    D --> D1[触发: 3个重复ACK]
    D --> D2[ssthresh=cwnd/2]
    D --> D3[cwnd=ssthresh+3]
    D --> D4[快速恢复后进CA]

    E --> E1[触发: RTO超时]
    E --> E2[ssthresh=cwnd/2]
    E --> E3[cwnd=1MSS 慢启动]

    F --> F1[CUBIC: Linux默认]
    F --> F2[BBR: 基于RTT和带宽]
    F --> F3[不依赖丢包触发]
```""", difficulty=4),

]  # END PHASE2

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 3  UDP、端口与Socket编程
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PHASE3 = [

R("doc", "UDP协议", "【知识文档】UDP协议特性与应用场景", r"""# UDP（用户数据报协议）

## 一、UDP概述
UDP（User Datagram Protocol）是传输层的无连接、不可靠、低延迟协议。
发送数据前**无需建立连接**，不保证顺序、不重传、无流量控制，但开销极小。

## 二、UDP 首部格式（8字节，极简）

```
 0              15 16             31
+----------------+----------------+
|   源端口号      |   目的端口号    |
+----------------+----------------+
|   UDP 长度     |    校验和       |
+----------------+----------------+
|           数据...               |
```
UDP 首部只有 **8 字节**，TCP 首部最少 20 字节。

## 三、UDP vs TCP 核心对比

| 特性 | UDP | TCP |
|------|-----|-----|
| 连接 | 无连接 | 面向连接（三次握手） |
| 可靠性 | 不可靠（尽力交付） | 可靠（确认+重传） |
| 有序性 | 不保证 | 保证有序 |
| 流量/拥塞控制 | 无 | 有 |
| 首部开销 | 8 字节 | 20-60 字节 |
| 速度 | 快（无握手延迟） | 较慢 |

## 四、UDP 适用场景

| 应用 | 原因 |
|------|------|
| DNS 查询 | 查询响应快，应用层处理重试 |
| 视频流/语音通话（RTP） | 实时性优先，少量丢帧可容忍 |
| 网络游戏 | 低延迟关键，旧帧丢失不影响 |
| DHCP | 广播场景，IP还未分配 |
| HTTP/3（QUIC） | 在UDP上自行实现可靠性 |

## 五、UDP 与广播/多播
UDP 支持单播、**广播**和**多播**（D类地址 224.0.0.0/4）。
TCP 只支持单播，这是UDP在广播场景必选的原因。
""", difficulty=2),

R("exercise", "UDP协议", "【练习题】UDP协议特性分析", r"""## 知识点：UDP 协议

---
### 选择题

**Q1. 以下哪些协议使用 UDP？（多选）**

A. DNS（域名解析）
B. FTP（文件传输）
C. DHCP（动态地址分配）
D. HTTP（网页浏览）
E. RTP（实时传输协议）

**答案：ACE**
**解析：** DNS 用 UDP 53 端口；DHCP 需要广播且IP未分配，必须用UDP；RTP（视频/音频）用UDP保证实时性。FTP和HTTP使用TCP（需要可靠传输）。

---
**Q2. UDP 首部大小是？（单选）**

A. 8 字节     B. 20 字节     C. 40 字节     D. 可变

**答案：A**
**解析：** UDP 首部固定 **8 字节**：源端口(2B)+目的端口(2B)+长度(2B)+校验和(2B)。

---
**Q3. HTTP/3（QUIC协议）选择UDP而非TCP的主要原因是？（单选）**

A. UDP性能绝对优于TCP
B. 避免TCP的队头阻塞，自行实现更灵活的可靠传输
C. HTTP/3不需要可靠传输
D. UDP不受防火墙影响

**答案：B**
**解析：** TCP存在队头阻塞（HOL blocking）——单个包丢失会阻塞整个连接所有流。QUIC在UDP上实现多路复用时，每个流的丢包只影响该流，同时自行实现了可靠性、拥塞控制等特性。

---
### 判断题

**Q4. UDP 数据报在传输中丢失后，UDP 协议会自动重传。（ ）**

**答案：错误**
**解析：** UDP 是不可靠协议，**不提供重传**。丢包处理由应用层负责（如DNS超时重发、RTP使用FEC等）。

---
### 简答题

**Q5. 直播平台使用 UDP/RTP 传输视频流，若发猁2%丢包，说明应采取哪些策略处理丢包。**

**参考答案：**
1. **帧插值**：重复使用最近的有效帧填充丢失帧（对用户影响最小）
2. **前向纠错（FEC）**：发送时额外发送冗余包，接收方可重建少量丢失包
3. **自适应码率（ABR）**：检测到丢包率上升，动态降低分辨率/码率
4. **关键帧重传**：仅对I帧（关键帧）发送NACK请求重传，P/B帧丢失忽略
5. **错误隐藏**：对音频用相邻帧插值补偿
""", difficulty=3),

R("code", "UDP协议", "【代码示例】UDP Socket编程与TCP对比", r"""
# UDP Socket 编程示例——对比 TCP 的无连接特性
import socket, threading, time


def udp_server(host='127.0.0.1', port=9998):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # DGRAM=UDP
    sock.bind((host, port))
    sock.settimeout(3.0)
    print(f"[UDP服务端] 监听 {host}:{port}")
    while True:
        try:
            data, addr = sock.recvfrom(1024)  # 一次接收完整数据报
            print(f"[UDP服务端] 来自 {addr}: {data.decode()}")
            sock.sendto(b"UDP-OK: " + data, addr)  # 必须指定目标地址
        except socket.timeout:
            break
    sock.close()


def udp_client(host='127.0.0.1', port=9998):
    time.sleep(0.1)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2.0)
    for msg in ["数据报1", "数据报2", "数据报3"]:
        sock.sendto(msg.encode(), (host, port))  # 无需建立连接
        try:
            data, _ = sock.recvfrom(1024)
            print(f"[UDP客户端] 回复: {data.decode()}")
        except socket.timeout:
            print(f"[UDP客户端] 超时，{msg} 可能丢失（UDP不自动重传）")
    sock.close()


def api_comparison():
    print("\n=== TCP vs UDP 编程API 对比 ===")
    diff = [
        ("建立方式", "SOCK_STREAM + connect()", "SOCK_DGRAM, 无需connect"),
        ("服务端", "bind→listen→accept", "bind，无需listen/accept"),
        ("发送", "send(data)", "sendto(data, addr)"),
        ("接收", "recv(size)", "recvfrom(size) ← 含来源地址"),
        ("消息边界", "无（字节流，需处理粘包）", "有（一次recvfrom=一个数据报）"),
    ]
    for name, tcp, udp in diff:
        print(f"  {name:<8}: TCP={tcp:<30} | UDP={udp}")


if __name__ == "__main__":
    api_comparison()
    print("\n=== UDP 通信演示 ===")
    t = threading.Thread(target=udp_server, daemon=True)
    t.start()
    udp_client()
    t.join(timeout=4)
""", difficulty=2, language="python"),

R("doc", "Socket编程", "【知识文档】Socket网络编程基础与粘包处理", r"""# Socket 网络编程基础

## 一、Socket 简介
Socket（套接字）是网络编程的**抽象接口**，提供统一 API 屏蔽底层协议细节。
**Socket 五元组**：协议 + 源IP + 源端口 + 目的IP + 目的端口，唯一标识一条连接。

## 二、Socket 类型

| 类型 | 对应协议 | 特点 |
|------|---------|------|
| SOCK_STREAM | TCP | 面向连接，字节流，可靠 |
| SOCK_DGRAM | UDP | 无连接，数据报，不可靠 |
| SOCK_RAW | IP层 | 可构造自IP头，需root权限 |

## 三、TCP Socket 工作流程

```
服务端                    客户端
socket()                  socket()
bind(IP, port)
listen(backlog)
                  ←三次握手→   connect(server_IP, port)
conn = accept()            [连接建立 ESTABLISHED]
send/recv ←──── 数据传输 ────→ send/recv
close()       ←四次挥手→      close()
```

## 四、关键 API

| API | 说明 |
|-----|------|
| `bind(addr)` | 绑定本地地址和端口 |
| `listen(backlog)` | 开始监听，backlog=全连接队列大小 |
| `accept()` | 阻塞等待客户端，返回新Socket |
| `connect(addr)` | 发起三次握手（阻塞直到建立） |
| `send/sendall(data)` | 发送（sendall循环发完） |
| `recv(size)` | 接收最多size字节 |
| `settimeout(t)` | 设置超时，防止永久阻塞 |

## 五、TCP 粘包问题与解决

**问题**：TCP 是字节流，无消息边界。`send("消息1")` + `send("消息2")` 接收方可能收到 `"消息1消息2"`（粘包）或 `"消息"` + `"1消息2"`（拆包）。

**解决方案**：

| 方法 | 说明 | 适用 |
|------|------|------|
| **长度前缀** | 消息夶4字节存数据长度，先读长度再读数据 | 最通用 |
| **定长消息** | 每条消息固N字节，不足补零 | 简单场景 |
| **分隔符** | 用`\n`或`\r\n`分隔消息 | 文本协议 |
| **TLV格式** | Type+Length+Value 结构 | 二进制协议 |

HTTP 用 `Content-Length` + `\r\n\r\n` 解决此问题。
""", difficulty=3),

R("code", "Socket编程", "【代码示例】TCP粘包处理——长度前缀协议", r"""
# TCP 粘包处理：长度前缀协议
# 使用"4字节长度 + 数据"格式解决TCP字节流的消息边界问题

import socket, struct, threading, time


def send_msg(sock, data: bytes):
    # 发送带长度前缀的消息（大焃4字节整数）
    sock.sendall(struct.pack('>I', len(data)) + data)


def recv_msg(sock) -> bytes:
    # 接收带长度前缀的消息，正确处理粘包/拆包
    raw_len = _recv_exact(sock, 4)  # 先读4字节长度头
    if not raw_len:
        return b''
    msg_len = struct.unpack('>I', raw_len)[0]
    return _recv_exact(sock, msg_len)  # 再读确切N字节


def _recv_exact(sock, n: int) -> bytes:
    # 循环接收直到得到n字节
    buf = b''
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("连接已关闭")
        buf += chunk
    return buf


def server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('127.0.0.1', 9997))
    srv.listen(1)
    conn, addr = srv.accept()
    for i in range(3):
        msg = recv_msg(conn)
        print(f"[服务端] 消息{i+1}: {msg.decode()}")
        send_msg(conn, f"已收到消息{i+1}".encode())
    conn.close(); srv.close()


def client():
    time.sleep(0.1)
    cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cli.connect(('127.0.0.1', 9997))
    for msg in ["Hello World", "这是第二条消息", "第三条消息" * 5]:
        send_msg(cli, msg.encode())
        reply = recv_msg(cli)
        print(f"[客户端] 回复: {reply.decode()}")
    cli.close()


if __name__ == "__main__":
    print("=== TCP粘包处理演示（长度前缀协议）===")
    t = threading.Thread(target=server, daemon=True)
    t.start()
    client()
    t.join(timeout=5)
""", difficulty=4, language="python"),

]  # END PHASE3

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 4  网络层
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PHASE4 = [

R("doc", "IP地址与子网划分", "【知识文档】IPv4地址与CIDR子网划分", r"""# IPv4 地址与子网划分

## 一、IPv4 地址基础
IPv4 地址 **32 位二进制数**，点分十进制表示。地址空间红43亿，通过 CIDR + NAT 延缓了耗尽问题。

## 二、CIDR 表示法
格式：`IP/前缀长度`，如 `192.168.1.0/24`
- **网络地址** = IP & 掩码
- **主机数** = 2^(32-前缀) - 2
- **广播地址** = 网络地址 | (全1的主机位)

## 三、常用前缀速查

| CIDR | 掩码 | 主机数 | 用途 |
|------|------|--------|------|
| /30 | 255.255.255.252 | 2 | 路由器互联链路 |
| /29 | 255.255.255.248 | 6 | 小型办公室 |
| /27 | 255.255.255.224 | 30 | 中型LAN |
| /24 | 255.255.255.0 | 254 | 标准C类网络 |
| /16 | 255.255.0.0 | 65534 | 标准B类网络 |

## 四、计算示例：10.0.0.66/27
```
前缀=27，主机位=5位，掩码=255.255.255.224
66 = 0100 0010 → 取前27位第4字节前5位 → 0100 0000 = 64
网络地址 = 10.0.0.64
广播地址 = 10.0.0.95（64+31）
主机范围 = 10.0.0.65 ~ 10.0.0.94（30台）
```

## 五、特殊地址

| 地址 | 含义 |
|------|------|
| 127.0.0.1 | 本地回环 |
| 10.0.0.0/8 | RFC1918 私有 |
| 172.16.0.0/12 | RFC1918 私有 |
| 192.168.0.0/16 | RFC1918 私有 |
| 169.254.0.0/16 | 链路本地（DHCP失败时） |
| 255.255.255.255 | 有限广播 |
""", difficulty=3),

R("exercise", "IP地址与子网划分", "【练习题】子网计算综合训练", r"""## 知识点：IP地址与子网划分

---
### 计算题

**Q1. 给定 172.16.100.200/20，求网络地址、广播地址和主机数。**

**参考答案：**
```
/20 → 掩码=255.255.240.0
100 = 0110 0100，取前4位(20-16)→ 0110 0000 = 96
网络地址 = 172.16.96.0
广播地址 = 172.16.111.255
主机数 = 2^12 - 2 = 4094台
```

---
**Q2. 哪些是私有IP地址？（多选）**

A. 10.255.255.254   B. 172.15.1.1   C. 172.31.0.1   D. 192.168.0.1   E. 192.169.1.1

**答案：ACD**
**解析：** RFC 1918：10.0.0.0/8（A✅）、172.16~31（B的172.15在范围外❌，C的172.31✅）、192.168.0.0/16（D✅，E的192.169❌）

---
**Q3. 将10.0.0.0/24分为6个子网，每子网至少20台主机，给出子网掩码。**

**参考答案：**
- 至少6子网 → 3位子网位（2^3=8≥6）
- 至少20台 → 5位主机位（2^5-2=30≥20）
- /24借3位 → **/27**，掩码**255.255.255.224**，每子网30台平备。

---
### 简答题

**Q4. 什么是"最长前缀匹配"？路由器有以下路由表，目的IP=192.168.1.100应匹配哪条？**
```
0.0.0.0/0     → G0
192.168.0.0/16→ G1
192.168.1.0/24→ G2
192.168.1.96/27→ G3
```

**参考答案：**
最长前缀匹配：选择前缀最长（最精确）的匹配条目。
192.168.1.100匹配：/27（192.168.1.96-127✅）、/24✅、/16✅、/0✅
选择**192.168.1.96/27 → G3**（前缀27最长）
""", difficulty=4),

R("code", "IP地址与子网划分", "【代码示例】Python子网计算器实现", r"""# 子网计算器 - 手动实现展示IP地址位运算原理

def ip_to_int(ip: str) -> int:
    p = [int(x) for x in ip.split('.')]
    return (p[0] << 24) | (p[1] << 16) | (p[2] << 8) | p[3]


def int_to_ip(n: int) -> str:
    return f"{(n>>24)&0xFF}.{(n>>16)&0xFF}.{(n>>8)&0xFF}.{n&0xFF}"


def subnet_calc(cidr: str) -> None:
    # 计算并显示子网详细信息
    ip_str, prefix_str = cidr.split('/')
    prefix = int(prefix_str)
    ip_int = ip_to_int(ip_str)
    mask_int = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
    network_int = ip_int & mask_int
    broadcast_int = network_int | (~mask_int & 0xFFFFFFFF)
    host_count = max(0, (1 << (32 - prefix)) - 2)
    print(f"CIDR: {cidr}")
    print(f"  掩码:       {int_to_ip(mask_int)}")
    print(f"  网络地址:    {int_to_ip(network_int)}")
    print(f"  广播地址:    {int_to_ip(broadcast_int)}")
    print(f"  主机范围:    {int_to_ip(network_int+1)} ~ {int_to_ip(broadcast_int-1)}")
    print(f"  可用主机数:  {host_count}")


def is_private(ip: str) -> bool:
    # 判断RFC1918私有地址
    n = ip_to_int(ip)
    return any(lo <= n <= hi for lo, hi in [
        (ip_to_int("10.0.0.0"), ip_to_int("10.255.255.255")),
        (ip_to_int("172.16.0.0"), ip_to_int("172.31.255.255")),
        (ip_to_int("192.168.0.0"), ip_to_int("192.168.255.255")),
    ])


if __name__ == "__main__":
    for cidr in ["192.168.1.100/24", "172.16.100.200/20", "10.0.0.66/27"]:
        print()
        subnet_calc(cidr)
    print("\n私有地址判断:")
    for ip in ["10.0.0.1", "172.15.1.1", "172.31.0.1", "192.168.1.1", "8.8.8.8"]:
        print(f"  {ip}: {'私有' if is_private(ip) else '公网'}")
""", difficulty=3, language="python"),

R("doc", "ARP协议", "【知识文档】ARP地址解析协议详解", r"""
# ARP（地址解析协议）

## 一、ARP 的作用
已知目标的 **IP 地址**，通过 ARP 获取其 **MAC 地址**，用于封装以太网帧。

**关键规则**：
- 同一网段直接 ARP 目标主机
- 不同网段 ARP **默认网关**的 MAC（路由器代为转发）

## 二、工作流程

```
A（192.168.1.1）要发数据给 B（192.168.1.2）

1. 检查ARP缓存 → 未找到
2. A 发 ARP 请求（以太网广播，目的MAC=FF:FF:FF:FF:FF:FF）:
   "谁的IP是192.168.1.2？请告诉我你的MAC"
3. 全网段主机收到广播，只有B响应（IP匹配）
4. B 发 ARP 回复（单播给A）:
   "我是192.168.1.2，MAC是DD:EE:FF:44:55:66"
5. A 更新ARP缓存并封装以太网帧发送
```

## 三、ARP 缓存
- 老化时间红20分钟，超时后重新ARP
- Linux: `ip neigh` / Windows: `arp -a`

## 四、免费 ARP（Gratuitous ARP）
主机发送**发送方IP=目标IP=自己IP**的特殊 ARP。
- 检测 IP 冲突：若收到回应，说明有IP冲突
- 高可用切换时通知其他主机更新ARP表

## 五、ARP 欺骗（安全威胁）
攻击者发送虚假ARP回复，将自己MAC与受害者IP绑定，实施中间人攻击。
防御：动态ARP检测（DAI）、静态ARP绑定、HTTPS加密。
""", difficulty=3),

R("mindmap", "ARP协议", "【思维导图】ARP工作机制全景", r"""```mermaid
graph TD
    A[ARP协议] --> B[作用: IP→MAC映射]
    A --> C[工作流程]
    A --> D[特殊形式]
    A --> E[安全威胁]
    A --> F[ARP缓存]

    B --> B1[同网段: 直接ARP目标]
    B --> B2[跨网段: ARP默认网关]

    C --> C1[广播ARP请求]
    C --> C2[目标单播回复]
    C --> C3[更新本地ARP表]

    D --> D1[免费ARP: 自己IP做IP源和目标]
    D --> D2[用途: 检测IP冲突]
    D --> D3[用途: 高可用切换更新缓存]

    E --> E1[ARP欺骗/中间人攻击]
    E --> E2[防御: 动态ARP检测DAI]

    F --> F1[TTL红20分钟]
    F --> F2[Linux: ip neigh]
```""", difficulty=3),

R("doc", "ICMP协议", "【知识文档】ICMP协议与网络诊断工具", r"""
# ICMP（互联网控制消息协议）

## 一、ICMP 的作用
传递**控制消息**和**错误报告**，是 IP 协议的伴生协议（IP协议号=1）。

## 二、重要 ICMP 类型

| 类型 | 代码 | 含义 | 应用 |
|------|------|------|------|
| 0 | 0 | Echo Reply | ping 响应 |
| 3 | 0 | Network Unreachable | 目标网络不可达 |
| 3 | 1 | Host Unreachable | 目标主机不可达 |
| 3 | 3 | Port Unreachable | UDP端口不存在 |
| 8 | 0 | Echo Request | ping 发送 |
| 11 | 0 | TTL Exceeded | traceroute利用 |

## 三、ping 工作原理
```
客户端 ――ICMP Echo Request(类型8)――► 目标主机
客户端 ◄――ICMP Echo Reply(类型0)―― 目标主机
RTT = 收到Reply时间 - 发出Request时间
```

## 四、traceroute 工作原理
利用 **TTL 递增** + **ICMP Type 11（TTL超时）**：
```
发 TTL=1 → 第1跳路由器 TTL减为0 → 回 ICMP超时（含路由器IP）→ 得1跳
发 TTL=2 → 第2跳超时 → 得2跳...
直到 TTL=N 到达目标主机 → 路径完成
```

## 五、TTL（生存时间）
- 每经过一个**路由器**，TTL-1
- TTL=0 时路由器丢弃并回 ICMP Type 11
- **默认值**：Linux=64，Windows=128
- **作用**：防止数据报在路由环路中无限转发

## 六、Path MTU Discovery（PMTUD）
利用 ICMP Type 3 Code 4（需要分片但DF=1）：
发送方设 DF 位 → 路径中小 MTU 的路由器丢弃并回 ICMP 3/4 →
发送方降低大小重发 → 逐步找到路径最小 MTU
""", difficulty=3),

R("doc", "NAT技术", "【知识文档】NAT网络地址转换原理", r"""
# NAT（网络地址转换）

## 一、NAT 的背景
IPv4地址已极度不足。NAT 允许**私有地址网络多台主机共享少量公网IP**上网。

## 二、NAPT（最常见形式）
用**端口号**区分不同内网主机：
```
内网主机 A: 192.168.1.10:54321 → [公网IP:12345] → 服务剗1.2.3.4:80
内网主机 B: 192.168.1.20:54322 → [公网IP:12346] → 服务剗1.2.3.4:80
回程包按目的端口(12345/12346)区分转发给对应内网主机
```

## 三、NAT 类型（穿透性从好到差）
| Full Cone | 任何外部IP:Port 都可主动连入。最容易穿透 |
| Restricted Cone | 只有曾通信过的外部IP可连入 |
| Symmetric NAT | 每个不同目标对应不同映射端口。最难穿透 |

## 四、NAT 的问题
| 无法被动接受连接 | 外网主机无法主动连接 NAT 后的内网服务 |
| 协议兼容性 | FTP主动模式、SIP需要 NAT ALG 辅助 |

## 五、NAT 穿透技术
| STUN | 探测公网IP和NAT类型 |
| TURN | 通过中继转发（穿透失败时备选） |
| ICE | 综合STUN+TURN（WebRTC/VoIP使用） |
| 端口转发 | 手动配置公网IP:端口 → 内网IP:端口 |
""", difficulty=4),

R("doc", "路由算法", "【知识文档】路由算法与动态路由协议", r"""
# 路由算法与动态路由协议

## 一、路由基础
路由器根据**路由表**进行**最长前缀匹配**选择转发接口。
路由来源：直连路由、静态路由、动态路由协议。

## 二、两类基础路由算法

### 距离向量（DV）
- 每台路由器只知道**邻居**的距离信息，定期广播路由表
- Bellman-Ford算法，缺点：收敛慢、计数到无穷问题
- 代表：**RIP**

### 链路状态（LS）
- 每台路由器向全网**洪泛** 自己链路状态，构建全局拓扑图
- Dijkstra算法，优点：收敛快、无环路
- 代表：**OSPF**

## 三、主要路由协议

### RIP
- DV，度量=**跳数**（最大7，16=不可达）
- UDP 520端口，每30秒广播路由表
- 适用：小型简单网络

### OSPF
- LS，支持多种度量（默认按带宽）
- 支持**区域划分**（Area 0为骨干区）
- 适用：中大型企业网络

### BGP
- **AS间**路由协议，互联网的骨干
- TCP 179端口，路径向量协议
- AS路径+策略驱动

## 四、路由聚合
```
192.168.0.0/24
192.168.1.0/24  → 汇总 → 192.168.0.0/22
192.168.2.0/24
192.168.3.0/24
```
""", difficulty=4),

R("mindmap", "路由算法", "【思维导图】路由协议体系全景", r"""```mermaid
graph TD
    A[路由协议体系] --> B[IGP 域内路由]
    A --> C[EGP 域间路由]
    A --> D[算法分类]

    B --> RIP[RIP 距离向量]
    B --> OSPF[OSPF 链路状态]

    RIP --> R1[度量: 跳数 最大7]
    RIP --> R2[UDP 520端口]
    RIP --> R3[缺陷: 收敛慢]

    OSPF --> O1[度量: 带宽等]
    OSPF --> O2[Dijkstra算法]
    OSPF --> O3[Area 0骨干区]

    C --> BGP
    BGP --> B1[TCP 179端口]
    BGP --> B2[AS间路由]
    BGP --> B3[策略驱动]

    D --> DV[距离向量: 只知邻居]
    D --> LS[链路状态: 全局拓扑]
```""", difficulty=4),

]  # END PHASE4


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 4 补充  网络层（ARP/ICMP/NAT/路由 练习+代码+思维导图）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PHASE4B = [

# ──────────── ARP 练习+代码 ────────────
R("exercise", "ARP协议", "【练习题】ARP协议综合练习", r"""## 知识点：ARP协议

---
### 判断题

**Q1. ARP 请求是广播发送，ARP 回复是单播发送。（ ）**
**答案：✅ 正确**
解析：ARP 请求目的 MAC=FF:FF:FF:FF:FF:FF（广播），而回复时已知请求方 MAC，直接单播回复。

---
**Q2. 主机 A 要与位于不同子网的主机 B 通信，A 应该对 B 的 IP 地址发 ARP 请求。（ ）**
**答案：❌ 错误**
解析：不同子网不能直接 ARP。A 应该对**默认网关（路由器）**的 IP 发 ARP 请求，由路由器转发。

---
### 选择题

**Q3. 下列关于 ARP 缓存的说法正确的是？（单选）**

A. ARP 缓存永久有效，不会超时
B. ARP 缓存一般有老化时间（约 20 分钟），超时后重新发请求
C. 每次通信前都必须发送 ARP 请求
D. ARP 缓存存储的是域名与 IP 的映射

**答案：B**

---
**Q4. 免费 ARP（Gratuitous ARP）的作用是？（多选）**

A. 检测局域网内 IP 地址冲突
B. 高可用故障切换时通知其他主机更新 ARP 缓存
C. 加速 DNS 解析
D. 为路由器获取远程 MAC 地址

**答案：AB**

---
### 简答题

**Q5. 什么是 ARP 欺骗攻击？如何防御？**

**参考答案：**
ARP 欺骗是攻击者发送虚假 ARP 回复，将自己的 MAC 地址与受害者 IP 绑定，
使局域网内其他主机将数据包发往攻击者（中间人攻击）。

防御手段：
1. 动态 ARP 检测（DAI）：交换机校验 ARP 包的合法性
2. 静态 ARP 绑定：手动绑定关键主机的 IP-MAC 对
3. 启用端口安全，限制每个端口允许的 MAC 数量
4. 使用 HTTPS/TLS 加密传输层，即使流量被截获也无法解密
""", difficulty=3),

R("code", "ARP协议", "【代码示例】用 Scapy 演示 ARP 请求/回复构造", r"""# ARP 报文构造演示（使用 Scapy 库，需 root/管理员权限）
# Scapy 是 Python 网络安全领域常用的报文构造工具
# pip install scapy

from scapy.all import ARP, Ether, srp, conf
import ipaddress


def arp_scan(network: str, iface: str = None) -> list:
    # 对指定网段进行 ARP 扫描，返回在线主机列表
    conf.verb = 0
    ans, _ = srp(
        Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=network),
        timeout=2,
        iface=iface,
        retry=1,
    )
    results = []
    for sent, received in ans:
        results.append({
            "ip": received.psrc,
            "mac": received.hwsrc,
        })
    return results


def show_arp_packet_structure():
    # 展示 ARP 报文字段含义（无需 root 权限）
    pkt = ARP()
    print("ARP 报文字段说明：")
    print(f"  hwtype (硬件类型):  {pkt.hwtype} (1=以太网)")
    print(f"  ptype  (协议类型):  0x{pkt.ptype:04X} (0x0800=IPv4)")
    print(f"  hwlen  (MAC长度):   {pkt.hwlen} 字节")
    print(f"  plen   (IP长度):    {pkt.plen} 字节")
    print(f"  op     (操作码):    {pkt.op} (1=请求, 2=回复)")
    print(f"  hwsrc  (发送方MAC): {pkt.hwsrc}")
    print(f"  psrc   (发送方IP):  {pkt.psrc}")
    print(f"  hwdst  (目标MAC):   {pkt.hwdst}")
    print(f"  pdst   (目标IP):    {pkt.pdst}")


if __name__ == "__main__":
    show_arp_packet_structure()
    print()
    # 扫描示例（实际运行需 root 权限）
    # results = arp_scan("192.168.1.0/24")
    # for r in results:
    #     print(f"  {r['ip']:16s}  {r['mac']}")
""", difficulty=4, language="python"),

# ──────────── ICMP 练习+代码+思维导图 ────────────
R("exercise", "ICMP协议", "【练习题】ICMP与网络诊断工具", r"""## 知识点：ICMP协议

---
### 选择题

**Q1. ping 命令使用的 ICMP 消息类型组合是？**

A. Type 8（请求）+ Type 0（回复）
B. Type 3（请求）+ Type 4（回复）
C. Type 11（请求）+ Type 0（回复）
D. Type 0（请求）+ Type 8（回复）

**答案：A**
解析：Echo Request = Type 8，Echo Reply = Type 0。

---
**Q2. traceroute 利用了哪种 ICMP 消息？**

A. ICMP Type 0（Echo Reply）
B. ICMP Type 3（Destination Unreachable）
C. ICMP Type 11（Time Exceeded）
D. ICMP Type 8（Echo Request）

**答案：C**
解析：traceroute 依次发送 TTL=1,2,3... 的 UDP/ICMP 包，每跳路由器 TTL-1=0 时返回
ICMP Type 11（TTL Exceeded），从而确定路径上每个路由器的 IP。

---
**Q3. 一台 Linux 主机默认 TTL 值是多少？**

A. 64
B. 128
C. 255
D. 32

**答案：A**
解析：Linux 默认 TTL=64，Windows 默认 TTL=128。可通过 ping 结果的 TTL 字段估算跳数。

---
### 简答题

**Q4. 解释 Path MTU Discovery（PMTUD）原理，以及 ICMP 在其中的作用。**

**参考答案：**
PMTUD 用于发现端到端路径上的最小 MTU，避免 IP 分片。

工作原理：
1. 发送方在 IP 头设置 DF（Don't Fragment）位=1
2. 如果路径中某路由器的链路 MTU 小于当前数据包，该路由器丢弃数据包
3. 并返回 ICMP Type 3 Code 4（Fragmentation Needed, DF Set），附带下一跳 MTU 值
4. 发送方收到后降低 MSS 重新发送
5. 重复直到找到路径最小 MTU

注意：如果防火墙过滤 ICMP，PMTUD 会失败（黑洞路由），导致 TCP 连接建立但数据无法传输。
""", difficulty=3),

R("code", "ICMP协议", "【代码示例】Python 实现简化版 ping 与 traceroute", r"""# 简化版 ping 和 traceroute 实现，展示 ICMP 原理
# 完整实现需要 root/管理员权限（原始套接字）
import socket
import struct
import time
import select


def checksum(data: bytes) -> int:
    # 计算 Internet 校验和
    if len(data) % 2:
        data += b'\x00'
    total = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i + 1]
        total += word
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return ~total & 0xFFFF


def build_icmp_echo(seq: int, pid: int) -> bytes:
    # 构造 ICMP Echo Request (Type=8, Code=0)
    header = struct.pack('!BBHHH', 8, 0, 0, pid, seq)
    payload = b'PingData' * 4
    csum = checksum(header + payload)
    header = struct.pack('!BBHHH', 8, 0, csum, pid, seq)
    return header + payload


def simple_ping(host: str, count: int = 4) -> None:
    # 发送 ICMP Echo 请求（需要管理员权限）
    pid = 12345
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    dest_ip = socket.gethostbyname(host)
    print(f"Pinging {host} [{dest_ip}]")
    for seq in range(count):
        pkt = build_icmp_echo(seq, pid)
        t_send = time.time()
        sock.sendto(pkt, (dest_ip, 0))
        ready = select.select([sock], [], [], 2)
        if ready[0]:
            data, _ = sock.recvfrom(1024)
            rtt = (time.time() - t_send) * 1000
            # IP 头 20 字节，ICMP 从第 20 字节开始
            icmp_type = data[20]
            print(f"  Reply from {dest_ip}: type={icmp_type}, time={rtt:.2f}ms")
        else:
            print(f"  Request timeout for seq={seq}")
        time.sleep(0.5)
    sock.close()


# 展示 ICMP 报文结构（不需要权限）
def show_icmp_types():
    types = [
        (0, 0, "Echo Reply", "ping 回复"),
        (3, 0, "Net Unreachable", "目标网络不可达"),
        (3, 1, "Host Unreachable", "目标主机不可达"),
        (3, 3, "Port Unreachable", "目标端口不可达（UDP无监听）"),
        (3, 4, "Frag Needed", "需要分片但DF=1（PMTUD）"),
        (8, 0, "Echo Request", "ping 请求"),
        (11, 0, "TTL Exceeded", "TTL超时（traceroute利用）"),
    ]
    print(f"{'Type':>4} {'Code':>4}  {'名称':<20} {'用途'}")
    print("-" * 60)
    for t, c, name, desc in types:
        print(f"{t:>4} {c:>4}  {name:<20} {desc}")


if __name__ == "__main__":
    show_icmp_types()
    # 需要管理员权限：
    # simple_ping("8.8.8.8")
""", difficulty=4, language="python"),

R("mindmap", "ICMP协议", "【思维导图】ICMP协议与网络诊断", r"""```mermaid
graph TD
    A[ICMP协议] --> B[消息类型]
    A --> C[诊断工具]
    A --> D[TTL机制]
    A --> E[PMTUD]

    B --> T0[Type 0: Echo Reply]
    B --> T3[Type 3: Destination Unreachable]
    B --> T8[Type 8: Echo Request]
    B --> T11[Type 11: TTL Exceeded]

    T3 --> T3_0[Code 0: 网络不可达]
    T3 --> T3_1[Code 1: 主机不可达]
    T3 --> T3_3[Code 3: 端口不可达]
    T3 --> T3_4[Code 4: 需要分片DF=1]

    C --> PING[ping: Type8+Type0]
    C --> TRACE[traceroute: TTL递增+Type11]

    D --> D1[每跳路由器TTL-1]
    D --> D2[TTL=0时丢弃并回Type11]
    D --> D3[Linux默认TTL=64]
    D --> D4[Windows默认TTL=128]

    E --> E1[发送方DF=1]
    E --> E2[小MTU路由器回Type3 Code4]
    E --> E3[发送方降低MSS重发]
```""", difficulty=3),

# ──────────── NAT 练习+代码+思维导图 ────────────
R("exercise", "NAT技术", "【练习题】NAT原理与穿透", r"""## 知识点：NAT网络地址转换

---
### 选择题

**Q1. NAPT（网络地址端口转换）用什么方式区分不同内网主机的连接？**

A. IP地址
B. MAC地址
C. 端口号
D. 序列号

**答案：C**
解析：NAPT 将多个内网主机映射到同一公网 IP 的不同端口，用（公网IP: 端口号）唯一标识每个连接。

---
**Q2. 下列哪种 NAT 类型最难被 P2P 穿透？**

A. Full Cone NAT
B. Restricted Cone NAT
C. Port Restricted Cone NAT
D. Symmetric NAT

**答案：D**
解析：Symmetric NAT 对每个不同的（目标IP:端口）组合使用不同的外部端口，P2P 很难预测端口映射。

---
### 简答题

**Q3. 解释为什么 NAT 会破坏 FTP 主动模式，如何解决？**

**参考答案：**
FTP 主动模式中，客户端将自己的 IP 和数据端口号通过 PORT 命令告知服务器，
服务器主动连接客户端。问题在于：
- 客户端告诉服务器的是**私有 IP**（如 192.168.1.10）
- 服务器无法连接私有 IP（不可路由）

解决方案：
1. 使用 FTP **被动模式（PASV）**：由服务器提供端口，客户端主动连接，绕过 NAT 问题
2. 配置 NAT **ALG（应用层网关）**：NAT 设备识别 FTP PORT 命令并替换其中的私有 IP 为公网 IP

---
**Q4. 简述 WebRTC 使用 ICE 框架进行 NAT 穿透的步骤。**

**参考答案：**
1. 双方各自收集候选地址：本地地址、STUN 反射地址（公网IP:Port）、TURN 中继地址
2. 通过信令服务器交换候选地址列表
3. 按优先级顺序尝试连通性检测（STUN binding request）
4. 选择延迟最小的可用连接路径
5. 如果直连失败（对称 NAT），使用 TURN 服务器中继
""", difficulty=4),

R("mindmap", "NAT技术", "【思维导图】NAT技术全景", r"""```mermaid
graph TD
    A[NAT技术] --> B[工作原理]
    A --> C[NAT类型]
    A --> D[NAT的问题]
    A --> E[穿透技术]

    B --> B1[私有地址+端口 映射到 公网IP+端口]
    B --> B2[NAT表记录映射关系]
    B --> B3[回程包按端口反向转发]

    C --> FC[Full Cone: 最易穿透]
    C --> RC[Restricted Cone]
    C --> SYM[Symmetric: 最难穿透]

    D --> D1[外网无法主动连接内网]
    D --> D2[打破端到端原则]
    D --> D3[FTP主动模式兼容性]
    D --> D4[SIP/VoIP需ALG辅助]

    E --> STUN[STUN: 探测公网地址]
    E --> TURN[TURN: 中继服务器]
    E --> ICE[ICE: 综合STUN+TURN]
    E --> PF[端口转发: 手动静态映射]
```""", difficulty=4),

# ──────────── 路由算法 练习+代码 ────────────
R("exercise", "路由算法", "【练习题】路由协议综合练习", r"""## 知识点：路由算法与动态路由协议

---
### 选择题

**Q1. OSPF 使用哪种路由算法计算最短路径？**

A. Bellman-Ford
B. Dijkstra
C. Floyd-Warshall
D. 贪心算法

**答案：B**
解析：OSPF 是链路状态协议，每台路由器基于全局拓扑图用 Dijkstra 算法计算最短路径树。

---
**Q2. RIP 协议的最大跳数限制是多少？超过后如何处理？**

A. 8跳，超过丢弃
B. 15跳，超过视为不可达（跳数=16）
C. 32跳，超过广播路由更新
D. 无限制

**答案：B**
解析：RIP 最大有效跳数 = 15，16 表示不可达（无穷大）。这限制了 RIP 只能用于小型网络。

---
**Q3. 关于 BGP 的描述，错误的是？**

A. BGP 运行在 TCP 179 端口之上
B. BGP 是 AS 间的路由协议
C. BGP 使用链路带宽作为度量值
D. BGP 使用 AS-PATH 防止路由环路

**答案：C**
解析：BGP 是路径向量协议，度量基于**策略**（如 AS-PATH 长度、LOCAL_PREF、MED 等），不使用简单的带宽度量。

---
### 计算题

**Q4. 路由聚合：将以下4条路由聚合为一条路由**
```
10.0.4.0/24
10.0.5.0/24
10.0.6.0/24
10.0.7.0/24
```

**参考答案：**
```
4 = 0000 0100
5 = 0000 0101
6 = 0000 0110
7 = 0000 0111
前22位相同: 0000 1 00 -> 10.0.4.0/22
```
聚合结果：**10.0.4.0/22**（包含 .4.0 ~ .7.255）

---
**Q5. 解释距离向量协议的"计数到无穷"问题及水平分割如何解决它。**

**参考答案：**
问题描述：网络故障时，两台路由器 A 和 B 互相告知对方可达某不可达网络，
导致跳数不断增加直到达到无穷大值（16），收敛极慢。

水平分割（Split Horizon）：从某接口学到的路由信息，不再从该接口通告回去，
切断路由信息回流，防止形成计数环路。

加强版：带毒化反转的水平分割（Split Horizon with Poison Reverse）：
不仅不通告，而且主动通告该路由度量=无穷大（16），更快消除错误路由。
""", difficulty=4),

R("code", "路由算法", "【代码示例】Dijkstra最短路径算法演示（OSPF原理）", r"""# Dijkstra 算法实现 - OSPF 链路状态路由原理演示
import heapq
from typing import Dict, List, Tuple


Graph = Dict[str, List[Tuple[str, int]]]  # 邻接表: 节点 -> [(邻居, 权重)]


def dijkstra(graph: Graph, start: str) -> Tuple[Dict[str, int], Dict[str, str]]:
    # 返回 (到各节点的最小代价, 最短路径的前驱节点)
    dist = {node: float('inf') for node in graph}
    prev = {node: None for node in graph}
    dist[start] = 0
    heap = [(0, start)]  # (代价, 节点)

    while heap:
        cost, u = heapq.heappop(heap)
        if cost > dist[u]:
            continue  # 过期条目，跳过
        for v, w in graph[u]:
            new_cost = dist[u] + w
            if new_cost < dist[v]:
                dist[v] = new_cost
                prev[v] = u
                heapq.heappush(heap, (new_cost, v))

    return dist, prev


def reconstruct_path(prev: Dict[str, str], start: str, end: str) -> List[str]:
    # 从前驱表重建最短路径
    path = []
    cur = end
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path if path[0] == start else []


def print_routing_table(graph: Graph, router: str) -> None:
    # 模拟 OSPF 为指定路由器生成路由表
    dist, prev = dijkstra(graph, router)
    print(f"路由器 {router} 的最短路径表 (OSPF Dijkstra):")
    print(f"{'目的节点':<10} {'代价':<8} {'下一跳'}")
    print("-" * 35)
    for dest in sorted(graph):
        if dest == router:
            continue
        cost = dist[dest]
        path = reconstruct_path(prev, router, dest)
        next_hop = path[1] if len(path) > 1 else "-"
        print(f"{dest:<10} {cost:<8} {next_hop}  (路径: {' -> '.join(path)})")


if __name__ == "__main__":
    # 拓扑图示例（节点=路由器，权重=链路代价）
    topo: Graph = {
        "R1": [("R2", 1), ("R3", 4)],
        "R2": [("R1", 1), ("R3", 2), ("R4", 5)],
        "R3": [("R1", 4), ("R2", 2), ("R4", 1)],
        "R4": [("R2", 5), ("R3", 1)],
    }
    print_routing_table(topo, "R1")
    print()
    print("注：OSPF 代价通常 = 100Mbps / 链路带宽，代价越小链路越快")
""", difficulty=4, language="python"),

]  # END PHASE4B


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 5  应用层
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PHASE5 = [

# ──────────── HTTP 协议 ────────────
R("doc", "HTTP协议", "【知识文档】HTTP/1.1 协议全载", r"""# HTTP/1.1 协议全载

## 一、HTTP 基础
HTTP（HyperText Transfer Protocol）是 Web 的基础协议，层于 TCP 之上，
默认端口 **80**，HTTPS 端口 **443**。HTTP 是**无状态协议**——每个请求都是独立的。

## 二、HTTP 方法

| 方法 | 语义 | 幂等性 | 安全性 |
|------|------|---------|--------|
| GET | 请求资源 | 是 | 是 |
| POST | 提交数据 | 否 | 否 |
| PUT | 全量更新资源 | 是 | 否 |
| PATCH | 部分更新资源 | 否 | 否 |
| DELETE | 删除资源 | 是 | 否 |
| HEAD | 只取响应头 | 是 | 是 |
| OPTIONS | 查询支持方法 | 是 | 是 |

> 幂等性：多次操作结果相同。安全性：不修改服务器状态。

## 三、常用状态码

| 类别 | 类型 | 常用程序员必知 |
|------|------|---|
| 1xx | 信息性响应 | 101 Switching Protocols（WebSocket升级） |
| 2xx | 成功 | 200 OK, 201 Created, 204 No Content |
| 3xx | 重定向 | 301 永久, 302 临时, 304 Not Modified |
| 4xx | 客户端错误 | 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found |
| 5xx | 服务器错误 | 500 Internal Error, 502 Bad Gateway, 503 Unavailable |

## 四、HTTP/1.1 请求报文格式

```
GET /api/users?page=1 HTTP/1.1\r\n
Host: example.com\r\n
Accept: application/json\r\n
Accept-Encoding: gzip, deflate\r\n
Connection: keep-alive\r\n
Cookie: session=abc123\r\n
\r\n
(无请求体)
```

## 五、持久连接与流水线

- **HTTP/1.0**：每次请求新建 TCP 连接，常需 `Connection: keep-alive`
- **HTTP/1.1**：默认持久连接（keep-alive），支持流水线（pipelining）
- **流水线问题**：入队头阻塞（HOL blocking）—后续请求必须等前一个完成

## 六、HTTP/2 的改进

- **二进制帧层**：每个请求/响应分成帧
- **多路复用**：单一 TCP 连接并发多请求，解决 HOL blocking
- **头部压缩**：HPACK 算法
- **服务器推送**：服务器主动推送资源

## 七、HTTP/3 与 QUIC

- 底层使用 **QUIC（基于 UDP）** 替代 TCP
- 彩色多路复用：彼此独立的流，一条流错误不影响其他
- 建立连接时延更低：0-RTT 重连

## 八、Cookie 与 Session

| | Cookie | Session |
|-|--------|---------|
| 存储位置 | 客户端浏览器 | 服务器端 |
| 安全性 | 较低（可被篡改） | 较高 |
| 容量 | ~4KB | 无限制 |
| 现代替代方案 | JWT（无状态 Token） | |
""", difficulty=3),

R("exercise", "HTTP协议", "【练习题】HTTP协议综合练习", r"""## 知识点：HTTP协议

---
### 判断题

**Q1. HTTP 是有状态协议。（ ）**
**答案：✗ 错误**
解析：HTTP 本身是无状态协议，服务器不保存两次请求之间的状态。Cookie/Session 是应用层引入的状态管理机制。

---
**Q2. HTTP/1.1 默认使用持久连接（keep-alive）。（ ）**
**答案：✅ 正确**
解析：HTTP/1.1 在请求头 `Connection: keep-alive` 下默认持久连接，不必每次重建 TCP。

---
### 选择题

**Q3. 以下 HTTP 状态码中，表示资源未修改可直接使用缓存的是？**

A. 200
B. 301
C. 304
D. 404

**答案：C**
解析：304 Not Modified 表示客户端缓存仍有效，服务器不需返回资源体。客户端需在请求中携带 `If-None-Match`/`If-Modified-Since`。

---
**Q4. HTTP POST 请求与 GET 请求的主要区别是？（多选）**

A. POST 有请求体，GET 通常没有
B. POST 不幂等，多次提交产生不同结果；GET 幂等
C. POST 参数在 URL 中，GET 参数在请求体中
D. GET 有浏览器缓存，POST 一般不缓存

**答案：ABD**
解析：C 反了——是 GET 参数在 URL 中，POST 参数在请求体。

---
### 简答题

**Q5. 解释 HTTP/2 如何解决 HTTP/1.1 的队头阻塞（HOL Blocking）问题。**

**参考答案：**
HTTP/1.1 的流水线机制要求响应必须按请求顺序返回，若第一个请求延迟，后续请求必须等待。

HTTP/2 引入二进制帧层和流多路复用：
- 每个请求/响应划分为多个帧，每帧有流ID
- 单一 TCP 连接上并发发送不同流的帧
- 帧可乱序到达，接收方按流ID和帧序号重组
- 帧层面的 HOL blocking 仍在 TCP 层存在，HTTP/3 用 QUIC 解决

---
**Q6. 一个完整的 HTTP 请求/响应周期是怎样的？**

**参考答案：**
1. DNS 解析域名得到服务器 IP
2. TCP 三次握手建立连接
3. （HTTPS）TLS 握手建立加密信道
4. 发送 HTTP 请求报文
5. 服务器处理并返回 HTTP 响应报文
6. 浏览器解析 HTML/CSS/JS，对子资源重复步骤4-5
7. TCP 四次挥手（持久连接则在限时后关闭）
""", difficulty=3),

R("code", "HTTP协议", "【代码示例】Python 原生 Socket 实现 HTTP 客户端与服务器", r"""# 用原生 TCP 套接字实现最小化 HTTP/1.1 客户端
# 展示 HTTP 报文的真实结构
import socket
import threading


def http_get(host: str, path: str = "/", port: int = 80) -> tuple:
    # 返回 (status_code, headers_dict, body_str)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((host, port))

    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Connection: close\r\n"
        f"Accept: */*\r\n"
        f"\r\n"
    )
    sock.sendall(request.encode())

    buf = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
    sock.close()

    header_end = buf.find(b"\r\n\r\n")
    header_raw = buf[:header_end].decode(errors="replace")
    body = buf[header_end + 4:]

    lines = header_raw.split("\r\n")
    status_code = int(lines[0].split(" ")[1])
    headers = {}
    for line in lines[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()

    return status_code, headers, body.decode(errors="replace")


def run_http_server(port: int = 8080):
    # 极简 HTTP/1.1 服务器示例
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("", port))
    srv.listen(5)
    print(f"HTTP 服务器监听于端口 {port}")

    def handle(conn, addr):
        data = conn.recv(4096).decode(errors="replace")
        req_line = data.split("\r\n")[0]
        print(f"[{addr[0]}] {req_line}")
        body = "<h1>Hello from raw Python HTTP server!</h1>"
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            f"Content-Length: {len(body.encode())}\r\n"
            "Connection: close\r\n"
            "\r\n"
            + body
        )
        conn.sendall(response.encode())
        conn.close()

    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    code, hdrs, body = http_get("httpbin.org", "/get")
    print(f"Status: {code}")
    print(f"Headers: {dict(list(hdrs.items())[:4])}")
    print(f"Body (100 chars): {body[:100]}")
""", difficulty=4, language="python"),

R("mindmap", "HTTP协议", "【思维导图】HTTP协议体系", r"""```mermaid
graph TD
    A[HTTP协议] --> B[版本演进]
    A --> C[方法]
    A --> D[状态码]
    A --> E[持久连接与性能]
    A --> F[应用机制]

    B --> V1[HTTP/1.0: 短连接]
    B --> V2[HTTP/1.1: 持久+流水线]
    B --> V3[HTTP/2: 二进制+多路复用]
    B --> V4[HTTP/3: QUIC底层]

    C --> GET[GET: 幂等+安全]
    C --> POST[POST: 非幂等]
    C --> PUT[PUT: 全量更新]
    C --> DEL[DELETE: 删除]

    D --> D2xx[2xx: 成功]
    D --> D3xx[3xx: 重定向]
    D --> D4xx[4xx: 客户端错]
    D --> D5xx[5xx: 服务器错]

    E --> KEEP[持久连接: 复用TCP连接]
    E --> PIPE[流水线: 并发请求]
    E --> HOL[HOL阻塞: HTTP/1.1缺陷]

    F --> COOKIE[Cookie: 客户端状态]
    F --> CACHE[Cache-Control: 缓存控制]
    F --> CORS[CORS: 跨域资源共享]
```""", difficulty=3),

# ──────────── HTTPS/TLS ────────────
R("doc", "HTTPS与TLS", "【知识文档】HTTPS 与 TLS 1.3 安全传输详解", r"""# HTTPS 与 TLS 1.3 详解

## 一、HTTPS 概述
HTTPS = HTTP + TLS。TLS（Transport Layer Security）在 TCP 和 HTTP 之间，提供：
- **加密（Confidentiality）**：内容对第三方不可读
- **完整性（Integrity）**：MAC 防篡改
- **认证（Authentication）**：证书验证服务器身份

## 二、TLS 1.3 握手流程（1-RTT）

```
客户端                               服务器
  |--ClientHello--------------------->|  发送支持的密码套件列表、TLS版本
  |  (包含 key_share: 公钥 ECDH)       、key_share 公钥
  |<--ServerHello----------------------|  选定密码套件、key_share
  |<--EncryptedExtensions--------------|  其他扩展
  |<--Certificate----------------------|  服务器证书
  |<--CertificateVerify----------------|  证书属于该服务器的签名
  |<--Finished-------------------------|  HMAC验证握手
  |双方已导出会话密钥|
  |---Finished+HTTP Request----------->|  1-RTT 完成，开始加密通信
```

## 三、TLS 1.3 密码套件
TLS 1.3 只保留 5 个密码套件，均具有前向保密（PFS）：
- TLS_AES_128_GCM_SHA256
- TLS_AES_256_GCM_SHA384
- TLS_CHACHA20_POLY1305_SHA256

废除：RSA 密钥交换、RC4、DES、SHA-1

## 四、数字证书

```
证书结构：
  版本、序列号、签名算法
  主题：domain.com
  公钥：服务器RSA/ECDSA公钥
  有效期
  签发机构（CA）的数字签名

证书验证链：
  主证书 --由--> 中间证书 --由--> 根CA证书（浏览器内置信任）
```

## 五、HSTS（HTTP Strict Transport Security）
服务器在响应头设置：
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
```
浏览器受到后在 max-age 期内强制使用 HTTPS，防止 SSL Stripping 攻击。

## 六、常见 TLS 攻击

| 攻击 | TLS版本 | 防御 |
|------|---------|------|
| BEAST | TLS 1.0 | 升级到 TLS 1.2+ |
| POODLE | SSL 3.0 | 禁用 SSL 3.0 |
| Heartbleed | OpenSSL漏洞 | 打补丁 |
| 中间人证书炮射 | 任意 | CA浏览器钉退、CT日志 |
""", difficulty=4),

R("exercise", "HTTPS与TLS", "【练习题】HTTPS与TLS安全练习", r"""## 知识点：HTTPS 与 TLS

---
### 选择题

**Q1. TLS 1.3 完成握手需要多少个 RTT？**

A. 0
B. 1
C. 2
D. 3

**答案：B**
解析：TLS 1.3 在 1-RTT 内完成握手（展示是指建立层面 1 个往返 RTT）。已知服务器时支持 0-RTT 恢复连接。

---
**Q2. 前向保密（PFS）的含义是？**

A. 即使将来服务器私钥被盗，过去的会话密文也无法被解密
B. 客户端必须先同服务器交换公钥才能通信
C. 密码套件越多越安全
D. 所有 TLS 版本都具备前向保密

**答案：A**
解析：TLS 1.3 强制使用临时密钥（每次会话生成不同的 DH/ECDH 私钥），即使双方长期私钥被奺，历史会话不泄露。

---
**Q3. 数字证书中含有哪些信息？（多选）**

A. 服务器域名
B. 服务器的公钥
C. CA 的数字签名
D. TLS 会话密钥

**答案：ABC**
解析：D 错误——TLS 会话密钥是在握手过程中当场派生的，不存在于证书中。

---
### 简答题

**Q4. 解释 HSTS 如何防御 SSL Stripping 攻击。**

**参考答案：**
SSL Stripping 是中间人攻击：攻击者将客户端的 HTTPS 请求降级为 HTTP，
自己再用 HTTPS 连接服务器，客户端就不知情发送了明文。

HSTS 预先修复：服务器在 HTTPS 响应头中添加
`Strict-Transport-Security: max-age=31536000`，浏览器收到后在指定期限内
**拒绝任何 HTTP 升级请求**，直接将 http:// URL 内部转化为 https://，
即使显示中间人也无法降级连接。
""", difficulty=4),

R("code", "HTTPS与TLS", "【代码示例】Python ssl 模块实现 TLS 客户端与证书查验", r"""# Python ssl 模块展示 TLS 连接测试与证书信息获取
import ssl
import socket
from datetime import datetime


def tls_connect_info(hostname: str, port: int = 443) -> dict:
    # 连接并获取 TLS 证书信息
    ctx = ssl.create_default_context()
    with socket.create_connection((hostname, port), timeout=5) as raw:
        with ctx.wrap_socket(raw, server_hostname=hostname) as tls:
            cert = tls.getpeercert()
            cipher = tls.cipher()   # (name, proto, bits)
            proto = tls.version()   # 'TLSv1.3'
    return {
        "hostname": hostname,
        "tls_version": proto,
        "cipher_name": cipher[0],
        "cipher_bits": cipher[2],
        "subject": dict(x[0] for x in cert.get("subject", [])),
        "issuer": dict(x[0] for x in cert.get("issuer", [])),
        "not_after": cert.get("notAfter"),
        "san": [v for t, v in cert.get("subjectAltName", []) if t == "DNS"],
    }


def check_cert_expiry(hostname: str, warn_days: int = 30) -> str:
    # 检查证书过期时间，返回警告信息
    info = tls_connect_info(hostname)
    not_after = datetime.strptime(info["not_after"], "%b %d %H:%M:%S %Y %Z")
    days_left = (not_after - datetime.utcnow()).days
    status = "OK" if days_left > warn_days else "WARNING"
    return f"[{status}] {hostname}: 证书剩余 {days_left} 天到期 ({not_after.date()})"


if __name__ == "__main__":
    for host in ["www.baidu.com", "www.github.com"]:
        try:
            info = tls_connect_info(host)
            print(f"\n{host}:")
            print(f"  TLS 版本: {info['tls_version']}")
            print(f"  密码套件: {info['cipher_name']} ({info['cipher_bits']}bits)")
            print(f"  CN: {info['subject'].get('commonName', 'N/A')}")
            print(f"  签发机构: {info['issuer'].get('organizationName', 'N/A')}")
            print(f"  SAN: {info['san'][:3]}")
            print(f"  到期: {info['not_after']}")
        except Exception as e:
            print(f"{host}: 错误 - {e}")
""", difficulty=4, language="python"),

# ──────────── DNS 协议 ────────────
R("doc", "DNS协议", "【知识文档】DNS 域名解析系统详解", r"""# DNS 域名解析系统

## 一、DNS 的作用
将人类可读的域名（如 www.example.com）解析为 IP 地址。
基于 **UDP 53** 端口（大于 512B 时用 TCP）。

## 二、层次结构

```
域名结构（右到左）：  . -> com -> example -> www

  .根域          (13个根服务器组，A-M)
  |-- .com          TLD 服务器 (ICANN/威瑞迩)
      |-- example.com    权威 DNS 服务器
          |-- www        A 记录 -> 93.184.216.34
```

## 三、解析过程（递归+迭代）

```
1. 客户端           2. 本地缓存          3. 递归解析器(运营商DNS)
   查询www.ex.com -->找到缓存?->No--> 递归解析器
                                         |
                     4. 根服务器 <---迭代查询----|
                        返回 .com TLD地址
                     5. .com TLD <--迭代查询
                        返回 example.com权威DNS
                     6. example.com权威DNS <--迭代查询
                        返回 www.example.com A记录
                     7. 递归解析器缓存并返回客户端
```

## 四、常用 DNS 记录类型

| 类型 | 含义 | 示例 |
|------|------|------|
| A | IPv4 地址 | example.com -> 93.184.216.34 |
| AAAA | IPv6 地址 | example.com -> 2606:2800::1 |
| CNAME | 别名 | www -> example.com |
| MX | 邮件服务器 | MX 10 mail.example.com |
| NS | 名称服务器 | example.com NS ns1.registrar.com |
| TXT | 任意文本 | SPF、DKIM、域名验证 |
| PTR | 反向解析 IP->domain | 用于反查 |
| SOA | 类起始授权 | 区域主要信息 |

## 五、TTL 与 DNS 缓存

- DNS 答案中将 **TTL**（Time To Live）指定缓存局期
- 修改 DNS 前先将 TTL 降低（如 300s），完成切换后恢复

## 六、DNS 安全

| DNSSEC | 使用数字签名验证 DNS 记录的负性 |
| DNS over HTTPS（DoH） | 通过 HTTPS 加密 DNS 查询 |
| DNS over TLS（DoT） | 通过 TLS 加密 DNS 查询 |
| DNS 污染 | 攻击者注入假 DNS 记录 |
""", difficulty=3),

R("exercise", "DNS协议", "【练习题】DNS解析系统综合练习", r"""## 知识点：DNS域名解析

---
### 判断题

**Q1. DNS 递归查询中，本地 DNS 解析器代替客户端完成全部迭代过程。（ ）**
**答案：✅ 正确**
解析：客户端只向本地解析器发一次递归查询，本地解析器依次向根/TLD/权威DNS发迭代查询。

---
### 选择题

**Q2. DNS 记录类型 CNAME 表示什么？**

A. IPv6 地址
B. 域名的别名（指向另一个域名）
C. 邮件服务器地址
D. 反向解析

**答案：B**

---
**Q3. 查询 www.example.com A 记录最完整的迭代解析顺序是？**

A. 根服务器 -> .com TLD -> example.com权威 -> A记录
B. .com TLD -> 根服务器 -> example.com权威 -> A记录
C. example.com权威 -> .com TLD -> 根服务器 -> A记录
D. 根服务器 -> example.com权威 -> .com TLD -> A记录

**答案：A**
解析：迭代解析从根开始，根->TLD->权威DNS服务器->记录。

---
### 简答题

**Q4. 为什么 DNS 查询使用 UDP 而非 TCP？哪种情况下会改用 TCP？**

**参考答案：**
UDP 原因：
- DNS 查询通常很小（<512B），UDP 满足
- UDP 无连接建立开销，延迟更低
- 如查询失败重发即可

改用 TCP 的情况：
- 响应数据超过 512B（EDNS0 是4096B）
- DNS 区域传输（主-备服务器同步的所有记录）
- DNSSEC 记录较大时
""", difficulty=3),

R("code", "DNS协议", "【代码示例】Python 实现 DNS 查询工具与解析流程展示", r"""# DNS 查询工具示例 - 展示常用记录类型查询
import socket
import struct
import random


def simple_dns_query(domain: str, qtype: str = "A",
                     server: str = "8.8.8.8") -> dict:
    # 不依赖第三方库的最小 DNS 查询实现
    QTYPES = {"A": 1, "AAAA": 28, "MX": 15, "NS": 2, "TXT": 16, "CNAME": 5}
    qtype_code = QTYPES.get(qtype.upper(), 1)

    txid = random.randint(0, 65535)
    flags = 0x0100  # 递归查询
    header = struct.pack("!HHHHHH", txid, flags, 1, 0, 0, 0)

    question = b""
    for label in domain.split("."):
        question += bytes([len(label)]) + label.encode()
    question += b"\x00"  # 根域名结束
    question += struct.pack("!HH", qtype_code, 1)  # QTYPE, QCLASS=IN

    pkt = header + question
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(3)
    sock.sendto(pkt, (server, 53))
    resp, _ = sock.recvfrom(512)
    sock.close()

    ancount = struct.unpack_from("!H", resp, 6)[0]
    return {"txid": txid, "answers": ancount, "raw_len": len(resp)}


def dns_lookup_demo():
    # 利用标准库 socket.getaddrinfo 演示多记录类型查询
    demos = [
        ("www.baidu.com", socket.AF_INET),
        ("ipv6.baidu.com", socket.AF_INET6),
    ]
    for domain, family in demos:
        try:
            results = socket.getaddrinfo(domain, None, family)
            ips = list({r[4][0] for r in results})
            print(f"{domain:30s} -> {ips}")
        except socket.gaierror as e:
            print(f"{domain:30s} -> 错误: {e}")


def show_dns_hierarchy():
    # 展示域名层次结构
    domain = "mail.corp.example.com."
    print(f"\n域名层次分析：{domain}")
    labels = domain.rstrip(".").split(".")
    levels = ["."] + ["." + ".".join(labels[-i:]) for i in range(1, len(labels)+1)]
    print("  " + " -> ".join(reversed(levels)))
    print()
    print("解析顺序：")
    print("  1. 根服务器返回 .com TLD 服务器地址")
    print("  2. .com TLD 返回 example.com 权威 DNS")
    print("  3. example.com 返回 corp.example.com 权威 DNS")
    print("  4. corp.example.com 返回 mail.corp.example.com A 记录")


if __name__ == "__main__":
    print("=== DNS A/AAAA 记录查询 ===")
    dns_lookup_demo()
    show_dns_hierarchy()
    print("\n=== 手工构造 DNS 查询包 ===")
    r = simple_dns_query("www.baidu.com", "A")
    print(f"  TxID={r['txid']}, 返回答案数={r['answers']}, 响应大小={r['raw_len']}B")
""", difficulty=4, language="python"),

R("mindmap", "DNS协议", "【思维导图】DNS域名解析体系", r"""```mermaid
graph TD
    A[DNS域名解析] --> B[层次结构]
    A --> C[查询模式]
    A --> D[记录类型]
    A --> E[DNS安全]
    A --> F[TTL与缓存]

    B --> B1[根域 .]
    B --> B2[TLD: .com .cn .org]
    B --> B3[权威 DNS: example.com]
    B --> B4[主机: www]

    C --> C1[递归查询: 客户端->本地解析器]
    C --> C2[迭代查询: 本地解析器->根->TLD->权威]

    D --> A_REC[A: IPv4地址]
    D --> AAAA[AAAA: IPv6地址]
    D --> CNAME[别名记录]
    D --> MX[邮件服务器]
    D --> TXT[TXT: SPF/DKIM]

    E --> DNSSEC[数字签名验证]
    E --> DoH[DoH: DNS over HTTPS]
    E --> DoT[DoT: DNS over TLS]
    E --> POISON[DNS污染防护]

    F --> F1[TTL控制缓存期限]
    F --> F2[切换前降低TTL]
```""", difficulty=3),

]  # END PHASE5



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 6  数据链路层
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PHASE6 = [

# ──────────── 以太网帧格式 ────────────
R("doc", "以太网与帧格式", "【知识文档】以太网帧格式与数据链路层", r"""# 以太网帧格式与数据链路层

## 一、数据链路层的作用
- 将网络层传来的 IP 数据包封装成**帧（Frame）**
- 实现**帧同步**、**MAC 寻址**、**差错检测**（CRC）
- 控制**物理介质访问**（CSMA/CD 等）

## 二、以太网 II 帧格式（IEEE 802.3）

```
 7字节     1字节    6字节   6字节    2字节   46~1500字节   4字节
+--------+-------+-------+-------+--------+------------+------+
|前导码  |帧起始 |目标MAC|源MAC  |类型/长度|  数据载荷   |  FCS |
|Preamble|  SFD  | DA(6B)| SA(6B)|EtherType|  Payload  | CRC32|
+--------+-------+-------+-------+--------+------------+------+
```

| 字段 | 说明 |
|------|------|
| 前导码（7B） | 7个 0xAA，用于同步时钟 |
| SFD（1B） | 0xAB，帧起始界定符 |
| 目标 MAC（6B） | 接收方 MAC，广播=FF:FF:FF:FF:FF:FF |
| 源 MAC（6B） | 发送方 MAC |
| EtherType（2B） | 0x0800=IPv4, 0x0806=ARP, 0x86DD=IPv6, 0x8100=VLAN |
| 数据（46~1500B） | 最小 46B（不足补填充），最大 1500B=以太网 MTU |
| FCS（4B） | CRC-32 差错检测 |

## 三、MAC 地址

- **48 位（6 字节）**，十六进制表示：`AA:BB:CC:DD:EE:FF`
- **前 3 字节（OUI）**：厂商唯一标识，IEEE 分配
- **后 3 字节**：厂商自定义设备序列号
- **单播**：最低位=0（如 00:1A:2B:...）
- **组播**：最低位=1（如 01:00:5E:... 为 IPv4 组播）
- **广播**：全 1（FF:FF:FF:FF:FF:FF）

## 四、以太网 MTU 与分片

- **以太网 MTU = 1500B**（不含帧头）
- IP 数据报超过 MTU 时，**网络层**负责分片
- 巨帧（Jumbo Frame）：最大 9000B，需双方交换机支持

## 五、VLAN（虚拟局域网）

802.1Q 标准：在以太网帧头中插入 **4B VLAN 标签**：
```
EtherType(0x8100) + PCP(3bit) + DEI(1bit) + VID(12bit)
```
VLAN ID 范围 1-4094，0 和 4095 保留。
不同 VLAN 间通信需经过三层设备（路由器/三层交换机）。
""", difficulty=3),

R("exercise", "以太网与帧格式", "【练习题】以太网帧格式与MAC地址综合练习", r"""## 知识点：以太网与帧格式

---
### 判断题

**Q1. 以太网帧的最小数据部分是 46 字节，不足时需填充。（ ）**
**答案：✅ 正确**
解析：以太网帧最小总长 64 字节（6+6+2+46+4=64），数据不足 46 字节时需要填充，
以确保 CSMA/CD 碰撞检测有效工作。

---
**Q2. MAC 地址全球唯一，任何情况下都不会重复。（ ）**
**答案：✗ 错误**
解析：理论上 OUI 保证全球唯一，但虚拟机、网卡驱动可以软件修改 MAC（MAC Spoofing）；
部分厂商也曾出现重复。

---
### 选择题

**Q3. EtherType 值 0x0806 表示？**

A. IPv4
B. IPv6
C. ARP
D. VLAN

**答案：C**
解析：常见 EtherType：0x0800=IPv4，0x86DD=IPv6，0x0806=ARP，0x8100=802.1Q VLAN。

---
**Q4. 以太网 MTU 是多少字节？（不含帧头）**

A. 512
B. 1024
C. 1500
D. 9000

**答案：C**
解析：标准以太网 MTU = 1500B。Jumbo Frame 可达 9000B，需特别配置。

---
### 简答题

**Q5. 解释 MAC 地址的单播/组播/广播区别，各有何用途？**

**参考答案：**
- **单播（Unicast）**：第一字节最低位=0，发给某一具体设备，普通通信使用
- **组播（Multicast）**：第一字节最低位=1，发给一组设备，
  如 IPv4 组播用 01:00:5E:xx:xx:xx
- **广播（Broadcast）**：全F（FF:FF:FF:FF:FF:FF），发给同一网段所有设备，
  如 ARP 请求

---
**Q6. 什么是 VLAN？为什么需要 VLAN？如何实现不同 VLAN 间通信？**

**参考答案：**
VLAN（Virtual LAN）是在物理交换网络上划分的逻辑子网。

需要 VLAN 的原因：
1. 隔离广播域，提高网络安全性（不同部门互相隔离）
2. 灵活的网络规划，不受物理位置限制
3. 减少广播流量，提升性能

不同 VLAN 间通信需要三层设备：
1. **路由器单臂路由**：物理路由器通过 Sub-interface 实现 VLAN 间路由
2. **三层交换机**：集成路由功能的交换机，VLAN 间直接路由，效率更高
""", difficulty=3),

R("code", "以太网与帧格式", "【代码示例】Python 解析以太网帧结构", r"""# 以太网帧解析器 - 展示帧格式字段含义
import struct


ETHERTYPE_NAMES = {
    0x0800: "IPv4",
    0x0806: "ARP",
    0x86DD: "IPv6",
    0x8100: "802.1Q VLAN",
    0x8847: "MPLS",
    0x88CC: "LLDP",
}


def parse_ethernet_frame(raw: bytes) -> dict:
    # 解析以太网帧各字段（不包含前导码/SFD，从目的MAC开始）
    if len(raw) < 14:
        raise ValueError(f"帧太短: {len(raw)} 字节")

    dst_mac = ":".join(f"{b:02X}" for b in raw[0:6])
    src_mac = ":".join(f"{b:02X}" for b in raw[6:12])
    ethertype = struct.unpack_from("!H", raw, 12)[0]

    result = {
        "dst_mac": dst_mac,
        "src_mac": src_mac,
        "ethertype": f"0x{ethertype:04X}",
        "ethertype_name": ETHERTYPE_NAMES.get(ethertype, "Unknown"),
        "payload_len": len(raw) - 14,
        "is_broadcast": dst_mac == "FF:FF:FF:FF:FF:FF",
        "is_multicast": (raw[0] & 0x01) == 1,
    }

    # 如果是 VLAN 标记帧，解析 802.1Q
    if ethertype == 0x8100 and len(raw) >= 18:
        vlan_tag = struct.unpack_from("!H", raw, 14)[0]
        result["vlan_id"] = vlan_tag & 0x0FFF
        result["vlan_pcp"] = (vlan_tag >> 13) & 0x07
        inner_type = struct.unpack_from("!H", raw, 16)[0]
        result["inner_ethertype"] = f"0x{inner_type:04X}"
        result["inner_ethertype_name"] = ETHERTYPE_NAMES.get(inner_type, "Unknown")

    return result


def mac_classify(mac: str) -> str:
    # 判断 MAC 地址类型
    first_byte = int(mac.split(":")[0], 16)
    if mac.upper() == "FF:FF:FF:FF:FF:FF":
        return "广播"
    elif first_byte & 0x01:
        return "组播"
    else:
        return "单播"


def show_oui_info(mac: str) -> str:
    # 显示 MAC 地址的 OUI（前3字节，厂商标识）
    parts = mac.upper().split(":")
    oui = ":".join(parts[:3])
    return f"OUI={oui} (向 IEEE 注册的厂商唯一标识)"


if __name__ == "__main__":
    # 构造示例以太网帧（ARP 请求示意）
    sample_frame = (
        b"\xff\xff\xff\xff\xff\xff"  # dst: broadcast
        b"\xaa\xbb\xcc\xdd\xee\xff"  # src: 示例MAC
        b"\x08\x06"                  # EtherType: ARP
        b"\x00\x01\x08\x00\x06\x04\x00\x01"  # ARP payload示意
    )
    parsed = parse_ethernet_frame(sample_frame)
    print("解析结果：")
    for k, v in parsed.items():
        print(f"  {k}: {v}")

    print()
    for mac in ["FF:FF:FF:FF:FF:FF", "01:00:5E:7F:FF:FA", "AA:BB:CC:DD:EE:FF"]:
        print(f"  {mac} -> {mac_classify(mac)}  {show_oui_info(mac)}")
""", difficulty=3, language="python"),

R("mindmap", "以太网与帧格式", "【思维导图】数据链路层与以太网体系", r"""```mermaid
graph TD
    A[数据链路层] --> B[以太网帧格式]
    A --> C[MAC地址]
    A --> D[差错检测]
    A --> E[VLAN技术]
    A --> F[交换机工作原理]

    B --> B1[前导码7B+SFD1B]
    B --> B2[目标MAC 6B]
    B --> B3[源MAC 6B]
    B --> B4[EtherType 2B]
    B --> B5[数据 46-1500B]
    B --> B6[FCS CRC32 4B]

    C --> C1[48位 6字节]
    C --> C2[前3字节OUI厂商标识]
    C --> C3[单播: 最低位=0]
    C --> C4[组播: 最低位=1]
    C --> C5[广播: FF:FF:FF:FF:FF:FF]

    D --> D1[CRC-32循环冗余校验]
    D --> D2[检测但不纠错]

    E --> E1[802.1Q标准]
    E --> E2[VID 12位 1-4094]
    E --> E3[隔离广播域]
    E --> E4[VLAN间需三层设备]

    F --> F1[MAC地址表学习]
    F --> F2[未知单播泛洪]
    F --> F3[已知单播转发]
    F --> F4[广播泛洪]
```""", difficulty=3),

# ──────────── CSMA/CD ────────────
R("doc", "CSMA/CD", "【知识文档】CSMA/CD 碰撞检测与介质访问控制", r"""# CSMA/CD 介质访问控制

## 一、背景
早期以太网使用**共享总线**，多台主机竞争同一物理介质，需要协调机制避免冲突。

## 二、CSMA/CD 工作原理

**CSMA/CD = 载波侦听多路访问/碰撞检测**

```
发送前：
1. 载波侦听（CS）：检测信道是否空闲
2. 若空闲，开始发送帧

发送中：
3. 碰撞检测（CD）：持续监听信道
4. 若检测到碰撞（信号叠加）：
   a. 立即停止发送
   b. 发送 JAM 信号（32bit）确保所有主机知道碰撞
   c. 等待随机时间（截断二进制指数退避算法）
   d. 重新回到步骤 1，重发（最多 16 次）
```

## 三、截断二进制指数退避算法

第 k 次碰撞后，等待时间 = 随机整数 r × 512 bit time
- r 从 [0, 2^min(k,10) - 1] 中随机选取
- k=1: r ∈ {0,1}
- k=2: r ∈ {0,1,2,3}
- k=10以上: r ∈ {0,...,1023}（上限不再增加）
- k>16: 放弃，报告发送失败

## 四、最小帧长 64 字节的原因

碰撞检测要求：发送方在**帧发送完毕前**必须能检测到碰撞。
设端到端最大传播延迟为 τ，则帧发送时长必须 ≥ 2τ（round-trip）。

对于 10Mbps 以太网（最大 2500m）：
- 传播延迟约 25.6 μs，往返约 51.2 μs
- 10Mbps 下 51.2 μs = 512 bit = 64 字节

因此**最小帧长 = 64 字节**（数据最少 46 字节）。

## 五、CSMA/CD 的局限性与现代替代

| 半双工以太网 | 使用 CSMA/CD，存在碰撞 |
| **全双工以太网** | 点对点链路，**不需要 CSMA/CD** |
| 交换式以太网 | 每个端口独立点对点，消除碰撞域 |
| 无线以太网（Wi-Fi） | 使用 **CSMA/CA**（碰撞避免，无法检测） |

> 现代交换机网络已全面转向全双工模式，CSMA/CD 实际上不再使用，
> 但仍是计算机网络课程的核心考点。

## 六、碰撞域与广播域

| 设备 | 碰撞域 | 广播域 |
|------|--------|--------|
| Hub（集线器） | 一个 | 一个 |
| 交换机（Switch） | 每端口独立 | 一个 |
| 路由器（Router） | 每端口独立 | 每端口独立 |
""", difficulty=3),

R("exercise", "CSMA/CD", "【练习题】CSMA/CD 碰撞检测综合练习", r"""## 知识点：CSMA/CD 介质访问控制

---
### 判断题

**Q1. 现代全双工交换式以太网仍然使用 CSMA/CD。（ ）**
**答案：✗ 错误**
解析：全双工点对点链路没有碰撞，不需要 CSMA/CD。CSMA/CD 只用于半双工共享介质以太网。

---
### 计算题

**Q2. 10Mbps 以太网最大网段长 2500m，信号传播速度 2×10^8 m/s，最小帧长为多少字节？**

**参考答案：**
```
单程传播延迟 = 2500 / (2×10^8) = 12.5 μs
往返传播延迟 = 25 μs
最小帧发送时间 >= 2τ = 25 μs
10Mbps 下 25μs 能发送 = 10×10^6 × 25×10^-6 = 250 bit = 31.25 字节
```
实际标准取整到 **64 字节**（512 bit），同时考虑了中间设备延迟。

---
### 选择题

**Q3. CSMA/CD 中，检测到碰撞后，发送方的正确处理步骤是？**

A. 立即重发，不等待
B. 停止发送，发 JAM 信号，按指数退避等待随机时间后重发
C. 停止发送，等固定 1 秒后重发
D. 切换到另一个信道重发

**答案：B**

---
**Q4. 下列设备中，能分割碰撞域但不能分割广播域的是？**

A. Hub（集线器）
B. 交换机（Switch）
C. 路由器（Router）
D. 网卡

**答案：B**
解析：交换机每个端口是独立的碰撞域，但默认所有端口在同一广播域。
路由器既分割碰撞域也分割广播域。

---
### 简答题

**Q5. 解释截断二进制指数退避算法，及其为什么选择随机等待时间而不是固定等待。**

**参考答案：**
截断二进制指数退避：第 k 次碰撞后，等待时间 = r × 512 bit time，
其中 r 从 [0, 2^min(k,10)-1] 随机选取，超过 16 次放弃。

选择随机等待的原因：
- 若固定等待时间，同时碰撞的多台主机会在相同时刻重发，必然再次碰撞
- 随机化使各主机重发时间错开，大幅降低再次碰撞概率
- 指数增长使碰撞次数多时等待时间更长，网络负载越高等待越久，起到自适应流量控制作用
""", difficulty=4),

# ──────────── 交换机工作原理 ────────────
R("doc", "交换机工作原理", "【知识文档】以太网交换机工作原理详解", r"""# 以太网交换机工作原理

## 一、交换机 vs 集线器

| | 集线器（Hub） | 交换机（Switch） |
|-|------------|----------------|
| 工作层 | 物理层（L1） | 数据链路层（L2） |
| 碰撞域 | 所有端口共享 | 每端口独立 |
| 转发方式 | 广播所有端口 | 按 MAC 表转发 |
| 全双工 | 不支持 | 支持 |
| 当前使用 | 已淘汰 | 广泛使用 |

## 二、MAC 地址表（CAM 表）

交换机维护一张 **MAC 地址→端口** 映射表。

**自学习过程：**
```
1. 收到帧时，记录源 MAC + 入端口 -> 写入 MAC 表
2. 查询目的 MAC：
   - 已知：仅从对应端口转发（单播）
   - 未知：向所有端口泛洪（除入端口外）
   - 广播/组播：向所有端口泛洪
3. MAC 表条目老化时间（通常 300s），超时删除
```

## 三、STP（生成树协议）

多个交换机互联时，冗余链路会形成**广播风暴**。
STP（IEEE 802.1D）通过选举根桥、阻塞冗余端口，形成无环树形拓扑：

```
1. 选举根桥（Root Bridge）：最小 Bridge ID（优先级+MAC）
2. 每台非根交换机选择离根桥最近的根端口（Root Port）
3. 每个网段选择指定端口（Designated Port）
4. 其余端口进入阻塞（Blocking）状态
```

RSTP（IEEE 802.1w）：快速收敛版本，毫秒级收敛。

## 四、三层交换机

三层交换机在 ASIC 硬件上实现路由，以线速处理 VLAN 间路由，
性能远超软件路由器，用于企业核心网络。

工作模式：**首包路由，后续硬件转发**（路由缓存）。

## 五、端口安全

- **端口绑定**：限制端口允许的 MAC 地址数量或绑定固定 MAC
- **802.1X**：基于端口的身份认证，连接前需 RADIUS 认证
- **BPDU Guard**：防止接入层端口接收 STP BPDU，防止伪造根桥攻击
""", difficulty=4),

R("exercise", "交换机工作原理", "【练习题】交换机工作原理综合练习", r"""## 知识点：以太网交换机工作原理

---
### 选择题

**Q1. 交换机收到一个目的 MAC 地址未在 MAC 表中的单播帧，交换机的处理方式是？**

A. 丢弃该帧
B. 向所有端口（除入端口）泛洪
C. 向入端口返回一个 ICMP 报文
D. 向根桥请求目的 MAC 对应端口

**答案：B**
解析：未知单播目的的处理和广播一样——泛洪所有端口（除入端口），
等待目标主机回复时学习其端口。

---
**Q2. STP 协议的主要目的是？**

A. 加速 MAC 地址学习
B. 防止二层网络中的广播风暴（消除环路）
C. 实现 VLAN 间路由
D. 提高端口带宽

**答案：B**
解析：STP 通过阻塞冗余端口，将有环的交换网络变为树形拓扑，消除广播风暴。

---
### 简答题

**Q3. 描述交换机的 MAC 地址自学习过程，MAC 表老化有什么作用？**

**参考答案：**
自学习过程：
1. 交换机收到帧，提取**源 MAC 地址**和**入端口号**
2. 将 (源MAC, 入端口) 写入 MAC 地址表，同时记录时间戳
3. 查询**目的 MAC**：
   - 找到 -> 仅从对应端口转发（精准转发）
   - 未找到 -> 向除入端口外所有端口泛洪

老化作用：
- MAC 表容量有限，超时老化（通常 300s）释放空间
- 设备移动（IP/MAC 变化）后，旧条目会自动清除，避免转发错误
- 防止 MAC 地址表满溢（表满时交换机退化为集线器模式）

---
**Q4. 为什么需要 STP？简述根桥选举过程。**

**参考答案：**
需要 STP 的原因：多台交换机互联提供冗余时，物理环路导致广播帧无限循环，
消耗所有带宽——即广播风暴，导致网络瘫痪。

根桥选举：
1. 所有交换机初始都认为自己是根桥，发送 BPDU 报文
2. 比较 Bridge ID（2字节优先级 + 6字节 MAC）
3. **Bridge ID 最小**的交换机成为根桥
4. 优先级相同时，MAC 地址较小者胜出
5. 选出根桥后，其他交换机选择距根桥最近的端口为根端口，其余冗余端口进入阻塞
""", difficulty=4),

]  # END PHASE6



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 主执行块 - 汇总所有阶段并写入数据库
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ALL_RESOURCES = (
    PHASE1
    + PHASE2
    + PHASE3
    + PHASE4
    + PHASE4B
    + PHASE5
    + PHASE6
)


def main() -> None:
    log.info(f"开始写入高质量学习资源，共 {len(ALL_RESOURCES)} 条...")
    ok = 0
    fail = 0
    for i, res in enumerate(ALL_RESOURCES):
        try:
            ResourceRepository.save(res)
            ok += 1
            if (i + 1) % 10 == 0:
                log.info(f"  已写入 {i + 1}/{len(ALL_RESOURCES)} 条...")
        except Exception as exc:
            fail += 1
            log.error(f"  写入失败 [{res.get('title', '?')}]: {exc}")

    log.info(f"完成！成功 {ok} 条，失败 {fail} 条。")
    log.info("知识点覆盖：")
    from collections import Counter
    kp_count = Counter(r["knowledge_point"] for r in ALL_RESOURCES)
    for kp, cnt in sorted(kp_count.items()):
        log.info(f"  {kp}: {cnt} 条资源")


if __name__ == "__main__":
    main()
