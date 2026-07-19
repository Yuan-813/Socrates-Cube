# Socrates-Cube 软件需求规格说明书 v1.0

| 项目 | 内容 |
| --- | --- |
| 文档版本 | v1.0 |
| 编写日期 | 2026-05-17（初稿）/ 2026-07-13（终稿） |
| 适用阶段 | Phase 0–Phase 6 |
| 关联文档 | `docs/项目定位说明.md`、`config/api_schema.yaml`、`docs/architecture/系统开发说明书_v1.md` |

---

## 第一章 项目概述

### 1.1 项目背景

高校《计算机网络》课程知识点密集、协议流程抽象、学生错误模式多样。传统问答系统难以同时完成**知识检索、认知诊断、个性化推荐和过程可解释**。Socrates-Cube 面向软件杯 A3 赛题，构建多智能体自适应学习系统，以谢希仁《计算机网络》第 8 版五章内容为知识边界，为学生提供可追问、可诊断、可规划的一体化辅学体验。

### 1.2 建设目标

1. 提供苏格拉底式流式对话，支持多 Agent 协作过程可视化。
2. 基于课程文档、协议规范、误区库和知识图谱，实现可溯源问答。
3. 提供三层认知诊断，识别表层错误、根因薄弱点与典型误区模式。
4. 维护学生八维画像，驱动资源生成与学习路径规划。
5. 支持在线星火 API 与离线 Mock 双模式，保证答辩演示稳定。

### 1.3 用户与角色

| 角色 | 主要诉求 |
| --- | --- |
| 学生 | 提问概念/流程/计算题，查看诊断、资源和路径推荐 |
| 助教 | 查看诊断标签、Agent 日志，验证系统可解释性 |
| 教师 | 关注知识库来源、误区库质量、验收记录与系统稳定性 |

### 1.4 建设范围

| 范围项 | 说明 |
| --- | --- |
| 课程章节 | 第 1 章概述、第 3 章传输层、第 4 章网络层、第 5 章数据链路层、第 6 章应用层 |
| 后端能力 | FastAPI、多 Agent 编排、SSE、SQLite、向量检索、知识图谱 |
| 前端能力 | Vue3 对话界面、诊断面板、画像雷达、路径时间轴、资源卡片、协议仿真 |
| 不在范围 | 正式教务系统对接、付费内容分发、SeeDance 视频平台最终接入 |

---

## 第二章 功能需求

### 2.1 功能需求总表

| 编号 | 功能名称 | 描述摘要 | 优先级 | 主要接口/模块 |
| --- | --- | --- | --- | --- |
| F01 | 流式对话 | 接收学生问题并以 SSE 流式返回主回复 | P0 | `/api/v1/chat/stream` |
| F02 | 知识库检索 | 联合检索课程文档、协议规范、误区库与知识图谱 | P0 | `RetrieverAgent.search_all()` |
| F03 | 三层认知诊断 | 识别表层错误、根因分析与误区模式匹配 | P0 | `DiagnosisAgent.diagnose()` |
| F04 | 学生画像维护 | 提取并更新八维画像与 mastery_map | P0 | `/api/v1/profile/{id}` |
| F05 | Agent 调度与日志 | 编排多 Agent 调用链并记录运行日志 | P0 | `OrchestratorAgent`、`/api/v1/logs` |
| F06 | 学习资源生成 | 生成 doc / exercise / code / mindmap / script 五类学习资源 | P1 | `/api/v1/resources` |
| F07 | 学习路径规划 | 基于知识图谱前置依赖生成学习路径 | P1 | `/api/v1/path/plan` |
| F08 | 协议仿真演示 | 可视化展示 7 种协议场景（握手/挥手/滑动窗口/HTTP/DNS/拥塞控制） | P1 | `SimulatorPlayer.vue` |
| F09 | 系统可信机制 | 越界拦截 + 引用溯源 + 不确定性声明 | P0 | `trust_mechanism.py` |

### 2.2 F01 流式对话

| 需求项 | 说明 |
| --- | --- |
| 输入 | `message`、`user_id`、`session_id` |
| 输出 | 统一 JSON SSE 事件流 |
| 约束 | 必须支持 `token` 流式输出；整轮结束发送 `done` |
| 降级 | 星火 API 未配置时自动进入 Mock LLM 模式 |
| 验收 | 前端输入「什么是 TCP 三次握手」可看到流式回复 |

### 2.3 F02 知识库检索

