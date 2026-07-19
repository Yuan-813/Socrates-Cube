<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'

// ─── Protocol knowledge database ─────────────────────────────────────────────
const PROTO_DB: Record<string, { full: string; rfc: string; layer: string; desc: string; features: string[] }> = {
  'OSPF': { full: 'Open Shortest Path First', rfc: 'RFC 2328', layer: 'L3 网络层', desc: '链路状态路由协议，Dijkstra 最短路径算法，支持 VLSM/CIDR，适用大型企业网络，收敛速度 < 1s。', features: ['LSA 链路状态广播', 'SPF 算法计算最优路径', 'Area 0 骨干区域化设计', '< 1s 快速收敛'] },
  'BGP': { full: 'Border Gateway Protocol', rfc: 'RFC 4271', layer: 'L3-L4', desc: '互联网骨干路由协议，用于自治系统（AS）间路由交换，路径向量算法，建立在 TCP 179 端口之上。', features: ['路径向量防环机制', 'AS-Path 属性传递', 'TCP 179 建立 eBGP 会话', 'iBGP/eBGP 两种模式'] },
  'NAT': { full: 'Network Address Translation', rfc: 'RFC 3022', layer: 'L3-L4', desc: '将内网私有 IP 转换为公网地址，解决 IPv4 地址不足并提供一定安全隔离，分静态/动态/PAT 三种模式。', features: ['静态/动态/PAT 三种模式', 'IP 报头地址改写', '连接追踪表维护', '破坏端到端透明性'] },
  'RIP': { full: 'Routing Information Protocol', rfc: 'RFC 2453', layer: 'L3', desc: '距离向量路由协议，跳数为度量，最大 15 跳，30s 周期广播，简单易配，适用小型网络。', features: ['跳数度量（最大 15）', '30s 周期全表广播', 'Bellman-Ford 算法', '水平分割防环路'] },
  '802.1Q': { full: 'IEEE 802.1Q VLAN', rfc: 'IEEE 802.1Q', layer: 'L2 数据链路层', desc: 'VLAN 帧标记标准，以太网帧中插入 4 字节 Tag，支持最多 4094 个 VLAN，实现广播域隔离。', features: ['4 字节 VLAN Tag 插入', '支持 4094 个 VLAN', 'Trunk 链路多 VLAN 传输', 'Native VLAN 无 Tag 传输'] },
  'STP': { full: 'Spanning Tree Protocol', rfc: 'IEEE 802.1D', layer: 'L2', desc: '通过选举根桥并阻塞冗余端口，防止交换网络中的二层环路，RSTP 版本可 < 1s 快速收敛。', features: ['BPDU 报文选举根桥', '根端口/指定端口/阻塞', '5 种端口状态机', 'RSTP 快速收敛 < 1s'] },
  'LACP': { full: 'Link Aggregation Control Protocol', rfc: 'IEEE 802.3ad', layer: 'L2', desc: '动态协商链路聚合，将多条物理链路捆绑为一条逻辑链路，提升带宽和冗余可靠性。', features: ['最多 8 条链路聚合', 'PDU 动态协商机制', '哈希负载均衡算法', '成员链路故障自动切换'] },
  'CDP': { full: 'Cisco Discovery Protocol', rfc: 'Cisco 私有', layer: 'L2', desc: 'Cisco 专有设备发现协议，自动发现直连 Cisco 设备信息，每 60s 广播，仅支持 Cisco 设备。', features: ['邻居设备自动发现', '传递型号/IP/端口信息', '60s 广播周期', '仅 Cisco 设备间可用'] },
  'HTTP/2': { full: 'HyperText Transfer Protocol v2', rfc: 'RFC 9113', layer: 'L7 应用层', desc: '基于二进制帧分帧，支持多路复用和 HPACK 头部压缩，大幅提升 Web 传输效率。', features: ['二进制帧分帧层', '多路复用（单 TCP 多并发流）', 'HPACK 头部压缩', '服务器主动推送 Push'] },
  'DNS': { full: 'Domain Name System', rfc: 'RFC 1034/1035', layer: 'L7 应用层', desc: '将域名解析为 IP 地址，层级树状结构，UDP/TCP 53 端口，支持递归和迭代两种查询模式。', features: ['A/AAAA/CNAME/MX 记录类型', 'TTL 缓存过期机制', '递归 vs 迭代查询', 'DNSSEC 安全扩展'] },
  'TLS 1.3': { full: 'Transport Layer Security 1.3', rfc: 'RFC 8446', layer: 'L4-L7', desc: 'TLS 1.3 简化握手至 1-RTT，移除不安全密码套件，强制前向保密（PFS），是现代 HTTPS 核心。', features: ['1-RTT 握手（比 TLS 1.2 快 1 轮）', '0-RTT 会话快速恢复', '前向保密 PFS 强制', '废弃 RSA 密钥交换'] },
  'SSH': { full: 'Secure Shell', rfc: 'RFC 4251', layer: 'L7 应用层', desc: '加密远程登录协议，替代明文 Telnet，提供安全命令行管理、端口转发和 SFTP 文件传输。', features: ['非对称密钥认证', '加密终端会话', 'TCP 22 端口转发隧道', 'SFTP 安全文件传输'] },
  'ACL': { full: 'Access Control List', rfc: 'RFC 3198', layer: 'L3-L4', desc: '基于 IP、端口、协议的包过滤规则列表，顺序匹配即停止，是防火墙基础安全机制。', features: ['顺序匹配，命中即停止', '标准 ACL（源 IP）', '扩展 ACL（五元组）', '入/出方向独立配置'] },
  'DPI': { full: 'Deep Packet Inspection', rfc: '厂商私有实现', layer: 'L4-L7', desc: '深度检查数据包应用层内容，识别 7000+ 应用特征，实现精细化流量管理和内容安全防护。', features: ['7000+ 应用特征库识别', '内容过滤与病毒扫描', 'QoS 流量整形控制', '加密流量行为分析'] },
  'IPS': { full: 'Intrusion Prevention System', rfc: 'ISO/IEC 27035', layer: 'L3-L7', desc: '实时检测并主动阻断网络入侵行为，基于 CVE 签名库与行为异常检测双引擎工作。', features: ['CVE 签名库规则匹配', '行为基线异常检测', '实时 Drop/Reset 阻断', '告警日志与威胁溯源'] },
  'IPsec': { full: 'IP Security Protocol Suite', rfc: 'RFC 4301', layer: 'L3 网络层', desc: '为 IP 层提供加密、认证和完整性保护，是站点间 VPN 隧道主流实现方案。', features: ['AH 认证 + ESP 加密载荷', 'IKEv2 自动密钥协商', '隧道模式 vs 传输模式', 'AES-256/SHA-256 强算法'] },
}

