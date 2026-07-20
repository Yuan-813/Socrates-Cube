# 数据库设计说明书（DBDD）
# Database Design Description

| 文档标识 | SC-DBDD-001 |
|:---:|:---|
| 项目名称 | Socrates-Cube 多智能体自适应《计算机网络》学习系统 |
| 版本号 | v1.0 |
| 编制日期 | 2026-07-20 |
| 参考标准 | GB/T 8567-2006《计算机软件文档编制规范》 |
| 依赖文档 | SC-SDD-001 |

---

## 第一章 数据库总体设计

### 1.1 数据库选型

系统采用**四种存储类型**的混合数据架构，各司其职：

| 存储类型 | 技术实现 | 环境 | 用途 |
|---|---|---|---|
| 关系数据库 | SQLite（开发）/ MySQL（生产）| 必选 | 结构化业务数据（用户/画像/会话/日志/路径）|
| 向量数据库 | ChromaDB 0.5.0 | 可选（降级到TF-IDF）| 语义向量检索（课程/协议/误解库）|
| 本地JSON索引 | TF-IDF本地关键词索引 | 自动降级 | ChromaDB不可用时的备选检索 |
| JSON文档 | 文件系统（data/*.json）| 必选 | 知识图谱节点、误解库、演示数据 |

**SQLite vs MySQL选型理由**：
- **开发环境（SQLite）**：零配置，文件直接存储（edu_agent.db），aiosqlite提供异步驱动，与FastAPI完美兼容
- **生产环境（MySQL/TDSQL-C）**：通过 `DATABASE_URL` 环境变量切换，SQLAlchemy ORM层对上层代码透明
- **驱动层**：SQLite使用 aiosqlite 0.20.0，MySQL使用 PyMySQL（requirements.txt可扩展）

### 1.2 数据架构概览

```
┌─────────────────────────────────────────────────────────┐
│  业务数据层（关系数据库，10张表）                          │
│  users / student_profiles / chat_sessions               │
│  agent_logs / knowledge_nodes / learning_resources       │
│  learning_paths / learning_path_nodes                   │
│  assessment_records / misconception_records             │
├─────────────────────────────────────────────────────────┤
│  语义检索层（ChromaDB向量库）                             │
│  course_docs | protocol_specs | misconceptions          │
├─────────────────────────────────────────────────────────┤
│  降级索引层（TF-IDF本地索引）                             │
│  data/vector_db/local_index.json                        │
├─────────────────────────────────────────────────────────┤
│  非结构化数据层（JSON文档）                               │
│  data/misconceptions.json（150条误解）                   │
│  data/demo_cases.json（演示案例）                         │
│  data/certificate_exams.json（证书考试题库）              │
└─────────────────────────────────────────────────────────┘
```

---

## 第二章 关系数据库设计

### 2.1 ER实体关系概述

系统关系数据库围绕**用户（User）**作为核心实体，通过外键关联扩展学习数据：

```mermaid
erDiagram
    users ||--o{ student_profiles : "1:1 has"
    users ||--o{ chat_sessions : "1:N creates"
    users ||--o{ learning_paths : "1:N owns"
    users ||--o{ assessment_records : "1:N has"
    users ||--o{ misconception_records : "1:N has"
    learning_paths ||--o{ learning_path_nodes : "1:N contains"
    knowledge_nodes ||--o{ learning_resources : "1:N generates"
    chat_sessions ||--o{ agent_logs : "1:N records"
```

### 2.2 表详细设计

#### 表1：users（用户表）

| 字段名 | 数据类型 | 约束 | 说明 |
|---|---|---|---|
| id | String | PK, NOT NULL | 用户唯一标识（UUID格式）|
| username | String | NOT NULL, UNIQUE | 用户名（唯一） |
| create_time | DateTime | DEFAULT now() | 创建时间 |
| update_time | DateTime | DEFAULT now(), ON UPDATE | 最后更新时间 |

**索引**：username（唯一索引，用于登录查询）

---

#### 表2：student_profiles（学生画像表）

| 字段名 | 数据类型 | 约束 | 说明 |
|---|---|---|---|
| user_id | String | PK, FK→users.id | 用户ID（一对一关系）|
| profile_json | Text | NOT NULL, DEFAULT '{}' | 8维画像+mastery_map的JSON序列化 |
| update_time | DateTime | DEFAULT now(), ON UPDATE | 最后更新时间 |

**profile_json 内部结构**：
```json
{
  "conceptual_understanding": 0.65,
  "protocol_analysis": 0.50,
  "calculation_ability": 0.45,
  "error_diagnosis": 0.55,
  "system_design": 0.40,
  "knowledge_connection": 0.60,
  "expression_clarity": 0.70,
  "self_correction": 0.50,
  "mastery_map": {"kn_005": 0.72, "kn_008": 0.43},
  "weak_points": ["kn_008", "kn_007"],
  "strong_points": ["kn_001"],
  "turn_count": 12
}
```

---

#### 表3：chat_sessions（对话会话表）

| 字段名 | 数据类型 | 约束 | 说明 |
|---|---|---|---|
| session_id | String | PK, INDEX | 会话唯一标识（UUID）|
| user_id | String | FK→users.id, NULLABLE | 用户ID（可为空，支持游客会话）|
| messages | Text | DEFAULT '[]' | 对话历史JSON数组（最多80条）|
| create_time | DateTime | DEFAULT now() | 会话创建时间 |
| update_time | DateTime | DEFAULT now(), ON UPDATE | 最后消息时间 |

**messages 内部结构**：
```json
[
  {"role": "user", "content": "TCP三次握手是什么", "timestamp": "2026-07-20T10:00:00"},
  {"role": "assistant", "content": "...", "timestamp": "2026-07-20T10:00:03"}
]
```
> 超过80条时自动裁剪，保留最近80条（`messages[-80:]`）

---

#### 表4：agent_logs（Agent执行日志表）

| 字段名 | 数据类型 | 约束 | 说明 |
|---|---|---|---|
| log_id | String | PK, INDEX | 日志唯一标识（UUID）|
| session_id | String | INDEX | 关联会话ID |
| agent_name | String | NOT NULL | Agent名称（Orchestrator/Retriever/Diagnosis/Profiler等）|
| action | String | NOT NULL | 执行动作描述（如"search_all"/"diagnose"）|
| state | Text | DEFAULT '{}' | 输入输出状态JSON（含input/output/duration_ms）|
| timestamp | DateTime | DEFAULT now() | 日志记录时间 |
| result | Text | DEFAULT '{}' | 执行结果JSON快照 |

**索引**：session_id（用于日志查询 `GET /api/v1/logs/session/{session_id}`）

---

#### 表5：knowledge_nodes（知识节点记录表）

| 字段名 | 数据类型 | 约束 | 说明 |
|---|---|---|---|
| node_id | String | PK, INDEX | 节点ID（kn_xxx格式）|
| name | String | NOT NULL, INDEX | 知识点名称（如"TCP三次握手"）|
| chapter | String | NOT NULL, INDEX | 所属章节（如"第5章"）|
| node_type | String | NOT NULL, DEFAULT 'concept' | 节点类型（concept/skill/protocol）|
| difficulty | Integer | NOT NULL, DEFAULT 3 | 难度等级（1-5）|
| estimated_time | Integer | NOT NULL, DEFAULT 30 | 预计学习时间（分钟）|
| keywords_json | Text | NOT NULL, DEFAULT '[]' | 关键词数组JSON |
| description | Text | NOT NULL, DEFAULT '' | 知识点描述文本 |
| prerequisite_ids_json | Text | NOT NULL, DEFAULT '[]' | 前置知识节点ID列表JSON |
| create_time | DateTime | DEFAULT now() | 创建时间 |

---

#### 表6：learning_resources（学习资源表）

| 字段名 | 数据类型 | 约束 | 说明 |
|---|---|---|---|
| resource_id | String | PK, INDEX | 资源唯一标识（UUID）|
| knowledge_node_id | String | INDEX, NULLABLE | 关联知识节点ID |
| knowledge_point | String | NOT NULL, INDEX | 知识点名称（如"TCP三次握手"）|
| resource_type | String | NOT NULL, INDEX | 资源类型（doc/exercise/code）|
| difficulty | Integer | NOT NULL, DEFAULT 3 | 难度等级（1-5）|
| title | String | NOT NULL | 资源标题 |
| content | Text | NOT NULL | 资源正文内容 |
| metadata_json | Text | NOT NULL, DEFAULT '{}' | 元数据JSON（含difficulty/language/question_count等）|
| quality_score | Float | NOT NULL, DEFAULT 0.75 | 质量评分 [0.6, 1.0] |
| create_time | DateTime | DEFAULT now() | 创建时间 |
| update_time | DateTime | DEFAULT now(), ON UPDATE | 最后更新时间 |

---

#### 表7：learning_paths（学习路径表）

| 字段名 | 数据类型 | 约束 | 说明 |
|---|---|---|---|
| path_id | String | PK, INDEX | 路径唯一标识（UUID）|
| user_id | String | FK→users.id, INDEX | 用户ID |
| title | String | NOT NULL | 路径标题（如"计算机网络个性化学习路径（6个节点）"）|
| description | Text | NOT NULL, DEFAULT '' | 路径描述 |
| status | String | NOT NULL, DEFAULT 'active' | 路径状态（active/completed）|
| total_estimated_time | Integer | NOT NULL, DEFAULT 0 | 总预计学习时间（分钟）|
| plan_json | Text | NOT NULL, DEFAULT '{}' | 完整路径计划JSON（含nodes数组）|
| create_time | DateTime | DEFAULT now() | 创建时间 |
| update_time | DateTime | DEFAULT now(), ON UPDATE | 最后更新时间 |

---

#### 表8：learning_path_nodes（路径节点表）

| 字段名 | 数据类型 | 约束 | 说明 |
|---|---|---|---|
| id | String | PK | 节点标识（{path_id}:{node_id}格式）|
| path_id | String | FK→learning_paths.path_id, INDEX | 父路径ID |
| node_id | String | INDEX | 知识节点ID |
| sequence | Integer | NOT NULL | 节点顺序（从1开始）|
| status | String | NOT NULL, DEFAULT 'pending' | 节点状态（pending/in_progress/completed/locked）|
| current_mastery | Float | NOT NULL, DEFAULT 0.0 | 当前掌握度 [0, 1] |
| recommendation_reason | Text | NOT NULL, DEFAULT '' | 推荐理由文字 |
| create_time | DateTime | DEFAULT now() | 创建时间 |

---

#### 表9：assessment_records（测评记录表）

| 字段名 | 数据类型 | 约束 | 说明 |
|---|---|---|---|
| assessment_id | String | PK, INDEX | 测评记录ID（UUID）|
| user_id | String | FK→users.id, INDEX | 用户ID |
| knowledge_node_id | String | INDEX | 测评关联的知识节点ID |
| question_type | String | NOT NULL | 题目类型（choice/judge/short_answer/calculation）|
| score | Float | NOT NULL | 实际得分 |
| max_score | Float | NOT NULL, DEFAULT 100.0 | 满分值 |
| answer_json | Text | NOT NULL, DEFAULT '{}' | 学生答案JSON |
| diagnosis_json | Text | NOT NULL, DEFAULT '{}' | 诊断结果JSON（三层诊断报告）|
| create_time | DateTime | DEFAULT now() | 记录时间 |

---

#### 表10：misconception_records（用户误解记录表）

| 字段名 | 数据类型 | 约束 | 说明 |
|---|---|---|---|
| id | String | PK | 记录唯一标识 |
| user_id | String | FK→users.id, INDEX | 用户ID |
| knowledge_node_id | String | INDEX | 相关知识节点ID |
| pattern | String | INDEX | 误解模式名称（与misconceptions.json对应）|
| severity | Float | NOT NULL, DEFAULT 0.5 | 严重程度 [0, 1] |
| evidence | Text | NOT NULL, DEFAULT '' | 触发误解的具体证据描述 |
| intervention | Text | NOT NULL, DEFAULT '' | 推荐干预策略 |
| last_seen | DateTime | DEFAULT now() | 最后出现时间 |

**唯一约束**：`(user_id, knowledge_node_id, pattern)` 三元组唯一，防止重复记录

---

### 2.3 核心外键关系

| 外键所在表 | 外键字段 | 引用表 | 引用字段 | 关系类型 |
|---|---|---|---|---|
| student_profiles | user_id | users | id | 1:1 |
| chat_sessions | user_id | users | id | N:1 |
| learning_paths | user_id | users | id | N:1 |
| learning_path_nodes | path_id | learning_paths | path_id | N:1 |
| assessment_records | user_id | users | id | N:1 |
| misconception_records | user_id | users | id | N:1 |

---

## 第三章 向量数据库设计

### 3.1 ChromaDB集合设计

ChromaDB存储3个命名集合，相似度度量均使用余弦相似度（`"hnsw:space": "cosine"`）：

| 集合名称 | 内容 | 文档数量（示意）| 主要元数据字段 |
|---|---|---|---|
| course_docs | 课程章节讲义片段 | 约100-200片段 | source/chapter/type |
| protocol_specs | RFC协议规范摘要片段 | 约200-400片段 | rfc_number/protocol/section |
| misconceptions | 150条误解记录全文 | 150文档 | mc_id/error_type/knowledge_point |

### 3.2 Embedding策略

ChromaDB使用内置的默认嵌入模型（all-MiniLM-L6-v2 via sentence-transformers）生成向量。通过 `VectorStore.add_documents()` 写入：

```python
vector_store.add_documents(
    collection_name="course_docs",
    documents=["文档全文..."],
    metadatas=[{"source": "chapter3_transport.md", "chapter": "第3章"}],
    ids=["doc_001"]
)
```

### 3.3 降级方案设计动机

`local_index.json` 是一个JSON文件，结构为：
```json
{
  "course_docs": [
    {"id": "doc_001", "document": "...", "metadata": {...}, "tokens": ["tcp", "握手", "三次"]},
    ...
  ],
  "protocol_specs": [...],
  "misconceptions": [...]
}
```

**设计动机**：
1. 演示环境可能没有安装ChromaDB依赖（numpy版本冲突）
2. 竞赛现场网络环境不稳定，需保证离线可用性
3. TF-IDF降级检索质量低于向量检索，但足够支撑基本QA场景

---

## 第四章 非结构化数据设计

### 4.1 误解库JSON结构（data/misconceptions.json）

文件大小：约3120行，共150条误解记录

每条记录的schema：

```json
{
  "id": "mc_001",                          // 误解条目ID
  "knowledge_point": "TCP 三次握手",        // 关联知识点名称
  "misconception": "认为两次握手足以建立...", // 错误描述（自然语言）
  "error_type": "flow_omission",           // 错误类型（23种之一）
  "correct_answer": "第三次ACK用来确认...",  // 正确解答
  "chapter": "computer_networking",        // 所属章节
  "knowledge_node_ids": ["acu_025"],       // ACU层节点ID列表
  "weak_prerequisites": ["kp_013"],        // 薄弱前置知识KP节点
  "interventions": ["simulation", "follow_up_question"], // 干预策略列表
  "kp_node_ids": ["kp_014"]               // 关联KP层节点
}
```

**23种错误类型完整列表**：
flow_omission / concept_confusion / layer_misplacement / over_simplification /
term_confusion / calculation_error / reasoning_breakdown / factual /
algorithm_confusion / classification_error / direction_reversal /
incomplete_understanding / layer_confusion / mechanism_confusion /
metric_confusion / outdated_understanding / overgeneralization /
protocol_confusion / range_error / scale_confusion / scope_error /
syntax_confusion / technology_outdated / version_confusion

### 4.2 学生画像JSON结构

存储在 student_profiles.profile_json 字段中，运行时解析为Python字典：

```json
{
  "conceptual_understanding": 0.65,    // 8维能力分数（float，[0.1, 1.0]）
  "protocol_analysis": 0.50,
  "calculation_ability": 0.45,
  "error_diagnosis": 0.55,
  "system_design": 0.40,
  "knowledge_connection": 0.60,
  "expression_clarity": 0.70,
  "self_correction": 0.50,
  "mastery_map": {                    // 知识点掌握度映射（float，[0, 1]）
    "kn_005": 0.72,
    "kn_008": 0.43,
    "kn_001": 0.85
  },
  "weak_points": ["kn_008", "kn_007"],  // 掌握度<0.5的节点ID列表
  "strong_points": ["kn_001"],           // 掌握度≥0.8的节点ID列表
  "turn_count": 12,                      // 累计对话轮次
  "last_agent_trace": { ... }            // 最近一次Profiler执行追踪
}
```

---

## 第五章 数据库环境配置

### 5.1 开发环境

```bash
# 默认使用SQLite（无需额外配置）
DATABASE_URL=sqlite:///./edu_agent.db   # .env 文件中配置

# 初始化（首次运行）
python scripts/init_db.py
```

`init_db.py` 执行流程：
1. 调用 `init_db()` 创建所有10张表（SQLAlchemy `Base.metadata.create_all()`）
2. 注入10个核心KP知识节点（TOPICS列表）
3. 生成3000条演示用户和画像数据（用于展示效果）

### 5.2 生产环境

```bash
# MySQL/TDSQL-C（腾讯云兼容MySQL协议）
DATABASE_URL=mysql+pymysql://user:password@host:3306/socrates_cube
```

SQLAlchemy ORM层对上层代码完全透明，切换数据库无需修改Agent代码。

### 5.3 向量库初始化

```bash
# 向量化所有课程文档（课程章节 + RFC规范）
python scripts/ingest_docs.py

# 重新注入误解库
python scripts/reingest_misconceptions.py

# 验证向量库状态
python scripts/verify_env.py
```

---

*本文档遵循 GB/T 8567-2006 规范编制，所有表结构来自 src/loopse/db/models.py 的实际ORM定义。*
