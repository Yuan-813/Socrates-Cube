# 软件需求规格说明书（SRS）
# Software Requirements Specification

| 文档标识 | SC-SRS-001 |
|:---:|:---|
| 项目名称 | Socrates-Cube 多智能体自适应《计算机网络》学习系统 |
| 版本号 | v1.0 |
| 编制日期 | 2026-07-20 |
| 参考标准 | GB/T 8567-2006《计算机软件文档编制规范》 |

---

## 第一章 引言

### 1.1 项目背景

计算机网络是高校计算机专业的核心基础课程。课程内容涵盖OSI分层模型、TCP/IP协议栈、HTTP/DNS应用协议、TLS安全机制等复杂知识点，概念抽象、协议细节多，学生学习过程中极易产生认知误区。

传统在线学习辅助系统（题库、视频课程）存在以下不足：
- **只判断对错，不解释原因**：系统无法告知学生"为什么错了"，更无法定位根因
- **内容千篇一律**：不同认知基础的学生获得相同的学习资源，缺乏个性化适配
- **学习路径固定**：不能根据学生薄弱点动态调整学习顺序
- **缺乏追问引导**：无法模拟苏格拉底式教学中的层层追问

**Socrates-Cube** 系统（第十五届中国软件杯A3赛道参赛项目）针对上述痛点，以多智能体协同架构为技术底座，通过三层认知诊断、8维学习画像、RAG增强检索和拓扑排序路径规划，构建个性化学习闭环。

### 1.2 建设目标

| 目标编号 | 建设目标 | 量化指标 |
|:---:|---|---|
| G01 | 实现三层认知诊断 | 诊断输出包含≥10个结构化字段，响应延迟<3秒 |
| G02 | 建立8维学习画像 | 每轮对话后更新，涵盖8个能力维度 |
| G03 | 生成个性化学习资源 | 支持doc/exercise/code三类资源按需生成 |
| G04 | 规划个性化学习路径 | 基于知识图谱拓扑排序，最多10个节点 |
| G05 | 实时可视化Agent执行链路 | SSE事件流，前端实时展示各Agent状态 |
| G06 | 系统高可用性 | 支持Mock离线模式，LLM不可用时不影响基础功能 |

### 1.3 术语与缩略语

| 术语/缩略语 | 全称/说明 |
|---|---|
| Agent | 智能代理，具备自主感知、决策和行动能力的软件实体 |
| SSE | Server-Sent Events，服务器推送事件，基于HTTP的单向实时数据流协议 |
| LLM | Large Language Model，大语言模型 |
| RAG | Retrieval-Augmented Generation，检索增强生成技术 |
| KP | Knowledge Point，知识点节点，知识图谱中粒度较粗的学习概念单元 |
| ACU | Atomic Cognitive Unit，原子认知单元，与误解条目精确对应的细粒度节点 |
| ChromaDB | 开源向量数据库，支持余弦相似度语义检索 |
| JWT | JSON Web Token，无状态用户认证令牌 |
| TF-IDF | Term Frequency-Inverse Document Frequency，词频-逆文档频率算法 |
| Mock模式 | 当LLM API不可用时，系统使用预设模板回复的降级工作模式 |
| Orchestrator | 编排者，本系统中负责调度各专业Agent的中枢Agent |
| Diagnosis | 诊断Agent，执行三层认知错误分析 |
| Profiler | 画像Agent，维护学生8维能力画像 |
| Retriever | 检索Agent，执行多集合向量检索和知识图谱查询 |
| ResourceGenerator | 资源生成Agent，生成doc/exercise/code三类学习资源 |
| PathPlanner | 路径规划Agent，执行基于知识图谱的个性化路径规划 |

### 1.4 参考资料

1. GB/T 8567-2006《计算机软件文档编制规范》
2. RFC 9293《Transmission Control Protocol》（TCP规范）
3. RFC 9110《HTTP Semantics》
4. RFC 1034/1035《Domain Names》（DNS规范）
5. RFC 8446《The Transport Layer Security Protocol Version 1.3》
6. FastAPI 官方文档（https://fastapi.tiangolo.com）
7. 第十五届中国软件杯 A3赛题说明书

---

## 第二章 总体描述

### 2.1 产品概述

Socrates-Cube 是一个面向高校《计算机网络》课程的多智能体自适应学习系统。系统采用前后端分离架构，后端基于 FastAPI（Python 3.10）构建，前端基于 Vue3 构建。系统核心由6个专业Agent组成，通过SSE流式通信实时向前端推送执行状态和学习结果。

