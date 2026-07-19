# 系统开发说明书 v1.0

## 一、项目概述

**项目名称：** Socrates-Cube 苏格拉底问答学习系统  
**目标赛项：** 软件杯 A3 — AI 赋能教育创新  
**核心场景：** 面向《计算机网络》课程的多智能体自适应学习系统  
**文档版本：** v1.0 终稿（2026-07-19 最终更新）

> **开源工具集成声明**：本系统集成以下开源项目
> - [MinerU](https://github.com/opendatalab/MinerU) (Apache 2.0) — PDF 高精度解析引擎
> - [OpenMAIC](https://github.com/THU-MAIC/OpenMAIC) (MIT) — 清华大学 MAIC 实验室多智能体教学平台（架构参考）
> - [ChatGLM3](https://github.com/THUDM/ChatGLM3) (Apache 2.0) — 清华大学 KEG 实验室开源对话模型（GLM-4 商业版接入）
> - [SenseNova-U1](https://github.com/OpenSenseNova/SenseNova-U1) — 多模态信息图生成

---

## 二、技术栈

### 后端
| 组件 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 运行时 |
| FastAPI | 0.111.0 | Web 框架 |
| uvicorn | 0.29.0 | ASGI 服务器 |
| sse-starlette | 2.1.0 | SSE 推送 |
| SQLAlchemy | 2.0.30 | ORM |
| aiosqlite | 0.20.0 | 异步 SQLite |
| ChromaDB | 0.5.0 | 向量数据库 |
| spark-ai-python | >=0.4.5 | 讯飞星火 LLM |
| python-dotenv | 1.0.1 | 环境变量管理 |

### 前端
| 组件 | 版本 | 用途 |
|------|------|------|
| Vue | 3.x | UI 框架 |
| TypeScript | 5.x | 类型安全 |
| Vite | 5.x | 构建工具 |
| TailwindCSS | 3.x | 样式 |
| Pinia | 2.x | 状态管理 |
| ECharts | 5.x | 数据可视化 |
| markdown-it | 14.x | Markdown 渲染 |

---

## 三、C4 架构设计

### 3.1 Context 上下文图（C4 - Level 1）

```
┌─────────────────────────────────────────────────────────────────┐
│                        学生 / 教师用户                          │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              │ 浏览器访问
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Socrates-Cube 系统                              │
│  ┌──────────┐  ┌────────────┐  ┌───────────────┐              │
│  │ 前端 SPA  │  │  后端 API   │  │  知识库/数据库 │              │
│  └──────────┘  └────────────┘  └───────────────┘              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              │ API 调用
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    讯飞星火大模型 API                             │
└─────────────────────────────────────────────────────────────────┘
```

**系统上下文说明：**
- **主要用户**：学习计算机网络的学生、课程助教、授课教师
- **外部依赖**：讯飞星火大模型 API（提供自然语言理解与生成能力）
- **核心价值**：通过多 Agent 协作为学生提供个性化、自适应的计算机网络课程辅导

### 3.2 Container 容器图（C4 - Level 2）

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                          Socrates-Cube 应用系统                                      │
│                                                                               │
│  ┌─────────────────────┐    ┌──────────────────────────────────────┐               │
│  │   前端应用 (Vue)   │    │        后端服务 (FastAPI)        │               │
│  │                   │    │                                  │               │
│  │  - ChatPanel      │    │  ┌──────────────────────────┐   │               │
│  │  - DiagnosisPanel │    │  │   API 路由层             │   │               │
│  │  - ProfileRadar   │    │  │   (chat/resources/...)    │   │               │
│  │  - PathTimeline    │    │  └──────────┬───────────────┘   │               │
│  │  - AgentLogPanel  │    │             │                   │               │
│  └─────────┬─────────┘    │  ┌──────────▼───────────────┐   │               │
│            │              │  │   OrchestratorAgent        │   │               │
│  HTTP/SSE  │              │  │   (多Agent协调器)           │   │               │
│            │              │  └──────┬───────┬───────┬──────┘   │               │
│            │              │         │       │       │          │               │
│            │              │  ┌────▼───┐ ┌─▼────┐ ┌▼───────┐ ┌▼──────────┐ │
│            │              │  │Retriever│ │Diagnosis│ │Profiler│ │ResourceGen│ │
│            │              │  │  Agent  │ │ Agent │ │ Agent │ │  Agent  │ │
│            │              │  └─────────┬─┘ └───────┘ └───────┘ └─────────┘ │
│            │              │          │                                    │               │
│            │              │  ┌───────▼─────────┐    ┌──────────────┐    │               │
│            │              │  │  PathPlanner    │    │  数据访问层     │    │               │
│            │              │  │    Agent         │    │  (Repository)  │    │               │
│            │              │  └─────────────────┘    └───────┬──────┘    │               │
│            │              │                           │             │               │
└────────────┴──────────────┘───────────────────────────┼─────────────┘               │
                                                         │                             │
                                                         ▼                             │
                                               ┌─────────────────┐                  │
                                               │   数据存储层        │                  │
                                               │  - SQLite (业务)│                  │
                                               │  - ChromaDB (向量)│                  │
                                               │  - 知识图谱 JSON  │                  │
                                               └─────────────────┘                  │
                                                                                   └───────────────┘
```

**容器说明：**

| 容器 | 技术选型 | 职责 |
|------|----------|------|
| 前端 SPA | Vue 3 + TypeScript | 用户交互界面，展示对话、诊断、画像、路径、资源、日志 |
| 后端 API 服务 | FastAPI + uvicorn | 提供 REST API 和 SSE 流式接口，协调各 Agent 工作 |
| 数据库 | SQLite + SQLAlchemy | 存储用户、会话、画像、路径、资源、日志等业务数据 |
| 向量数据库 | ChromaDB | 存储课程文档、协议规范、误区库，支持相似度检索 |
| 知识图谱 | JSON 文件 + 内存索引 | 描述知识点之间的前置依赖关系，支持路径规划 |

### 3.3 Component 组件图（C4 - Level 3 - 后端 Agent 层）

```
┌─────────────────────────────────────────────────────────────────┐
│                    OrchestratorAgent                              │
│  (总协调器 - 意图识别、流程编排、SSE 事件发射)                     │
└──┬────────────┬────────────┬────────────┬────────────┬─────────┘
   │            │            │            │            │
   ▼            ▼            ▼            ▼            ▼
┌───────┐  ┌─────────┐  ┌────────┐  ┌──────────┐  ┌──────────┐
│Retriever│  │Diagnosis│  │Profiler│  │Resource  │  │PathPlanner│
│ Agent  │  │ Agent   │  │ Agent  │  │Generator │  │  Agent    │
│        │  │         │  │        │  │  Agent   │  │           │
│-向量检索│  │-表层错误  │  │-八维画像│  │-文档生成  │  │-拓扑排序   │
│-图谱检索│  │-根因分析  │  │-薄弱点  │  │-题目生成  │  │-进阶路径   │
│-误区检索│  │-模式匹配  │  │-更新维护│  │-代码生成  │  │-节点推荐   │
└───┬────┘  └────┬────┘  └───┬────┘  └────┬─────┘  └─────┬─────┘
    │              │             │              │                │
    └──────────────┴─────────────┴──────────────┴────────────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │  AgentCoordinator  │
                        │  (意图识别与路由)   │
                        └─────────────────────┘
```

### 3.4 Component 组件图（C4 - Level 3 - 前端层）

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端应用层                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Views (页面层)                             │    │
│  │  HomeView / ChatView / DiagnosisView / ProfileView       │    │
│  │  PathView / ResourcesView / LogsView / ChallengerView  │    │
│  └───────────────────────┬─────────────────────────────────┘    │
│                          │                                      │
│  ┌──────────────────────▼─────────────────────────────────┐    │
│  │                   Components (组件层)                      │    │
│  │  ChatPanel / DiagnosisPanel / AgentStatusBar         │    │
│  │  AgentLogPanel / ProfileRadar / PathTimeline           │    │
│  │  ResourceTabBar / ChatMessage                        │    │
│  └───────────────────────┬─────────────────────────────────┘    │
│                          │                                      │
│  ┌──────────────────────▼─────────────────────────────────┐    │
│  │                    Stores (状态层 - Pinia)                   │    │
│  │  chatStore / userStore / pathStore / resourceStore   │    │
│  └───────────────────────┬─────────────────────────────────┘    │
│                          │                                      │
│  ┌──────────────────────▼─────────────────────────────────┐    │
│  │                  Composables (组合层)                  │    │
│  │  useChatSSE / useFetchSSE                              │    │
│  └───────────────────────┬─────────────────────────────────┘    │
│                          │                                      │
│  ┌──────────────────────▼─────────────────────────────────┐    │
│  │                    API Layer (API 层)                          │    │
│  │  chat.ts / logs.ts / resources.ts / path.ts              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、状态图（State Diagram）

### 4.1 对话会话状态图

```
                    ┌─────────────┐
                    │   Idle    │
                    │ (空闲等待) │
                    └──────┬──────┘
                           │
                    用户输入消息
                           │
                           ▼
                    ┌─────────────┐
                    │  Receiving   │
                    │ (接收输入)   │
                    └──────┬──────┘
                           │
                 开始 SSE 连接
                           │
                           ▼
              ┌──────────────────────────┐
              │  Agent_Retrieving    │
              │ (检索知识库)     │
              └────────┬─────────┘
                       │
              检索完成，开始诊断
                       │
                       ▼
              ┌──────────────────┐
              │  Diagnosing    │
              │ (三层诊断中)    │
              └────────┬─────────┘
                       │
                诊断完成，生成回复
                       │
                       ▼
              ┌──────────────────┐
              │  Replying       │
              │ (流式回复中)   │
              └────────┬─────────┘
                       │
              回复完成，更新画像
                       │
                       ▼
              ┌──────────────────┐
              │  UpdatingProfile│
              │ (更新画像/路径) │
              └────────┬─────────┘
                       │
                  全部完成
                       │
                       ▼
                    ┌─────────────┐
                    │   Done     │
                    │ (回复完成)   │
                    └──────┬──────┘
                           │
                           ┌───────
                    错误/异常
                           │
                           ▼
                    ┌─────────────┐
                    │   Error    │
                    │ (错误状态)  │
                    └─────────────┘
```

### 4.2 Agent 生命周期状态图

```
           初始化
             │
             ▼
        ┌─────────┐
        │  Idle   │◄───────────┐
        │ (空闲)  │            │
        └────┬────┘            │
             │ 调用开始        │
             ▼                 │
        ┌─────────┐           │
        │ Running  │           │
        │ (运行中) │           │
        └────┬────┘           │
             │                 完成/失败       │
             ▼                 │
        ┌─────────┐           │
        │  Done  │───────────┘
        │ (完成)  │
        └─────────┘
```

### 4.3 学习路径节点状态图

```
        ┌──────────┐
        │  Locked  │
        │ (已锁定)  │
        └─────┬────┘
              │
         前置条件满足
              │
              ▼
        ┌──────────┐
        │ Pending  │──────────┐
        │ (待学习)  │      │
        └─────┬────┘      │
              │           用户开始学习   │
              ▼           │
        ┌──────────┐      │
        │In_Progress│     │
        │ (学习中)   │     │
        └─────┬────┘      │
              │           │
         学习完成         跳过
              │           │
              ▼           │
        ┌──────────┐      │
        │Completed │◄─────┘
        │ (已完成)  │
        └──────────┘
```

---

## 五、接口规格说明

### 5.1 对话接口

#### 5.1.1 SSE 流式对话

| 项目 | 说明 |
|------|------|
| 方法 | POST |
| 路径 | `/api/v1/chat/stream |
| Content-Type | application/json |
| 响应类型 | text/event-stream (SSE) |

**请求体：**
```json
{
  "message": "什么是TCP三次握手？",
  "user_id": "user_001",
  "session_id": "session_001"
}
```

**SSE 事件类型：**

| 事件类型 | 触发时机 | 数据字段 |
|---------|---------|---------|
| `agent_start` | Agent 开始执行 | `agent_name`, `data.message` |
| `agent_end` | Agent 执行完成 | `agent_name`, `data.message` |
| `tool_call` | Agent 调用工具 | `agent_name`, `data.tool_name`, `data.status` |
| `token` | LLM 流式 token 到达 | `agent_name`, `data.token` |
| `diagnosis` | 诊断完成 | `agent_name`, `data` (DiagnosisResult) |
| `resource` | 资源生成完成 | `agent_name`, `data` (LearningResource) |
| `path_update` | 路径更新完成 | `agent_name`, `data` (LearningPath) |
| `done` | 整轮对话完成 | `agent_name`, `data.session_id`, `data.total_time_ms` |
| `error` | 发生错误 | `agent_name`, `data.error` |

### 5.2 画像接口

#### 5.2.1 获取用户画像

| 项目 | 说明 |
|------|------|
| 方法 | GET |
| 路径 | `/api/v1/profile/{user_id} |
| 响应 | StudentProfile 对象 |

#### 5.2.2 更新用户画像

| 项目 | 说明 |
|------|------|
| 方法 | POST |
| 路径 | `/api/v1/profile/{user_id}` |
| 请求体 | 部分画像更新字段 |
| 响应 | 更新后的 StudentProfile |

### 5.3 学习路径接口

#### 5.3.1 获取当前学习路径

| 项目 | 说明 |
|------|------|
| 方法 | GET |
| 路径 | `/api/v1/path/{user_id}` |
| 响应 | LearningPath 对象 |

#### 5.3.2 规划新路径

| 项目 | 说明 |
|------|------|
| 方法 | POST |
| 路径 | `/api/v1/path/plan` |
| 请求体 | `{ user_id, target_nodes?, max_nodes? }` |
| 响应 | LearningPath 对象 |

#### 5.3.3 更新节点进度

| 项目 | 说明 |
|------|------|
| 方法 | POST |
| 路径 | `/api/v1/path/{user_id}/progress` |
| 请求体 | `{ node_id, status, mastery? }` |
| 响应 | 更新后的 LearningPath |

### 5.4 资源接口

#### 5.4.1 生成指定类型资源

| 项目 | 说明 |
|------|------|
| 方法 | POST |
| 路径 | `/api/v1/resources/generate` |
| 请求体 | `{ knowledge_point, resource_type, difficulty? }` |
| 响应 | LearningResource 对象 |

#### 5.4.2 一次性生成全部三类资源

| 项目 | 说明 |
|------|------|
| 方法 | POST |
| 路径 | `/api/v1/resources/generate-all` |
| 请求体 | `{ knowledge_point, difficulty? }` |
| 响应 | `{ knowledge_point, docs, exercise, code, total_resources }` |

#### 5.4.3 检索知识库

| 项目 | 说明 |
|------|------|
| 方法 | POST |
| 路径 | `/api/v1/resources/search` |
| 请求体 | `{ knowledge_point, top_k? }` |
| 响应 | 检索结果数组 |

### 5.5 日志接口

#### 5.5.1 获取会话 Agent 日志

| 项目 | 说明 |
|------|------|
| 方法 | GET |
| 路径 | `/api/v1/logs/session/{session_id}` |
| 响应 | AgentLog 数组 |

### 5.6 健康检查接口

| 项目 | 说明 |
|------|------|
| 方法 | GET |
| 路径 | `/health` |
| 响应 | `{ status: "ok" }` |

---

## 六、目录结构

```
Socrates-Cube/
├── src/loopse/
│   ├── agents/        # 8个Agent：orchestrator, coordinator, diagnosis, 
│   │                  # retriever, profiler, resource_generator,
│   │                  # path_planner, cognitive_engine
│   ├── api/           # FastAPI路由：chat, profile, logs, resources, path
│   ├── core/          # llm_client（Spark API + mock回退）
│   ├── db/            # SQLAlchemy模型、连接、仓库层
│   ├── kb/            # vector_store（ChromaDB）+ knowledge_graph
│   └── main.py        # 应用入口，路由注册
├── config/
│   ├── prompts/       # 按Agent分类的提示词模板文件
│   └── api_schema.yaml
├── data/
│   ├── cleaned/       # Markdown课程文本（5章）
│   ├── raw/          # misconceptions.json（24条）
│   └── knowledge_graph.json  # 20节点21边知识图谱
├── frontend/src/
│   ├── types/         # TypeScript类型定义（按领域拆分）
│   ├── api/           # API客户端：chat, path, resources, logs
│   ├── stores/        # Pinia：chat, user, path, resource
│   ├── composables/   # useSSE（SSE流处理）
│   ├── components/    # UI组件（资源卡片、路径时间轴等）
│   └── views/         # 页面视图
├── scripts/
│   ├── init_db.py     # 数据库初始化
│   ├── verify_env.py  # 环境校验
│   ├── ingest_docs.py # 课程文档入库ChromaDB
│   └── build_knowledge_base.py # 一键构建知识库
└── tests/
    ├── unit/          # 单元测试
    └── conftest.py    # pytest全局配置
```

---

## 七、部署说明

### 7.1 后端启动

```bash
cd Socrates-Cube
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows
# source .venv/bin/activate       # macOS / Linux

pip install -r requirements.txt
copy .env.example .env              # 填入讯飞 API Key（可选）

# 知识库入库（必做）
python scripts/build_knowledge_base.py

# 初始化数据库
python scripts/init_db.py

# 启动服务
uvicorn src.loopse.main:app --reload --host 0.0.0.0 --port 8000
```

### 7.2 前端启动

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

### 7.3 一键启动（Windows）

直接双击项目根目录下的 `start.bat` 即可启动后端服务。

---

## 八、Agent 协作流程

### 8.1 正常问答链路

```
用户输入 → Orchestrator → Profiler(画像) → Retriever(检索) → LLM流式回复
```

### 8.2 诊断链路

```
用户输入 → Orchestrator → Profiler → Retriever → Diagnosis(三层诊断) → ResourceGen(资源) → PathPlanner(路径)
```

### 8.3 仿真链路

```
用户输入 → Orchestrator → Retriever → Simulator(仿真场景数据) → ResourceGen(配套资源)
```

### 8.4 全链路协作流程

```
用户输入
    │
    ▼
OrchestratorAgent（接收问题）
    │
    ├─→ AgentCoordinator（意图识别 + 知识点提取）
    │
    ├─→ RetrieverAgent（三库联合检索：course_docs / protocol_specs / misconceptions + 知识图谱）
    │
    ├─→ DiagnosisAgent（三层认知诊断：表层错误 → 根因分析 → 误区模式匹配）
    │
    ├─→ LLM 流式生成主回复（SSE token 事件）
    │
    ├─→ TrustMechanism（可信机制：范围校验 + 溯源标注 + 不确定性声明）
    │
    ├─→ ProfilerAgent（八维画像 + mastery_map 更新）
    │
    ├─→ [按需] ResourceGeneratorAgent（doc/exercise/code/mindmap/script 五类资源）
    │
    └─→ [按需] PathPlannerAgent（知识图谱路径规划 + 进阶路径）
    │
    ▼（各 Agent 结果封装为 SSE 事件）
前端 useChatSSE() 消费：
    ├─── chatStore（消息+流token+诊断结果+Agent状态）
    ├─── userStore（画像更新→雷达图）
    ├─── resourceStore（资源卡片）
    └─── pathStore（路径时间轴）
```

---

## 九、协议仿真引擎设计

### 9.1 参数化仿真原理

协议仿真引擎采用「场景数据 + Canvas渲染」分离架构。每个仿真场景定义为一组有序的报文步骤，每步包含发送方、接收方、标志位、序列号、确认号、状态变化、描述等结构化数据。前端 `SimulatorPlayer.vue` 根据步骤数据驱动 Canvas 动画。

### 9.2 场景库结构

当前支持 7 个仿真场景：

| 场景ID | 名称 | 步骤数 | 说明 |
|--------|------|:------:|------|
| three_way_handshake | TCP 三次握手 | 3 | 建立连接 |
| four_way_wavehand | TCP 四次挥手 | 4 | 关闭连接 |
| sliding_window | 滑动窗口 | 6 | 流量控制 |
| http_request | HTTP 请求响应 | 11 | 完整 HTTP 过程 |
| http_encapsulation | HTTP 分层封装 | 6 | 逐层封装/解封装 |
| dns_resolution | DNS 解析 | 5 | 递归+迭代查询 |
| congestion_control_basic | 拥塞控制 | 6 | 慢启动/拥塞避免 |

### 9.3 前端渲染协议

- 动画引擎：Canvas 2D + requestAnimationFrame
- 布局：双栏（Canvas 动画 + 侧面板状态机 + 步骤详情）
- 交互：点击步骤查看报文详情，支持步进/播放/暂停/重置/速度调节

---

## 十、系统可信机制设计

### 10.1 三层防护架构

```
用户问题
    │
    ├─→ 第一层：范围校验（verify_scope / check_question_scope）
    │    快速关键词匹配 + LLM 辅助判断
    │    越界问题 → 拒答 + 提示课程范围
    │
    ├─→ 第二层：溯源标注（add_source_annotations）
    │    检索来源编号 + 内容末尾追加参考来源列表
    │
    └─→ 第三层：不确定性声明（add_uncertainty_statement）
         置信度 < 0.6 → 追加「仅供参考」声明
```

### 10.2 溯源机制

- 每篇生成内容最多引用 5 个来源
- 来源包含名称 + 关键片段摘要
- 来源按检索相关性排序

### 10.3 范围校验

- 维护约 50 个计算机网络领域关键词
- 命中 ≥3 个关键词：放行
- 匹配越界模式（编程/娱乐/翻译）：拒答
- 无法确定：宽松放行

---

## 十一、数据库设计

### 11.1 ER 图文字描述

- **users** (1) → (N) **student_profiles**：用户拥有画像
- **users** (1) → (N) **chat_sessions**：用户拥有会话
- **chat_sessions** (1) → (N) **agent_logs**：会话产生日志
- **users** (1) → (N) **learning_paths**：用户拥有路径
- **resources** 独立表：由 ResourceGenerator 生成

### 11.2 五张表字段说明

| 表名 | 关键字段 | 说明 |
|------|----------|------|
| users | id, user_id, created_at | 用户基本信息 |
| student_profiles | id, user_id, profile_json, updated_at | 八维画像 JSON |
| chat_sessions | id, session_id, user_id, messages_json, created_at | 会话消息列表 |
| agent_logs | id, session_id, agent_name, action, input_state, output_state, timestamp | Agent 调度日志 |
| learning_paths | id, user_id, nodes_json, created_at, updated_at | 路径节点列表 |

---

## 十二、知识库设计

### 12.1 三库结构

系统知识库由三个独立集合组成，支持联合检索：

| 集合名称 | 数据源 | 条目数 | 检索方式 |
|---------|---------|:------:|----------|
| course_docs | 谢希仁《计算机网络》第8版 5 章 | 5 章 Markdown | 向量检索 + 文本切分 |
| protocol_specs | RFC 规范 + IANA 协议号 | 11 份 RFC/IANA | 向量检索 + 关键词 |
| misconceptions | 常见误解库 | 60+ 条 | JSON 索引 + 语义匹配 |

### 12.2 知识图谱设计

- **节点规模**：20 个知识点节点，覆盖 6 个章节
- **边关系**：21 条前置依赖边 + 关联边
- **节点属性**：id, name, chapter, type, difficulty(1-5), estimated_time, keywords, description
- **查询能力**：前置依赖查询、拓扑排序、薄弱前置筛选

### 12.3 误解库设计

每条误解包含 7 个字段：
- `id`：唯一标识（mc_001 ~ mc_060）
- `knowledge_node_id`：对应知识点（kp_001 ~ kp_020）
- `wrong_statement`：学生典型错误表述
- `correct_explanation`：正确解释
- `root_cause`：根因分析
- `misconception_pattern`：所属误解模式（8 种枚举）
- `difficulty`：隐蔽程度 1-5

---

## 十三、关键算法与机制

### 13.1 三层诊断算法

```
输入：学生回答文本 + 当前画像
    │
    ▼
第一层：表面错误检测 (surface_error.txt)
    ├── 7 种错误类型匹配 + 置信度校准
    ├── 输出：error_type, is_correct, confidence
    │
    ▼
第二层：根因溯源 (root_cause.txt)
    ├── 知识图谱节点注入 + 画像维度关联
    ├── 输出：root_causes[], missing_prerequisites[]
    │
    ▼
第三层：模式匹配 (pattern_match.txt)
    ├── 6 种模式 + 混合模式 + 干预建议
    └── 输出：pattern, intervention_suggestion, follow_up_question
```

### 13.2 路径规划算法

```
输入：画像 + 目标节点 + 知识图谱
    │
    ▼
Step 1：拓扑排序 → 确定学习顺序
    │
    ▼
Step 2：前置依赖检查 → 补充缺失节点
    │
    ▼
Step 3：三维理由生成
    ├── graph_dependency：知识图谱前置依赖链
    ├── diagnosis_result：诊断结果关联
    └── cognitive_style：认知风格适配
    │
    ▼
输出：LearningPath（≥ 3 节点 + 三维理由）
```

### 13.3 画像增量更新策略

- **确定性更新（每轮）**：根据诊断结果直接调整对应维度分数
  - 回答正确：conceptual_understanding +0.03，expression_clarity +0.02
  - 回答错误：conceptual_understanding -0.02，self_correction +0.01
- **LLM 校准（每 5 轮）**：调用 LLM 进行全量画像校准，避免累积偏差

### 13.4 可信机制实现

- **范围校验**：快速关键词匹配（≥ 2 个网络关键词放行） + LLM 辅助判断双层
- **溯源标注**：检索来源编号 + 内容末尾追加参考来源列表（最多 5 个）
- **不确定性声明**：置信度 < 0.6 自动追加“以上内容仅供参考”声明

---

## 十四、部署架构

### 14.1 单机部署（当前方案）

```
┌─────────────────────────────────────────┐
│              单机服务器                 │
│                                         │
│  ┌───────────────┐  ┌───────────────┐ │
│  │  前端 (Vite) │  │  后端 (FastAPI)│ │
│  │  端口: 5173    │  │  端口: 8000    │ │
│  └───────────────┘  └───────┬───────┘ │
│                                     │    │
│  ┌───────────────┐  ┌───────┴───────┐ │
│  │  SQLite DB      │  │  ChromaDB       │ │
│  │  (edu_agent.db) │  │  (向量索引)     │ │
│  └───────────────┘  └───────────────┘ │
└─────────────────────────────────────────┘
```

- **启动命令**：`start.bat [--mock-mode]`
- **前端代理**：Vite 开发服务器将 /api 请求代理到后端 8000 端口
- **Mock 模式**：`start.bat --mock-mode` 启用后端 Mock Provider + 前端 Mock 拦截器

### 14.2 可扩展架构（未来方案）

- 前端：Nginx 静态部署 + CDN
- 后端：Docker 容器 + 负载均衡
- 数据库：SQLite 迁移至 PostgreSQL
- 向量库：ChromaDB 迁移至 Milvus
- LLM：支持多模型切换（星火 / GPT / 本地模型）
