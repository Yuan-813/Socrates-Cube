# 项目知识地图（Project Knowledge Map）

> 本文件是 Socrates-Cube 的项目知识理解层，基于对源代码、配置、数据的全量分析生成。
> 所有文档生成必须以此为知识来源，确保内容100%来自项目实际。

---

## 一、项目基本信息

| 属性 | 内容 |
|------|------|
| 系统名称 | Socrates Cube（苏格拉底方块） |
| 系统全称 | 多智能体自适应计算机网络学习系统 |
| 参赛标识 | 第十五届中国软件杯 A3赛道参赛作品 |
| 目标用户 | 高校《计算机网络》课程学习者、认证考试备考者 |
| 教材参考 | 谢希仁《计算机网络》第8版 |
| 技术基座 | 讯飞星火大模型（Spark v3.5/Spark-X） |
| 项目版本 | v1.0.0（pyproject.toml） |
| Python约束 | ==3.10.* （严格锁定） |

---

## 二、核心业务定位

### 2.1 解决的核心问题
传统问答系统只判断"对与错"，缺乏对"为什么答错"的深层分析。本系统通过三层认知诊断引擎，深入分析学生错误的根因，生成个性化学习资源和路径。

### 2.2 三大核心创新

**创新1：三层认知诊断框架**
```
学生错误答案
    │
    ▼
L1: 表面错误层（9种错误类型分类）
    LLM提示 + 关键词规则
    错误类型：layer_misplacement/flow_omission/concept_confusion/
             field_misunderstanding/reasoning_breakdown/factual/
             security_misconception/performance_confusion/over_simplification
    │
    ▼
L2: 根因分析层（知识图谱反向遍历 + LLM推理）
    定位缺失的前置知识节点（missing_prerequisites）
    支持多根因排序（root_causes列表）
    │
    ▼
L3: 误区模式层（误解库向量检索 + 模式匹配）
    24+条误解模式库向量匹配
    生成干预建议（intervention_suggestion）
    输出结构化诊断报告 → 驱动资源生成与路径规划
```

**创新2：KP-ACU双层知识图谱**
- KP层：20个课程知识节点（宏观结构，按章节组织）
- ACU层：48个认知理解单元（微观原子点，细粒度分解）
- 边关系：87条有向边（前置依赖 + 知识关联）
- 误解映射：ACU ↔ misconceptions 双向索引

**创新3：混合更新画像策略**
- 确定性增量更新：每轮对话后根据诊断结果调整，无需LLM，延迟<50ms
- LLM全量校准：每5轮触发一次，带10秒去抖窗口（防止频繁调用）
- 8个能力维度持续追踪

---

## 三、系统架构

### 3.1 总体架构（分层）

