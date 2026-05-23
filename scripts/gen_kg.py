"""生成 knowledge_graph.json（避免PowerShell编码问题）"""
import json
import os

data = {
    "version": "1.0",
    "course": "计算机网络（谢希仁第8版）",
    "nodes": [
        {"id": "kn_001", "name": "计算机网络基本概念", "chapter": "第1章", "type": "concept", "difficulty": 1, "estimated_time": 30, "keywords": ["网络", "协议", "体系结构"], "description": "计算机网络的定义、分类、组成"},
        {"id": "kn_002", "name": "OSI七层参考模型", "chapter": "第1章", "type": "concept", "difficulty": 2, "estimated_time": 45, "keywords": ["OSI", "七层", "封装", "解封装"], "description": "物理层/数据链路层/网络层/传输层/会话层/表示层/应用层"},
        {"id": "kn_003", "name": "TCP/IP四层模型", "chapter": "第1章", "type": "concept", "difficulty": 2, "estimated_time": 40, "keywords": ["TCP/IP", "四层", "网际层", "传输层"], "description": "网络接口层/网际层/传输层/应用层，与OSI对比"},
        {"id": "kn_004", "name": "数据封装与解封装", "chapter": "第1章", "type": "process", "difficulty": 2, "estimated_time": 30, "keywords": ["封装", "PDU", "帧", "报文", "数据报"], "description": "数据在各层的封装格式"},
        {"id": "kn_005", "name": "UDP协议基础", "chapter": "第5章", "type": "protocol", "difficulty": 2, "estimated_time": 35, "keywords": ["UDP", "无连接", "不可靠", "数据报"], "description": "UDP首部格式、特点、适用场景"},
        {"id": "kn_006", "name": "TCP协议基础特性", "chapter": "第5章", "type": "protocol", "difficulty": 3, "estimated_time": 50, "keywords": ["TCP", "面向连接", "可靠", "全双工"], "description": "TCP的六个特点"},
        {"id": "kn_007", "name": "TCP报文段格式", "chapter": "第5章", "type": "format", "difficulty": 3, "estimated_time": 45, "keywords": ["首部", "序号", "确认号", "SYN", "ACK", "FIN"], "description": "TCP首部各字段含义"},
        {"id": "kn_008", "name": "TCP三次握手", "chapter": "第5章", "type": "process", "difficulty": 3, "estimated_time": 60, "keywords": ["三次握手", "SYN", "SYN-ACK", "连接建立"], "description": "三次握手过程、状态转换"},
        {"id": "kn_009", "name": "TCP四次挥手", "chapter": "第5章", "type": "process", "difficulty": 4, "estimated_time": 60, "keywords": ["四次挥手", "FIN", "TIME_WAIT", "连接释放"], "description": "四次挥手过程、TIME_WAIT的作用"},
        {"id": "kn_010", "name": "TCP可靠传输机制", "chapter": "第5章", "type": "mechanism", "difficulty": 4, "estimated_time": 70, "keywords": ["确认", "重传", "RTT", "超时", "序列号"], "description": "停止等待协议、连续ARQ协议"},
        {"id": "kn_011", "name": "TCP流量控制", "chapter": "第5章", "type": "mechanism", "difficulty": 4, "estimated_time": 50, "keywords": ["滑动窗口", "rwnd", "接收窗口"], "description": "滑动窗口机制"},
        {"id": "kn_012", "name": "TCP拥塞控制", "chapter": "第5章", "type": "mechanism", "difficulty": 5, "estimated_time": 80, "keywords": ["慢启动", "拥塞避免", "快重传", "快恢复", "cwnd"], "description": "四种拥塞控制算法"},
        {"id": "kn_013", "name": "HTTP协议基础", "chapter": "第6章", "type": "protocol", "difficulty": 3, "estimated_time": 60, "keywords": ["HTTP", "请求", "响应", "状态码"], "description": "HTTP/1.0/1.1区别"},
        {"id": "kn_014", "name": "HTTPS与TLS", "chapter": "第6章", "type": "protocol", "difficulty": 4, "estimated_time": 70, "keywords": ["HTTPS", "TLS", "证书", "加密"], "description": "TLS握手过程、证书验证"},
        {"id": "kn_015", "name": "DNS解析", "chapter": "第6章", "type": "process", "difficulty": 3, "estimated_time": 45, "keywords": ["DNS", "域名解析", "递归查询", "迭代查询"], "description": "DNS查询过程"},
        {"id": "kn_016", "name": "IP地址与子网划分", "chapter": "第4章", "type": "concept", "difficulty": 3, "estimated_time": 60, "keywords": ["IP地址", "子网掩码", "CIDR"], "description": "IP地址分类、子网掩码"},
        {"id": "kn_017", "name": "路由算法基础", "chapter": "第4章", "type": "algorithm", "difficulty": 4, "estimated_time": 75, "keywords": ["路由表", "距离向量", "链路状态", "RIP", "OSPF"], "description": "RIP与OSPF对比"},
        {"id": "kn_018", "name": "ARP协议", "chapter": "第4章", "type": "protocol", "difficulty": 2, "estimated_time": 35, "keywords": ["ARP", "MAC地址", "地址解析"], "description": "ARP工作原理"},
        {"id": "kn_019", "name": "网络性能指标", "chapter": "第1章", "type": "concept", "difficulty": 2, "estimated_time": 40, "keywords": ["带宽", "吞吐量", "时延", "RTT"], "description": "七大性能指标"},
        {"id": "kn_020", "name": "以太网与MAC帧", "chapter": "第3章", "type": "protocol", "difficulty": 3, "estimated_time": 50, "keywords": ["以太网", "MAC地址", "CSMA/CD", "帧格式"], "description": "以太网MAC帧格式"}
    ],
    "edges": [
        {"from": "kn_001", "to": "kn_002", "relation": "prerequisite"},
        {"from": "kn_001", "to": "kn_003", "relation": "prerequisite"},
        {"from": "kn_002", "to": "kn_004", "relation": "prerequisite"},
        {"from": "kn_003", "to": "kn_004", "relation": "prerequisite"},
        {"from": "kn_003", "to": "kn_005", "relation": "prerequisite"},
        {"from": "kn_003", "to": "kn_006", "relation": "prerequisite"},
        {"from": "kn_006", "to": "kn_007", "relation": "prerequisite"},
        {"from": "kn_007", "to": "kn_008", "relation": "prerequisite"},
        {"from": "kn_007", "to": "kn_009", "relation": "prerequisite"},
        {"from": "kn_008", "to": "kn_010", "relation": "prerequisite"},
        {"from": "kn_010", "to": "kn_011", "relation": "prerequisite"},
        {"from": "kn_011", "to": "kn_012", "relation": "prerequisite"},
        {"from": "kn_006", "to": "kn_013", "relation": "prerequisite"},
        {"from": "kn_013", "to": "kn_014", "relation": "prerequisite"},
        {"from": "kn_001", "to": "kn_015", "relation": "prerequisite"},
        {"from": "kn_001", "to": "kn_016", "relation": "prerequisite"},
        {"from": "kn_016", "to": "kn_017", "relation": "prerequisite"},
        {"from": "kn_016", "to": "kn_018", "relation": "prerequisite"},
        {"from": "kn_001", "to": "kn_019", "relation": "related"},
        {"from": "kn_001", "to": "kn_020", "relation": "prerequisite"},
        {"from": "kn_020", "to": "kn_018", "relation": "related"}
    ],
    "chapters": {
        "第1章": ["kn_001", "kn_002", "kn_003", "kn_004", "kn_019"],
        "第3章": ["kn_020"],
        "第4章": ["kn_016", "kn_017", "kn_018"],
        "第5章": ["kn_005", "kn_006", "kn_007", "kn_008", "kn_009", "kn_010", "kn_011", "kn_012"],
        "第6章": ["kn_013", "kn_014", "kn_015"]
    }
}

out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "knowledge_graph.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"Written to {out_path}")