系统的核心工作流程为：用户通过聊天界面提问 → OrchestratorAgent识别意图并调度专业Agent → RetrieverAgent检索相关知识 → DiagnosisAgent执行三层错误诊断 → LLM生成流式主回复（通过token事件推送） → ProfilerAgent更新画像 → 按意图触发资源生成或路径规划 → 前端实时渲染结果。

### 2.2 用户特征

| 用户角色 | 描述 | 主要操作 |
|---|---|---|
| 学生 | 高校计算机网络课程学习者（本科/研究生） | 智能对话、查看诊断结果、获取个性化资源、查看学习路径 |
| 游客 | 未注册的临时访问者 | 基础对话体验（使用默认student-001账户） |

> 说明：当前版本不含独立的教师/管理员角色，系统以学生视角为主要交互方式。

### 2.3 运行环境

#### 2.3.1 服务端环境

| 环境要素 | 要求 |
|---|---|
| 操作系统 | Windows 10+ / Ubuntu 20.04+ / macOS 12+ |
| Python版本 | Python 3.10.* （严格锁定，aiosqlite兼容性要求） |
| 内存 | ≥4GB RAM（推荐8GB，ChromaDB向量检索需要）|
| 存储 | ≥2GB 可用磁盘空间（含向量库索引） |

#### 2.3.2 客户端环境

| 环境要素 | 要求 |
|---|---|
| 浏览器 | Chrome 90+ / Firefox 88+ / Edge 90+（需支持EventSource API） |
| 网络 | 与服务端可达；LLM模式下需访问讯飞星火API（wss://spark-api.xf-yun.com） |

#### 2.3.3 软件依赖（核心）

| 组件 | 版本 | 用途 |
|---|---|---|
| FastAPI | 0.111.0 | 后端Web框架 |
| SQLAlchemy | 2.0.30 | ORM数据库操作 |
| aiosqlite | 0.20.0 | SQLite异步驱动 |
| ChromaDB | 0.5.0 | 向量语义检索 |
| sparkai | 0.1.8 | 讯飞星火LLM SDK |
| Vue3 | 3.5.29 | 前端框架 |
| Vite | 5.4.21 | 前端构建工具 |

### 2.4 假设与依赖

1. **LLM API依赖**：系统核心功能依赖讯飞星火API（XUNFEI_APP_ID/API_KEY/API_SECRET）。若API不可用，系统自动切换Mock模式，使用预设模板回复，基础对话功能可用。
2. **ChromaDB可选**：向量检索功能依赖ChromaDB。若ChromaDB未初始化或不可用，系统降级至本地TF-IDF关键词检索（local_index.json），检索质量降低但不影响系统运行。
3. **网络连接**：LLM模式下，后端服务需能访问讯飞星火WebSocket端点（wss://spark-api.xf-yun.com/v3.5/chat）。
4. **数据库初始化**：首次启动前需执行 `python scripts/init_db.py` 完成数据库表创建和知识节点种子注入。

---

## 第三章 功能需求

### F01 用户认证与会话管理

**功能描述**：支持用户通过用户名创建或获取账号，维护对话会话。

**输入**：用户名（username，字符串，1-50字符）；会话ID（session_id，可选，UUID格式）

**处理逻辑**：
1. `UserRepository.get_or_create(username)` 若用户名不存在则创建新用户（UUID主键）
2. `SessionRepository.get_or_create(session_id, user_id)` 创建或恢复对话会话
3. 会话消息保留最近80条（历史裁剪机制）

**输出**：用户ID（UUID）、会话ID

**验收标准**：同一用户名重复请求返回相同用户ID；会话消息不超过80条

---

### F02 智能流式对话（核心功能）

**功能描述**：通过SSE（Server-Sent Events）实现多智能体协同的流式对话，实时可视化Agent执行链路。

**输入**：
- `message`（用户消息，字符串，1-2000字符，必填）
- `user_id`（用户ID，字符串，默认"student-001"）
- `session_id`（会话ID，可选，不填则自动创建）

**处理逻辑**：
1. OrchestratorAgent 识别用户意图（qa/resource/planning/simulation）
2. RetrieverAgent 执行三库向量检索 + 知识图谱关键词匹配
3. DiagnosisAgent 执行三层认知诊断
4. LLM 生成流式主回复，逐token推送
5. ProfilerAgent 更新8维学习画像
6. 按意图触发：ResourceGeneratorAgent（resource意图）或 PathPlannerAgent（planning意图）

