/**
 * 知识图谱节点 ID → 名称映射表（静态内嵌，来源：data/knowledge_graph.json）
 *
 * kp_xxx：课程知识节点（KnowledgeNode）
 * acu_xxx：认知理解单元（CognitiveUnit）
 */
export const KP_NAMES: Record<string, string> = {
  kp_001: '计算机网络概述',
  kp_002: 'OSI七层模型',
  kp_003: 'TCP/IP体系结构',
  kp_004: '物理层基本概念',
  kp_005: '数据链路层基本概念',
  kp_006: '局域网技术',
  kp_007: '网络层基本概念',
  kp_008: 'IP地址与子网划分',
  kp_009: 'ARP协议',
  kp_010: '路由选择协议',
  kp_011: '运输层基本概念',
  kp_012: 'UDP协议',
  kp_013: 'TCP协议基础',
  kp_014: 'TCP三次握手与四次挥手',
  kp_015: 'TCP流量控制与拥塞控制',
  kp_016: '应用层基本概念',
  kp_017: 'DNS协议',
  kp_018: 'HTTP与HTTPS',
  kp_019: '网络安全基础',
  kp_020: '综合应用与故障排查',
}

export const ACU_NAMES: Record<string, string> = {
  acu_001: 'OSI与TCP/IP分层映射',
  acu_002: 'IP标识主机 vs 端口标识进程',
  acu_003: '交换机MAC转发 vs 路由器IP转发',
  acu_004: '以太网帧长度 vs MTU载荷上限',
  acu_005: '全双工交换网中CSMA/CD已淘汰',
  acu_006: 'VLAN标签在交换机层的处理',
  acu_007: 'MTU大小与分片代价权衡',
  acu_008: 'ICMP属于网络层非传输层',
  acu_009: 'IP分片是网络层职责非TCP',
  acu_010: '子网前缀长度与主机位计算',
  acu_011: 'DHCP提供完整网络配置',
  acu_012: 'IPv6全面改进特性',
  acu_013: 'IPv6前缀子网划分机制',
  acu_014: 'CIDR同时适用IPv4和IPv6',
  acu_015: 'ARP解析IP→MAC vs DNS解析域名',
  acu_016: 'BGP作为外部网关协议',
  acu_017: 'OSPF链路代价 vs RIP跳数',
  acu_018: 'UDP在实际场景的应用价值',
  acu_019: 'TCP可靠传输不仅依赖ACK',
  acu_020: 'TCP按字节流编号的序号机制',
  acu_021: 'RTT是往返时间非单向时延',
  acu_022: 'Socket是通信端点抽象非端口号',
  acu_023: '超时重传 vs 快速重传触发条件',
  acu_024: 'Nagle算法适用场景与禁用条件',
  acu_025: 'TCP为何需要三次握手而非两次',
  acu_026: 'TCP四次挥手的全双工关闭逻辑',
  acu_027: 'SYN洪水攻击消耗服务端资源',
  acu_028: '流量控制rwnd vs 拥塞控制cwnd',
  acu_029: '慢启动阶段cwnd指数增长',
  acu_030: '正向代理 vs 反向代理',
  acu_031: 'FTP控制连接与数据连接双端口',
  acu_032: 'SMTP邮件中继路由流程',
  acu_033: 'WebSocket通过HTTP Upgrade建立',
  acu_034: 'DNS递归查询 vs 迭代查询',
  acu_035: 'CDN能力远超DNS解析调度',
  acu_036: 'DNS记录TTL机制与缓存过期',
  acu_037: 'DNS污染威胁与DNSSEC防护',
  acu_038: 'HTTP依赖传输层非直接运行在IP',
  acu_039: 'HTTP状态码1xx-5xx五类语义',
  acu_040: 'Web缓存多层架构',
  acu_041: 'HTTP/2规范中TLS非强制',
  acu_042: 'HTTP/1.1默认Keep-Alive持久连接',
  acu_043: 'Cookie可由服务端Set-Cookie设置',
  acu_044: 'NAT地址改写破坏端到端透明性',
  acu_045: 'TLS提供机密性完整性和认证',
  acu_046: 'QUIC是基于UDP的传输层协议',
  acu_047: '现代防火墙超越IP/端口深度检测',
  acu_048: '负载均衡器支持多种调度策略',
}

/**
 * 根据节点 ID 返回可读名称，未知 ID 直接返回原值
 */
export function resolveNodeName(id: string): string {
  return KP_NAMES[id] ?? ACU_NAMES[id] ?? id
}

/**
 * 判断 ID 类型
 */
export function nodeType(id: string): 'kp' | 'acu' | 'unknown' {
  if (id.startsWith('kp_')) return 'kp'
  if (id.startsWith('acu_')) return 'acu'
  return 'unknown'
}