// ─── Device data ──────────────────────────────────────────────────────────────
const DEVICES = [
  {
    id: 'router', name: '路由器', fullName: 'EdgeRouter X', modelId: 'ER-X',
    model: 'Cisco ISR 4321', portCount: '5 × GbE', type: '路由器', year: '2022', osi: 'L3',
    status: 'active', icon: '📡', color: 0x7c3aed, hexStr: '#7C3AED', statusColor: '#22c55e',
    temp: 36, cpu: 12, mem: 28,
    protocols: ['OSPF', 'BGP', 'NAT', 'RIP'], rfc: 'RFC 791 / RFC 4271',
    diagnostics: [
      { name: '路由寻址', status: 'ACTIVE', color: '#22c55e', detail: '当前维护 1024 条路由表项，BGP 邻居 2 个，OSPF 邻接关系 4 个，路由收敛正常。' },
      { name: '数据包分发', status: 'ACTIVE', color: '#22c55e', detail: '基于目的 IP 最长前缀匹配，转发速率 148 万包/秒（1Gbps 线速），零丢包。' },
      { name: 'NAT转换', status: 'STANDBY', color: '#f59e0b', detail: 'NAT 转换条目 2847 条，PAT 复用公网 IP：203.0.113.1，NAPT 模式等待激活。' },
      { name: 'BGP协议', status: 'ACTIVE', color: '#22c55e', detail: 'eBGP 会话 2 条（AS 65001↔65002），接收前缀 432 条，通告 89 条，更新正常。' },
    ],
    stats: { routes: 1024, conn: '稳定', proto: 'BGP', throughput: '5.2GB/1.8GB', errRate: '<0.01%' },
    labels: [
      { text: '[BGP 数据包]', x: '14%', y: '28%', delay: '0s' }, { text: '[OSPF Hello]', x: '64%', y: '19%', delay: '0.8s' },
      { text: '[NAT 转换]', x: '10%', y: '64%', delay: '1.5s' }, { text: '[路由更新]', x: '68%', y: '68%', delay: '2.2s' },
      { text: '[路由数据]', x: '38%', y: '83%', delay: '1s' },
    ],
    portDetails: [
      { id: 'wan', name: 'WAN GE0/0/0', status: 'UP', ip: '203.0.113.1/24', speed: '1Gbps', desc: '上行互联网接口，配置 eBGP，连接 ISP' },
      { id: 'lan1', name: 'LAN GE0/0/1', status: 'UP', ip: '192.168.1.1/24', speed: '1Gbps', desc: '内网主干，VLAN Trunk，下联交换机' },
      { id: 'lan2', name: 'LAN GE0/0/2', status: 'UP', ip: '192.168.2.1/24', speed: '1Gbps', desc: '服务器区域接入，配置静态路由' },
      { id: 'lan3', name: 'LAN GE0/0/3', status: 'DOWN', ip: '未配置', speed: '1Gbps', desc: '备用接口，当前未激活' },
      { id: 'mgmt', name: 'Console RS-232', status: 'READY', ip: 'N/A', speed: '9600 baud', desc: '带外管理，串口调试终端' },
    ],
    ports: ['WAN × 1（GE0/0/0）', 'LAN × 4（GE0/0/1–4）', 'Console × 1（RS-232）'],
    structDesc: 'EdgeRouter X 外部采用金属机箱设计，正面板集成 LED 状态指示灯、端口组和控制按键，侧面设有散热通风槽，背面为电源接口与接地孔。整体符合 1U/2U 机架规格标准。',
    knowledge: '路由器工作于 OSI 第三层，基于 IP 路由表进行跨网段转发。支持 OSPF/BGP/RIP 动态路由协议，NAT 将内网私有 IP 映射到公网地址。\n\n• 端口 1-5：千兆以太网口，用于连接内网设备或其他网络设备\n• CONSOLE：控制台端口，用于命令行管理\n• RESET：恢复出厂设置按钮\n\n路由器通过维护路由表决定最优路径，支持静态路由和动态路由协议 OSPF/BGP。',
  },
  {
    id: 'switch', name: '交换机', fullName: 'Catalyst 2960-X', modelId: 'WS-C2960X',
    model: 'Cisco Catalyst 9300', portCount: '24 × GbE', type: '三层交换机', year: '2021', osi: 'L2',
    status: 'active', icon: '🔀', color: 0x0891b2, hexStr: '#0891B2', statusColor: '#22c55e',
    temp: 42, cpu: 8, mem: 35,
    protocols: ['802.1Q', 'STP', 'LACP', 'CDP'], rfc: 'IEEE 802.1Q / 802.3ad',
    diagnostics: [
      { name: 'MAC 学习', status: 'ACTIVE', color: '#22c55e', detail: 'MAC 地址表 8192 条，当前学习 3417 条，老化时间 300s，转发速率 14.8Mpps。' },
      { name: 'VLAN 隔离', status: 'ACTIVE', color: '#22c55e', detail: '配置 VLAN 12 个（ID 10~120），Trunk 端口 4 个，Access 端口 20 个，运行正常。' },
      { name: 'STP 收敛', status: 'ACTIVE', color: '#22c55e', detail: '本机为根桥（优先级 4096），拓扑稳定时间 28s，端口全部处于 Forwarding 状态。' },
      { name: 'LACP 聚合', status: 'STANDBY', color: '#f59e0b', detail: 'Port-Channel 1 配置 2 条成员链路，协商报文正常，等待上联设备启用聚合组。' },
    ],
    stats: { routes: 8192, conn: '正常', proto: '802.1Q', throughput: '9.8GB/3.2GB', errRate: '<0.001%' },
    labels: [
      { text: '[ARP 广播]', x: '12%', y: '24%', delay: '0s' }, { text: '[MAC 学习帧]', x: '60%', y: '17%', delay: '0.6s' },
      { text: '[STP BPDU]', x: '8%', y: '60%', delay: '1.3s' }, { text: '[VLAN Tag]', x: '67%', y: '64%', delay: '2s' },
      { text: '[Trunk 链路]', x: '37%', y: '81%', delay: '1.2s' },
    ],
    portDetails: [
      { id: 'gi01', name: 'GE1/0/1', status: 'UP', ip: 'Access VLAN10', speed: '1Gbps', desc: 'PC 接入端口，VLAN 10（办公区）' },
      { id: 'gi02', name: 'GE1/0/2-4', status: 'UP', ip: 'Access VLAN20', speed: '1Gbps', desc: '服务器 Access 端口，VLAN 20（服务器区）' },
      { id: 'trk1', name: 'GE1/0/24', status: 'UP', ip: 'Trunk All VLANs', speed: '1Gbps', desc: 'Trunk 上联路由器，承载全部 VLAN' },
      { id: 'sfp1', name: 'SFP+ 1/1', status: 'UP', ip: 'Trunk + LACP', speed: '10Gbps', desc: 'LACP 聚合成员，上联核心交换机' },
      { id: 'mgmt', name: 'MGMT 0/0', status: 'READY', ip: '192.168.0.254/24', speed: '100Mbps', desc: '带外管理接口，Telnet/SSH 登录' },
    ],
    ports: ['24 × GE（RJ45 1000BASE-T）', '4 × SFP+（10G）', 'Console × 1', 'Stack × 2（40G）'],
    structDesc: 'Catalyst 2960-X 采用固定端口设计，正面板含 24 个 RJ45 千兆口和 4 个 SFP+ 万兆口，LED 状态灯组指示每个端口状态，风扇模块支持热插拔更换。',
    knowledge: '交换机通过 MAC 地址表实现二层转发，在局域网内高速转发数据帧。\n\n• MAC 学习：自动学习源 MAC 地址并记录端口映射\n• VLAN：逻辑隔离广播域，提升网络安全性\n• STP：防止网络环路，保证链路稳定性\n\n与路由器不同，交换机不修改 IP 地址，仅操作 MAC 地址实现帧级高速转发。',
  },
  {
    id: 'server', name: '服务器', fullName: 'PowerEdge R740', modelId: 'R740',
    model: 'Dell PowerEdge R740', portCount: '4 × 10GbE', type: '机架式服务器', year: '2021', osi: 'L4-L7',
    status: 'active', icon: '🖥️', color: 0x7c3aed, hexStr: '#7C3AED', statusColor: '#22c55e',
    temp: 58, cpu: 45, mem: 62,
    protocols: ['HTTP/2', 'DNS', 'TLS 1.3', 'SSH'], rfc: 'RFC 9110 / RFC 8446',
    diagnostics: [
      { name: 'HTTP 监听', status: 'ACTIVE', color: '#22c55e', detail: 'Nginx 监听 80/443 端口，并发连接 1284，QPS 约 3200，P99 响应延迟 12ms。' },
      { name: 'TLS 握手', status: 'ACTIVE', color: '#22c55e', detail: 'TLS 1.3 握手成功率 99.97%，证书有效期 180d，ECDHE 密钥交换，AES-256-GCM。' },
      { name: 'DNS 解析', status: 'ACTIVE', color: '#22c55e', detail: '本地 DNS 缓存命中率 78%，上游 114.114.114.114，解析平均延迟 4ms。' },
      { name: '进程调度', status: 'HIGH LOAD', color: '#f59e0b', detail: 'CPU 45%，内存 62%，IO Wait 8%，建议扩容或优化数据库查询减少阻塞。' },
    ],
    stats: { routes: 256, conn: '高负载', proto: 'HTTP/2', throughput: '12GB/8.5GB', errRate: '0.05%' },
    labels: [
      { text: '[HTTP/2 请求]', x: '11%', y: '25%', delay: '0s' }, { text: '[TLS 握手]', x: '60%', y: '18%', delay: '0.6s' },
      { text: '[DNS 查询]', x: '9%', y: '60%', delay: '1.4s' }, { text: '[TCP 流控]', x: '64%', y: '65%', delay: '2.1s' },
      { text: '[HTTP 响应]', x: '38%', y: '83%', delay: '0.9s' },
    ],
    portDetails: [
      { id: 'nic0', name: 'NIC em1（10GbE）', status: 'UP', ip: '10.0.1.10/24', speed: '10Gbps', desc: '主业务网卡，承载 HTTP/HTTPS 流量' },
      { id: 'nic1', name: 'NIC em2（10GbE）', status: 'UP', ip: '10.0.2.10/24', speed: '10Gbps', desc: '副业务网卡，主备绑定（Bond0）' },
      { id: 'nic2', name: 'NIC em3（10GbE）', status: 'UP', ip: '10.0.3.10/24', speed: '10Gbps', desc: '存储网络专用网卡，iSCSI 流量' },
      { id: 'ipmi', name: 'iDRAC（IPMI）', status: 'READY', ip: '192.168.0.10/24', speed: '1Gbps', desc: '带外管理，硬件级远程电源/KVM 控制' },
      { id: 'usb', name: 'USB 3.0 × 4', status: 'READY', ip: 'N/A', speed: '5Gbps', desc: '外设接口，系统安装/配置数据导入' },
    ],
    ports: ['NIC × 4（10GbE SFP+）', 'iDRAC × 1（带外管理）', 'USB 3.0 × 4', 'VGA × 1'],
    structDesc: 'PowerEdge R740 为 2U 机架式服务器，前面板含 8 个热插拔 3.5" 硬盘仓、电源按钮和 LCD 诊断面板，后面板为双电源模块和 PCIe 扩展槽，支持双路 CPU。',
    knowledge: '服务器提供计算、存储和网络服务，是数据中心核心设备。HTTP/2 实现多路复用，TLS 1.3 提供加密传输。\n\n• HTTP/HTTPS：Web 服务，端口 80/443\n• DNS：域名解析，端口 53\n• SSH：安全远程管理，端口 22\n\n高可用服务器通过负载均衡和冗余配置保证服务的持续可用性，MTTR < 15 分钟。',
  },
  {
    id: 'firewall', name: '防火墙', fullName: 'Cisco ASA 5506-X', modelId: 'ASA5506',
    model: 'Cisco ASA 5506-X', portCount: '8 × GbE', type: 'NGFW 下一代防火墙', year: '2023', osi: 'L3-L7',
    status: 'warning', icon: '🛡️', color: 0xef4444, hexStr: '#EF4444', statusColor: '#f59e0b',
    temp: 48, cpu: 67, mem: 55,
    protocols: ['ACL', 'DPI', 'IPS', 'IPsec'], rfc: 'RFC 3511 / RFC 4301',
    diagnostics: [
      { name: 'ACL 过滤', status: 'ACTIVE', color: '#22c55e', detail: '已配置 ACL 规则 256 条，今日命中 18432 次，拦截可疑流量 342 条，最后更新 2h 前。' },
      { name: 'DPI 检测', status: 'ACTIVE', color: '#22c55e', detail: 'DPI 识别 7000+ 应用特征，当前检测到 P2P 流量 3.2%，已触发限速策略。' },
      { name: 'IPS 告警', status: 'ALERT', color: '#ef4444', detail: '⚠ 检测到 CVE-2024-1234 漏洞利用尝试 × 12 次，来源 IP：198.51.100.x，已拦截。' },
      { name: 'VPN 隧道', status: 'STANDBY', color: '#f59e0b', detail: 'IPsec VPN 预配置 3 条隧道（总部/分支/DR），IKEv2 密钥有效，等待远端拨入。' },
    ],
    stats: { routes: 512, conn: '告警', proto: 'IPsec', throughput: '2.1GB/0.8GB', errRate: '0.32%' },
    labels: [
      { text: '[ACL 过滤]', x: '11%', y: '27%', delay: '0s' }, { text: '[DPI 检测]', x: '62%', y: '19%', delay: '0.7s' },
      { text: '[IPS 拦截]', x: '8%', y: '62%', delay: '1.6s' }, { text: '[策略匹配]', x: '67%', y: '67%', delay: '2.1s' },
      { text: '[VPN 隧道]', x: '38%', y: '83%', delay: '1.1s' },
    ],
    portDetails: [
      { id: 'out', name: 'Outside GE1', status: 'UP', ip: '203.0.113.254/24', speed: '1Gbps', desc: 'WAN 上行接口，连接互联网，高安全等级区' },
      { id: 'in1', name: 'Inside GE2', status: 'UP', ip: '192.168.1.254/24', speed: '1Gbps', desc: '内网主区域，连接核心交换机' },
      { id: 'in2', name: 'Inside GE3', status: 'UP', ip: '192.168.2.254/24', speed: '1Gbps', desc: '内网次区域，服务器段' },
      { id: 'dmz', name: 'DMZ GE4', status: 'UP', ip: '172.16.1.254/24', speed: '1Gbps', desc: 'DMZ 隔离区，放置对外公开服务器' },
      { id: 'ha', name: 'HA GE8', status: 'READY', ip: 'HA Heartbeat', speed: '1Gbps', desc: '高可用心跳接口，连接 HA 对端' },
    ],
    ports: ['Outside × 1（WAN GE）', 'Inside × 4（LAN GE）', 'DMZ × 1', 'HA 心跳口 × 1'],
    structDesc: 'ASA 5506-X 为紧凑型桌面/1U 机箱，前面板含 8 个 RJ45 GE 口和安全区域指示灯，红/橙/绿分别对应 Outside/DMZ/Inside 区域，内置 SSD 存储安全策略数据库。',
    knowledge: '下一代防火墙综合多种安全技术，保护内网免受外部攻击。ACL 基于 IP/端口控制访问，DPI 识别应用层流量。\n\n• Outside：连接互联网（WAN）\n• Inside：连接内部网络（LAN）\n• DMZ：隔离区，放置公开服务\n\n现代 NGFW 可识别用户身份和应用类型，而非仅依赖端口号进行过滤决策。',
  },
]