| 需求项 | 说明 |
| --- | --- |
| 数据源 | `course_docs`、`protocol_specs`、`misconceptions` |
| 检索方式 | 向量检索 + 本地 JSON 索引降级 + 知识图谱关键词命中 |
| 最低数据量 | `course_docs` ≥ 30 块，`misconceptions` ≥ 20 条 |
| 验收 | 检索「TCP 三次握手」时 `course_docs` ≥ 3 条，`misconceptions` ≥ 3 条 |

### 2.4 F03 三层认知诊断

系统必须提供独立的三层诊断能力，并在 SSE 中通过 `diagnosis` 事件推送结果。

#### 2.4.1 第一层：表层错误识别（Surface Error）

| 字段 | 说明 |
| --- | --- |
| `is_correct` | 学生当前回答是否正确 |
| `surface_error` | 表层错误描述 |
| `error_type` | 错误类型，如 `layer_misplacement`、`flow_omission`、`concept_confusion` |
| `confidence` | 诊断置信度 0–1 |

**典型用例**：学生认为「HTTP 不需要 TCP」，应识别为 `layer_misplacement`。

#### 2.4.2 第二层：根因分析（Root Cause）

| 字段 | 说明 |
| --- | --- |
| `root_causes` | 导致错误的薄弱前置知识点列表 |
| `trigger` | 触发诊断的关键语句或证据 |

**要求**：根因分析需结合检索证据与知识图谱前置依赖，不得脱离知识库空泛生成。

#### 2.4.3 第三层：误区模式匹配（Pattern Match）

| 字段 | 说明 |
| --- | --- |
| `pattern` | 匹配到的典型误区模式名称 |
| `intervention_suggestion` | 可执行的干预建议 |

**要求**：优先匹配 `misconceptions` 集合中的已知误区；匹配失败时允许 LLM 归纳新模式，但需保留 `confidence` 字段。

#### 2.4.4 诊断输出结构

诊断结果必须符合 `config/api_schema.yaml` 中 `DiagnosisResult` 结构，并同步写入 `agent_logs`。

### 2.5 F04 学生画像维护

| 需求项 | 说明 |
| --- | --- |
| 画像维度 | 知识储备、认知风格、学习进度、协议理解、动手能力、常见错误、学习偏好、综合水平（8 维） |
| 能力 | `extract_profile()` 初次提取；`update_from_dialogue()` 增量更新 |
| 数据模型 | 新代码优先使用 `src/loopse/schema/profile.py` 中 YAML 对齐模型 |
| 验收 | `/api/v1/profile/{user_id}` 可返回画像 JSON，前端雷达图可渲染 |

### 2.6 F05 Agent 调度与日志

| 需求项 | 说明 |
| --- | --- |
| 调度器 | `OrchestratorAgent` 负责整轮编排 |
| 协调器 | `AgentCoordinator` 负责意图识别与下游 Agent 激活判断 |
| 日志 | 每轮关键 Agent 调用写入 `agent_logs` |
| SSE 事件 | 必须覆盖 `agent_start`、`agent_end`、`tool_call`、`token`、`diagnosis`、`resource`、`path_update`、`done`、`error` |
| 验收 | `/api/v1/logs/session/{session_id}` 可查询；前端 `AgentLogPanel` 可展示 |

### 2.7 F06 学习资源生成

| 需求项 | 说明 |
| --- | --- |
| 资源类型 | `doc`（知识文档）、`exercise`（练习题）、`code`（代码示例）、`mindmap`（思维导图）、`script`（视频脚本）共 5 类 |
| 生成方式 | 单类接口 `/api/v1/resources/generate`；全量接口 `/api/v1/resources/generate-all`（5 类一次性生成） |
| 触发条件 | 用户意图为资源请求，或 Orchestrator 判定需要生成学习材料 |
| 验收 | 生成结果包含标题、正文、来源/解析等字段，并可在前端资源区展示 |

### 2.8 F07 学习路径规划

| 需求项 | 说明 |
| --- | --- |
| 输入 | 学生画像、`target_nodes`、图谱前置依赖 |
| 输出 | ≥ 3 个路径节点，每节点含 `recommendation_reason`（≥ 20 字）和 `reason_sources`（三维推荐理由） |
| 三维理由 | `graph_dependency`（图谱依赖）、`diagnosis_result`（诊断结果）、`cognitive_style`（认知风格） |
| 进阶路径 | 掌握度 ≥ 0.82 时触发进阶学习目标 |
| 验收 | `POST /api/v1/path/plan` 对空画像不报错；前端 `PathTimeline` 可展示 |

### 2.9 F08 协议仿真演示

