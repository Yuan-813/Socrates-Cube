---
name: protocol-knowledge
description: 网络协议知识增强：RFC标准查询、协议知识添加、误解库扩充、知识图谱节点管理
---

# 网络协议知识增强技能

## 描述
帮助开发者快速查找 RFC 标准文档、向知识图谱添加新的网络协议知识点、扩充协议相关的误解库条目。Socrates-Cube 聚焦《计算机网络》（谢希仁第8版）课程范围，知识来源以 RFC 标准为主要权威引用。

## 使用场景
- 需要查找某个网络协议的 RFC 标准文档
- 向知识图谱添加新的协议知识点或 ACU 认知单元
- 需要为某个协议添加常见学生误解
- 更新或修正已有的协议知识内容
- 需要扩展某章节的知识覆盖范围

## 操作指南

### 1. 已收录的 RFC 标准文档

项目已收录以下 RFC，存放于 `data/cleaned/` 目录：

| 文件 | RFC编号 | 协议 | 所属层次 |
|------|---------|------|---------|
| `rfc9293_tcp.md` | RFC 9293 | TCP | 传输层 |
| `rfc768_udp.md` | RFC 768 | UDP | 传输层 |
| `rfc791_ipv4.md` | RFC 791 | IPv4 | 网络层 |
| `rfc8200_ipv6.md` | RFC 8200 | IPv6 | 网络层 |
| `rfc1034_dns_concepts.md` | RFC 1034 | DNS概念 | 应用层 |
| `rfc1035_dns_implementation.md` | RFC 1035 | DNS实现 | 应用层 |
| `rfc9110_http_semantics.md` | RFC 9110 | HTTP语义 | 应用层 |
| `rfc9112_http11.md` | RFC 9112 | HTTP/1.1 | 应用层 |
| `rfc8446_tls13.md` | RFC 8446 | TLS 1.3 | 安全 |
| `rfc9000_quic.md` | RFC 9000 | QUIC | 传输层 |
| `iana_protocol_numbers.md` | IANA | 协议号分配 | 参考 |

### 2. 添加新的 RFC 文档

**Step 1：下载新 RFC 原文**

在 `scripts/download_knowledge_sources.py` 的 `SOURCES` 列表中添加新条目：
```python
Source(
    "rfc_xxxx_protocol_name",          # id
    "RFC XXXX Protocol Title",          # title
    "https://www.rfc-editor.org/rfc/rfcXXXX.txt",  # url
    "protocol_specs",                    # collection
    "transport",                         # chapter: transport/network/application
    "Key concepts and focus areas"       # focus
)
```

**Step 2：执行下载**
```powershell
.venv\Scripts\python.exe scripts/download_knowledge_sources.py
```

**Step 3：导入向量库**
```powershell
.venv\Scripts\python.exe scripts/ingest_docs.py --reset
```

### 3. 向知识图谱添加新的协议知识点

**知识图谱结构：** `data/knowledge_graph.json`

```json
{
  "nodes": [
    {
      "id": "kp_0XX",
      "name": "协议名称",
      "chapter": "第X章",
      "type": "protocol",
      "keywords": ["关键词1", "关键词2"],
      "difficulty": 3,
      "estimated_time": 30,
      "description": "知识点描述"
    }
  ],
  "edges": [
    {
      "source": "kp_0XX",
      "target": "kp_0YY",
      "type": "prerequisite"
    }
  ],
  "cognitive_nodes": [
    {
      "id": "acu_0XX",
      "name": "认知单元名称",
      "chapter": "第X章",
      "difficulty": 3,
      "prerequisites": ["acu_0YY"],
      "knowledge_point_ids": ["kp_0XX"]
    }
  ]
}
```

**节点类型（type）：**
- `concept` — 概念性知识点
- `protocol` — 协议类知识点
- `skill` — 实践技能

**边类型：**
- `prerequisite` — 先修关系
- `contains` — 包含关系
- `maps_to` — 映射到 ACU
- `related` — 关联关系

**章节映射：**
| 章节 | 内容范围 |
|------|---------|
| 第1章 | 计算机网络概述、体系结构 |
| 第2章 | 物理层 |
| 第3章 | 数据链路层（以太网、VLAN、STP） |
| 第4章 | 网络层（IP、ARP、ICMP、路由） |
| 第5章 | 传输层（TCP、UDP） |
| 第6章 | 应用层（DNS、HTTP、FTP、SMTP） |

### 4. 添加协议相关误解

**误解库文件：** `data/misconceptions.json`

每条误解的数据结构：
```json
{
  "id": "mc_XXX",
  "knowledge_point": "知识点名称",
  "misconception": "学生的错误认知描述",
  "error_type": "错误类型",
  "correct_answer": "正确解释",
  "chapter": "computer_networking",
  "knowledge_node_ids": ["acu_0XX"],
  "weak_prerequisites": ["kp_0XX"],
  "interventions": ["intervention_type1", "intervention_type2"],
  "kp_node_ids": ["kp_0XX"]
}
```