**输出**：`text/event-stream` 格式的SSE事件流，事件类型包括：
- `agent_start`：Agent开始执行（携带Agent名称和说明）
- `agent_end`：Agent执行完毕（携带摘要信息）
- `diagnosis`：三层诊断完整结果（JSON结构）
- `token`：流式文字输出（单个token片段）
- `resource`：资源生成完成（resource_id、content等）
- `path_update`：学习路径更新（path_id、nodes列表）
- `done`：工作流完成（session_id、total_time_ms）
- `error`：执行错误（error描述）

**验收标准**：
- SSE连接建立后，首个agent_start事件在1秒内发出
- 完整诊断结果（diagnosis事件）包含≥8个字段
- done事件必须在error事件之前或最终发出
- LLM降级Mock模式下，系统仍能正常推送token事件

---

### F03 三层认知诊断

**功能描述**：对学生每条消息执行三层递进诊断，输出结构化诊断报告。

**输入**：用户消息文本、知识上下文文档列表、历史对话文本

**处理逻辑**：
1. **L1（_detect_surface_error）**：调用LLM判断是否存在表面错误，返回 is_correct/surface_error/error_type/confidence；内置硬规则：消息含"两次握手"/"二次握手"自动标记为 factual 错误
2. **L2（_analyze_root_cause）**：若L1检测到错误，调用LLM分析根本原因（root_causes）和缺失前置知识（missing_prerequisites）
3. **L3（_match_pattern）**：基于表面错误和根因，在误解库中匹配误区模式（pattern）和干预建议（intervention_suggestion）

**输出**（DiagnosisResult，10字段）：

| 字段 | 类型 | 说明 |
|---|---|---|
| is_correct | boolean | 是否正确 |
| confidence | float | 诊断置信度 (0~1) |
| surface_error | string \| null | 表面错误描述 |
| error_type | string | 错误类型（23种之一或"none"）|
| root_causes | list[string] | 根因列表 |
| missing_prerequisites | list[string] | 缺失前置知识ID列表 |
| pattern | string \| null | 误区模式名称 |
| intervention_suggestion | string | 干预建议 |
| related_node_ids | list[string] | 相关知识节点ID |
| agent_trace | dict | Agent执行追踪信息 |

**验收标准**：
- is_correct=False 时，surface_error 字段不为空
- 包含"两次握手"的输入必须产生 is_correct=False 的诊断结果
- 诊断响应时间 < 3秒（Mock模式下 < 500ms）

---

### F04 8维学习画像动态更新

**功能描述**：基于每轮对话和诊断结果，动态更新学生8维能力画像和知识掌握度图谱。

**输入**：用户ID、用户消息、Agent回复、DiagnosisResult

**处理逻辑**：
1. 加载当前画像（默认各维度0.5）
2. 调用LLM生成增量 delta，解析各维度 δ ∈ [-0.2, +0.2]
3. 应用增量：`dim_score = clamp(dim_score + delta, 0.1, 1.0)`
4. 根据诊断结果更新mastery_map：正确+0.05，错误-0.07（clamp到[0,1]）
5. 重新计算 weak_points（<0.5）和 strong_points（≥0.8）
6. 持久化到数据库 student_profiles 表

**输出**：更新后的完整画像JSON（8维分数 + mastery_map + weak_points + strong_points + turn_count）

**验收标准**：
- 画像更新后 turn_count +1
- 所有维度值在 [0.1, 1.0] 范围内
- LLM调用失败时，画像更新降级为纯确定性更新（mastery_map照常更新）

---

### F05 三类个性化学习资源生成

**功能描述**：按知识点和难度，生成doc（知识文档）、exercise（练习题）、code（代码示例）三类学习资源。

**输入**：
- `knowledge_point`（知识点名称，1-100字符）
- `resource_type`（"doc" | "exercise" | "code"）
- `difficulty`（难度1-5）
- 检索上下文文档（可选）

**处理逻辑**：
1. RetrieverAgent 检索 course_docs 集合，获取3条相关文档
2. 根据 resource_type 调用对应生成方法（_generate_doc/_generate_exercise/_generate_code）
3. 构建Prompt，调用LLM生成内容（doc 1000 tokens，exercise 800 tokens，code 800 tokens）
4. 质量评估：`quality_score = 0.6 + 0.4 * confidence`
5. 持久化到 learning_resources 表，返回 resource_id