| 需求项 | 说明 |
| --- | --- |
| 场景 | TCP 三次握手、四次挥手、滑动窗口、HTTP 请求响应、HTTP分层封装、DNS解析、拥塞控制（7种） |
| 展现 | Canvas/组件动画，支持步骤播放、步进、重置、速度调节 |
| 触发 | 用户消息含「演示/模拟/握手/流程」等关键词时由前端或意图路由触发 |
| 验收 | 仿真组件可渲染并播放所有 7 个场景 |

### 2.10 F09 系统可信机制

#### 2.10.1 知识库溯源要求

| 需求项 | 说明 |
| --- | --- |
| 来源标注 | 生成内容末尾自动追加「参考来源」列表，含来源名称和关键片段 |
| 编号引用 | 在回答中适当位置插入 [1][2] 等引用标记 |
| 最大来源数 | 单条回答最多引用 5 个来源 |

#### 2.10.2 内容安全过滤要求

| 需求项 | 说明 |
| --- | --- |
| 范围校验 | 检测回答是否超出计算机网络范畴 |
| 越界拦截 | 非网络课程问题返回标准拒答模板 |
| 关键词检测 | 快速关键词匹配 + LLM 辅助判断双层 |

#### 2.10.3 越界回答拦截规则

| 规则 | 处理方式 |
| --- | --- |
| 问题含 ≥2 个网络关键词 | 放行 |
| 匹配到越界模式（编程/娱乐/翻译等） | 拒答 + 提示课程范围 |
| 无法确定 | 宽松放行（避免误拦） |

#### 2.10.4 不确定性声明触发条件

| 条件 | 处理方式 |
| --- | --- |
| 诊断置信度 < 0.6 | 自动追加「以上内容仅供参考」声明 |
| LLM 回复质量分 < 0.5 | 追加质量警告 |
| 知识库检索结果为空 | 提示「未找到相关知识」 |

---

## 第三章 非功能需求

### 3.1 性能需求

| 编号 | 需求 |
| --- | --- |
| NFR-P01 | 本地开发环境启动后，`/health` 响应时间 < 1s |
| NFR-P02 | 首轮对话在 Mock 模式下应能完成全链路返回 |
| NFR-P03 | 知识库检索在本地 JSON 索引模式下可用于课堂演示 |

### 3.2 可靠性与降级

| 编号 | 需求 |
| --- | --- |
| NFR-R01 | ChromaDB 不可用时，系统必须降级到 `data/vector_db/local_index.json` |
| NFR-R02 | 星火 API 不可用时，系统自动切换 Mock LLM，不得导致服务崩溃 |
| NFR-R03 | 单个 Agent 失败时，Orchestrator 应尽可能返回可继续学习的答复 |

### 3.3 安全与合规

| 编号 | 需求 |
| --- | --- |
| NFR-S01 | `.env`、数据库文件、向量库运行目录不得提交 Git |
| NFR-S02 | SSE `error` 事件不得泄露 API Key 或完整堆栈 |
| NFR-S03 | 知识库资料仅用于教学演示，不做商业分发 |

### 3.4 可维护性

| 编号 | 需求 |
| --- | --- |
| NFR-M01 | Prompt 模板统一存放于 `config/prompts/`，禁止核心业务硬编码 |
| NFR-M02 | 单元测试可在本地虚拟环境运行，`pytest-asyncio` 支持 async 用例 |
| NFR-M03 | 新环境按 README 执行后可完成健康检查、联通测试与知识库入库 |

### 3.5 兼容性

| 编号 | 需求 |
| --- | --- |
| NFR-C01 | 推荐 Python 3.10；3.10+ 允许运行但给出版本提示 |
| NFR-C02 | Windows / macOS / Linux 均可安装核心依赖 |
| NFR-C03 | 核心 `requirements.txt` 安装不得因 ChromaDB 编译失败而中断 |

---

## 第四章 数据与接口需求

### 4.1 知识库数据需求

| 编号 | 需求 |
| --- | --- |
| FR-KB-01 | 知识库包含 `course_docs`、`protocol_specs`、`misconceptions` 三类集合 |
| FR-KB-02 | 协议规范来源可为 RFC Editor、IANA 等公开资料 |
| FR-KB-03 | 新 clone 环境必须执行 `download_knowledge_sources.py` + `ingest_docs.py --reset` |
| FR-KB-04 | 文本切分统一使用 `src/loopse/kb/text_splitter.py` |

### 4.2 知识图谱需求