**错误类型（error_type）：**
- `concept_confusion` — 概念混淆
- `algorithm_confusion` — 算法混淆
- `scope_error` — 范围错误（层次混淆）
- `mechanism_error` — 机制理解错误
- `parameter_confusion` — 参数/数值混淆
- `process_error` — 流程步骤错误
- `security_misconception` — 安全认知错误

**干预策略（interventions）：**
- `comparison_table` — 对比表格
- `follow_up_question` — 追问验证
- `visual_diagram` — 可视化图示
- `analogy` — 类比解释
- `step_by_step` — 分步讲解
- `counterexample` — 反例说明

### 5. 批量扩充误解库

```powershell
# 使用已有脚本扩充（追加50条）
.venv\Scripts\python.exe scripts/expand_misconceptions.py

# 扩充后重新导入向量库
.venv\Scripts\python.exe scripts/reingest_misconceptions.py

# 验证误解库状态
.venv\Scripts\python.exe scripts/check_misconceptions.py
```

### 6. 协议知识检索测试

```powershell
# 启动后端后，通过搜索 API 测试检索效果
curl "http://localhost:8000/api/v1/search?q=TCP%E4%B8%89%E6%AC%A1%E6%8F%A1%E6%89%8B"

# 或在 Swagger UI 中测试
# http://localhost:8000/docs#/search
```

### 7. RFC 在线查询参考

常用 RFC 查询地址：
- RFC Editor：https://www.rfc-editor.org/
- RFC 文本格式：`https://www.rfc-editor.org/rfc/rfc{number}.txt`
- IANA 协议号：https://www.iana.org/assignments/protocol-numbers/

**课程相关核心 RFC：**
| RFC | 协议 | 重要性 |
|-----|------|--------|
| RFC 9293 | TCP | 核心 |
| RFC 768 | UDP | 核心 |
| RFC 791 | IPv4 | 核心 |
| RFC 8200 | IPv6 | 重要 |
| RFC 1034/1035 | DNS | 核心 |
| RFC 9110/9112 | HTTP | 核心 |
| RFC 8446 | TLS 1.3 | 重要 |
| RFC 9000 | QUIC | 扩展 |
| RFC 826 | ARP | 核心 |
| RFC 792 | ICMP | 重要 |
| RFC 2328 | OSPF | 重要 |
| RFC 4271 | BGP-4 | 扩展 |

## 关键文件清单

| 文件路径 | 说明 |
|---------|------|
| `data/knowledge_graph.json` | 知识图谱（KP + ACU + 边） |
| `data/misconceptions.json` | 误解库 |
| `data/cleaned/rfc*.md` | 已清洗的 RFC 文档 |
| `data/cleaned/chapter*.md` | 课程章节文档 |
| `data/raw/external_sources.json` | 外部源清单 |
| `scripts/download_knowledge_sources.py` | RFC 下载脚本 |
| `scripts/expand_knowledge_graph.py` | 图谱扩展脚本 |
| `scripts/expand_misconceptions.py` | 误解库扩展脚本 |
| `scripts/expand_acu.py` | ACU 扩展脚本 |
| `docs/architecture/acu_specification_v1.md` | ACU 规格说明 |
| `docs/architecture/cognitive_kg_design_v1.md` | 认知知识图谱设计 |
| `docs/references/知识库资料清单.md` | 知识库资料清单 |

## 常见问题

### Q: 如何确定新知识点的 ID 编号？
A: 查看 `data/knowledge_graph.json` 中现有节点的最大 ID，递增即可。KP 节点用 `kp_0XX`，ACU 用 `acu_0XX`，误解用 `mc_XXX`。

### Q: 添加的知识点需要建立哪些边？
A: 必须建立：
1. `prerequisite` 边：指向先修知识点
2. `maps_to` 边：KP 与 ACU 之间的映射
可选建立：
3. `related` 边：相关知识点关联
4. `contains` 边：章节包含关系

### Q: 误解库中的 interventions 如何选择？
A: 根据错误类型推荐：
- 概念混淆 → `comparison_table` + `follow_up_question`
- 流程错误 → `step_by_step` + `visual_diagram`
- 参数混淆 → `counterexample` + `analogy`

### Q: 课程范围之外的协议是否需要收录？
A: 项目锁定谢希仁《计算机网络》第8版范围。扩展内容（如 QUIC、HTTP/3）可作为"进阶扩展"类型收录，difficulty 设为 4-5。

### Q: 如何验证新添加的知识是否被诊断 Agent 正确使用？
A: 
1. 重建向量库：`scripts/ingest_docs.py --reset`
2. 启动后端，通过对话测试相关知识点
3. 检查 Agent 日志是否正确检索到新知识
4. 运行诊断测试：`scripts/run_diagnosis_accuracy_test.py`