**输出**：resource_id、resource_type、knowledge_point、title、content、metadata、created_at、quality_score

**验收标准**：
- 内容长度 ≥ 30 字符
- 包含 resource_id（UUID格式）
- 不支持的 resource_type 返回 400 错误
- quality_score 在 [0.6, 1.0] 范围内

---

### F06 知识图谱引导的个性化学习路径规划

**功能描述**：基于学生画像的薄弱点和知识图谱前置依赖关系，规划个性化学习路径。

**输入**：用户ID、学生画像（含mastery_map和weak_points）、目标知识点ID列表（可选）、最大节点数（1-20，默认10）

**处理逻辑**：
1. 确定学习目标：优先使用 weak_points[:3]；若无薄弱点，选择图谱前3个节点
2. `find_weak_prerequisites`：DFS遍历目标节点的所有前置知识，筛选掌握度 < 0.65 的节点
3. `topological_sort`（Kahn算法）：确定学习顺序，按章节/难度/ID三级排序
4. `_build_path_nodes`：为每个节点计算状态（completed/in_progress/pending/locked）和推荐理由
5. 持久化到 learning_paths 和 learning_path_nodes 表

**输出**：path_id、title、total_estimated_time（分钟）、nodes列表（含node_id/node_name/status/current_mastery/recommendation_reason/suggested_resources）

**验收标准**：
- 输出节点数 ≤ max_nodes
- 每个节点包含 recommendation_reason（≥12字符）
- 前置节点在目标节点之前排列（拓扑顺序正确）

---

### F07 协议仿真实验室（SimulatorView）

**功能描述**：提供网络协议交互式仿真，通过可视化动画演示协议运行过程。

**输入**：仿真场景选择（TCP握手/HTTP请求/DNS解析等）

**处理逻辑**：前端SimulatorView基于Canvas动画实现协议状态机可视化

**输出**：协议执行步骤动画展示、状态转换说明

**验收标准**：SimulatorView页面可访问，至少展示TCP三次握手场景

---

### F08 Agent执行日志查询

**功能描述**：记录并查询每个会话中各Agent的执行日志，用于调试和教学追踪。

**输入**：session_id

**处理逻辑**：查询 agent_logs 表，按时间顺序返回该会话的所有Agent执行记录

**输出**：日志列表（log_id、agent_name、action、state、result、timestamp）

**验收标准**：
- 每次chat/stream请求至少生成3条日志（Retriever/Diagnosis/Orchestrator）
- 返回数据按 timestamp 升序排列

---

### F09 RAG知识库检索与问答

**功能描述**：通过向量检索三个知识库（课程文档/协议规范/误解库），为LLM生成提供精确上下文。

**输入**：检索查询文本

**处理逻辑**：
1. LLM扩展检索关键词（_expand_query）
2. 并行检索三个ChromaDB集合（course_docs/protocol_specs/misconceptions）
3. ChromaDB不可用时降级至TF-IDF本地索引
4. 知识图谱关键词匹配（search_by_keyword，返回前5个节点）

**输出**：docs列表、protocols列表、misconceptions列表、graph_nodes列表

**验收标准**：
- 返回结构包含4个键（docs/protocols/misconceptions/graph_nodes）
- ChromaDB降级后系统仍能返回检索结果（来源标记为"local_index"）

---

## 第四章 非功能需求

### 4.1 性能需求

| 性能指标 | 要求 | 说明 |
|---|---|---|
| SSE首字响应 | < 1秒 | 从请求到首个agent_start事件的延迟 |
| 诊断完成时间 | < 3秒 | 从接收消息到diagnosis事件推送的总时间 |
| 学习路径生成 | < 2秒 | 从请求到path_update事件推送的时间 |
| Mock模式响应 | < 500ms | LLM降级模式下的整体响应时间 |
| 数据库查询 | < 100ms | 单次SQLite/MySQL读写操作 |

### 4.2 安全需求

| 安全要素 | 实现方式 |
|---|---|
| API接口保护 | 接口通过 FastAPI HTTPException 处理非法请求 |
| 数据隔离 | session_id 作为用户数据隔离标识，不同会话数据独立 |
| 密码安全 | 环境变量存储API密钥，.env文件已加入.gitignore |
| 域外问题拦截 | Orchestrator内置意图识别，非计算机网络领域问题可标记 |