// ─── Reactive state ───────────────────────────────────────────────────────────
const canvasRef = ref<HTMLCanvasElement | null>(null)
const selectedId = ref('router')
const isLoading = ref(true)
const mode = ref<'realtime' | 'explode'>('realtime')
const flowEnabled = ref(true)
const structTab = ref('exterior')
const structTabs = [
  { id: 'exterior', name: '外部结构' }, { id: 'ports', name: '端口面板' },
  { id: 'internal', name: '内部结构' }, { id: 'board', name: '主板布局' }, { id: 'power', name: '电源模块' },
]

// Interaction state
const expandedDiag = ref<string | null>(null)
const showPortPopup = ref(false)
const portPopupPos = ref({ x: 0, y: 0 })
const portPopupData = ref<{ name: string; ip: string; status: string; speed: string; desc: string } | null>(null)
const showProtoPanel = ref(false)
const selectedProtoKey = ref('')
const selectedProto = computed(() => selectedProtoKey.value ? PROTO_DB[selectedProtoKey.value] : null)

const currentDevice = computed(() => DEVICES.find(d => d.id === selectedId.value) ?? DEVICES[0])

// ─── Three.js runtime ─────────────────────────────────────────────────────────
const ctx: any = { renderer: null, scene: null, camera: null, modelGroup: null, animId: null, THREE: null, pts: null, pGeo: null, pMat: null, pData: null, pl1: null, pl2: null, explodeOffsets: [] }
let isDragging = false, prevMouse = { x: 0, y: 0 }
let rotX = 0.15, rotY = 0, zoomDist = 5.5

function buildHoloModel(THREE: any, id: string) {
  const g = new THREE.Group()
  const dev = DEVICES.find(d => d.id === id)!
  const wireColor = dev.color
  const solidColor = id === 'firewall' ? 0x1a0514 : id === 'switch' ? 0x021a22 : 0x0a0f2a
  if (id === 'router' || id === 'firewall') {
    const body = new THREE.Mesh(new THREE.BoxGeometry(3, 0.5, 1.6), new THREE.MeshPhongMaterial({ color: solidColor, transparent: true, opacity: 0.92, specular: 0x4444aa, shininess: 200 }))
    body.userData = { type: 'body', deviceId: id }; g.add(body)
    g.add(new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(3, 0.5, 1.6)), new THREE.LineBasicMaterial({ color: wireColor })))
    for (let i = 0; i < 8; i++) {
      const ph = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.16, 0.04), new THREE.MeshBasicMaterial({ color: wireColor, transparent: true, opacity: 0.6 }))
      ph.position.set(-1.2 + i * 0.35, 0, 0.82); ph.userData = { type: 'port', portIndex: i < 5 ? i : -1 }; g.add(ph)
      const pl = new THREE.Mesh(new THREE.SphereGeometry(0.025, 8, 8), new THREE.MeshBasicMaterial({ color: i < 6 ? 0x22c55e : (id === 'firewall' ? 0xef4444 : 0xf59e0b) }))
      pl.position.set(-1.2 + i * 0.35, 0.28, 0.82); g.add(pl)
    }
  } else if (id === 'switch') {
    const body = new THREE.Mesh(new THREE.BoxGeometry(4, 0.28, 1.5), new THREE.MeshPhongMaterial({ color: solidColor, transparent: true, opacity: 0.92, specular: 0x0088cc, shininess: 220 }))
    body.userData = { type: 'body', deviceId: id }; g.add(body)
    g.add(new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(4, 0.28, 1.5)), new THREE.LineBasicMaterial({ color: wireColor })))
    for (let row = 0; row < 2; row++) for (let col = 0; col < 12; col++) {
      const ph = new THREE.Mesh(new THREE.SphereGeometry(0.022, 6, 6), new THREE.MeshBasicMaterial({ color: (col + row) % 4 === 0 ? 0xf59e0b : 0x22c55e }))
      ph.position.set(-1.7 + col * 0.31, 0.15 - row * 0.18, 0.76); ph.userData = { type: 'port', portIndex: row * 12 + col }; g.add(ph)
    }
  } else {
    const body = new THREE.Mesh(new THREE.BoxGeometry(3, 1.4, 1.8), new THREE.MeshPhongMaterial({ color: solidColor, transparent: true, opacity: 0.92, specular: 0x6644aa, shininess: 180 }))
    body.userData = { type: 'body', deviceId: id }; g.add(body)
    g.add(new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(3, 1.4, 1.8)), new THREE.LineBasicMaterial({ color: wireColor })))
    for (let row = 0; row < 2; row++) for (let col = 0; col < 4; col++) {
      const bay = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.22, 0.04), new THREE.MeshBasicMaterial({ color: wireColor, transparent: true, opacity: 0.4 }))
      bay.position.set(-0.9 + col * 0.62, 0.3 - row * 0.3, 0.93); bay.userData = { type: 'port', portIndex: row * 4 + col }; g.add(bay)
    }
  }
  for (let i = 0; i < 3; i++) {
    const ring = new THREE.Mesh(new THREE.RingGeometry(1.8 + i * 0.4, 1.82 + i * 0.4, 64), new THREE.MeshBasicMaterial({ color: wireColor, transparent: true, opacity: 0.15 - i * 0.04, side: THREE.DoubleSide }))
    ring.rotation.x = Math.PI / 2; ring.position.y = -0.1 - i * 0.12; g.add(ring)
  }
  // Store original positions for explode
  ctx.explodeOffsets = g.children.map((c: any) => ({ orig: c.position.clone(), dir: c.position.clone().normalize() }))
  return g
}