```
┌─────────────────────────── 表现层 ──────────────────────────────┐
│  Vue3 + TypeScript + Element Plus + TailwindCSS + Pinia        │
│  25个视图页面：对话/诊断/画像/资源/路径/仿真/3D可视化/教材书库等  │
└────────────────────────── SSE流式通信 ──────────────────────────┘
                               ↕ HTTP / SSE
┌─────────────────────────── API层 ──────────────────────────────┐
│  FastAPI 0.111 + Uvicorn 0.29 + sse-starlette 2.1             │
│  23个路由模块：auth/chat/profile/resources/path/simulator等     │
└────────────────────────────────────────────────────────────────┘
                               ↕ 内部调用
┌─────────────────────────── Agent层 ────────────────────────────┐
│  OrchestratorAgent（调度中枢）                                   │
│  ├── DiagnosisAgent（三层认知诊断）                              │
│  ├── ProfilerAgent（8维能力画像）                               │
│  ├── RetrieverAgent（知识检索）                                 │
│  ├── ResourceGeneratorAgent（5类资源生成）                      │
│  ├── PathPlannerAgent（学习路径规划）                           │
│  ├── ChallengerAgent（概念挑战追问）                            │
│  └── SimulatorAgent（协议仿真）                                 │
└────────────────────────────────────────────────────────────────┘
                               ↕
┌─────────────────────────── 知识层 ────────────────────────────┐
│  ChromaDB向量库（三库）  SQLite/MySQL关系库  知识图谱JSON       │
│  course_docs(30+)        11张业务表         20节点+87边        │
│  protocol_specs(200+)    users/profiles/    48 ACU单元        │
│  misconceptions(24+)     chat_sessions/...  误解库24+条        │
└────────────────────────────────────────────────────────────────┘
                               ↕
┌─────────────────────────── LLM层 ─────────────────────────────┐
│  讯飞星火 Spark-X（主，wss://spark-api.xf-yun.com/x2）         │
│  ARK/Doubao（备，OpenAI兼容，doubao-pro-32k）                  │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 前后端通信协议

- **REST API**：认证、画像查询、路径规划等同步操作
- **SSE流式**：`POST /api/v1/chat/stream` → 实时推送Agent执行事件
- **SSE事件类型**：agent_start / agent_end / token / diagnosis / resource / path_update / state_change / done / error / persona_set / scope_notice
- **心跳机制**：每15秒发送 `: heartbeat\n\n` 防止代理超时断连

---

## 四、技术栈全览

### 4.1 后端技术栈

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| Web框架 | FastAPI | 0.111 | API服务 |
| ASGI服务器 | Uvicorn | 0.29 | 进程托管 |
| SSE推送 | sse-starlette | 2.1 | 流式输出 |
| 数据验证 | Pydantic | 2.7.1 | 请求/响应校验 |
| ORM | SQLAlchemy | 2.0.30 | 数据库操作 |
| 异步SQLite | aiosqlite | 0.20.0 | 开发数据库 |
| MySQL | PyMySQL | ≥1.1.0 | 生产数据库 |
| 鉴权 | python-jose | ≥3.3.0 | JWT令牌 |
| 密码 | passlib[bcrypt] | ≥1.7.4 | 密码哈希 |
| LLM-星火 | spark-ai-python | ≥0.4.5 | 讯飞星火API |
| 向量库 | ChromaDB | 可选 | 知识检索 |
| 测试 | pytest | 8.2.0 | 单元测试 |

### 4.2 前端技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 框架 | Vue3 + TypeScript | 3.5 / 5.9 |
| 构建工具 | Vite | 5.4 |
| 状态管理 | Pinia + persistedstate | 2.3 |
| UI组件 | Element Plus | 2.13 |
| CSS框架 | TailwindCSS | 3.4 |
| 数据可视化 | ECharts + vue-echarts | 5.6 |
| 3D渲染 | Three.js | — |
| 思维导图 | Mermaid | 11.x |
| Markdown | marked + highlight.js | — |

### 4.3 AI技术栈

| 组件 | 技术 | 状态 |
|------|------|------|
| 主LLM | 讯飞星火 Spark-X | 已配置 |
| 备用LLM | ARK/Doubao（OpenAI兼容） | 已配置 |
| 向量化 | ChromaDB内置 | 可选 |
| PDF解析 | MinerU（magic-pdf） | 可选，降级PyMuPDF |
| 多模态 | SenseNova-U1 | 可选 |
| TTS | 讯飞超拟人语音合成 | 已配置 |
| 视频生成 | 火山引擎Seedance | 已配置 |

---

## 五、核心功能模块详述

### 5.1 多智能体协同架构

#### OrchestratorAgent（编排器）
- **文件**：`src/loopse/agent/orchestrator.py`（572行）
- **职责**：统一调度7个专业Agent，管理对话状态机，SSE流式推送
- **状态机**：idle → learning → consolidation（5轮触发Challenger）→ planning
- **关键方法**：`async_stream_reply(session_id, user_id, user_message, agent_persona)`
- **人格路由**：4种人格（professor/engineer/peer/interviewer）通过Prompt切换

#### DiagnosisAgent（三层诊断）
- **文件**：`src/loopse/agent/diagnosis.py`（381行）
- **职责**：三层递进式误解诊断
- **参考标准**：RFC 9293(TCP)/RFC 8446(TLS)/RFC 4301(IPsec)/RFC 791(IPv4)/RFC 1034/1035(DNS)/RFC 9110(HTTP)
- **关键方法**：`diagnose()` → `_detect_surface_error()` + `_analyze_root_cause()` + `_match_pattern()`
- **输出字段**：is_correct / confidence / surface_error / error_type / root_causes / missing_prerequisites / pattern / intervention_suggestion / related_node_ids / agent_trace

#### ProfilerAgent（8维画像）
- **文件**：`src/loopse/agent/profiler.py`（362行）
- **8个维度**：conceptual_understanding / protocol_analysis / calculation_ability / error_diagnosis / system_design / knowledge_connection / expression_clarity / self_correction
- **更新策略**：确定性增量（每轮）+ LLM校准（每5轮，带10秒去抖）
- **掌握度**：mastery_map（20个KP节点的掌握度0-1）
- **认知风格**：visual / practical / textual / analogical

#### ResourceGeneratorAgent（资源生成）
- **文件**：`src/loopse/agent/resource_generator.py`（660行）
- **5类资源**：doc / exercise / code / mindmap / script
- **风格映射**：visual→[mindmap,script,doc]；practical→[code,exercise,doc]；textual→[doc,exercise,mindmap]；analogical→[doc,script,exercise]
- **诊断增强**：flow_omission→追加simulator；layer_misplacement→追加mindmap；concept_confusion→追加exercise
- **RL集成**：LinUCB上下文赌博机（软依赖，不可用时降级规则策略）

#### PathPlannerAgent（路径规划）
- **文件**：`src/loopse/agent/path_planner.py`（304行）
- **算法**：拓扑排序（Kahn算法）+ DFS前置依赖搜索
- **三维推荐理由**：graph_dependency / diagnosis_result / cognitive_style
- **节点状态**：completed / in_progress / pending / locked
- **RL集成**：DQN路径节点选择器（软依赖）

#### ChallengerAgent（概念挑战）
- **文件**：`src/loopse/agent/challenger.py`（517行）
- **触发条件**：诊断有误 OR 学习5轮后
- **追问策略**：答对提升难度，答错降维引导（最多5轮，至少2轮）
- **内置题库**：3道fallback挑战题（TCP握手/UDP vs TCP/ARP与MAC）

#### RetrieverAgent（知识检索）
- **文件**：`src/loopse/agent/retriever.py`
- **职责**：向量检索 + 知识图谱查询
- **三库检索**：course_docs(课程文档) / protocol_specs(RFC规范) / misconceptions(误解库)

### 5.2 知识库设计

#### ChromaDB向量库（三库结构）
- **course_docs**：30+条课程文档片段（来自5章Markdown教材）
- **protocol_specs**：200+条RFC协议规范（16个RFC文档清洗后入库）
- **misconceptions**：24+条误解记录（含向量索引）
- **降级方案**：`data/vector_db/local_index.json`（无ChromaDB时使用）

#### 知识图谱（data/knowledge_graph.json）
- **KP节点**（20个）：kp_001~kp_020，按第1-7章组织
- **ACU节点**（48个）：细粒度认知单元
- **边**（87条）：from/to有向依赖关系
- **节点属性**：id/name/chapter/type/difficulty(1-5)/estimated_time(分钟)/keywords/description

#### 误解库（data/misconceptions.json）
- **条数**：24+条，id格式 mc_001~mc_024+
- **字段**：id / knowledge_point / misconception / error_type / correct_answer / chapter / knowledge_node_ids(ACU) / weak_prerequisites(KP) / interventions / kp_node_ids
- **9种错误类型**：flow_omission / layer_misplacement / concept_confusion / field_misunderstanding / reasoning_breakdown / factual / security_misconception / performance_confusion / over_simplification

### 5.3 API设计

#### 核心API端点（按模块）

| 路由模块 | 端点 | 方法 | 说明 |
|---------|------|------|------|
| chat | /api/v1/chat/stream | POST | SSE流式对话（核心接口） |
| profile | /api/v1/profile/{uid} | GET/POST | 8维画像查询/更新 |
| profile | /api/v1/profile/{uid}/report | GET | 学习成长报告 |
| resources | /api/v1/resources/generate-all | POST | 5类资源一键生成 |
| resources | /api/v1/resources/generate | POST | 单类资源生成 |
| path | /api/v1/path/plan | POST | 学习路径规划 |
| simulator | /api/v1/simulator/{scene} | GET | 协议仿真数据 |
| challenger | /api/v1/challenge | POST | 概念挑战 |
| question | /api/v1/question/batch | POST | 批量题目生成 |
| auth | /api/v1/auth/login | POST | JWT登录 |
| auth | /api/v1/auth/register | POST | 用户注册 |
| kb | /api/v1/kb/upload-pdf | POST | PDF知识库上传 |
| exam | /api/v1/exam/... | — | 模拟考试 |
| health | /health | GET | 健康检查 |

---

## 六、数据库设计

### 6.1 数据库选型
- **开发环境**：SQLite（`./edu_agent.db`）
- **生产环境**：MySQL/TDSQL-C Serverless（腾讯云）
- **ORM**：SQLAlchemy 2.0 + aiosqlite 0.20

### 6.2 全部数据表（11张）

| 表名 | 主要字段 | 说明 |
|------|---------|------|
| users | id/username/password_hash/email/phone/role_type/meta_json/is_first_login/onboarded | 用户基本信息 |
| student_profiles | user_id/profile_json/update_time | 8维画像数据（JSON存储） |
| chat_sessions | session_id/user_id/messages/create_time | 对话会话记录 |
| agent_logs | log_id/session_id/agent_name/action/state/timestamp/result | Agent执行日志 |
| knowledge_nodes | node_id/name/chapter/node_type/difficulty/estimated_time/keywords_json/description/prerequisite_ids_json | 知识节点 |
| learning_resources | resource_id/knowledge_node_id/knowledge_point/resource_type/difficulty/title/content/metadata_json/quality_score | 学习资源 |
| learning_paths | path_id/user_id/title/description/status/total_estimated_time/plan_json | 学习路径 |
| learning_path_nodes | id/path_id/node_id/sequence/status/current_mastery/recommendation_reason | 路径节点 |
| assessment_records | assessment_id/user_id/knowledge_node_id/question_type/score/max_score/answer_json/diagnosis_json | 测评记录 |
| misconception_records | id/user_id/knowledge_node_id/pattern/severity/evidence/intervention/last_seen | 用户误解记录 |
| memory_records | id/user_id/persona/memory_type/content/created_at/archived_at | Agent长期记忆 |
| bookmarks | id/user_id/resource_url/resource_title/resource_type/source | 收藏 |

---

## 七、前端页面清单

### 7.1 核心学习功能页面（路由表来源：frontend/src/router/index.ts）

| 页面 | 路由 | 组件文件 | 说明 |
|------|------|---------|------|
| 登录/注册 | /login | LoginViewScheme2.vue | JWT鉴权，支持游客登录 |
| AI引导初始化 | /onboarding | OnboardingScheme1.vue | 5步式新用户画像收集 |
| 系统首页 | / | HomeView.vue | 导航入口 |
| 智能对话 | /chat | ChatViewScheme1.vue | SSE流式，多人格，执行链路可视化 |
| 能力画像 | /profile | ProfileView.vue | 8维雷达图 |
| 诊断面板 | /diagnosis | DiagnosisViewScheme1.vue | 三层诊断交互 |
| 学习资源 | /resources | ResourcesViewScheme1.vue | 5类资源卡片，知识点输入 |
| 学习路径 | /path | PathViewScheme1.vue | 时间线+知识图谱联动 |
| 协议仿真 | /simulator | SimulatorViewScheme3.vue | 7场景Canvas动画 |
| 概念挑战 | /challenger | ChallengerView.vue | 自适应追问 |
| 3D硬件可视化 | /device3d | Hardware3DViewScheme2.vue | Three.js 3D渲染 |
| 教材书库 | /bookhouse | BookHouseScheme3.vue | PDF浏览阅读 |
| PDF知识库 | /bookshelf | BookshelfView.vue | 上传/搜索/问答 |
| Agent日志 | /logs | LogsView.vue | 执行链路追踪 |
| 职业导航 | /career | CareerView.vue | 职业路径推荐 |
| 模拟考试 | /exam | ExamView.vue | 证书备考题库 |
| AI面试 | /interview | InterviewView.vue | 模拟技术面试 |
| AI图谱助手 | /kg-assist | AIKGView.vue | ECharts知识图谱 |
| 统计仪表盘 | /dashboard | DashboardView.vue | 学习数据统计 |
| 用户手册 | /manual | UserManualView.vue | 系统使用说明 |

---

## 八、环境配置与部署

### 8.1 关键环境变量

| 变量名 | 用途 | 必填 |
|--------|------|------|
| XUNFEI_APP_ID | 讯飞星火AppID | 必填（否则Mock模式） |
| XUNFEI_API_KEY | 讯飞API Key | 必填 |
| XUNFEI_API_SECRET | 讯飞API Secret | 必填 |
| XUNFEI_SPARK_URL | 讯飞WebSocket URL | 必填（wss://spark-api.xf-yun.com/x2） |
| OPENAI_COMPAT_BASE_URL | 备用LLM地址 | 可选 |
| DATABASE_URL | 数据库连接串 | 默认sqlite:///./edu_agent.db |
| JWT_SECRET_KEY | JWT密钥（≥32位） | 必填 |
| CHROMA_DB_PATH | ChromaDB路径 | 默认./chroma_db |

### 8.2 启动方式

```bash
# 一键启动（Windows）
start.bat  # 自动创建venv → 安装依赖 → 启动后端

