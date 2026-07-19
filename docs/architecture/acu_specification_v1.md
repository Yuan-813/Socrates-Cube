# ACU 规格卡 v1.0

## 概述

- **总计**：48 个 ACU（原子认知单元）
- **第一批（高优先级）**：TCP/DNS/HTTP/IP/路由相关，29 个
- **第二批（次优先级）**：OSI/链路层/局域网/基础概念/安全/应用层，19 个
- **规格卡用途**：驱动 Diagnosis 定位、Intervention 触发、Challenge 验证、Profiler 画像
- **数据来源**：`data/knowledge_graph.json`（cognitive_nodes）、`data/misconceptions.json`、`docs/architecture/cognitive_kg_design_v1.md`
- **质量门槛**：每个 ACU 的 Definition 可独立区分、Verification Questions 可判定修复效果、Repair Strategy 可指导内容生成

---

## 第一批：高价值 ACU（TCP / DNS / HTTP / IP / 路由）

### kp_013 TCP协议基础（6 个 ACU）

---

### acu_019: tcp_reliability_beyond_ack

| 字段 | 内容 |
|---|---|
| **ACU ID** | tcp_reliability_beyond_ack |
| **Label** | 理解TCP可靠传输不仅依赖ACK确认 |
| **Definition** | TCP的可靠传输是序号、累积确认、超时重传、校验和、流量控制五种机制协同的结果，ACK仅是其中确认环节，单独ACK无法防止乱序、重复、比特错误等问题 |
| **Misconceptions** | mc_016 |
| **Error Model** | 学生将"有ACK回复"等同于"数据一定送达且正确"，忽略了ACK本身可能丢失、数据可能乱序到达、校验和可能检测到位错误等场景 |
| **Repair Strategy** | 可靠传输全景机制图解（序号+确认+重传+校验+超时估计五要素拼图）+ ACK丢失导致重传的场景仿真 |
| **Verification Questions** | 1. 如果ACK报文本身在网络中丢失，TCP如何保证数据最终被正确接收？ 2. 除了ACK确认，TCP还依赖哪些机制来确保字节流的完整性和有序性？ |
| **Prerequisites** | 无 |

---

### acu_020: tcp_byte_stream_sequence_numbering

| 字段 | 内容 |
|---|---|
| **ACU ID** | tcp_byte_stream_sequence_numbering |
| **Label** | 掌握TCP按字节流编号的序号机制 |
| **Definition** | TCP序号是按字节流中每个字节的位置递增编号的，每个报文段的序号等于该段第一个数据字节在整个字节流中的偏移量，而非按报文段的发送顺序计数 |
| **Misconceptions** | mc_020 |
| **Error Model** | 学生认为TCP序号像"第1段、第2段、第3段"这样按报文个数递增，导致无法正确计算下一个序号值或确认号 |
| **Repair Strategy** | TCP字节流编号原理图解（展示字节偏移与段序号的关系）+ 序号计算练习（给定MSS和初始序号，计算第N个段的序号） |
| **Verification Questions** | 1. 若初始序号为100，第一个段携带500字节数据，第二个段的序号是多少？ 2. 接收方回复ACK=1001代表什么含义？ |
| **Prerequisites** | 无 |

---

### acu_021: rtt_round_trip_measurement

| 字段 | 内容 |
|---|---|
| **ACU ID** | rtt_round_trip_measurement |
| **Label** | 理解RTT是往返时间而非单向传播时延 |
| **Definition** | RTT（Round-Trip Time）是从发送端发出数据段到收到对应ACK的总耗时，包含两个方向的传播时延、发送时延、排队时延和处理时延，约为单向传播时延的2倍以上 |
| **Misconceptions** | mc_021 |
| **Error Model** | 学生将RTT等同于光信号从A到B的单向传播时延，导致在计算超时重传定时器（RTO）和吞吐量时产生2倍数量级错误 |
| **Repair Strategy** | RTT组成分析图（正向传播+排队+处理+反向传播+排队+处理）+ RTT数值计算练习（给定链路参数计算实际RTT） |
| **Verification Questions** | 1. 单向传播时延为10ms的链路，RTT至少是多少？为什么说"至少"？ 2. RTT的测量值会受到哪些因素的动态影响？ |
| **Prerequisites** | acu_020 |

---

### acu_022: socket_abstraction_definition

| 字段 | 内容 |
|---|---|
| **ACU ID** | socket_abstraction_definition |
| **Label** | 理解Socket是通信端点抽象而非仅端口号 |
| **Definition** | Socket是操作系统提供的通信端点抽象，由（IP地址, 端口号, 协议类型）三元组唯一标识一个通信端点，同一端口号在不同IP或不同协议下对应不同的Socket |
| **Misconceptions** | mc_042 |
| **Error Model** | 学生将Socket简化为端口号本身，无法解释"同一服务器80端口如何同时服务多个客户端"以及"TCP/UDP可以使用相同端口号"等现象 |
| **Repair Strategy** | Socket三元组定义辨析对比表（Socket vs 端口号 vs IP地址）+ 多客户端并发连接场景分析（展示不同Socket如何共享端口） |
| **Verification Questions** | 1. 服务器的80端口同时接受了来自两个不同客户端的TCP连接，操作系统如何区分这两个连接？ 2. TCP和UDP能否同时使用同一个端口号？为什么？ |
| **Prerequisites** | acu_002 |

---

### acu_023: timeout_vs_fast_retransmission

| 字段 | 内容 |
|---|---|
| **ACU ID** | timeout_vs_fast_retransmission |
| **Label** | 区分超时重传与快速重传的触发条件 |
| **Definition** | 超时重传由RTO定时器到期触发，适用于所有丢包场景；快速重传由连续收到3个重复ACK触发，无需等待超时即可推断特定段丢失，恢复速度更快 |
| **Misconceptions** | mc_044 |
| **Error Model** | 学生认为TCP只有一种重传方式或将两者视为同一机制的不同名称，无法解释为什么快速重传能在RTO到期前就触发重传 |
| **Repair Strategy** | 超时重传vs快速重传触发条件对比表（RTO定时器到期 vs 3次重复ACK）+ 时序图仿真（展示快速重传如何节省等待时间） |
| **Verification Questions** | 1. 发送方连续收到3个对序号1001的重复ACK，这意味着什么？应执行什么操作？ 2. 在什么场景下快速重传无法生效，只能依赖超时重传？ |
| **Prerequisites** | acu_019 |

---

### acu_024: nagle_algorithm_applicability

| 字段 | 内容 |
|---|---|
| **ACU ID** | nagle_algorithm_applicability |
| **Label** | 理解Nagle算法的适用场景与禁用条件 |
| **Definition** | Nagle算法通过延迟发送小数据包（等到前一个ACK返回或数据累积到MSS）来减少网络中的小包数量，适合批量传输但会增加交互式应用的延迟，SSH/游戏/实时通信通常需设置TCP_NODELAY禁用 |
| **Misconceptions** | mc_045 |
| **Error Model** | 学生认为Nagle算法是TCP的普适性能优化，对所有应用都有益，忽略了它对实时交互场景的延迟代价 |
| **Repair Strategy** | Nagle适用vs禁用场景分析表（批量文件传输=适用 vs SSH按键回显/在线游戏=禁用）+ TCP_NODELAY设置的效果对比仿真 |
| **Verification Questions** | 1. 为什么SSH客户端通常需要设置TCP_NODELAY？如果不设置会出现什么现象？ 2. Nagle算法在什么条件下才会发送已缓存的小数据包？ |
| **Prerequisites** | acu_019 |