async function initThree() {
  if (!canvasRef.value) return
  await nextTick()
  try {
    const THREE = await import('three')
    ctx.THREE = THREE
    const canvas = canvasRef.value
    const rect = canvas.getBoundingClientRect()
    const w = rect.width || canvas.clientWidth || 800, h = rect.height || canvas.clientHeight || 520
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true })
    renderer.setSize(w, h); renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); renderer.setClearColor(0x040d1a, 1)
    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 100)
    camera.position.set(0, 1.5, zoomDist); camera.lookAt(0, 0, 0)
    scene.add(new THREE.AmbientLight(0x0a0a2e, 2))
    const dir = new THREE.DirectionalLight(0x4444ff, 1); dir.position.set(3, 5, 3); scene.add(dir)
    const pl1 = new THREE.PointLight(0x7c3aed, 4, 20); pl1.position.set(-3, 2, 3); scene.add(pl1); ctx.pl1 = pl1
    const pl2 = new THREE.PointLight(0x0ea5e9, 3, 15); pl2.position.set(3, -1, -2); scene.add(pl2); ctx.pl2 = pl2
    const grid = new THREE.GridHelper(16, 32, 0x1a1a4a, 0x0a0a2a); grid.position.y = -1.2; scene.add(grid)
    ctx.modelGroup = buildHoloModel(THREE, selectedId.value); scene.add(ctx.modelGroup)
    const pCount = 150, pGeo = new THREE.BufferGeometry(), pPos = new Float32Array(pCount * 3)
    const pData: any[] = []
    for (let i = 0; i < pCount; i++) {
      const a = Math.random() * Math.PI * 2, r = 2.5 + Math.random() * 2
      pData.push({ a, r, speed: 0.012 + Math.random() * 0.008, y: (Math.random() - 0.5) * 2.5, vy: (Math.random() - 0.5) * 0.004 })
      pPos[i * 3] = Math.cos(a) * r; pPos[i * 3 + 1] = pData[i].y; pPos[i * 3 + 2] = Math.sin(a) * r
    }
    pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3))
    const pMat = new THREE.PointsMaterial({ color: 0x7c3aed, size: 0.07, transparent: true, opacity: 0.9 })
    const pts = new THREE.Points(pGeo, pMat); scene.add(pts)
    ctx.pts = pts; ctx.pGeo = pGeo; ctx.pMat = pMat; ctx.pData = pData
    ctx.renderer = renderer; ctx.scene = scene; ctx.camera = camera
    let t = 0, explodeT = 0
    const animate = () => {
      ctx.animId = requestAnimationFrame(animate); t += 0.01
      // explode animation
      const targetET = mode.value === 'explode' ? 1 : 0
      explodeT += (targetET - explodeT) * 0.04
      if (ctx.modelGroup && ctx.explodeOffsets?.length) {
        ctx.modelGroup.children.forEach((c: any, i: number) => {
          const eo = ctx.explodeOffsets[i]
          if (eo) { c.position.x = eo.orig.x + eo.dir.x * explodeT * 0.8; c.position.y = eo.orig.y + eo.dir.y * explodeT * 0.6; c.position.z = eo.orig.z + eo.dir.z * explodeT * 0.6 }
        })
      }
      if (!isDragging) rotY += 0.004
      const r = zoomDist
      camera.position.x = r * Math.sin(rotY) * Math.cos(rotX)
      camera.position.y = r * Math.sin(rotX) + 1
      camera.position.z = r * Math.cos(rotY) * Math.cos(rotX)
      camera.lookAt(0, 0, 0)
      if (ctx.modelGroup) ctx.modelGroup.position.y = Math.sin(t * 0.5) * 0.08
      if (flowEnabled.value && ctx.pGeo && ctx.pData) {
        const pa = ctx.pGeo.attributes.position.array as Float32Array
        ctx.pData.forEach((p: any, i: number) => {
          p.a += p.speed; p.y += p.vy; if (Math.abs(p.y) > 1.5) p.vy *= -1
          pa[i * 3] = Math.cos(p.a) * p.r; pa[i * 3 + 1] = p.y; pa[i * 3 + 2] = Math.sin(p.a) * p.r
        })
        ctx.pGeo.attributes.position.needsUpdate = true; pts.visible = true
      } else { pts.visible = false }
      if (ctx.pl1) ctx.pl1.intensity = 3 + Math.sin(t * 1.5) * 1.5
      if (ctx.pl2) ctx.pl2.intensity = 2.5 + Math.cos(t * 1.2) * 1
      renderer.render(scene, camera)
    }
    animate(); isLoading.value = false
  } catch (e) { console.error(e); isLoading.value = false }
}

function switchDevice(id: string) {
  selectedId.value = id; structTab.value = 'exterior'; showPortPopup.value = false
  if (!ctx.scene || !ctx.THREE) return
  if (ctx.modelGroup) {
    ctx.scene.remove(ctx.modelGroup)
    ctx.modelGroup.traverse((c: any) => { c.geometry?.dispose(); c.material && (Array.isArray(c.material) ? c.material.forEach((m: any) => m.dispose()) : c.material.dispose()) })
  }
  ctx.modelGroup = buildHoloModel(ctx.THREE, id); ctx.scene.add(ctx.modelGroup)
  const dev = DEVICES.find(d => d.id === id)!
  if (ctx.pMat) ctx.pMat.color.setHex(dev.color)
  if (ctx.pl1) ctx.pl1.color.setHex(dev.color)
}

// ─── Interaction handlers ─────────────────────────────────────────────────────
function onMouseDown(e: MouseEvent) { isDragging = true; prevMouse = { x: e.clientX, y: e.clientY } }
function onMouseMove(e: MouseEvent) {
  if (!isDragging) return
  rotY += (e.clientX - prevMouse.x) * 0.008
  rotX = Math.max(-0.4, Math.min(0.5, rotX + (e.clientY - prevMouse.y) * 0.008))
  prevMouse = { x: e.clientX, y: e.clientY }
}
function onMouseUp() { isDragging = false }

function onWheel(e: WheelEvent) {
  e.preventDefault()
  zoomDist = Math.max(3, Math.min(12, zoomDist + e.deltaY * 0.008))
}

function onCanvasClick(e: MouseEvent) {
  if (!ctx.renderer || !ctx.camera || !ctx.modelGroup || !ctx.THREE || !canvasRef.value) return
  const rect = canvasRef.value.getBoundingClientRect()
  const mouse = new ctx.THREE.Vector2(
    ((e.clientX - rect.left) / rect.width) * 2 - 1,
    -((e.clientY - rect.top) / rect.height) * 2 + 1,
  )
  const raycaster = new ctx.THREE.Raycaster()
  raycaster.setFromCamera(mouse, ctx.camera)
  const hits = raycaster.intersectObjects(ctx.modelGroup.children, true)
  if (hits.length === 0) { showPortPopup.value = false; return }
  const ud = hits[0].object.userData
  const dev = currentDevice.value
  if (ud.type === 'port' && ud.portIndex >= 0 && dev.portDetails[ud.portIndex]) {
    portPopupData.value = dev.portDetails[ud.portIndex]
  } else {
    portPopupData.value = { name: dev.fullName, ip: dev.modelId, status: dev.status === 'active' ? 'ACTIVE' : 'WARNING', speed: dev.portCount, desc: dev.type + ' · 点击端口查看详细信息' }
  }
  const cx = Math.min(e.clientX - rect.left + 12, rect.width - 220)
  const cy = Math.min(e.clientY - rect.top + 12, rect.height - 140)
  portPopupPos.value = { x: cx, y: cy }
  showPortPopup.value = true
}

function onCanvasDblClick() { resetView() }

function onKeyDown(e: KeyboardEvent) {
  const step = 0.06
  if (e.key === 'ArrowLeft') rotY -= step
  else if (e.key === 'ArrowRight') rotY += step
  else if (e.key === 'ArrowUp') rotX = Math.max(-0.4, rotX - step)
  else if (e.key === 'ArrowDown') rotX = Math.min(0.5, rotX + step)
  else if (e.key === 'Escape') { showPortPopup.value = false; showProtoPanel.value = false }
  else return
  e.preventDefault()
}

function resetView() { rotX = 0.15; rotY = 0; zoomDist = 5.5 }
function zoomIn() { zoomDist = Math.max(3, zoomDist - 0.6) }
function zoomOut() { zoomDist = Math.min(12, zoomDist + 0.6) }

function openProto(key: string) { selectedProtoKey.value = key; showProtoPanel.value = true }
function toggleDiag(name: string) { expandedDiag.value = expandedDiag.value === name ? null : name }

function resizeCanvas() {
  if (!ctx.renderer || !ctx.camera || !canvasRef.value) return
  const rect = canvasRef.value.getBoundingClientRect()
  const w = Math.max(1, rect.width || 800), h = Math.max(1, rect.height || 480)
  ctx.renderer.setSize(w, h); ctx.camera.aspect = w / h; ctx.camera.updateProjectionMatrix()
}
let resizeObs: ResizeObserver | null = null
onMounted(() => {
  initThree().then(() => {
    if (canvasRef.value && 'ResizeObserver' in window) {
      resizeObs = new ResizeObserver(() => resizeCanvas()); resizeObs.observe(canvasRef.value)
    }
  })
  window.addEventListener('resize', resizeCanvas)
  window.addEventListener('keydown', onKeyDown)
})
onUnmounted(() => {
  if (resizeObs && canvasRef.value) resizeObs.unobserve(canvasRef.value)
  window.removeEventListener('resize', resizeCanvas)
  window.removeEventListener('keydown', onKeyDown)
  if (ctx.animId) cancelAnimationFrame(ctx.animId); ctx.renderer?.dispose?.()
})
</script>