### 4.3 可用性需求

| 可用性要素 | 要求 |
|---|---|
| LLM不可用降级 | 系统自动切换Mock模式，返回预设模板回复 |
| ChromaDB不可用降级 | 自动切换本地TF-IDF索引（local_index.json） |
| 数据持久化 | 对话历史、画像、日志持久化到SQLite/MySQL |
| 会话恢复 | 相同session_id重连后可恢复历史上下文 |
| 演示账号 | 内置 student-001 默认账号，无需注册即可体验 |

### 4.4 可维护性需求

| 可维护性要素 | 实现方式 |
|---|---|
| 单元测试 | pytest测试框架，3个测试文件覆盖核心Agent逻辑 |
| 日志系统 | Python logging，INFO级别记录Agent执行状态 |
| 模块化Agent | 各Agent独立实现，通过Orchestrator松耦合调度 |
| Prompt可配置 | Prompt模板存储在config/prompts/目录，支持热更新 |
| 环境变量管理 | .env.example提供配置模板，生产环境通过环境变量注入 |

---

## 第五章 接口需求

### 5.1 用户界面接口

系统前端提供9个Vue3单页应用页面：

| 路由 | 页面名称 | 主要功能 |
|---|---|---|
| / | HomeView | 系统首页与功能导航 |
| /chat | ChatView | 智能流式对话 + Agent执行链路可视化 |
| /profile | ProfileView | 8维能力画像展示（雷达图/仪表盘） |
| /simulator | SimulatorView | 网络协议交互式仿真 |
| /diagnosis | DiagnosisView | 三层诊断结果展示 |
| /resources | ResourcesView | 学习资源生成与管理 |
| /path | PathView | 个性化学习路径展示 |
| /logs | LogsView | Agent执行日志查看 |
| /challenger | ChallengerView | 概念挑战问答 |

### 5.2 外部系统接口

| 外部系统 | 接口方式 | 说明 |
|---|---|---|
| 讯飞星火API | WebSocket（wss://spark-api.xf-yun.com/v3.5/chat） | LLM对话生成，认证方式为HMAC-SHA256签名 |
| 讯飞TTS | WebSocket（wss://tts-api.xf-yun.com/v2/tts） | 文字转语音（可选功能） |
| ChromaDB | Python SDK（本地进程内调用） | 向量语义检索 |

### 5.3 API接口列表

| 端点 | 方法 | 功能 |
|---|---|---|
| /health | GET | 服务健康检查 |
| /api/v1/chat/stream | POST | SSE流式对话（核心接口）|
| /api/v1/profile/{user_id} | GET | 获取学生画像 |
| /api/v1/profile/{user_id} | POST | 更新学生画像 |
| /api/v1/path/{user_id} | GET | 获取学习路径 |
| /api/v1/path/plan | POST | 规划学习路径 |
| /api/v1/path/{user_id}/progress | POST | 更新节点学习进度 |
| /api/v1/resources/ | GET | 获取最近生成的资源列表 |
| /api/v1/resources/generate | POST | 生成学习资源 |
| /api/v1/logs/session/{session_id} | GET | 查询Agent执行日志 |

---

## 第六章 附录

### 附录A：词汇表

参见第1.3节术语与缩略语表。

### 附录B：需求跟踪矩阵

| 需求编号 | 需求名称 | 实现Agent/模块 | 测试覆盖 |
|:---:|---|---|---|
| F01 | 用户认证与会话管理 | UserRepository / SessionRepository | 隐式覆盖 |
| F02 | 智能流式对话 | OrchestratorAgent + SSE | test_orchestrator.py |
| F03 | 三层认知诊断 | DiagnosisAgent | test_diagnosis_agent.py |
| F04 | 8维学习画像 | ProfilerAgent | test_student_profile_schema.py |
| F05 | 三类学习资源生成 | ResourceGeneratorAgent | test_resource_generator.py |
| F06 | 个性化路径规划 | PathPlannerAgent + KnowledgeGraph | test_path_planner.py |
| F07 | 协议仿真实验室 | SimulatorView（前端）| 前端E2E |
| F08 | Agent执行日志 | AgentLogRepository | 隐式覆盖 |
| F09 | RAG知识库检索 | RetrieverAgent + VectorStore | test_retriever_agent.py |

---

*本文档遵循 GB/T 8567-2006 SRS 规范编制，所有功能描述均基于项目实际实现代码，不含未实现功能。*