---

### kp_014 TCP三次握手与四次挥手（3 个 ACU）

---

### acu_025: tcp_three_way_handshake_necessity

| 字段 | 内容 |
|---|---|
| **ACU ID** | tcp_three_way_handshake_necessity |
| **Label** | 理解为什么TCP需要三次握手而非两次 |
| **Definition** | 三次握手的第三次ACK用于确认客户端已收到服务端的SYN-ACK，防止因网络延迟导致的旧SYN请求到达服务端时建立无效连接，从而占用服务端资源形成半开连接 |
| **Misconceptions** | mc_001 |
| **Error Model** | 学生认为两次报文交换（SYN + SYN-ACK）足以建立可靠连接，忽略了网络延迟可能导致旧SYN重放到达服务端的场景 |
| **Repair Strategy** | 三次握手状态机动画（展示SYN→SYN-ACK→ACK正常流程）+ 两次握手失败场景仿真（展示旧SYN到达导致服务端误建连接） |
| **Verification Questions** | 1. 如果去掉第三次ACK，网络延迟的旧SYN到达服务器会发生什么？ 2. 两次握手能否防止半开连接？请说明原因。 |
| **Prerequisites** | 无 |

---

### acu_026: tcp_four_way_close_full_duplex

| 字段 | 内容 |
|---|---|
| **ACU ID** | tcp_four_way_close_full_duplex |
| **Label** | 理解TCP四次挥手的全双工独立关闭逻辑 |
| **Definition** | TCP是全双工协议，两个方向的数据流需要分别关闭：主动方发FIN关闭自己的发送方向，被动方ACK后仍可继续发送数据（半关闭状态），待被动方也发FIN后连接才完全释放 |
| **Misconceptions** | mc_002 |
| **Error Model** | 学生类比三次握手，认为断开也是三次报文，忽略了全双工两个方向需要独立关闭以及半关闭状态的存在 |
| **Repair Strategy** | 四次挥手全双工独立关闭流程动画（展示FIN/ACK两个方向的时序）+ 半关闭状态场景仿真（被动方ACK后继续发送数据） |
| **Verification Questions** | 1. TCP断开连接时，为什么被动关闭方的ACK和FIN不能合并为一个报文？ 2. 什么是半关闭状态？请描述一个半关闭状态下数据仍在传输的场景。 |
| **Prerequisites** | acu_025 |

---

### acu_027: syn_flood_server_resource_attack

| 字段 | 内容 |
|---|---|
| **ACU ID** | syn_flood_server_resource_attack |
| **Label** | 理解SYN洪水攻击消耗服务端资源的原理 |
| **Definition** | SYN Flood攻击利用三次握手机制，攻击者发送大量SYN但不回复第三次ACK，导致服务端为每个半开连接分配内存（TCB）并维护在半连接队列中，队列满后无法接受正常连接请求 |
| **Misconceptions** | mc_043 |
| **Error Model** | 学生认为SYN洪水主要消耗客户端资源，或认为双方资源消耗对等，不理解为什么服务端是攻击的主要受害者 |
| **Repair Strategy** | SYN Flood攻击原理图解（客户端伪造IP→服务端分配TCB→半连接队列溢出）+ 客户端vs服务端资源消耗对比表 + SYN Cookie防御机制讲解 |
| **Verification Questions** | 1. SYN Flood攻击中，服务端的哪种资源会被耗尽？为什么攻击者几乎不消耗自身资源？ 2. SYN Cookie技术如何在不维护半开连接状态的情况下完成三次握手？ |
| **Prerequisites** | acu_025 |

---

### kp_015 TCP流量控制与拥塞控制（2 个 ACU）

---

### acu_028: flow_control_vs_congestion_control

| 字段 | 内容 |
|---|---|
| **ACU ID** | flow_control_vs_congestion_control |
| **Label** | 区分流量控制rwnd与拥塞控制cwnd的职责 |
| **Definition** | 流量控制通过接收窗口rwnd保护接收端缓冲区不溢出；拥塞控制通过拥塞窗口cwnd避免网络中间链路过载；实际发送窗口=min(rwnd, cwnd)，两者保护对象和调节机制完全不同 |
| **Misconceptions** | mc_006, mc_015 |
| **Error Model** | 学生将rwnd和cwnd视为同一个变量，或将流量控制等同于拥塞控制，无法区分"保护接收端"和"保护网络路径"这两个独立目标 |
| **Repair Strategy** | rwnd/cwnd双窗口对比表（保护对象/调节方/反馈信号/典型值）+ 发送窗口=min(rwnd,cwnd)公式推导 + 两种窗口独立变化的场景分析 |
| **Verification Questions** | 1. 当rwnd=8KB且cwnd=4KB时，发送方最多能发送多少未确认数据？为什么？ 2. 如果网络不拥塞但接收方处理很慢，哪个窗口会成为瓶颈？ |
| **Prerequisites** | 无 |

---

### acu_029: slow_start_exponential_growth

| 字段 | 内容 |
|---|---|
| **ACU ID** | slow_start_exponential_growth |
| **Label** | 掌握慢启动阶段cwnd的指数增长规律 |
| **Definition** | 慢启动阶段每收到一个ACK就将cwnd增加1个MSS，由于每个RTT内所有已发送段都会被确认，cwnd实际按RTT翻倍（指数增长：1→2→4→8...），直到达到ssthresh阈值后切换为拥塞避免的线性增长 |
| **Misconceptions** | mc_007 |
| **Error Model** | 学生将"慢启动"字面理解为"缓慢线性增长"，计算cwnd变化时使用+1/RTT而非×2/RTT，导致对TCP启动阶段带宽利用效率的严重低估 |
| **Repair Strategy** | cwnd增长曲线数值计算练习（逐RTT列出cwnd值）+ 慢启动vs拥塞避免增长率对比图（指数vs线性） |
| **Verification Questions** | 1. 初始cwnd=1MSS，经过4个RTT后慢启动阶段的cwnd是多少？ 2. "慢启动"这个名称中的"慢"是相对于什么而言的？ |
| **Prerequisites** | acu_028 |

---

### kp_017 DNS协议（4 个 ACU）

---

### acu_034: dns_recursive_vs_iterative_query

| 字段 | 内容 |
|---|---|
| **ACU ID** | dns_recursive_vs_iterative_query |
| **Label** | 区分DNS递归查询与迭代查询的流程差异 |
| **Definition** | 递归查询中客户端只向本地DNS服务器发出一次请求，由本地DNS负责逐级查询并返回最终结果；迭代查询中本地DNS逐级询问根/TLD/权威服务器，每级只返回下一步应查询的服务器地址 |
| **Misconceptions** | mc_005 |
| **Error Model** | 学生将递归和迭代混为一谈，认为客户端需要自己逐级查询所有DNS服务器，或认为所有查询都由单一服务器完成 |
| **Repair Strategy** | 递归vs迭代查询流程对比图（递归：客户端→本地DNS→全程代理；迭代：本地DNS→根→TLD→权威逐级返回referral）+ 查询路径追踪练习 |
| **Verification Questions** | 1. 在递归查询模式下，客户端总共需要发出几次DNS请求？ 2. 迭代查询中，根DNS服务器收到查询后返回的是最终IP还是下一级服务器地址？ |
| **Prerequisites** | 无 |

---

### acu_035: cdn_beyond_dns_resolution