# 前端启动
cd frontend && npm install && npm run dev

# 后端手动启动
uvicorn src.loopse.main:app --reload --host 0.0.0.0 --port 8000
```

### 8.3 服务地址

| 服务 | 地址 |
|------|------|
| 后端API | http://localhost:8000 |
| API文档 | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/health |
| 前端界面 | http://localhost:5173 |

---

## 九、已实现功能 vs Mock/未完成功能

### 已完全实现 ✅
- 8 Agent多智能体协同架构（含OrchestratorAgent调度逻辑）
- 三层认知诊断引擎（L1/L2/L3完整实现，带RFC标准参考）
- 8维能力画像及混合更新策略
- 5类学习资源自适应生成
- 知识图谱KP-ACU双层建模
- 学习路径规划（拓扑排序+三维推荐理由）
- 概念挑战自适应追问（2-5轮）
- SSE流式输出与Agent执行链路可视化
- 协议仿真7场景（TCP握手/挥手/滑动窗口/HTTP/DNS/拥塞控制）
- 多人格虚拟教师（4种人格系统提示词）
- JWT鉴权与5步式用户引导
- ChromaDB三库向量检索
- 域外问题拦截（trust_mechanism.check_question_scope）
- RAG引用溯源机制

### 降级/软依赖（功能可用但效果降级）⚠️
- 域外检测完整性（基础功能已实现，待精细化）
- RL优化（LinUCB/DQN）：不可用时降级到规则策略
- 虚拟教师TTS：无API Key时降级为文字展示
- MinerU PDF解析：无GPU时降级PyMuPDF
- SenseNova多模态：可选，未配置时降级LLM

---

## 十、测试体系

### 10.1 测试框架
- **工具**：pytest 8.2.0 + pytest-asyncio 0.23.7
- **测试目录**：`tests/unit/`
- **配置**：`pyproject.toml` + `tests/conftest.py`

### 10.2 已有测试用例（tests/unit/目录）
- `test_diagnosis_agent.py` - DiagnosisAgent三层诊断测试
- `test_orchestrator.py` - Orchestrator状态机测试
- `test_profiler_agent.py` - ProfilerAgent画像更新测试
- `test_resource_generator.py` - 资源生成测试
- `test_challenger_agent.py` - 概念挑战测试
- `test_path_planner.py` - 路径规划测试
- `test_retriever_agent.py` - 知识检索测试
- `test_knowledge_graph.py` - 知识图谱测试
- `test_misconception_registry.py` - 误解库测试
- `tests/test_student_profile_schema.py` - 画像Schema测试