<template>
  <div class="s2-page">

    <!-- ── BANNER ───────────────────────────────────────────────────────── -->
    <div class="s2-banner">
      <div class="scan-line"></div>
      <div class="banner-inner">
        <div class="banner-logo" :style="`box-shadow:0 0 18px ${currentDevice.hexStr}55`">🖥️</div>
        <div class="banner-text">
          <h1 class="s2-banner-title">3D 硬件与数据流全息可视化实验室</h1>
          <p class="s2-banner-sub">交互式探索网络设备结构，理解硬件功能与协议数据流过程 · 拖拽旋转 / 滚轮缩放 / 双击复位</p>
          <div class="banner-tags">
            <span class="btag" @click="mode='realtime'"><span class="btag-icon">🔄</span>360° 旋转<br><small>拖拽旋转视角</small></span>
            <span class="btag" @click="mode='explode'"><span class="btag-icon">🔧</span>模块拆解<br><small>查看内部结构</small></span>
            <span class="btag" @click="flowEnabled=!flowEnabled"><span class="btag-icon">✦</span>实时数据流<br><small>点击开关切换</small></span>
            <span class="btag" @click="showProtoPanel=!showProtoPanel"><span class="btag-icon">🤖</span>知识引导<br><small>AI 智能讲解</small></span>
          </div>
        </div>
      </div>
      <div class="holo-cube-wrap">
        <div v-for="i in 4" :key="i" class="cube-layer"
          :style="`width:${30+i*10}px;height:${30+i*10}px;animation-delay:${(i-1)*0.35}s;border-color:${currentDevice.hexStr}${['77','55','33','22'][i-1]}`"></div>
      </div>
    </div>

    <!-- ── TOOLBAR ──────────────────────────────────────────────────────── -->
    <div class="s2-toolbar">
      <div class="mode-btns">
        <button :class="['mBtn', {active: mode==='realtime'}]" @click="mode='realtime'">实时模式</button>
        <button :class="['mBtn', {active: mode==='explode'}]" @click="mode='explode'">拆解模式</button>
      </div>
      <div class="tb-sep"></div>
      <div class="tb-ctrl">
        <span class="tb-label">视角控制</span>
        <button class="tb-btn" @click="resetView" title="复位视角（双击画布也可）">↺</button>
        <button class="tb-btn" @click="zoomIn" title="放大">+</button>
        <button class="tb-btn" @click="zoomOut" title="缩小">−</button>
      </div>
      <div class="tb-sep"></div>
      <div class="tb-ctrl">
        <span class="tb-label">数据流</span>
        <div :class="['flow-tog', {on: flowEnabled}]" @click="flowEnabled=!flowEnabled">
          <div class="tog-knob"></div>
        </div>
      </div>
      <div class="tb-sep"></div>
      <span class="tb-hint">← → ↑ ↓ 键盘旋转 · 滚轮缩放 · 点击模型查看端口</span>
      <div class="tb-right">
        <span class="curr-label" :style="`color:${currentDevice.hexStr}`">{{ currentDevice.name }}</span>
        <span class="curr-dot" :style="`background:${currentDevice.statusColor};box-shadow:0 0 5px ${currentDevice.statusColor}`"></span>
      </div>
    </div>

    <!-- ── MAIN AREA ────────────────────────────────────────────────────── -->
    <div class="s2-main">
      <!-- 3D Canvas -->
      <div class="s2-canvas-wrap">
        <div v-if="isLoading" class="loading-holo"><div class="holo-spin"></div><p>初始化全息渲染引擎...</p></div>
        <div class="matrix-bg"></div>
        <canvas ref="canvasRef" class="s2-canvas"
          @mousedown="onMouseDown" @mousemove="onMouseMove"
          @mouseup="onMouseUp" @mouseleave="onMouseUp"
          @click="onCanvasClick" @dblclick="onCanvasDblClick"
          @wheel.prevent="onWheel"/>
        <!-- Node overlay -->
        <div class="node-overlay">
          <div class="node-title">{{ currentDevice.name }}（{{ currentDevice.model }}）· 数据包路由路径诊断中</div>
          <div class="node-stats">
            <span>*表项：{{ currentDevice.stats.routes }}</span>
            <span>*协议：{{ currentDevice.stats.proto }}</span>
            <span>*误码率：{{ currentDevice.stats.errRate }}</span>
            <span v-if="mode==='explode'" class="node-explode-badge">⚡ 拆解中</span>
          </div>
        </div>
        <!-- Floating protocol labels (clickable) -->
        <template v-for="(lb, i) in currentDevice.labels" :key="i">
          <div class="proto-label clickable" :style="`left:${lb.x};top:${lb.y};animation-delay:${lb.delay};border-color:${currentDevice.hexStr}66`"
            @click.stop="openProto(currentDevice.protocols[i % currentDevice.protocols.length])">
            {{ lb.text }}<span class="label-hint">点击</span>
          </div>
        </template>
        <!-- Port click popup -->
        <div v-if="showPortPopup && portPopupData" class="port-popup"
          :style="`left:${portPopupPos.x}px;top:${portPopupPos.y}px`"
          @click.stop>
          <div class="pp-close" @click="showPortPopup=false">✕</div>
          <div class="pp-title">{{ portPopupData.name }}</div>
          <div class="pp-row"><span>状态</span><span :style="`color:${portPopupData.status==='UP'||portPopupData.status==='ACTIVE'?'#22c55e':portPopupData.status==='DOWN'?'#ef4444':'#f59e0b'}`">● {{ portPopupData.status }}</span></div>
          <div class="pp-row"><span>IP/配置</span><span>{{ portPopupData.ip }}</span></div>
          <div class="pp-row"><span>速率</span><span>{{ portPopupData.speed }}</span></div>
          <div class="pp-desc">{{ portPopupData.desc }}</div>
        </div>
        <div class="canvas-statusbar">
          <span class="sb-dot"></span>
          * 实时{{ currentDevice.stats.proto }}数据 · 吞吐量: {{ currentDevice.stats.throughput }} · {{ currentDevice.stats.conn }} · 误码率: {{ currentDevice.stats.errRate }}
        </div>
      </div>

      <!-- Right Panel -->
      <div class="s2-right">
        <!-- Device Selection -->
        <div class="s2-sect">
          <div class="s2-sect-title">设备选择</div>
          <div class="s2-dev-list">
            <div v-for="dev in DEVICES" :key="dev.id"
              :class="['s2-dev-card', {active: selectedId===dev.id}]"
              :style="selectedId===dev.id ? `border-color:${dev.hexStr};box-shadow:0 0 10px ${dev.hexStr}44;background:${dev.hexStr}18` : ''"
              @click="switchDevice(dev.id)">
              <span class="s2-dev-icon">{{ dev.icon }}</span>
              <div class="s2-dev-info">
                <div class="s2-dev-name" :style="selectedId===dev.id ? `color:${dev.hexStr}` : ''">{{ dev.name }}</div>
                <div class="s2-dev-sub">{{ dev.osi }} · {{ dev.modelId }}</div>
              </div>
              <div class="s2-dev-dot" :style="`background:${dev.statusColor};box-shadow:0 0 5px ${dev.statusColor}`"></div>
            </div>
          </div>
        </div>

        <!-- Device Info -->
        <div class="s2-sect">
          <div class="s2-sect-title">设备规格</div>
          <div class="s2-specs-grid">
            <div class="s2-spec"><div class="sg-l">型号</div><div class="sg-v">{{ currentDevice.modelId }}</div></div>
            <div class="s2-spec"><div class="sg-l">端口</div><div class="sg-v">{{ currentDevice.portCount }}</div></div>
            <div class="s2-spec"><div class="sg-l">类型</div><div class="sg-v">{{ currentDevice.type.split(' ')[0] }}</div></div>
            <div class="s2-spec"><div class="sg-l">年份</div><div class="sg-v">{{ currentDevice.year }}</div></div>
          </div>
          <table class="s2-info-table">
            <tr><td>设备名称</td><td>{{ currentDevice.fullName }}</td></tr>
            <tr><td>产品型号</td><td>{{ currentDevice.modelId }}</td></tr>
            <tr><td>端口配置</td><td>{{ currentDevice.portCount }}</td></tr>
            <tr><td>设备类型</td><td>{{ currentDevice.type }}</td></tr>
            <tr><td>发布年份</td><td>{{ currentDevice.year }}</td></tr>
          </table>
          <div class="s2-spec-link" :style="`color:${currentDevice.hexStr}`"
            @click="structTab='ports'">
            查看端口详情 ›
          </div>
        </div>

        <!-- Protocol Diagnostics (clickable rows) -->
        <div class="s2-sect s2-diag-sect">
          <div class="s2-sect-title" :style="`color:${currentDevice.hexStr}`">协议诊断分析 <span class="click-hint">点击展开</span></div>
          <div v-for="d in currentDevice.diagnostics" :key="d.name" class="s2-diag-wrap">
            <div class="s2-diag-row" :class="{expanded: expandedDiag===d.name}" @click="toggleDiag(d.name)">
              <span class="s2-diag-dot" :style="`background:${d.color};box-shadow:0 0 5px ${d.color}`"></span>
              <span class="s2-diag-name">{{ d.name }}</span>
              <span class="s2-diag-stat" :style="`color:${d.color}`">{{ d.status }}</span>
              <span class="s2-diag-chevron" :class="{open: expandedDiag===d.name}">›</span>
            </div>
            <div v-if="expandedDiag===d.name" class="s2-diag-detail">{{ d.detail }}</div>
          </div>
          <div class="diag-metrics">
            <div class="dm-row"><span>吞吐量</span><span class="dm-val">{{ currentDevice.stats.throughput }}</span></div>
            <div class="dm-row"><span>误码率</span><span class="dm-val">{{ currentDevice.stats.errRate }}</span></div>
          </div>
        </div>

        <!-- Inset Topology Map -->
        <div class="s2-sect s2-map-sect">
          <div class="s2-sect-title">⊞ 网络拓扑预览</div>
          <svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">
            <defs><marker id="arr5" markerWidth="5" markerHeight="5" refX="2.5" refY="2.5" orient="auto"><path d="M0,0 L5,2.5 L0,5 Z" fill="#4f6a9e"/></marker></defs>
            <rect width="200" height="120" fill="#040d1a"/>
            <circle cx="100" cy="14" r="10" fill="#0a1628" :stroke="currentDevice.hexStr" stroke-width="1.5"/>
            <text x="100" y="18" text-anchor="middle" fill="#94a3b8" font-size="5.5">Internet</text>
            <line x1="100" y1="24" x2="100" y2="42" stroke="#4f6a9e" stroke-width="1" stroke-dasharray="3,2" marker-end="url(#arr5)"/>
            <rect x="80" y="43" width="40" height="18" rx="3" :fill="`${currentDevice.hexStr}22`" :stroke="currentDevice.hexStr" stroke-width="1"/>
            <text x="100" y="55" text-anchor="middle" :fill="currentDevice.hexStr" font-size="6.5">{{ currentDevice.name }}</text>
            <line x1="80" y1="61" x2="45" y2="82" stroke="#4f6a9e" stroke-width="1" stroke-dasharray="3,2" marker-end="url(#arr5)"/>
            <line x1="100" y1="61" x2="100" y2="82" stroke="#4f6a9e" stroke-width="1" stroke-dasharray="3,2" marker-end="url(#arr5)"/>
            <line x1="120" y1="61" x2="155" y2="82" stroke="#4f6a9e" stroke-width="1" stroke-dasharray="3,2" marker-end="url(#arr5)"/>
            <circle cx="35" cy="92" r="9" fill="#0a1628" stroke="#4f6a9e" stroke-width="1"/><text x="35" y="96" text-anchor="middle" fill="#6b7fa3" font-size="5.5">PC × 4</text>
            <circle cx="100" cy="92" r="9" fill="#0a1628" stroke="#0891b2" stroke-width="1"/><text x="100" y="96" text-anchor="middle" fill="#6b7fa3" font-size="5.5">Switch</text>
            <circle cx="165" cy="92" r="9" fill="#0a1628" stroke="#7c3aed" stroke-width="1"/><text x="165" y="96" text-anchor="middle" fill="#6b7fa3" font-size="5.5">Server</text>
          </svg>
        </div>
      </div>
    </div>

    <!-- ── STATUS BAR ────────────────────────────────────────────────────── -->
    <div class="s2-status">
      <div class="ss-item">
        <div class="ss-label">运行状态</div>
        <div class="ss-val" :style="`color:${currentDevice.statusColor}`">
          <span class="ss-dot" :style="`background:${currentDevice.statusColor};box-shadow:0 0 6px ${currentDevice.statusColor}`"></span>
          {{ currentDevice.status === 'active' ? '正常运行' : '告警中' }}
        </div>
      </div>
      <div class="ss-item">
        <div class="ss-label">CPU使用率</div>
        <div class="ss-val">{{ currentDevice.cpu }}%
          <div class="ss-bar"><div class="ss-fill" :style="`width:${currentDevice.cpu}%;background:${currentDevice.hexStr};box-shadow:0 0 4px ${currentDevice.hexStr}`"></div></div>
        </div>
      </div>
      <div class="ss-item">
        <div class="ss-label">内存使用率</div>
        <div class="ss-val">{{ currentDevice.mem }}%
          <div class="ss-bar"><div class="ss-fill" :style="`width:${currentDevice.mem}%;background:#f59e0b;box-shadow:0 0 4px #f59e0b`"></div></div>
        </div>
      </div>
      <div class="ss-item">
        <div class="ss-label">温度</div>
        <div class="ss-val" :style="`color:${currentDevice.temp>50?'#ef4444':'#94a3b8'};${currentDevice.temp>50?'text-shadow:0 0 6px #ef444488':''}`">
          🌡 {{ currentDevice.temp }}℃
        </div>
      </div>
      <div class="ss-item">
        <div class="ss-label">电源状态</div>
        <div class="ss-val" style="color:#22c55e;text-shadow:0 0 5px #22c55e66">✓ 稳定供电</div>
      </div>
    </div>

    <!-- ── KNOWLEDGE SECTION ─────────────────────────────────────────────── -->
    <div class="s2-know-wrap">
      <!-- Device Structure -->
      <div class="s2-know-card">
        <h3 class="s2-know-title">设备结构</h3>
        <div class="s2-stabs">
          <button v-for="t in structTabs" :key="t.id" :class="['s2-stab', {active: structTab===t.id}]"
            :style="structTab===t.id ? `border-color:${currentDevice.hexStr};color:${currentDevice.hexStr};background:${currentDevice.hexStr}20;box-shadow:0 0 7px ${currentDevice.hexStr}44` : ''"
            @click="structTab=t.id">{{ t.name }}</button>
        </div>
        <div class="s2-struct-body">
          <p v-if="structTab==='exterior'" class="s2-struct-text">{{ currentDevice.structDesc }}</p>
          <div v-else-if="structTab==='ports'" class="s2-ports-list">
            <div v-for="p in currentDevice.portDetails" :key="p.id" class="s2-port-card" @click="portPopupData=p;showPortPopup=false">
              <div class="spc-head">
                <span class="s2-port-dot" :style="`background:${p.status==='UP'?'#22c55e':p.status==='DOWN'?'#ef4444':'#f59e0b'};box-shadow:0 0 4px ${p.status==='UP'?'#22c55e':p.status==='DOWN'?'#ef4444':'#f59e0b'}`"></span>
                <span class="spc-name">{{ p.name }}</span>
                <span class="spc-status" :style="`color:${p.status==='UP'?'#22c55e':p.status==='DOWN'?'#ef4444':'#f59e0b'}`">{{ p.status }}</span>
              </div>
              <div class="spc-info"><span>{{ p.ip }}</span><span>{{ p.speed }}</span></div>
              <div class="spc-desc">{{ p.desc }}</div>
            </div>
          </div>
          <p v-else-if="structTab==='internal'" class="s2-struct-text">内部采用高密度 PCB 设计，集成多核网络处理器（NPU）、DDR4 内存、Flash 存储及多个以太网 PHY 芯片。电源模块 DC-DC 转换，散热系统被动散热+风扇冗余，工作温度 0–40℃。</p>
          <p v-else-if="structTab==='board'" class="s2-struct-text">主板搭载 {{ currentDevice.osi }} 网络处理单元，CPU 当前负载 {{ currentDevice.cpu }}%，内存占用 {{ currentDevice.mem }}%。各模块通过高速 PCIe 总线互联，支持零停机固件升级与远程带外管理（iDRAC/IPMI/iLO）。</p>
          <p v-else class="s2-struct-text">电源规格：输入 100~240V AC，50/60Hz；{{ currentDevice.id === 'server' ? '输出 12V DC，额定功率 750W，双电源热冗余，支持在线更换' : '输出 12V DC，功率 30~60W，内置浪涌保护' }}。满足 80 Plus 认证，EMC 屏蔽，符合 CE/FCC 标准。</p>
        </div>
      </div>

      <!-- Knowledge Panel -->
      <div class="s2-know-card">
        <h3 class="s2-know-title">知识讲解
          <span class="s2-ai-badge" :style="`background:linear-gradient(135deg,${currentDevice.hexStr},${currentDevice.hexStr}99)`">AI 讲解中</span>
        </h3>
        <p class="s2-know-text">{{ currentDevice.knowledge }}</p>
        <div class="s2-proto-tags">
          <span v-for="p in currentDevice.protocols" :key="p" class="s2-ptag" title="点击查看协议详情"
            :style="`border-color:${currentDevice.hexStr}55;color:${currentDevice.hexStr};text-shadow:0 0 5px ${currentDevice.hexStr}66`"
            @click="openProto(p)">{{ p }}</span>
        </div>
        <div class="s2-rfc">参考标准：<span>{{ currentDevice.rfc }}</span></div>
        <div class="s2-more-link" :style="`color:${currentDevice.hexStr}`" @click="openProto(currentDevice.protocols[0])">了解更多 &gt;&gt;</div>
      </div>
    </div>

    <!-- ── PROTOCOL DETAIL PANEL ─────────────────────────────────────────── -->
    <transition name="panel-slide">
      <div v-if="showProtoPanel && selectedProto" class="proto-panel">
        <div class="proto-panel-header" :style="`border-bottom-color:${currentDevice.hexStr}44`">
          <div>
            <div class="proto-panel-name" :style="`color:${currentDevice.hexStr}`">{{ selectedProtoKey }}</div>
            <div class="proto-panel-full">{{ selectedProto.full }}</div>
          </div>
          <button class="proto-panel-close" @click="showProtoPanel=false">✕</button>
        </div>
        <div class="proto-panel-body">
          <div class="proto-meta">
            <span>{{ selectedProto.layer }}</span>
            <span class="pm-rfc">{{ selectedProto.rfc }}</span>
          </div>
          <p class="proto-desc">{{ selectedProto.desc }}</p>
          <div class="proto-features">
            <div class="pf-title">核心特性</div>
            <div v-for="f in selectedProto.features" :key="f" class="pf-item">
              <span class="pf-dot" :style="`background:${currentDevice.hexStr}`"></span>{{ f }}
            </div>
          </div>
          <div class="proto-other-title">本设备支持协议</div>
          <div class="proto-other-tags">
            <span v-for="p in currentDevice.protocols" :key="p"
              :class="['pot', {active: p===selectedProtoKey}]"
              :style="p===selectedProtoKey ? `border-color:${currentDevice.hexStr};color:${currentDevice.hexStr};background:${currentDevice.hexStr}22` : ''"
              @click="openProto(p)">{{ p }}</span>
          </div>
        </div>
      </div>
    </transition>

    <!-- Backdrop -->
    <div v-if="showProtoPanel" class="proto-backdrop" @click="showProtoPanel=false"></div>

  </div>