| 字段 | 内容 |
|---|---|
| **ACU ID** | cdn_beyond_dns_resolution |
| **Label** | 理解CDN的完整能力远超DNS解析调度 |
| **Definition** | CDN是覆盖全球边缘节点的分布式内容分发网络，虽然利用DNS做节点调度，但其核心能力还包括：边缘缓存、负载均衡、动态加速、DDoS防护、边缘计算等，DNS只是CDN调度的入口之一 |
| **Misconceptions** | mc_038 |
| **Error Model** | 学生将CDN简化为"一种DNS解析服务"，认为CDN只是把域名解析到最近的IP，不理解CDN边缘节点实际承担的缓存、计算和安全功能 |
| **Repair Strategy** | CDN完整能力架构图（DNS调度→边缘缓存→负载均衡→动态加速→安全防护→边缘计算）+ CDN vs 纯DNS服务功能对比表 |
| **Verification Questions** | 1. 如果CDN只是DNS服务，那它如何做到减少源站带宽压力？ 2. 请列举CDN除DNS调度外的至少3个核心能力。 |
| **Prerequisites** | acu_034 |

---

### acu_036: dns_ttl_cache_expiration

| 字段 | 内容 |
|---|---|
| **ACU ID** | dns_ttl_cache_expiration |
| **Label** | 理解DNS记录的TTL机制与缓存过期刷新 |
| **Definition** | 每条DNS记录都携带TTL（Time To Live）值，缓存服务器在TTL过期前直接返回缓存结果，TTL到期后必须重新向权威服务器查询；TTL过短增加查询负载，过长导致记录变更后传播延迟 |
| **Misconceptions** | mc_046 |
| **Error Model** | 学生认为DNS解析结果一旦获取就永久有效，不理解为什么域名变更后需要等待一段时间才能在所有地方生效 |
| **Repair Strategy** | DNS TTL缓存过期仿真（设定TTL=300s，展示缓存命中→过期→重新查询的完整周期）+ TTL设置策略分析（权衡响应速度与更新速度） |
| **Verification Questions** | 1. 一条TTL=3600的A记录被缓存后，如果源站在第1800秒修改了IP，客户端最长还要等多久才能获得新IP？ 2. 为什么DNS运维在计划迁移服务器前通常会先降低TTL？ |
| **Prerequisites** | acu_034 |

---

### acu_037: dns_security_poisoning_dnssec

| 字段 | 内容 |
|---|---|
| **ACU ID** | dns_security_poisoning_dnssec |
| **Label** | 理解DNS污染威胁与DNSSEC防护机制 |
| **Definition** | DNS协议本身无认证机制，攻击者可通过伪造响应（缓存投毒）或中间人篡改将用户引导到恶意IP；DNSSEC通过数字签名链（从根到权威）验证响应的真实性和完整性，但不提供加密 |
| **Misconceptions** | mc_047 |
| **Error Model** | 学生认为DNS天然可信，查询返回的结果一定是权威服务器的正确回答，不了解DNS响应可被篡改的攻击面 |
| **Repair Strategy** | DNS缓存投毒攻击流程图解（攻击者抢先响应→缓存被污染→后续查询返回恶意IP）+ DNSSEC签名验证链讲解（根签名→TLD签名→权威签名） |
| **Verification Questions** | 1. DNS缓存投毒攻击成功后，受影响的是哪一台DNS服务器？影响范围有多大？ 2. DNSSEC能否防止他人窃听DNS查询内容？为什么？ |
| **Prerequisites** | acu_034 |

---

### kp_018 HTTP与HTTPS（6 个 ACU）

---

### acu_038: http_requires_transport_layer

| 字段 | 内容 |
|---|---|
| **ACU ID** | http_requires_transport_layer |
| **Label** | 理解HTTP必须依赖传输层协议而非直接运行在IP上 |
| **Definition** | HTTP是应用层协议，需要传输层提供可靠字节流（TCP）或有序数据报（QUIC）服务，不能直接运行在网络层IP之上，因为IP只提供尽力而为的无连接数据报转发，无法保证有序完整交付 |
| **Misconceptions** | mc_003 |
| **Error Model** | 学生认为HTTP直接封装在IP数据报中发送，跳过了传输层，混淆了协议栈的层次依赖关系 |
| **Repair Strategy** | 协议栈层次依赖关系仿真（HTTP→TCP/QUIC→IP→链路层逐层封装动画）+ "去掉传输层后HTTP面临的问题"分析（无序、丢失、无端口复用） |
| **Verification Questions** | 1. 如果HTTP直接运行在IP上，它将面临哪些传输层本应解决的问题？ 2. HTTP/3使用QUIC而非TCP，QUIC本身属于哪一层？为什么HTTP仍然不能跳过传输层？ |
| **Prerequisites** | 无 |

---

### acu_039: http_status_code_categories

| 字段 | 内容 |
|---|---|
| **ACU ID** | http_status_code_categories |
| **Label** | 掌握HTTP状态码1xx-5xx五类分类语义 |
| **Definition** | HTTP状态码按首位数字分为五类：1xx信息性（请求已接收继续处理）、2xx成功、3xx重定向（需进一步操作）、4xx客户端错误（请求有误）、5xx服务器错误（服务端处理失败），每类指向不同的责任方和处理逻辑 |
| **Misconceptions** | mc_014 |
| **Error Model** | 学生无法区分4xx和5xx的责任归属，典型表现为认为"404表示服务器宕机"，混淆了"资源不存在（客户端请求了错误URL）"和"服务器内部故障" |
| **Repair Strategy** | HTTP状态码五类分类对比表（类别/含义/典型代码/责任方）+ 常见状态码场景判断练习（200/301/404/500/503） |
| **Verification Questions** | 1. 404和503都意味着用户无法获取内容，两者的根本区别是什么？ 2. 收到301状态码时，客户端应该执行什么操作？ |
| **Prerequisites** | 无 |

---

### acu_040: web_cache_hierarchy

| 字段 | 内容 |
|---|---|
| **ACU ID** | web_cache_hierarchy |
| **Label** | 理解Web缓存的多层架构而非仅浏览器缓存 |
| **Definition** | Web缓存存在于多个层次：浏览器本地缓存→企业/ISP代理缓存→CDN边缘缓存→源站缓存（如Redis），请求逐层查找，任一层命中即可返回，Cache-Control和ETag等头部协调各层缓存行为 |
| **Misconceptions** | mc_022 |
| **Error Model** | 学生认为缓存只存在于浏览器中，清除浏览器缓存即可获得最新内容，不理解代理/CDN/源站各层都可能返回过期内容 |
| **Repair Strategy** | Web缓存多层架构图（浏览器→代理→CDN→源站逐层命中/穿透流程）+ Cache-Control指令效果分析（no-cache/no-store/max-age对各层的影响） |
| **Verification Questions** | 1. 用户清除了浏览器缓存后仍获得旧内容，可能是哪一层的缓存在起作用？ 2. Cache-Control: no-store 和 no-cache 的区别是什么？ |
| **Prerequisites** | acu_039 |

---

### acu_041: http2_tls_optional_in_spec