| 编号 | 需求 |
| --- | --- |
| FR-KG-01 | `data/knowledge_graph.json` ≥ 20 节点、≥ 18 边 |
| FR-KG-02 | 节点字段含 `id`、`name`、`chapter`、`type`、`difficulty`、`estimated_time`、`keywords`、`description` |
| FR-KG-03 | 支持前置依赖查询、拓扑排序、薄弱前置筛选 |

### 4.3 接口需求

| 接口 | 方法 | 路径 | 说明 |
| --- | --- | --- | --- |
| 健康检查 | GET | `/health` | 返回 `status=ok` |
| 后端联通测试 | GET | `/api/v1/chat/test` | Phase 0 验收接口 |
| 流式对话 | POST | `/api/v1/chat/stream` | SSE 主入口 |
| 用户画像 | GET/POST | `/api/v1/profile/{user_id}` | 画像读写 |
| 学习路径 | GET/POST | `/api/v1/path/*` | 路径查询与规划 |
| 学习资源 | GET/POST | `/api/v1/resources/*` | 资源生成与列表 |
| Agent 日志 | GET | `/api/v1/logs/session/{session_id}` | 会话日志查询 |

详细字段定义以 `config/api_schema.yaml` 为准。

### 4.4 数据库需求

| 表名 | 用途 |
| --- | --- |
| `users` | 用户基本信息 |
| `student_profiles` | 学生画像持久化 |
| `chat_sessions` | 会话记录 |
| `agent_logs` | Agent 调度日志 |

Phase 1 最低要求为 4 表可读写；当前实现已扩展资源、路径等业务表。

---

## 第五章 资源生成与路径规划规格

### 5.1 资源生成规格

- FR-RG-01：系统应支持生成 5 类资源：知识文档（doc）、练习题（exercise）、代码示例（code）、思维导图（mindmap）、视频脚本（script）。
- FR-RG-02：每次资源生成应基于当前用户的 `cognitive_style` 维度调整输出风格。
- FR-RG-03：exercise 类型应根据 `error_type` 映射题型（choice / scenario / fill_blank）。
- FR-RG-04：生成结果应包含 `resource_id`、`resource_type`、`knowledge_point`、`title`、`content`、`metadata`、`created_at`，并写入资源仓储供前端展示。

### 5.2 学习路径规划规格

- FR-PP-01：路径规划应使用知识图谱拓扑排序确定学习顺序。
- FR-PP-02：每个路径节点必须包含 `recommendation_reason`（不少于 20 字）和 `reason_sources`（三维推荐理由结构）。
- FR-PP-03：路径节点数量默认 ≤ 6，可通过 API 参数 `max_nodes` 配置，最大不超过 20。
- FR-PP-04：节点包含 `status`（completed / in_progress / pending / locked）、`current_mastery`、`prerequisites`、`prerequisites_met`、`suggested_resources`。
- FR-PP-05：前端通过 `PathTimeline` 与 `PathReasonModal` 展示路径与节点详情。

### 5.3 知识图谱数据规格

- `data/knowledge_graph.json` 格式：`{ nodes: [...], edges: [...] }`。
- 节点属性：`id`、`name`、`chapter`、`type`、`difficulty`（1-5）、`estimated_time`、`keywords`、`description`。
- 边属性：`from`、`to`、`relation`（prerequisite / related）。
- 最小规模：20 节点，18 条边，覆盖 5 个章节。当前实现为 20 节点、21 条边，覆盖 6 个章节。

---

## 第六章 验收标准

### 6.1 Phase 0 验收

| 编号 | 验收项 | 通过标准 |
| --- | --- | --- |
| ACC-P0-01 | README 快速启动 | 含项目简介、后端/前端启动步骤 |
| ACC-P0-02 | 后端联通 | `GET /api/v1/chat/test` 返回 200 |
| ACC-P0-03 | 健康检查 | `GET /health` 返回 200 |
| ACC-P0-04 | 环境验证 | `python scripts/verify_env.py` 输出 `[OK]` |

### 6.2 Phase 1 验收

| 编号 | 验收项 | 通过标准 |
| --- | --- | --- |
| ACC-P1-01 | 星火流式 | 配置 API Key 后真流式输出；未配置时 Mock 可用 |
| ACC-P1-02 | 检索 TCP | `course_docs` ≥ 3，`misconceptions` ≥ 3 |
| ACC-P1-03 | 前端 SSE | `ChatPanel` 默认连接 `/api/v1/chat/stream` |
| ACC-P1-04 | 协议仿真 | 仿真组件可播放 SYN 动画 |

### 6.3 Phase 2 验收