</template>

<style scoped>
.s2-page { display:flex;flex-direction:column;gap:10px;background:#040d1a; }

/* BANNER */
.s2-banner { background:linear-gradient(135deg,#060c1c 0%,#0a1226 50%,#060c1c 100%);border:1px solid #1a2a5a;border-radius:14px;padding:18px 22px;display:flex;justify-content:space-between;align-items:center;position:relative;overflow:hidden; }
.scan-line { position:absolute;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 18px,rgba(99,102,241,.025) 18px,rgba(99,102,241,.025) 19px);pointer-events:none;z-index:0; }
.banner-inner { display:flex;align-items:center;gap:16px;position:relative;z-index:1; }
.banner-logo { width:48px;height:48px;background:linear-gradient(135deg,#1a2a5a,#2a3a7a);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:22px;border:1px solid rgba(99,102,241,.3);flex-shrink:0;transition:box-shadow .3s; }
.s2-banner-title { font-size:18px;font-weight:700;color:#e0e7ff;margin:0 0 4px;text-shadow:0 0 15px rgba(139,92,246,.5); }
.s2-banner-sub { font-size:11px;color:#6b7fa3;margin:0 0 10px; }
.banner-tags { display:flex;gap:10px; }
.btag { font-size:11px;color:#94a3b8;background:rgba(10,15,35,.85);border:1px solid #1a2a5a;border-radius:8px;padding:5px 10px;line-height:1.5;cursor:pointer;transition:all .2s; }
.btag:hover { border-color:#6366f1;color:#e0e7ff;box-shadow:0 0 8px rgba(99,102,241,.3); }
.btag-icon { font-size:11px;margin-right:3px; }
.btag small { font-size:10px;color:#3a4a6a;display:block; }
.holo-cube-wrap { flex-shrink:0;width:90px;height:90px;position:relative;display:flex;align-items:center;justify-content:center;z-index:1; }
.cube-layer { position:absolute;border:1.5px solid;border-radius:8px;animation:cube-pulse 3s ease-in-out infinite; }
@keyframes cube-pulse { 0%,100%{ opacity:.2;transform:rotate(0deg)scale(1); } 50%{ opacity:.7;transform:rotate(8deg)scale(1.08); } }

/* TOOLBAR */
.s2-toolbar { background:#070d1f;border:1px solid #1a2a5a;border-radius:10px;padding:9px 16px;display:flex;align-items:center;gap:12px; }
.mode-btns { display:flex;gap:4px; }
.mBtn { padding:6px 14px;border:1.5px solid #1a2a5a;border-radius:7px;background:#0d1433;color:#6b7fa3;font-size:12px;cursor:pointer;transition:all .18s; }
.mBtn.active { background:rgba(99,102,241,.15);border-color:#6366f1;color:#a5b4fc;box-shadow:0 0 8px rgba(99,102,241,.3); }
.tb-sep { width:1px;height:22px;background:#1a2a5a;flex-shrink:0; }
.tb-ctrl { display:flex;align-items:center;gap:7px; }
.tb-label { font-size:11px;color:#3a4a6a; }
.tb-btn { width:27px;height:27px;border:1px solid #1a2a5a;border-radius:5px;background:#0d1433;color:#94a3b8;font-size:13px;cursor:pointer;transition:all .15s;display:flex;align-items:center;justify-content:center; }
.tb-btn:hover { background:#1a2a5a;color:#e0e7ff; }
.flow-tog { width:38px;height:20px;border-radius:10px;background:#1a2a5a;cursor:pointer;position:relative;transition:all .2s; }
.flow-tog.on { background:#6366f1;box-shadow:0 0 8px rgba(99,102,241,.4); }
.tog-knob { width:16px;height:16px;border-radius:50%;background:white;position:absolute;top:2px;left:2px;transition:left .2s; }
.flow-tog.on .tog-knob { left:20px; }
.tb-hint { font-size:10px;color:#2a3a5a;font-family:monospace; }
.tb-right { margin-left:auto;display:flex;align-items:center;gap:7px; }
.curr-label { font-size:12px;font-weight:600;font-family:monospace; }
.curr-dot { width:7px;height:7px;border-radius:50%; }

/* MAIN */
.s2-main { display:flex;gap:0;min-height:0; }
.s2-canvas-wrap { flex:1;position:relative;overflow:hidden;background:#040d1a;min-height:460px;height:520px; }
.s2-canvas { position:absolute;inset:0;width:100%;height:100%;display:block;cursor:grab;z-index:0; }
.s2-canvas:active { cursor:grabbing; }
.matrix-bg { position:absolute;inset:0;background:repeating-linear-gradient(90deg,transparent,transparent 60px,rgba(30,50,100,.04) 60px,rgba(30,50,100,.04) 61px),repeating-linear-gradient(0deg,transparent,transparent 60px,rgba(30,50,100,.04) 60px,rgba(30,50,100,.04) 61px);pointer-events:none;z-index:1; }
.loading-holo { position:absolute;inset:0;background:#040d1a;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;color:#6b7fa3;font-size:13px;z-index:20; }
.holo-spin { width:36px;height:36px;border:2px solid rgba(139,92,246,.2);border-top-color:#7c3aed;border-radius:50%;animation:spin .8s linear infinite; }
.node-overlay { position:absolute;top:12px;left:12px;background:rgba(4,13,26,.88);border:1px solid rgba(99,102,241,.4);border-radius:8px;padding:8px 12px;z-index:10;backdrop-filter:blur(8px); }
.node-title { font-size:11px;color:#a5b4fc;font-weight:600;margin-bottom:4px; }
.node-stats { display:flex;gap:12px;align-items:center; }
.node-stats span { font-size:10px;color:#6b7fa3;font-family:monospace; }
.node-explode-badge { background:rgba(99,102,241,.2);border:1px solid #6366f1;color:#a5b4fc;border-radius:4px;padding:1px 6px;font-size:10px; }
.proto-label { position:absolute;font-size:11px;color:#a5b4fc;font-family:monospace;font-weight:600;background:rgba(4,13,26,.75);border:1px solid;border-radius:4px;padding:3px 8px;z-index:10;animation:float-label 3s ease-in-out infinite;text-shadow:0 0 8px rgba(139,92,246,.8); }
.proto-label.clickable { cursor:pointer;transition:background .15s; }
.proto-label.clickable:hover { background:rgba(99,102,241,.25); }
.label-hint { font-size:9px;color:#4a5a8a;margin-left:4px;opacity:.7; }
@keyframes float-label { 0%,100%{ transform:translateY(0);opacity:.8; } 50%{ transform:translateY(-6px);opacity:1; } }
/* Port popup */
.port-popup { position:absolute;z-index:20;background:rgba(7,13,31,.95);border:1px solid #2a3a7a;border-radius:10px;padding:12px 14px;width:210px;backdrop-filter:blur(12px);box-shadow:0 8px 32px rgba(0,0,0,.6); }
.pp-close { position:absolute;top:8px;right:10px;font-size:11px;color:#4a5a7a;cursor:pointer;line-height:1; }
.pp-close:hover { color:#e0e7ff; }
.pp-title { font-size:12px;font-weight:700;color:#e0e7ff;margin-bottom:8px;font-family:monospace; }
.pp-row { display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px; }
.pp-row span:first-child { color:#3a4a6a; }
.pp-row span:last-child { color:#94a3b8;font-family:monospace; }
.pp-desc { font-size:10px;color:#4a5a7a;border-top:1px solid #1a2a5a;padding-top:6px;margin-top:6px;line-height:1.5; }
.canvas-statusbar { position:absolute;bottom:0;left:0;right:0;background:rgba(4,13,26,.9);border-top:1px solid #1a2a5a;padding:5px 12px;font-size:10px;color:#6366f1;font-family:monospace;z-index:10; }
.sb-dot { display:inline-block;width:6px;height:6px;border-radius:50%;background:#6366f1;margin-right:6px;animation:blink 1.2s ease-in-out infinite; }

/* RIGHT PANEL */
.s2-right { width:278px;flex-shrink:0;display:flex;flex-direction:column;border-left:1px solid #1a2a5a;overflow-y:auto;background:#070d1f; }
.s2-right::-webkit-scrollbar { width:3px; }
.s2-right::-webkit-scrollbar-thumb { background:#1a2a5a; }
.s2-sect { padding:11px 13px;border-bottom:1px solid #0d1a38; }
.s2-sect-title { font-size:11px;font-weight:700;color:#3a5a7a;margin-bottom:8px;font-family:monospace;text-transform:uppercase;letter-spacing:.5px;display:flex;justify-content:space-between;align-items:center; }
.click-hint { font-size:9px;color:#2a3a5a;text-transform:none;font-weight:400; }
.s2-dev-list { display:flex;flex-direction:column;gap:5px; }
.s2-dev-card { display:flex;align-items:center;gap:8px;padding:9px 10px;border:1.5px solid #1a2a5a;border-radius:8px;background:#0d1829;cursor:pointer;transition:all .18s; }
.s2-dev-card:hover { border-color:#2a3a6a;background:#111e35; }
.s2-dev-icon { font-size:17px; }
.s2-dev-info { flex:1; }
.s2-dev-name { font-size:13px;font-weight:600;color:#94a3b8;transition:color .2s; }
.s2-dev-sub { font-size:10px;color:#3a4a6a;font-family:monospace; }
.s2-dev-dot { width:7px;height:7px;border-radius:50%;flex-shrink:0; }
.s2-specs-grid { display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-bottom:8px; }
.s2-spec { background:#0d1433;border-radius:6px;padding:5px 8px;border:1px solid #1a2a5a; }
.sg-l { font-size:9px;color:#3a4a6a;text-transform:uppercase; }
.sg-v { font-size:11px;color:#94a3b8;font-family:monospace;font-weight:600; }
.s2-info-table { width:100%;border-collapse:collapse;font-size:11px;margin-bottom:4px; }
.s2-info-table td { padding:4px 0;border-bottom:1px solid #0d1a38; }
.s2-info-table td:first-child { color:#3a4a6a;width:44%; }
.s2-info-table td:last-child { color:#94a3b8;font-family:monospace;font-weight:500; }
.s2-spec-link { font-size:11px;cursor:pointer;display:block;margin-top:5px; }
.s2-diag-sect { background:#060e1a; }
.s2-diag-wrap { margin-bottom:3px; }
.s2-diag-row { display:flex;align-items:center;gap:7px;padding:4px 3px;border-radius:5px;cursor:pointer;transition:background .15s; }
.s2-diag-row:hover,.s2-diag-row.expanded { background:rgba(99,102,241,.06); }
.s2-diag-dot { width:6px;height:6px;border-radius:50%;flex-shrink:0; }
.s2-diag-name { font-size:11px;color:#6b7fa3;flex:1; }
.s2-diag-stat { font-size:10px;font-family:monospace;font-weight:600; }
.s2-diag-chevron { font-size:13px;color:#3a4a6a;transition:transform .2s;transform:rotate(0deg); }
.s2-diag-chevron.open { transform:rotate(90deg); }
.s2-diag-detail { font-size:10px;color:#4a5a7a;line-height:1.6;padding:5px 8px 6px 16px;background:rgba(4,13,26,.5);border-left:2px solid #1a2a5a;border-radius:0 0 4px 4px;margin-top:1px; }
.diag-metrics { border-top:1px solid #0d1a38;padding-top:6px;margin-top:4px; }
.dm-row { display:flex;justify-content:space-between;font-size:10px;color:#3a4a6a;padding:2px 0; }
.dm-val { color:#6b7fa3;font-family:monospace; }
.s2-map-sect { background:#040d1a; }
.s2-map-sect svg { width:100%;height:auto;border-radius:6px;border:1px solid #1a2a5a; }

/* PORT DETAIL CARD */
.s2-port-card { background:#0d1433;border:1px solid #1a2a5a;border-radius:7px;padding:8px 10px;margin-bottom:6px;cursor:pointer;transition:border-color .15s; }
.s2-port-card:hover { border-color:#2a3a6a; }
.spc-head { display:flex;align-items:center;gap:6px;margin-bottom:4px; }
.spc-name { font-size:11px;font-weight:600;color:#94a3b8;font-family:monospace;flex:1; }
.spc-status { font-size:10px;font-family:monospace;font-weight:600; }
.spc-info { display:flex;justify-content:space-between;font-size:10px;color:#4a5a7a;font-family:monospace;margin-bottom:3px; }
.spc-desc { font-size:10px;color:#3a4a5a;line-height:1.5; }
.s2-port-dot { width:6px;height:6px;border-radius:50%;flex-shrink:0; }

/* STATUS BAR */
.s2-status { background:#070d1f;border:1px solid #1a2a5a;border-radius:12px;padding:12px 16px;display:grid;grid-template-columns:repeat(5,1fr);gap:12px; }
.ss-item { display:flex;flex-direction:column;gap:4px; }
.ss-label { font-size:11px;color:#3a4a6a;font-weight:500; }
.ss-val { font-size:13px;font-weight:600;color:#94a3b8;display:flex;align-items:center;gap:5px;flex-wrap:wrap; }
.ss-dot { width:7px;height:7px;border-radius:50%;display:inline-block;flex-shrink:0; }
.ss-bar { width:55px;height:4px;background:#1a2a5a;border-radius:2px;overflow:hidden; }
.ss-fill { height:100%;border-radius:2px;transition:width .5s; }

/* KNOWLEDGE */
.s2-know-wrap { display:flex;gap:10px; }
.s2-know-card { flex:1;background:#070d1f;border:1px solid #1a2a5a;border-radius:14px;padding:15px; }
.s2-know-title { font-size:14px;font-weight:700;color:#e0e7ff;margin:0 0 11px;display:flex;align-items:center;gap:8px;text-shadow:0 0 10px rgba(139,92,246,.2); }
.s2-ai-badge { font-size:10px;color:white;padding:2px 8px;border-radius:10px;font-weight:500;flex-shrink:0; }
.s2-stabs { display:flex;gap:4px;margin-bottom:10px;flex-wrap:wrap; }
.s2-stab { padding:4px 10px;border:1px solid #1a2a5a;border-radius:6px;background:#0d1433;font-size:11px;color:#3a4a6a;cursor:pointer;transition:all .15s; }
.s2-struct-body { min-height:80px; }
.s2-struct-text { font-size:12px;color:#6b7fa3;line-height:1.75;margin:0; }
.s2-ports-list { display:flex;flex-direction:column; }
.s2-know-text { font-size:12px;color:#6b7fa3;line-height:1.8;white-space:pre-line;margin:0 0 10px; }
.s2-proto-tags { display:flex;flex-wrap:wrap;gap:5px;margin-bottom:8px; }
.s2-ptag { font-size:11px;border:1px solid;border-radius:4px;padding:2px 7px;font-family:monospace;background:transparent;cursor:pointer;transition:all .15s; }
.s2-ptag:hover { transform:translateY(-1px);box-shadow:0 2px 8px rgba(0,0,0,.4); }
.s2-rfc { font-size:11px;color:#3a4a6a;margin-bottom:6px; }
.s2-rfc span { color:#6366f1;font-family:monospace; }
.s2-more-link { font-size:12px;cursor:pointer; }

/* PROTOCOL DETAIL PANEL */
.proto-panel { position:fixed;right:0;top:0;bottom:0;width:320px;background:#070d1f;border-left:1px solid #1a2a5a;z-index:100;display:flex;flex-direction:column;box-shadow:-10px 0 40px rgba(0,0,0,.6); }
.proto-panel-header { display:flex;justify-content:space-between;align-items:flex-start;padding:18px 16px 14px;border-bottom:1px solid; }
.proto-panel-name { font-size:22px;font-weight:800;font-family:monospace;letter-spacing:1px; }
.proto-panel-full { font-size:12px;color:#6b7fa3;margin-top:2px; }
.proto-panel-close { background:none;border:1px solid #1a2a5a;color:#6b7fa3;width:28px;height:28px;border-radius:6px;cursor:pointer;font-size:12px;flex-shrink:0;transition:all .15s; }
.proto-panel-close:hover { border-color:#6366f1;color:#e0e7ff; }
.proto-panel-body { flex:1;overflow-y:auto;padding:16px; }
.proto-panel-body::-webkit-scrollbar { width:3px; }
.proto-panel-body::-webkit-scrollbar-thumb { background:#1a2a5a; }
.proto-meta { display:flex;gap:10px;margin-bottom:12px; }
.proto-meta span { font-size:11px;background:#0d1433;border:1px solid #1a2a5a;border-radius:5px;padding:3px 8px;color:#6b7fa3;font-family:monospace; }
.pm-rfc { color:#6366f1 !important;border-color:#2a3a7a !important; }
.proto-desc { font-size:12px;color:#6b7fa3;line-height:1.8;margin-bottom:14px; }
.proto-features { margin-bottom:16px; }
.pf-title { font-size:11px;color:#3a5a7a;font-weight:700;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px; }
.pf-item { display:flex;align-items:center;gap:8px;font-size:12px;color:#94a3b8;margin-bottom:6px;line-height:1.5; }
.pf-dot { width:5px;height:5px;border-radius:50%;flex-shrink:0; }
.proto-other-title { font-size:11px;color:#3a5a7a;font-weight:700;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px; }
.proto-other-tags { display:flex;flex-wrap:wrap;gap:6px; }
.pot { font-size:11px;border:1px solid #1a2a5a;border-radius:4px;padding:3px 10px;font-family:monospace;color:#3a4a6a;cursor:pointer;transition:all .15s; }
.pot.active { font-weight:700; }
.proto-backdrop { position:fixed;inset:0;background:rgba(0,0,0,.3);z-index:99; }
.panel-slide-enter-active,.panel-slide-leave-active { transition:transform .25s ease; }
.panel-slide-enter-from,.panel-slide-leave-to { transform:translateX(100%); }

/* ANIMATIONS */
@keyframes spin { to { transform:rotate(360deg); } }
@keyframes blink { 0%,100%{ opacity:1; } 50%{ opacity:.3; } }
</style>