| 字段 | 内容 |
|---|---|
| **ACU ID** | http2_tls_optional_in_spec |
| **Label** | 理解HTTP/2规范中TLS非强制但浏览器要求 |
| **Definition** | RFC 7540定义了两种HTTP/2标识：h2（基于TLS/ALPN）和h2c（明文TCP上的HTTP/2），规范层面TLS非强制；但所有主流浏览器仅实现h2（即要求HTTPS），导致实际部署中HTTP/2几乎总是搭配TLS |
| **Misconceptions** | mc_035 |
| **Error Model** | 学生认为HTTP/2协议本身强制要求TLS加密，不知道h2c明文模式的存在，混淆了"协议规范"与"浏览器实现策略" |
| **Repair Strategy** | HTTP/2规范(h2 vs h2c)与浏览器实现差异分析表 + gRPC使用h2c的实例说明（证明非浏览器场景可不用TLS） |
| **Verification Questions** | 1. 后端微服务之间使用HTTP/2通信时，是否必须配置TLS证书？为什么？ 2. h2和h2c分别代表什么？浏览器支持哪一种？ |
| **Prerequisites** | acu_042 |

---

### acu_042: http11_persistent_connection

| 字段 | 内容 |
|---|---|
| **ACU ID** | http11_persistent_connection |
| **Label** | 理解HTTP/1.1默认Keep-Alive持久连接 |
| **Definition** | HTTP/1.1默认启用持久连接（Connection: keep-alive），同一TCP连接可依次传输多个请求/响应对，避免每次请求都经历三次握手和慢启动的开销；只有显式设置Connection: close时才会在响应后关闭连接 |
| **Misconceptions** | mc_036 |
| **Error Model** | 学生认为HTTP/1.1像HTTP/1.0一样每个请求都新建TCP连接，严重高估了HTTP/1.1的连接开销，也无法理解管线化等优化的基础 |
| **Repair Strategy** | HTTP/1.0短连接vs HTTP/1.1持久连接时序对比仿真（展示同一TCP连接上多个请求/响应的串行传输）+ Keep-Alive头部解析练习 |
| **Verification Questions** | 1. HTTP/1.1客户端想要在请求后立即关闭TCP连接，需要设置什么头部？ 2. 持久连接相比短连接节省了哪些网络开销？请至少说出两点。 |
| **Prerequisites** | acu_038 |

---

### acu_043: cookie_server_set_mechanism

| 字段 | 内容 |
|---|---|
| **ACU ID** | cookie_server_set_mechanism |
| **Label** | 理解Cookie可由服务端Set-Cookie头设置 |
| **Definition** | Cookie最主要的设置方式是服务器在HTTP响应中通过Set-Cookie头下发给浏览器，浏览器自动在后续请求中携带；设置HttpOnly属性的Cookie无法被JavaScript读取或修改，是防范XSS窃取会话的关键手段 |
| **Misconceptions** | mc_037 |
| **Error Model** | 学生认为Cookie只能由客户端JavaScript通过document.cookie设置，不了解服务端Set-Cookie头的存在，也无法解释HttpOnly Cookie的安全意义 |
| **Repair Strategy** | Set-Cookie响应头vs JavaScript设置Cookie对比表（设置方式/作用域/安全属性/XSS防护能力）+ HttpOnly Cookie安全场景分析 |
| **Verification Questions** | 1. 一个设置了HttpOnly属性的Cookie，前端JavaScript能否通过document.cookie读取它？ 2. 为什么说Session ID应该使用Set-Cookie而非JavaScript来设置？ |
| **Prerequisites** | 无 |

---

### kp_008 IP地址与子网划分（6 个 ACU）

---

### acu_009: ip_fragmentation_layer_responsibility

| 字段 | 内容 |
|---|---|
| **ACU ID** | ip_fragmentation_layer_responsibility |
| **Label** | 理解IP分片是网络层而非TCP的职责 |
| **Definition** | 当IP数据报超过链路MTU时，由网络层（IP协议）负责将其分片，并在目的主机的网络层完成重组；TCP工作在传输层，负责的是字节流分段（MSS），两者是不同层次的不同机制 |
| **Misconceptions** | mc_008 |
| **Error Model** | 学生认为TCP负责处理数据包过大的问题（包括分片和重组），混淆了网络层IP分片与传输层TCP分段的职责边界 |
| **Repair Strategy** | IP分片（网络层/基于MTU）vs TCP分段（传输层/基于MSS）职责对比仿真 + 分片重组过程动画（展示分片在目的端网络层重组后才交给传输层） |
| **Verification Questions** | 1. 一个4000字节的IP数据报经过MTU=1500的链路时，谁负责分片？在哪里重组？ 2. TCP的MSS和IP的MTU之间的数值关系是什么？ |
| **Prerequisites** | acu_001, acu_007 |

---

### acu_010: subnet_prefix_host_bits_calculation

| 字段 | 内容 |
|---|---|
| **ACU ID** | subnet_prefix_host_bits_calculation |
| **Label** | 掌握子网前缀长度与主机位数的计算 |
| **Definition** | /N表示前N位是网络前缀，剩余(32-N)位是主机位，可用主机地址数=2^(32-N)-2（减去网络地址和广播地址）；例如/24表示24位前缀、8位主机位、254个可用地址 |
| **Misconceptions** | mc_009 |
| **Error Model** | 学生将/24中的24直接理解为"24个主机地址"，不理解前缀长度表示的是网络位数，导致子网划分计算全面错误 |
| **Repair Strategy** | 前缀长度→主机位→可用地址数计算练习（/24→8位→254台, /28→4位→14台, /30→2位→2台）+ 子网掩码二进制展开对照 |
| **Verification Questions** | 1. 一个/28的子网最多能容纳多少台主机？请写出计算过程。 2. 为什么可用主机数要减2？这两个被减去的地址分别是什么？ |
| **Prerequisites** | 无 |

---

### acu_011: dhcp_full_configuration_scope

| 字段 | 内容 |
|---|---|
| **ACU ID** | dhcp_full_configuration_scope |
| **Label** | 理解DHCP提供的完整网络配置范围 |
| **Definition** | DHCP除分配IP地址外，还通过选项字段（Options）提供子网掩码、默认网关、DNS服务器地址、域名、租期（Lease Time）、NTP服务器等完整网络配置，是主机自动化配置的核心协议 |
| **Misconceptions** | mc_023 |
| **Error Model** | 学生将DHCP功能简化为"自动分配IP地址"，不知道DHCP同时配置了网关、DNS等关键参数，无法理解"DHCP出错导致无法上网但有IP"的故障场景 |
| **Repair Strategy** | DHCP Offer报文选项字段完整解析（列出Option 1/3/6/51等含义）+ "DHCP只给了IP但没给网关"的故障场景分析 |
| **Verification Questions** | 1. 主机通过DHCP获得了IP地址但无法访问外网，最可能是DHCP缺少了哪项配置？ 2. DHCP的"租期"是什么意思？租期到期后会发生什么？ |
| **Prerequisites** | 无 |

---

### acu_012: ipv6_comprehensive_improvements

| 字段 | 内容 |
|---|---|
| **ACU ID** | ipv6_comprehensive_improvements |
| **Label** | 理解IPv6相对IPv4的全面改进特性 |
| **Definition** | IPv6不仅将地址从32位扩展到128位，还简化了头部结构（固定40字节/取消校验和/取消分片字段移入扩展头）、引入NDP替代ARP/DHCP部分功能、支持扩展头链式处理、内置IPsec支持 |
| **Misconceptions** | mc_032 |
| **Error Model** | 学生认为IPv6唯一的改进就是"地址变长了"（从4字节到16字节），忽略了头部简化、协议架构重设计、邻居发现等重要改进 |
| **Repair Strategy** | IPv4 vs IPv6头部结构对比表（字段数量/长度/校验和/分片处理）+ IPv6新增特性清单讲解（NDP/扩展头/Flow Label/地址自动配置） |
| **Verification Questions** | 1. IPv6取消了IPv4头部中的哪些字段？这样做的好处是什么？ 2. IPv6中取代ARP功能的是什么协议？它属于哪一层？ |
| **Prerequisites** | 无 |