| 编号 | 验收项 | 通过标准 |
| --- | --- | --- |
| ACC-P2-01 | Orchestrator 调度 | SSE 可见 Retriever / Diagnosis 调用链 |
| ACC-P2-02 | Agent 日志 | `agent_logs` 有调度记录，前端日志面板接 API |
| ACC-P2-03 | 三层诊断 | 返回 surface / root / pattern 结构 |
| ACC-P2-04 | coordinator 拆分 | `coordinator.py` 独立存在并被 Orchestrator 调用 |

### 6.4 Phase 3 验收

| 编号 | 验收项 | 通过标准 |
| --- | --- | --- |
| ACC-P3-01 | 知识图谱 | ≥ 20 节点、≥ 18 边 |
| ACC-P3-02 | 三类资源 | `/api/v1/resources/generate-all` 可一次返回三类 |
| ACC-P3-03 | 路径规划 | 空画像返回 ≥ 3 节点且含推荐理由 |
| ACC-P3-04 | 前端组件链 | DocCard / ExerciseCard / CodeCard / PathTimeline 可用 |

### 6.5 Phase 4 验收

Phase 4 完整验收记录见 `docs/results/phase4_acceptance_results.md`。

### 6.6 Phase 5 验收（Code Freeze）

| 编号 | 验收项 | 通过标准 |
| --- | --- | --- |
| ACC-P5-01 | 三层诊断准确率 | 整体准确率 ≥ 85% |
| ACC-P5-02 | 误解库 | ≥ 50 条，覆盖全部 20 个知识点 |
| ACC-P5-03 | 协议仿真 | 7 个场景全部精品化（动画流畅 + 交互完整） |
| ACC-P5-04 | 仿真播放器 | 支持播放/暂停/步进/调速/进度拖拽/全屏/报文详情 |
| ACC-P5-05 | 路径理由 | 三维化（图谱 + 诊断 + 风格） |
| ACC-P5-06 | Mock 模式 | 前后端均可独立运行，全演示链路 0 报错 |
| ACC-P5-07 | 一键启动 | `start.bat` 一条命令启动前后端 |
| ACC-P5-08 | 文档 | SRS / 开发说明书终稿完成，测试/操作手册 ≥ 90% |
| ACC-P5-09 | PPT 大纲 | 14 页框架清晰，配合 7 分钟演示脚本 |

### 6.7 Phase 6 验收（体验打磨）

| 编号 | 验收项 | 通过标准 |
| --- | --- | --- |
| ACC-P6-01 | 后端稳定性 | LLM 超时降级 + 向量库兑底 + DB 异步写入 + SSE 心跳保活 |
| ACC-P6-02 | 后端性能 | 检索 TTL 缓存 5 分钟 + 画像去抖 10 秒 + 日志异步写入 |
| ACC-P6-03 | 前端三态 | Loading(spinner/dots/progress) + Empty(action) + Error(retry) |
| ACC-P6-04 | 前端过渡动效 | 消息滑入动画 + 页面 fade-slide 过渡 |
| ACC-P6-05 | 前端响应式 | 1280px 断点适配 + 首页改版完成 |
| ACC-P6-06 | 演示模式 | Ctrl+Shift+D 切换 + Ctrl+Shift+C 清空 + 演示徽章 |
| ACC-P6-07 | 代码质量 | Agent docstring 补充 + console.log 清理 + 构建零报错 |
| ACC-P6-08 | 演示文档 | 黄金脚本 + 分镜 + 逐字稿 + 答辩问答 + 技术问答 + PPT大纲 |
| ACC-P6-09 | 演示预热 | `python scripts/demo_warmup.py` 一键预热 |
| ACC-P6-10 | 5 类资源兑底 | _fallback_content() 为所有资源类型提供结构化备选 |

---

## 附录 A 术语表

| 术语 | 说明 |
| --- | --- |
| Agent | 具备单一职责的智能体模块，如 Retriever、Diagnosis |
| SSE | Server-Sent Events，服务器向浏览器推送流式事件 |
| RAG | Retrieval-Augmented Generation，检索增强生成 |
| Mock 模式 | 未配置外部 LLM 时的本地降级响应模式 |

## 附录 B 变更记录

| 版本 | 日期 | 变更说明 |
| --- | --- | --- |
| v1.0 | 2026-05-17 | 初稿 |
| v1.0-rev | 2026-07-12 | 按第一章至第六章标准结构重排；补齐 F01–F08 与三层诊断专节 |
| v1.0-final | 2026-07-13 | Phase 5 终稿：资源类型 3→5、三维路径理由、Phase 5 验收标准 |
| v1.0-phase6 | 2026-07-13 | Phase 6 终稿：增加体验打磨验收标准（ACC-P6-01~10） |