---

### acu_013: ipv6_subnet_prefix_mechanism

| 字段 | 内容 |
|---|---|
| **ACU ID** | ipv6_subnet_prefix_mechanism |
| **Label** | 理解IPv6的前缀子网划分机制 |
| **Definition** | IPv6仍然使用前缀长度进行子网划分，标准分配为/64子网（前64位为网络前缀、后64位为接口ID），组织通常获得/48前缀后自行划分为多个/64子网；128位地址空间不意味着不需要子网划分 |
| **Misconceptions** | mc_033 |
| **Error Model** | 学生认为IPv6地址空间足够大因此不需要子网划分，忽略了网络管理、路由聚合、安全隔离等划分子网的现实需求 |
| **Repair Strategy** | IPv4子网(/24)与IPv6子网(/64)对比表（前缀长度/接口位/划分目的）+ 组织从ISP获得/48后划分/64子网的实例讲解 |
| **Verification Questions** | 1. 一个获得了/48前缀的组织，最多可以划分出多少个标准/64子网？ 2. 即使IPv6地址"用不完"，为什么仍然需要子网划分？ |
| **Prerequisites** | acu_010, acu_012 |

---

### acu_014: cidr_applicability_both_ip_versions

| 字段 | 内容 |
|---|---|
| **ACU ID** | cidr_applicability_both_ip_versions |
| **Label** | 理解CIDR同时适用于IPv4和IPv6 |
| **Definition** | CIDR（无类域间路由）于1993年为解决IPv4地址耗尽和路由表膨胀而设计，使用任意长度前缀替代传统A/B/C类划分；IPv6从诞生起就采用CIDR表示法（如2001:db8::/32），CIDR是双栈通用的寻址方案 |
| **Misconceptions** | mc_034 |
| **Error Model** | 学生认为CIDR是IPv6专属技术，不知道CIDR最初是为IPv4设计的，也不了解CIDR如何解决了分类寻址的地址浪费问题 |
| **Repair Strategy** | CIDR历史演进讲解（分类寻址的浪费→1993年CIDR引入→IPv4/IPv6通用）+ 分类寻址vs CIDR对比表（地址利用率/路由聚合能力） |
| **Verification Questions** | 1. CIDR最初是为了解决什么问题而被引入的？它是IPv4还是IPv6时代的产物？ 2. 为什么说192.168.1.0/26比传统C类地址更灵活？ |
| **Prerequisites** | acu_010 |

---

### kp_010 路由选择协议（2 个 ACU）

---

### acu_016: bgp_exterior_gateway_classification

| 字段 | 内容 |
|---|---|
| **ACU ID** | bgp_exterior_gateway_classification |
| **Label** | 理解BGP作为外部网关协议的定位 |
| **Definition** | BGP（Border Gateway Protocol）是唯一广泛部署的域间路由协议（EGP），负责在自治系统（AS）之间交换路由可达性信息，其决策基于路径属性和策略而非最短路径；OSPF/RIP/IS-IS属于域内协议（IGP） |
| **Misconceptions** | mc_029 |
| **Error Model** | 学生将BGP归类为IGP（内部网关协议），与OSPF/RIP混淆，不理解域间路由（AS之间）与域内路由（AS内部）的本质区别 |
| **Repair Strategy** | IGP/EGP协议分类对比表（作用范围/代表协议/选路依据/部署位置）+ AS拓扑图中BGP与OSPF各自覆盖范围的可视化 |
| **Verification Questions** | 1. 中国电信和中国联通之间的路由信息交换使用的是什么协议？为什么不能用OSPF？ 2. BGP选路时考虑的因素与OSPF有何本质不同？ |
| **Prerequisites** | 无 |

---

### acu_017: ospf_vs_rip_metric_and_scalability

| 字段 | 内容 |
|---|---|
| **ACU ID** | ospf_vs_rip_metric_and_scalability |
| **Label** | 区分OSPF链路代价与RIP跳数及其适用规模 |
| **Definition** | OSPF使用链路状态算法，度量标准为链路代价（cost，通常=参考带宽/链路带宽），支持大规模网络和区域划分；RIP使用距离向量算法，以跳数为度量（最大15跳），收敛慢、适合小型网络 |
| **Misconceptions** | mc_030, mc_031 |
| **Error Model** | 学生认为OSPF也按跳数选路（混淆OSPF与RIP的度量标准），或认为RIP适用于大型互联网核心网（忽略15跳限制和收敛问题） |
| **Repair Strategy** | OSPF vs RIP特性对比表（算法类型/度量标准/最大规模/收敛速度/区域支持）+ 链路代价计算练习（给定带宽算cost） |
| **Verification Questions** | 1. 一条100Mbps链路和一条10Gbps链路，OSPF分别赋予多少代价？（参考带宽=100Gbps） 2. 为什么RIP不适合大型网络？请从跳数限制和收敛速度两方面说明。 |
| **Prerequisites** | 无 |

---

## 第二批：基础概念 ACU（OSI / 链路层 / 局域网 / 安全 / 应用层）

### kp_002 OSI七层模型（1 个 ACU）

---

### acu_001: osi_tcpip_model_mapping

| 字段 | 内容 |
|---|---|
| **ACU ID** | osi_tcpip_model_mapping |
| **Label** | 理解OSI与TCP/IP分层映射关系 |
| **Definition** | OSI是7层参考模型（物理/数据链路/网络/传输/会话/表示/应用），TCP/IP是4层实用模型（网络接口/网际/传输/应用）；两者非一一对应——OSI的会话/表示/应用三层对应TCP/IP的单一应用层，OSI的物理/数据链路对应TCP/IP的网络接口层 |
| **Misconceptions** | mc_025 |
| **Error Model** | 学生试图将OSI每一层严格映射到TCP/IP的一层，产生"TCP/IP有7层"或"OSI会话层=TCP/IP某层"的错误理解 |
| **Repair Strategy** | OSI七层与TCP/IP四层对照表（逐层映射关系+不对应层的合并说明）+ 模型映射填空练习 |
| **Verification Questions** | 1. OSI的会话层、表示层在TCP/IP模型中对应哪一层？为什么TCP/IP不单独设这两层？ 2. TCP/IP的"网络接口层"对应OSI的哪些层？ |
| **Prerequisites** | 无 |

---

### kp_003 TCP/IP体系结构（1 个 ACU）

---

### acu_002: port_vs_ip_host_identification

| 字段 | 内容 |
|---|---|
| **ACU ID** | port_vs_ip_host_identification |
| **Label** | 区分IP标识主机与端口标识进程 |
| **Definition** | 在TCP/IP体系中，IP地址标识网络中的主机（或接口），端口号标识主机上的某个应用进程；二者构成寻址层次——先通过IP路由到主机，再通过端口号分用到具体进程 |
| **Misconceptions** | mc_019 |
| **Error Model** | 学生认为端口号用于标识网络中的不同主机，混淆了网络层寻址（IP→主机）与传输层复用/分用（端口→进程）的职责分工 |
| **Repair Strategy** | IP标识主机 vs 端口标识进程分层寻址对比表 + 多进程共享同一主机IP的实例分析（Web服务:80 + SSH:22 在同一IP） |
| **Verification Questions** | 1. 同一台服务器上运行的Web服务和SSH服务，靠什么来区分发往它们的数据包？ 2. 不同主机上可以使用相同的端口号吗？为什么？ |
| **Prerequisites** | acu_001 |

---

### kp_006 局域网技术（4 个 ACU）

---

### acu_003: switch_mac_vs_router_ip_forwarding

| 字段 | 内容 |
|---|---|
| **ACU ID** | switch_mac_vs_router_ip_forwarding |
| **Label** | 区分交换机MAC转发与路由器IP转发 |
| **Definition** | 二层交换机根据帧的目的MAC地址查找MAC地址表进行端口转发，工作在数据链路层；路由器根据IP数据报的目的IP地址查找路由表进行下一跳转发，工作在网络层；两者的查找对象和工作层次不同 |
| **Misconceptions** | mc_017 |
| **Error Model** | 学生认为交换机也根据IP地址转发数据帧，混淆了二层转发（MAC）和三层转发（IP）的工作机制 |
| **Repair Strategy** | 交换机MAC转发vs路由器IP转发仿真（同一数据包在交换机和路由器中的处理流程对比）+ 转发依据/查找表/工作层次对比表 |
| **Verification Questions** | 1. 交换机收到一个帧后，查看的是帧中哪个字段来决定从哪个端口转发？ 2. 如果目的主机在不同子网，仅靠交换机能否完成数据转发？为什么？ |
| **Prerequisites** | 无 |

---

### acu_004: ethernet_frame_vs_mtu_definition

| 字段 | 内容 |
|---|---|
| **ACU ID** | ethernet_frame_vs_mtu_definition |
| **Label** | 区分以太网帧长度与MTU载荷上限 |
| **Definition** | 以太网帧的最大长度=头部(14B)+载荷(≤1500B)+FCS(4B)=1518B；MTU（Maximum Transmission Unit）指的是帧载荷部分的上限（通常1500B），而非整个帧的总长度 |
| **Misconceptions** | mc_026 |
| **Error Model** | 学生将"以太网帧最大长度"直接等同于"MTU=1518字节"，混淆了帧总长度与帧载荷上限的概念 |
| **Repair Strategy** | 以太网帧结构图解（前导码/目的MAC/源MAC/类型/载荷/FCS各部分字节数标注）+ 帧总长度 vs MTU（载荷上限）定义对比表 |
| **Verification Questions** | 1. 以太网MTU=1500字节，指的是帧的哪个部分的长度上限？ 2. 一个IP数据报为1500字节时，封装成以太网帧后实际在链路上传输的总字节数是多少？ |
| **Prerequisites** | 无 |

---

### acu_005: csma_cd_obsolescence_in_switched_lan

| 字段 | 内容 |
|---|---|
| **ACU ID** | csma_cd_obsolescence_in_switched_lan |
| **Label** | 理解全双工交换网络中CSMA/CD已被淘汰 |
| **Definition** | CSMA/CD是早期共享式以太网（集线器/总线拓扑）的冲突检测机制；现代交换式以太网中每个端口独立冲突域+全双工通信，不存在冲突，CSMA/CD已无实际作用 |
| **Misconceptions** | mc_027 |
| **Error Model** | 学生认为只要是以太网就必须使用CSMA/CD，不了解从共享介质（集线器）到交换机+全双工的技术演进已消除了冲突 |
| **Repair Strategy** | 以太网演进历史讲解（共享总线→集线器→交换机→全双工）+ "全双工为什么不冲突"的原理分析（独立收发通道） |
| **Verification Questions** | 1. 为什么连接到交换机的全双工以太网端口不需要CSMA/CD？ 2. 在什么条件下CSMA/CD仍然有效？（提示：半双工集线器环境） |
| **Prerequisites** | 无 |

---

### acu_006: vlan_tagging_at_switch_layer

| 字段 | 内容 |
|---|---|
| **ACU ID** | vlan_tagging_at_switch_layer |
| **Label** | 理解VLAN标签在交换机层的插入与剥离 |
| **Definition** | 802.1Q VLAN标签（4字节，含VLAN ID）由交换机在帧进入Trunk端口时插入、离开Trunk端口到达终端时剥离；交换机根据端口PVID或帧中已有的标签决定帧属于哪个VLAN，整个过程在数据链路层完成 |
| **Misconceptions** | mc_028 |
| **Error Model** | 学生认为VLAN标签是由路由器添加的（混淆了二层VLAN与三层路由的职责），不理解VLAN是交换机端口级别的隔离机制 |
| **Repair Strategy** | 802.1Q VLAN标签在交换机端口的插入/剥离仿真（Access端口添加标签→Trunk端口携带标签转发→目的Access端口剥离标签）+ 交换机VLAN配置场景练习 |
| **Verification Questions** | 1. 一个帧从PC进入交换机的Access端口时，交换机做了什么操作？ 2. 路由器在VLAN间通信中扮演什么角色？它负责添加VLAN标签吗？ |
| **Prerequisites** | acu_003 |

---

### kp_007 网络层基本概念（2 个 ACU）

---

### acu_007: mtu_size_tradeoff

| 字段 | 内容 |
|---|---|
| **ACU ID** | mtu_size_tradeoff |
| **Label** | 理解MTU大小与分片代价的权衡 |
| **Definition** | MTU并非越大越好：过大的包在经过低MTU链路时需要分片（增加开销和丢包概率），过小的包增加头部占比（降低有效载荷率）；路径MTU发现（PMTUD）通过设置DF位探测路径最小MTU来避免分片 |
| **Misconceptions** | mc_018 |
| **Error Model** | 学生认为MTU越大传输效率一定越高，忽略了路径中最小MTU的瓶颈效应和分片重组的代价（单个分片丢失导致整个原始包重传） |
| **Repair Strategy** | 路径MTU发现机制讲解（DF位设置→ICMP需要分片消息→调整包大小）+ 大包分片代价分析（分片丢失→整包重传的放大效应） |
| **Verification Questions** | 1. 发送一个4000字节的包经过MTU=1500的链路，如果其中一个分片丢失会发生什么？ 2. 路径MTU发现是如何避免中间路由器分片的？ |
| **Prerequisites** | acu_004 |

---

### acu_008: icmp_network_layer_classification

| 字段 | 内容 |
|---|---|
| **ACU ID** | icmp_network_layer_classification |
| **Label** | 理解ICMP属于网络层而非传输层 |
| **Definition** | ICMP（Internet Control Message Protocol）是网络层的控制和差错报告协议，虽然ICMP报文封装在IP数据报的数据部分，但它服务于网络层（报告不可达、超时、重定向等），不为应用提供端到端传输服务 |
| **Misconceptions** | mc_024 |
| **Error Model** | 学生因为ICMP"封装在IP里"或"有类似端口的类型字段"而将其归类为传输层协议，混淆了"被IP承载"与"属于传输层"的概念 |
| **Repair Strategy** | ICMP在协议栈中的封装关系仿真（IP头→ICMP头→ICMP数据，但功能服务于网络层）+ 网络层协议族归类表（IP/ICMP/IGMP/ARP） |
| **Verification Questions** | 1. ping命令使用ICMP协议，ICMP属于哪一层？为什么它不算传输层协议？ 2. ICMP报文是直接封装在以太网帧中还是封装在IP数据报中？ |
| **Prerequisites** | acu_001 |

---

### kp_009 ARP协议（1 个 ACU）

---

### acu_015: arp_ip_to_mac_resolution

| 字段 | 内容 |
|---|---|
| **ACU ID** | arp_ip_to_mac_resolution |
| **Label** | 区分ARP的IP到MAC解析与DNS的域名解析 |
| **Definition** | ARP在同一链路内将已知的目的IP地址解析为对应的MAC地址（网络层→链路层地址映射），通过广播请求/单播回复实现；DNS将域名解析为IP地址（应用层→网络层地址映射）——两者解析的对象和工作层次完全不同 |
| **Misconceptions** | mc_010 |
| **Error Model** | 学生将ARP与DNS混淆，认为ARP的功能是"把域名解析成地址"，不理解ARP工作在链路层只解决同一广播域内的IP→MAC映射 |
| **Repair Strategy** | ARP(IP→MAC/链路层/广播域内) vs DNS(域名→IP/应用层/全网)功能对比表 + ARP广播请求-单播回复过程仿真 |
| **Verification Questions** | 1. 主机A要发送数据给同一子网内的主机B，已知B的IP但不知道B的MAC，使用什么协议？该协议的请求报文如何寻址？ 2. ARP和DNS都是"解析"协议，它们各自解析的是什么到什么？ |
| **Prerequisites** | 无 |

---

### kp_012 UDP协议（1 个 ACU）

---

### acu_018: udp_practical_use_cases

| 字段 | 内容 |
|---|---|
| **ACU ID** | udp_practical_use_cases |
| **Label** | 理解UDP在实际场景中的应用价值 |
| **Definition** | UDP虽然不提供可靠传输保证，但其无连接、低开销、无拥塞控制的特性使其成为特定场景的最佳选择：DNS查询（快速单次问答）、实时音视频（容忍丢包不容忍延迟）、QUIC底层传输、多播/广播、游戏状态同步等 |
| **Misconceptions** | mc_004 |
| **Error Model** | 学生将"不可靠"等同于"没有用"，不理解很多场景下低延迟比完整性更重要，或应用层可以自行实现所需的可靠性子集 |
| **Repair Strategy** | UDP适用场景分析表（DNS/QUIC/音视频/游戏/IoT各场景为何选UDP）+ "应用层自定义可靠性"设计思路讲解（如QUIC在UDP上实现重传） |
| **Verification Questions** | 1. DNS为什么选择UDP而非TCP作为默认传输协议？在什么情况下DNS会切换到TCP？ 2. QUIC基于UDP构建，是否意味着QUIC也是不可靠的？为什么？ |
| **Prerequisites** | 无 |

---

### kp_016 应用层基本概念（4 个 ACU）

---

### acu_030: forward_vs_reverse_proxy

| 字段 | 内容 |
|---|---|
| **ACU ID** | forward_vs_reverse_proxy |
| **Label** | 区分正向代理与反向代理的方向与角色 |
| **Definition** | 正向代理代表客户端向服务器发起请求（客户端知道代理存在，服务器不知道真实客户端）；反向代理代表服务器接收客户端请求（客户端不知道代理存在，以为直接访问了服务器），典型场景分别为翻墙/缓存和负载均衡/安全 |
| **Misconceptions** | mc_041 |
| **Error Model** | 学生将正向代理和反向代理视为同一概念，不理解"代表谁"的方向性差异，无法区分VPN（正向）和Nginx负载均衡（反向）的架构差异 |
| **Repair Strategy** | 正向代理(代客户端)vs反向代理(代服务端)方向对比表（代表方/部署位置/对谁透明/典型场景）+ 网络拓扑图对比 |
| **Verification Questions** | 1. Nginx作为反向代理部署在服务端前面，客户端是否知道Nginx的存在？ 2. 企业出口处部署代理服务器供员工上网，这属于正向代理还是反向代理？为什么？ |
| **Prerequisites** | 无 |

---

### acu_031: ftp_dual_port_mechanism

| 字段 | 内容 |
|---|---|
| **ACU ID** | ftp_dual_port_mechanism |
| **Label** | 理解FTP控制连接与数据连接的双端口设计 |
| **Definition** | FTP使用分离的控制连接（端口21，持久，传输命令/响应）和数据连接（端口20或随机端口，按需建立，传输文件内容），主动模式由服务器发起数据连接，被动模式由客户端发起 |
| **Misconceptions** | mc_048 |
| **Error Model** | 学生认为FTP像HTTP一样只使用单一端口（21）完成所有通信，不理解命令通道和数据通道分离的设计以及主动/被动模式的区别 |
| **Repair Strategy** | FTP控制连接(21)vs数据连接(20/随机)双端口对比表 + 主动模式vs被动模式连接建立时序图 |
| **Verification Questions** | 1. FTP传输一个大文件时，控制连接和数据连接分别承担什么角色？ 2. 为什么在有防火墙的环境下通常需要使用FTP被动模式？ |
| **Prerequisites** | 无 |

---

### acu_032: smtp_relay_routing

| 字段 | 内容 |
|---|---|
| **ACU ID** | smtp_relay_routing |
| **Label** | 理解SMTP邮件经中继服务器路由的流程 |
| **Definition** | 发送邮件时客户端先通过SMTP将邮件提交到发件人的邮件服务器，发件服务器查询收件人域的MX记录，再通过SMTP中继将邮件路由到收件人的邮件服务器，最后收件人通过POP3/IMAP取信——不是客户端直连收件服务器 |
| **Misconceptions** | mc_049 |
| **Error Model** | 学生认为发件人客户端直接将邮件投递到收件人的邮箱服务器，忽略了发件服务器中继和MX记录查询的路由过程 |
| **Repair Strategy** | SMTP邮件路由全流程仿真（客户端→发件MTA→DNS MX查询→收件MTA→收件人POP3/IMAP取信）+ 多跳中继路径图解 |
| **Verification Questions** | 1. 从alice@gmail.com发邮件给bob@qq.com，邮件经过哪些服务器？客户端直接连接QQ邮件服务器吗？ 2. MX记录在邮件路由中起什么作用？ |
| **Prerequisites** | 无 |

---

### acu_033: websocket_protocol_upgrade

| 字段 | 内容 |
|---|---|
| **ACU ID** | websocket_protocol_upgrade |
| **Label** | 理解WebSocket通过HTTP Upgrade建立独立协议 |
| **Definition** | WebSocket通过HTTP/1.1的Upgrade机制握手（101 Switching Protocols），握手完成后连接升级为独立的全双工协议，不再是HTTP——WebSocket有自己的帧格式、opcode和关闭流程，是独立于HTTP的应用层协议 |
| **Misconceptions** | mc_050 |
| **Error Model** | 学生认为WebSocket是HTTP的一个方法（类似GET/POST），或认为WebSocket数据始终封装在HTTP报文中传输，不理解协议升级后连接已脱离HTTP |
| **Repair Strategy** | WebSocket Upgrade握手过程仿真（HTTP请求→101响应→协议切换→独立帧传输）+ WebSocket帧格式与HTTP报文格式对比 |
| **Verification Questions** | 1. WebSocket连接建立后，后续数据传输还使用HTTP格式吗？ 2. WebSocket握手的HTTP响应状态码是什么？握手成功后Connection字段的值是什么？ |
| **Prerequisites** | 无 |

---

### kp_019 网络安全基础（4 个 ACU）

---

### acu_044: nat_breaks_end_to_end_transparency

| 字段 | 内容 |
|---|---|
| **ACU ID** | nat_breaks_end_to_end_transparency |
| **Label** | 理解NAT地址改写对端到端透明性的破坏 |
| **Definition** | NAT通过改写IP数据报的源/目的地址和端口实现私有地址到公有地址的映射，这破坏了IP层端到端透明性：外部主机无法主动连接内网主机、IPsec等协议受干扰、P2P应用需要NAT穿越技术 |
| **Misconceptions** | mc_011 |
| **Error Model** | 学生认为NAT是一种网络增强技术，提高了通信的透明性和安全性，不理解NAT本质上是对端到端原则的妥协（以牺牲可达性换取地址复用） |
| **Repair Strategy** | NAT地址改写过程对比分析（改写前/后数据包头部变化）+ NAT对端到端通信的影响清单（被动连接失效/应用层协议嵌入IP失效/IPsec冲突） |
| **Verification Questions** | 1. NAT环境下，外部服务器如何主动发起连接到内网的一台Web服务器？需要什么额外配置？ 2. 为什么说NAT"破坏了端到端透明性"？请举一个具体受影响的场景。 |
| **Prerequisites** | 无 |

---

### acu_045: tls_triple_protection

| 字段 | 内容 |
|---|---|
| **ACU ID** | tls_triple_protection |
| **Label** | 理解TLS同时提供机密性、完整性和认证 |
| **Definition** | TLS提供三重安全保护：机密性（对称加密防窃听）、完整性（MAC/AEAD防篡改）、身份认证（证书链验证防冒充）；三者缺一不可——仅加密无法防中间人，仅认证无法防窃听 |
| **Misconceptions** | mc_012 |
| **Error Model** | 学生将TLS简化为"加密协议"，只知道它防窃听，不知道TLS同时通过证书验证对方身份、通过MAC保证数据未被篡改 |
| **Repair Strategy** | TLS三重保护对应关系表（机密性↔对称加密/完整性↔HMAC或AEAD/认证↔X.509证书链）+ "只加密不认证"中间人攻击场景分析 |
| **Verification Questions** | 1. 如果TLS只提供加密而没有身份认证，会面临什么攻击？ 2. TLS中保证数据完整性的具体机制是什么？它与加密是同一回事吗？ |
| **Prerequisites** | 无 |

---

### acu_046: quic_transport_layer_over_udp

| 字段 | 内容 |
|---|---|
| **ACU ID** | quic_transport_layer_over_udp |
| **Label** | 理解QUIC是基于UDP的传输层协议而非HTTP别名 |
| **Definition** | QUIC是Google设计的传输层协议，运行在UDP之上，提供类TCP的可靠传输+多路复用+内置TLS 1.3加密+0-RTT连接恢复；HTTP/3运行在QUIC之上，QUIC本身不是HTTP的别名而是替代TCP的新型传输层 |
| **Misconceptions** | mc_013 |
| **Error Model** | 学生认为QUIC只是HTTP/3的另一个名字，属于应用层，不理解QUIC是一个完整的传输层协议栈，提供连接管理、可靠传输、拥塞控制等传输层功能 |
| **Repair Strategy** | QUIC在协议栈中的层次定位仿真（HTTP/3→QUIC→UDP→IP对比HTTP/2→TCP→IP）+ QUIC vs TCP功能对比表 |
| **Verification Questions** | 1. QUIC基于UDP意味着它也是不可靠的吗？QUIC自身提供了哪些TCP类似的功能？ 2. 画出HTTP/3的协议栈层次（从应用层到网络层），QUIC位于哪一层？ |
| **Prerequisites** | acu_018, acu_045 |

---

### acu_047: modern_firewall_deep_inspection

| 字段 | 内容 |
|---|---|
| **ACU ID** | modern_firewall_deep_inspection |
| **Label** | 理解现代防火墙超越IP/端口的深度检测能力 |
| **Definition** | 现代防火墙（NGFW）已从早期的包过滤（仅检查IP/端口）演进到状态检测（跟踪连接状态）、深度包检测DPI（解析应用层协议内容）、应用识别（识别具体应用而非仅端口）、用户身份关联等多维度检测 |
| **Misconceptions** | mc_040 |
| **Error Model** | 学生认为防火墙只能基于五元组（源/目的IP、源/目的端口、协议号）做简单的允许/拒绝，不了解现代防火墙可以识别应用类型、检测恶意内容、关联用户身份 |
| **Repair Strategy** | 防火墙演进历程讲解（包过滤→状态检测→应用层网关→NGFW）+ 传统包过滤vs现代NGFW能力对比表 |
| **Verification Questions** | 1. 某防火墙能识别并阻止通过443端口传输的BitTorrent流量，这属于什么级别的检测能力？仅凭端口号能做到吗？ 2. 状态检测防火墙与简单包过滤防火墙的核心区别是什么？ |
| **Prerequisites** | 无 |

---

### kp_020 综合应用与故障排查（1 个 ACU）

---

### acu_048: load_balancing_strategies_variety

| 字段 | 内容 |
|---|---|
| **ACU ID** | load_balancing_strategies_variety |
| **Label** | 理解负载均衡器支持多种调度策略 |
| **Definition** | 负载均衡器支持多种调度算法：轮询（Round Robin）、加权轮询、最少连接、加权最少连接、IP哈希、一致性哈希等；不同策略适用于不同场景（无状态服务适合轮询，有状态服务需要会话保持/哈希） |
| **Misconceptions** | mc_039 |
| **Error Model** | 学生认为负载均衡器只有简单的轮询一种策略，不了解实际部署中需要根据业务特性（有无状态、请求均匀性、后端性能差异）选择不同算法 |
| **Repair Strategy** | 多种负载均衡策略对比分析表（算法/适用场景/优缺点）+ 实际场景策略选型练习（电商订单=会话保持, 图片CDN=轮询, 异构集群=加权） |
| **Verification Questions** | 1. 一个电商网站需要保证同一用户的请求始终到达同一后端服务器，应选择什么负载均衡策略？ 2. 后端服务器性能不均（有的4核有的8核），简单轮询会产生什么问题？应改用什么策略？ |
| **Prerequisites** | acu_030 |

---

## 附录：前置依赖关系总览

| ACU ID | 依赖的前置 ACU |
|---|---|
| acu_001 | 无 |
| acu_002 | acu_001 |
| acu_003 | 无 |
| acu_004 | 无 |
| acu_005 | 无 |
| acu_006 | acu_003 |
| acu_007 | acu_004 |
| acu_008 | acu_001 |
| acu_009 | acu_001, acu_007 |
| acu_010 | 无 |
| acu_011 | 无 |
| acu_012 | 无 |
| acu_013 | acu_010, acu_012 |
| acu_014 | acu_010 |
| acu_015 | 无 |
| acu_016 | 无 |
| acu_017 | 无 |
| acu_018 | 无 |
| acu_019 | 无 |
| acu_020 | 无 |
| acu_021 | acu_020 |
| acu_022 | acu_002 |
| acu_023 | acu_019 |
| acu_024 | acu_019 |
| acu_025 | 无 |
| acu_026 | acu_025 |
| acu_027 | acu_025 |
| acu_028 | 无 |
| acu_029 | acu_028 |
| acu_030 | 无 |
| acu_031 | 无 |
| acu_032 | 无 |
| acu_033 | 无 |
| acu_034 | 无 |
| acu_035 | acu_034 |
| acu_036 | acu_034 |
| acu_037 | acu_034 |
| acu_038 | 无 |
| acu_039 | 无 |
| acu_040 | acu_039 |
| acu_041 | acu_042 |
| acu_042 | acu_038 |
| acu_043 | 无 |
| acu_044 | 无 |
| acu_045 | 无 |
| acu_046 | acu_018, acu_045 |
| acu_047 | 无 |
| acu_048 | acu_030 |
