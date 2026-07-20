# 系统开发说明书

---

| 项目名称 | Socrates-Cube 多智能体自适应网络协议学习系统 |
|----------|----------------------------------------------|
| 文档编号 | SC-SDD-2026-001 |
| 版本号   | V2.0 |
| 编制日期 | 2026-07-20 |
| 文档状态 | 正式发布 |
| 保密级别 | 内部资料 |
| 编制依据 | GB/T 8567-2006《计算机软件文档编制规范》 |

---

## 变更历史

| 版本 | 日期 | 变更说明 | 编制人 |
|------|------|----------|--------|
| V1.0 | 2026-05-20 | 初稿，建立基础架构框架 | B |
| V1.1 | 2026-07-13 | 补充 C4 架构图、状态图、接口规格、算法描述 | B |
| V2.0 | 2026-07-20 | 依据 GB/T 8567-2006 全面升级，增加组件详细设计、AI 技术融合方案、知识库详细设计 | A+B |

---

## 目录

1. 引言
2. 总体设计
3. 多智能体核心设计
4. 接口设计
5. 数据结构设计
6. AI 技术融合设计
7. 运行设计
8. 系统出错处理设计
9. 附录

---

## 1 引言

### 1.1 编写目的

本文档是 Socrates-Cube 系统的系统开发说明书，依据 GB/T 8567-2006 § 5.6 编制。文档详细描述系统的总体架构、多智能体设计、接口规格、数据结构、关键算法及 AI 技术融合方案，供开发人员、测试人员及评审专家参考。

本文档是在软件需求规格说明书（SC-SRS-2026-001）基础上进行的设计细化，需与其配套阅读。

### 1.2 背景

**系统名称：** Socrates-Cube（苏格拉底方块）  
**参赛赛项：** 第十五届"中国软件杯"A3 赛题  
**核心技术路线：** 大语言模型（LLM）+ 检索增强生成（RAG）+ 多智能体协同（Multi-Agent）+ 知识图谱（KG）

系统创新地将认知科学中的诊断模型（错误识别→根因追溯→模式归类）与 AI 技术深度融合，面向计算机网络课程构建了具有可解释性的自适应学习闭环。

### 1.3 定义与缩略词

参见《软件需求规格说明书》（SC-SRS-2026-001）第 1.3 节。

新增本文档特定术语：

| 术语 | 定义 |
|------|------|
| C4 架构 | Context-Container-Component-Code 四层软件架构描述模型 |
| SSE 事件 | 通过 text/event-stream 协议推送的结构化 JSON 事件 |
| Pydantic Schema | 使用 Python Pydantic 库定义的数据模型，含类型校验 |
| SQLAlchemy | Python 的异步 ORM 框架，用于数据库操作 |
| Kahn 算法 | 基于入度的拓扑排序算法，用于知识路径规划 |
| Mock Provider | 无外部 LLM 时的本地响应提供器，预置典型问答数据 |
| DFP | Domain Filter Policy，域外问题过滤策略 |

### 1.4 参考资料

1. GB/T 8567-2006《计算机软件文档编制规范》
2. SC-SRS-2026-001《Socrates-Cube 软件需求规格说明书》
3. FastAPI 官方文档（https://fastapi.tiangolo.com）
4. Vue 3 Composition API 文档（https://vuejs.org）
5. OpenMAIC 多智能体教学平台（清华大学，MIT License）——架构参考
6. Kahn 算法论文《Topological sorting of large networks》(1962)

---

## 2 总体设计

### 2.1 需求规定

本系统需实现的核心能力如下（详见 SC-SRS-2026-001）：

| 需求 ID | 需求摘要 | 设计应对 |
|---------|---------|---------|
| F01 | SSE 流式对话 | OrchestratorAgent + SSE 中间件 |
| F02 | 三库知识检索 | RetrieverAgent + ChromaDB/本地 JSON |
| F03 | 三层认知诊断 | DiagnosisAgent + 三层 Prompt 链 |
| F04 | 八维学习画像 | ProfilerAgent + SQLite 持久化 |
| F05 | 多 Agent 编排 | OrchestratorAgent + AgentCoordinator |
| F06 | 五类资源生成 | ResourceGeneratorAgent + 5 类 Prompt |
| F07 | 可解释路径规划 | PathPlannerAgent + Kahn 算法 + KG |
| F08 | 协议仿真 | SimulatorPlayer.vue + Canvas 2D |
| F09 | 可信机制 | TrustMechanism + DFP 过滤 |

### 2.2 运行环境

| 类别 | 规格 |
|------|------|
| 服务端 Python | 3.10+（3.12.7 已验证），asyncio 异步运行时 |
| Web 框架 | FastAPI 0.111.0 + Uvicorn 0.29.0 ASGI 服务器 |
| 数据库 | SQLite 3（aiosqlite 0.20.0 异步驱动） |
| 向量库 | ChromaDB 0.5.0（可选），降级方案：本地 JSON |
| LLM 服务 | 讯飞星火 Spark v3.5（spark-ai-python ≥ 0.4.5） |
| 前端运行时 | Node.js 18+，Vue 3.5，Vite 5.4 |
| 浏览器 | Chrome/Edge 90+，支持 Canvas 2D + SSE |
| 操作系统 | Windows 10/11 / Ubuntu 20.04+ / macOS 12+ |

### 2.3 基本设计概念与处理流程

#### 2.3.1 核心设计理念

系统采用三项核心设计理念：

**（1）认知闭环驱动（Cognitive Loop Driven）**

整个系统流程围绕"诊断→生成→规划→反馈"认知闭环设计：学生每次交互产生诊断数据，诊断结果驱动资源生成，资源使用更新画像，画像变化触发路径重规划。

**（2）多智能体星形协同（Star-Topology Multi-Agent）**

OrchestratorAgent 作为中枢节点，按意图路由激活专业 Agent 子集，避免全链路串行执行。各 Agent 职责单一，通过 Python asyncio 并发运行，结果通过 SSE 事件流实时推送。

**（3）可信优先（Trust-First）**

知识库来源可溯（三库联合检索 + 引用标注），域外问题主动拦截（DFP），不确定内容主动声明。防幻觉机制不依赖单一 LLM 自我约束，而是通过结构化检索结果注入实现。

#### 2.3.2 主处理流程

```
学生输入问题
      │
      ▼
[1] OrchestratorAgent 接收
  │  ├─ 意图分类（AgentCoordinator）
  │  └─ 可信过滤（DFP 第一层：域外拦截）
      │
      ▼
[2] RetrieverAgent 知识检索
  │  ├─ 三库向量检索（ChromaDB/JSON）
  │  ├─ 查询扩展（同义词+缩略词）
  │  └─ 知识图谱节点命中
      │
      ▼
[3] DiagnosisAgent 三层诊断（若检测到错误）
  │  ├─ L1：表面错误识别
  │  ├─ L2：根因分析
  │  └─ L3：误区模式匹配
      │
      ▼
[4] LLM 流式生成主回复（token SSE 事件流）
      │
      ▼
[5] TrustMechanism 可信处理（第二、三层）
  │  ├─ 溯源标注（引用 [1][2]）
  │  └─ 不确定性声明（confidence < 0.6）
      │
      ▼
[6] ProfilerAgent 画像更新
  │  ├─ 确定性增量更新
  │  └─ 每 5 轮 LLM 全量校准
      │
      ▼
[7] 按需激活（ResourceGenerator / PathPlanner）
  │  ├─ 五类资源生成（含兜底 fallback）
  │  └─ 知识图谱路径规划
      │
      ▼
[8] SSE done 事件，前端渲染
```

### 2.4 系统结构（C4 架构）

#### 2.4.1 上下文图（Level 1）

```
┌─────────────────────────────────────────────────────────────────┐
│  外部参与者                                                     │
│  ┌─────────┐   ┌─────────┐   ┌────────────────────────────┐   │
│  │  学  生  │   │  助  教  │   │  讯飞星火 LLM API (可选)    │   │
│  └────┬────┘   └────┬────┘   └──────────────┬─────────────┘   │
└───────┼─────────────┼───────────────────────┼─────────────────┘
        │ 浏览器访问   │                        │ HTTPS/WS
        ▼             ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Socrates-Cube 应用系统                         │
│  ┌───────────────────┐    ┌──────────────────────────────────┐ │
│  │  前端 SPA (Vue3)  │◄──►│  后端 API + 多 Agent 引擎        │ │
│  │  Port: 5173        │    │  FastAPI / Port: 8000            │ │
│  └───────────────────┘    └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.4.2 容器图（Level 2）

```
┌───────────────────────────────────────────────────────────────┐
│                     Socrates-Cube 应用系统                    │
│                                                               │
│  ┌──────────────────┐  HTTP/SSE  ┌───────────────────────┐  │
│  │  前端 SPA         │◄──────────►│  FastAPI 后端           │  │
│  │  Vue3+TS+Pinia    │            │  uvicorn ASGI 服务器    │  │
│  │                  │            │                       │  │
│  │  · ChatView      │            │  ┌─────────────────┐  │  │
│  │  · ProfileView   │            │  │  API 路由层      │  │  │
│  │  · DiagnosisView │            │  │  /chat /profile  │  │  │
│  │  · ResourcesView │            │  │  /path /resources│  │  │
│  │  · PathView      │            │  └────────┬────────┘  │  │
│  │  · SimulatorView │            │           │           │  │
│  │  · ChallengerView│            │  ┌────────▼────────┐  │  │
│  │  · LogsView      │            │  │  Agent 引擎层   │  │  │
│  └──────────────────┘            │  │  (8 个 Agent)   │  │  │
│                                  │  └────────┬────────┘  │  │
│                                  │           │           │  │
│                                  │  ┌────────▼────────┐  │  │
│                                  │  │  知识库 + 数据库  │  │  │
│                                  │  │  SQLite/ChromaDB │  │  │
│                                  │  └─────────────────┘  │  │
│                                  └───────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

#### 2.4.3 后端组件图（Level 3 — Agent 层）

```
┌─────────────────────────────────────────────────────────────────────┐
│                       OrchestratorAgent                             │
│  职责：接收请求→意图识别→调度 Agent→合成 SSE 事件流→返回响应         │
└─────┬───────────┬──────────────┬──────────────┬────────────┬───────┘
      │           │              │              │            │
      ▼           ▼              ▼              ▼            ▼
┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────┐
│Retriever│ │Diagnosis │ │ Profiler │ │  Resource    │ │  Path    │
│ Agent   │ │  Agent   │ │  Agent   │ │  Generator   │ │ Planner  │
│         │ │          │ │          │ │    Agent     │ │  Agent   │
│向量检索  │ │L1表面错误 │ │八维画像  │ │5类资源生成   │ │拓扑路径   │
│查询扩展  │ │L2根因分析 │ │增量更新  │ │fallback兜底  │ │三维理由   │
│KG命中   │ │L3模式匹配 │ │LLM校准  │ │资源持久化    │ │进阶路径   │
└─────────┘ └──────────┘ └──────────┘ └──────────────┘ └──────────┘
                                    ▲
      ┌─────────────────────────────┘
      │
┌─────┴────────────────────────────────────────────────────────────┐
│  横切关注点                                                       │
│  · AgentCoordinator（意图路由）· TrustMechanism（可信机制）       │
│  · LLMClient（API/Mock 统一入口）· MockProvider（离线降级）       │
└──────────────────────────────────────────────────────────────────┘
```

#### 2.4.4 前端组件图（Level 3 — 前端层）

```
┌──────────────────────────────────────────────────────────────────┐
│                         Views（页面层）                          │
│  ChatView / ProfileView / DiagnosisView / ResourcesView           │
│  PathView / SimulatorView / ChallengerView / LogsView             │
└─────────────────────────────┬────────────────────────────────────┘
                              │ 使用
┌─────────────────────────────▼────────────────────────────────────┐
│                       Components（组件层）                       │
│  ChatPanel / AgentStatusBar / AgentLogPanel / ProfileRadar        │
│  DiagnosisPanel / PathTimeline / PathReasonModal                  │
│  ResourceTabBar / DocCard / ExerciseCard / CodeCard               │
│  SimulatorPlayer / ChallengerPanel / ChatMessage                  │
└─────────────────────────────┬────────────────────────────────────┘
                              │ 读写
┌─────────────────────────────▼────────────────────────────────────┐
│                       Stores（状态层 Pinia）                     │
│  chatStore / userStore / pathStore / resourceStore                │
└─────────────────────────────┬────────────────────────────────────┘
                              │ 调用
┌─────────────────────────────▼────────────────────────────────────┐
│                   Composables + API Layer                        │
│  useChatSSE（SSE 流处理）/ useFetchSSE                           │
│  chat.ts / profile.ts / path.ts / resources.ts / logs.ts         │
└──────────────────────────────────────────────────────────────────┘
```

### 2.5 功能需求与程序模块的关系

| 功能需求 | 主要后端模块 | 主要前端模块 |
|---------|------------|------------|
| F01 流式对话 | `orchestrator.py`, `coordinator.py`, `llm_client.py`, `api/chat.py` | `ChatView.vue`, `ChatPanel.vue`, `useSSE.ts` |
| F02 知识检索 | `retriever.py`, `kb/vector_store.py`, `kb/knowledge_graph.py` | `ChatPanel.vue`（间接） |
| F03 三层诊断 | `diagnosis.py`, `kb/misconception_registry.py` | `DiagnosisPanel.vue`, `DiagnosisView.vue` |
| F04 八维画像 | `profiler.py`, `schema/profile.py`, `db/repositories/` | `ProfileView.vue`, `ProfileRadar.vue` |
| F05 多 Agent 编排 | `orchestrator.py`, `coordinator.py`, `api/logs.py` | `AgentStatusBar.vue`, `AgentLogPanel.vue` |
| F06 资源生成 | `resource_generator.py`, `api/resources.py` | `ResourcesView.vue`, `ResourceTabBar.vue`, `*Card.vue` |
| F07 路径规划 | `path_planner.py`, `kb/knowledge_graph.py`, `api/path.py` | `PathView.vue`, `PathTimeline.vue`, `PathReasonModal.vue` |
| F08 协议仿真 | `api/simulator.py`（场景数据） | `SimulatorView.vue`, `SimulatorPlayer.vue` |
| F09 可信机制 | `core/trust_mechanism.py` | 回答尾部引用标注展示（ChatMessage.vue） |

---

## 3 多智能体核心设计

### 3.1 Agent 设计规格

#### 3.1.1 OrchestratorAgent

**文件：** `src/loopse/agent/orchestrator.py`  
**设计模式：** 事件驱动的有状态协调器

```python
# 核心接口签名
async def process_message(
    message: str,
    user_id: int,
    session_id: str
) -> AsyncGenerator[SSEEvent, None]
```

**调度决策逻辑：**

```
接收消息
    ├─ 调用 AgentCoordinator.classify_intent()
    ├─ 检查 TrustMechanism.check_domain()
    │     └─ 越界 → yield error_event, return
    ├─ 并发启动 RetrieverAgent（必启）
    ├─ 若 is_answer_type → 并发启动 DiagnosisAgent
    ├─ 流式 LLM 生成（逐 token yield）
    ├─ 异步更新 ProfilerAgent
    ├─ 按需触发 ResourceGeneratorAgent
    └─ 按需触发 PathPlannerAgent
```

**SSE 事件序列示例：**

```
→ agent_start {agent:"orchestrator"}
→ agent_start {agent:"retriever"}
→ agent_end   {agent:"retriever", elapsed_ms:85}
→ agent_start {agent:"diagnosis"}
→ diagnosis   {data:{is_correct:false, surface_error:...}}
→ agent_end   {agent:"diagnosis", elapsed_ms:320}
→ token       {data:{token:"根据"}}
→ token       {data:{token:"TCP"}}
   ... (流式 token 事件) ...
→ resource    {data:{doc:{...}, exercise:{...}}}
→ path_update {data:{nodes:[...]}}
→ done        {data:{session_id:"...", total_ms:2340}}
```

#### 3.1.2 DiagnosisAgent

**文件：** `src/loopse/agent/diagnosis.py`  
**设计模式：** 三层 Prompt 链（Chain-of-Thought）

三层 Prompt 模板路径：
- L1：`config/prompts/diagnosis/surface_error.txt`
- L2：`config/prompts/diagnosis/root_cause.txt`
- L3：`config/prompts/diagnosis/pattern_match.txt`

**关键实现：Prompt 注入知识库上下文**

```python
# L1 Prompt 构建
context = retriever.search_all(question)
prompt = load_template("surface_error.txt").format(
    question=question,
    student_answer=student_answer,
    context_docs=context.course_docs[:3],
    error_types=ERROR_TYPE_ENUM
)
```

**误区模式库加载：**

`MisconceptionRegistry` 在启动时从 `data/misconceptions.json` 加载 150 条误区记录，构建内存索引，支持按 `knowledge_node_id` 和 `misconception_pattern` 两个维度检索。

#### 3.1.3 ProfilerAgent

**文件：** `src/loopse/agent/profiler.py`  
**设计模式：** 增量状态更新 + 周期性全量校准

**增量更新规则（每轮触发）：**

| 对话事件 | 维度变化 |
|---------|---------|
| 回答正确 | `knowledge_depth += 0.03`, `learning_progress += 0.02` |
| 回答错误 | `knowledge_depth -= 0.02`, `common_mistakes` 追加记录 |
| 使用代码资源 | `practical_skill += 0.02` |
| 使用思维导图 | `cognitive_style` 向 `visual` 偏移 |
| 完成知识节点 | `mastery_map[node_id] = max(current, 0.8)` |

**LLM 深度校准（每 5 轮）：**

```python
if self.interaction_count % 5 == 0:
    calibrated = await self._llm_calibrate(
        profile=current_profile,
        recent_messages=session[-5:]
    )
    profile.merge(calibrated, weight=0.3)  # 保留历史权重 0.7
```

#### 3.1.4 ResourceGeneratorAgent

**文件：** `src/loopse/agent/resource_generator.py`  
**设计模式：** 策略模式（5 类资源各自策略 + 统一 fallback）

| 资源类型 | Prompt 模板 | 兜底策略 |
|---------|------------|---------|
| doc | `generate_doc.txt` | 返回结构化知识点摘要 |
| exercise | `generate_exercise.txt` | 返回选择题模板 |
| code | `generate_code.txt` | 返回 TCP Socket 示例代码 |
| mindmap | `generate_mindmap.txt` | 返回 Mermaid 骨架图 |
| script | `generate_script.txt` | 返回分步讲解模板 |

**兜底机制：** 当 LLM 生成失败时，`_fallback_content()` 为所有 5 类资源提供结构化备选内容，确保前端不出现空白卡片。

#### 3.1.5 PathPlannerAgent

**文件：** `src/loopse/agent/path_planner.py`  
**核心算法：** Kahn 拓扑排序 + DFS 前置依赖搜索

```python
def plan_path(profile: StudentProfile, target_nodes: List[str]) -> LearningPath:
    # Step 1: 找出需要补充的前置节点
    missing = self.kg.find_missing_prerequisites(
        targets=target_nodes,
        mastered=profile.mastery_map
    )
    # Step 2: 拓扑排序确定学习顺序
    ordered = self.kg.topological_sort(missing + target_nodes)
    # Step 3: 为每个节点生成三维推荐理由
    nodes = []
    for nid in ordered[:max_nodes]:
        reason = self._generate_three_dim_reason(nid, profile, diagnosis)
        nodes.append(PathNode(node_id=nid, reason_sources=reason, ...))
    return LearningPath(nodes=nodes)
```

**三维推荐理由生成：**

```python
def _generate_three_dim_reason(self, node_id, profile, diagnosis):
    return ReasonSources(
        graph_dependency=self.kg.get_dependency_reason(node_id),
        diagnosis_result=self._map_diagnosis_to_reason(node_id, diagnosis),
        cognitive_style=self._adapt_to_style(node_id, profile.cognitive_style)
    )
```

### 3.2 AgentCoordinator 意图路由设计

**文件：** `src/loopse/agent/coordinator.py`

意图分类结果决定激活的 Agent 子集：

| 意图类型 | 激活 Agent | 典型触发词 |
|---------|-----------|---------|
| `answer_question` | Retriever, Diagnosis, Profiler | 问题句式 |
| `request_resource` | Retriever, ResourceGenerator | 「生成」「给我」「推荐」 |
| `request_path` | PathPlanner | 「路径」「计划」「怎么学」 |
| `request_simulation` | Simulator | 「演示」「仿真」「模拟」「握手」 |
| `challenge_question` | Challenger | 概念挑战模式 |
| `general_chat` | Retriever, Profiler | 其他 |

### 3.3 TrustMechanism 可信机制设计

**文件：** `src/loopse/core/trust_mechanism.py`

#### 3.3.1 域外过滤策略（DFP）

```python
NETWORK_KEYWORDS = {
    "TCP", "UDP", "IP", "HTTP", "DNS", "协议", "握手", "路由", ...
    # 约 80 个核心词
}

OUT_OF_DOMAIN_PATTERNS = [
    r"帮.*?(写|生成|实现).*(代码|程序)",  # 通用编程请求
    r"翻译|英文|语言",                   # 翻译请求
    r"天气|新闻|娱乐",                   # 非学习内容
]

def check_domain(message: str) -> DomainCheckResult:
    kw_count = sum(1 for kw in NETWORK_KEYWORDS if kw in message)
    if kw_count >= 2:
        return DomainCheckResult(in_domain=True, confidence=0.95)
    for pattern in OUT_OF_DOMAIN_PATTERNS:
        if re.search(pattern, message):
            return DomainCheckResult(in_domain=False, reason="域外问题")
    return DomainCheckResult(in_domain=True, confidence=0.6)  # 宽松放行
```

#### 3.3.2 引用溯源机制

```python
def add_source_annotations(content: str, sources: List[KBSource]) -> str:
    # 1. 在回答中插入 [n] 引用标记
    # 2. 末尾追加 "参考来源：[1] ... [2] ..." 章节
    ...
```

---

## 4 接口设计

### 4.1 用户接口

前端页面详见第 2.4.4 节，界面设计原则：
- 流式输出打字机效果（token 事件驱动）
- Markdown 渲染（marked + highlight.js）
- 多模态内容卡片化（资源卡片、诊断卡片、路径时间轴）
- Agent 状态实时可见（AgentStatusBar 颜色编码）
- 最低支持 1280px 宽度响应式布局

### 4.2 外部接口

#### 4.2.1 讯飞星火 API

| 项目 | 说明 |
|------|------|
| SDK | spark-ai-python ≥ 0.4.5 |
| 模型 | Spark v3.5（`generalv3.5`） |
| 认证 | AppID + APIKey + APISecret（HMAC-SHA256） |
| 接入 | WebSocket 流式接口 |
| 超时 | 30 秒，超时自动降级 Mock |

#### 4.2.2 ChromaDB 向量库

| 项目 | 说明 |
|------|------|
| 版本 | chromadb 0.5.0（可选） |
| 集合 | `course_docs`, `protocol_specs`, `misconceptions` |
| 降级 | 不可用时自动切换 `data/vector_db/local_index.json` |

### 4.3 内部接口（REST API）

#### 4.3.1 核心接口清单

| 接口路径 | HTTP 方法 | 说明 | 响应类型 |
|---------|---------|------|---------|
| `/health` | GET | 健康检查 | JSON |
| `/api/v1/chat/stream` | POST | SSE 流式对话 | text/event-stream |
| `/api/v1/profile/{user_id}` | GET | 获取八维画像 | JSON |
| `/api/v1/profile/{user_id}` | POST | 更新画像 | JSON |
| `/api/v1/path/{user_id}` | GET | 获取当前路径 | JSON |
| `/api/v1/path/plan` | POST | 规划新路径 | JSON |
| `/api/v1/path/{user_id}/progress` | POST | 更新节点进度 | JSON |
| `/api/v1/resources/generate` | POST | 生成单类资源 | JSON |
| `/api/v1/resources/generate-all` | POST | 生成全部 5 类 | JSON |
| `/api/v1/logs/session/{session_id}` | GET | 会话 Agent 日志 | JSON |
| `/api/v1/diagnosis` | POST | 独立触发诊断 | JSON |
| `/api/v1/simulator/{scene_id}` | GET | 获取仿真场景数据 | JSON |
| `/api/v1/challenge` | POST | 概念挑战问答 | JSON |

#### 4.3.2 SSE 事件格式规范

所有 SSE 事件均使用如下统一格式：

```
event: <event_type>
data: {"agent_name":"<agent>","timestamp":<ms>,"data":{...}}

```

**示例：token 事件**

```
event: token
data: {"agent_name":"orchestrator","timestamp":1720876800123,"data":{"token":"TCP"}}

```

**示例：diagnosis 事件**

```
event: diagnosis
data: {
  "agent_name":"diagnosis",
  "timestamp":1720876800456,
  "data":{
    "is_correct":false,
    "confidence":0.91,
    "surface_error":"误认为TCP三次握手为两次",
    "error_type":"flow_omission",
    "root_causes":["TCP连接管理","可靠传输"],
    "pattern":"握手次数混淆",
    "intervention_suggestion":"建议复习TCP三次握手必要性..."
  }
}

```

---

## 5 数据结构设计

### 5.1 核心数据模型

#### 5.1.1 StudentProfile（学生画像）

```python
# src/loopse/schema/profile.py
class StudentProfile(BaseModel):
    user_id: int
    knowledge_depth: float = 0.5        # 知识储备 [0,1]
    cognitive_style: CognitiveStyle = CognitiveStyle.mixed  # 认知风格
    learning_progress: float = 0.0      # 学习进度 [0,1]
    protocol_understanding: float = 0.5 # 协议理解 [0,1]
    practical_skill: float = 0.5        # 动手能力 [0,1]
    common_mistakes: List[str] = []     # 常见错误类型列表
    learning_preference: Dict[str, float] = {}  # 资源偏好权重
    overall_level: OverallLevel = OverallLevel.beginner  # 综合水平
    mastery_map: Dict[str, float] = {}  # 知识点掌握度地图
    interaction_count: int = 0          # 累计交互轮数
    updated_at: datetime = ...
```

#### 5.1.2 DiagnosisResult（诊断结果）

```python
class DiagnosisResult(BaseModel):
    is_correct: bool
    confidence: float                   # [0,1]
    surface_error: Optional[str]        # 表面错误描述
    error_type: ErrorType               # 错误分类枚举
    root_causes: List[str]              # 根因知识点
    missing_prerequisites: List[str]    # 缺失前置知识
    trigger: Optional[str]              # 触发证据
    pattern: Optional[str]              # 误区模式名称
    intervention_suggestion: str        # 干预建议
    related_node_ids: List[str]         # 相关图谱节点
```

#### 5.1.3 PathNode（学习路径节点）

```python
class PathNode(BaseModel):
    node_id: str                        # 知识图谱节点 ID
    name: str                           # 知识点名称
    status: PathStatus                  # completed/in_progress/pending/locked
    current_mastery: float              # 当前掌握度 [0,1]
    recommendation_reason: str          # 推荐理由（≥20字）
    reason_sources: ReasonSources       # 三维推荐理由
    prerequisites: List[str]            # 前置节点列表
    prerequisites_met: bool             # 前置是否满足
    suggested_resources: List[str]      # 推荐资源 ID
```

#### 5.1.4 LearningResource（学习资源）

```python
class LearningResource(BaseModel):
    resource_id: str                    # UUID
    resource_type: ResourceType         # doc/exercise/code/mindmap/script
    knowledge_point: str                # 关联知识点
    title: str                          # 资源标题
    content: str                        # 资源正文（Markdown）
    metadata: ResourceMetadata          # 难度/风格/来源引用
    created_at: datetime
```

### 5.2 数据库物理结构

#### 5.2.1 users 表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER PK AUTOINCREMENT | 主键 |
| user_id | VARCHAR(64) UNIQUE | 业务 ID |
| username | VARCHAR(128) | 用户名 |
| password_hash | VARCHAR(256) | bcrypt 哈希 |
| created_at | DATETIME | 注册时间 |

#### 5.2.2 student_profiles 表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER PK | 主键 |
| user_id | INTEGER FK→users | 关联用户 |
| profile_json | TEXT | 八维画像 JSON |
| mastery_map_json | TEXT | 知识掌握度地图 JSON |
| interaction_count | INTEGER | 交互轮数 |
| updated_at | DATETIME | 最后更新时间 |

#### 5.2.3 chat_sessions 表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER PK | 主键 |
| session_id | VARCHAR(64) UNIQUE | 会话 UUID |
| user_id | INTEGER FK→users | 关联用户 |
| messages_json | TEXT | 消息列表 JSON |
| created_at | DATETIME | 会话创建时间 |
| updated_at | DATETIME | 最后活跃时间 |

#### 5.2.4 agent_logs 表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER PK | 主键 |
| session_id | VARCHAR(64) FK→chat_sessions | 关联会话 |
| agent_name | VARCHAR(64) | Agent 名称 |
| action | VARCHAR(128) | 执行动作 |
| input_state | TEXT | 输入摘要（脱敏） |
| output_state | TEXT | 输出摘要 |
| elapsed_ms | INTEGER | 执行耗时（毫秒） |
| status | VARCHAR(32) | success/error |
| timestamp | DATETIME | 执行时间 |

#### 5.2.5 learning_paths 表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER PK | 主键 |
| user_id | INTEGER FK→users | 关联用户 |
| nodes_json | TEXT | 路径节点列表 JSON |
| target_topic | VARCHAR(128) | 学习目标主题 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 最后更新时间 |

### 5.3 知识库结构

#### 5.3.1 知识图谱节点结构

```json
{
  "id": "KP-TCP-HANDSHAKE",
  "name": "TCP 三次握手",
  "chapter": "第3章 传输层",
  "type": "protocol_mechanism",
  "difficulty": 3,
  "estimated_time": 45,
  "keywords": ["SYN", "ACK", "连接建立", "半连接"],
  "description": "TCP通过三次握手建立全双工可靠连接...",
  "rfc_reference": "RFC 793 §3.4"
}
```

**知识图谱规模：** 100 节点，82 条有向边，覆盖 6 个章节

#### 5.3.2 误区条目结构

```json
{
  "id": "MC-001",
  "knowledge_node_id": "KP-TCP-HANDSHAKE",
  "wrong_statement": "TCP 两次握手就能建立连接",
  "correct_explanation": "三次握手是为了验证双方的收发能力...",
  "root_cause": "对全双工通信原理理解不足",
  "misconception_pattern": "流程遗漏型",
  "difficulty": 2,
  "frequency": "high"
}
```

**误区库规模：** 150 条，覆盖 20 个核心知识点，8 种误区模式

---

## 6 AI 技术融合设计

### 6.1 大语言模型集成方案

#### 6.1.1 LLM Client 统一入口

```python
# src/loopse/core/llm_client.py
class LLMClient:
    async def stream_chat(
        self, messages: List[Message], temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        if self.mock_mode:
            async for token in self.mock_provider.stream(messages):
                yield token
        else:
            async for token in self.spark_client.stream(messages):
                yield token
```

所有 Agent 通过 `LLMClient` 统一调用 LLM，不直接调用 SDK，便于：
- 切换不同 LLM 提供商（星火/GPT/本地模型）
- 统一 Mock/Real 模式切换
- 统一 token 计数和成本监控

#### 6.1.2 RAG 架构设计

```
用户问题
    │
    ├─ 查询扩展（同义词/缩略词）
    │
    ├─ 向量检索（ChromaDB/本地JSON）
    │   ├─ course_docs：语义相似度 Top-3
    │   ├─ protocol_specs：语义相似度 Top-2
    │   └─ misconceptions：相似度 Top-2
    │
    ├─ 知识图谱关键词命中
    │
    └─ 检索结果注入 Prompt
           └─ LLM 生成基于知识库的回答
                  └─ 来源引用标注
```

#### 6.1.3 Prompt 工程设计

所有 Prompt 模板采用以下结构：

```
[系统角色定义]
你是一位计算机网络课程的专业教师助手...

[任务说明]
请根据以下学生回答进行三层诊断...

[知识库上下文注入]
{context_docs}

[结构化输出要求]
请以JSON格式返回：{"is_correct":...}

[安全约束]
仅回答计算机网络课程范围内的问题...
```

**关键 Prompt 文件清单：**

| 文件路径 | 用途 | 字数 |
|---------|------|------|
| `config/prompts/diagnosis/surface_error.txt` | L1 表面错误识别 | ~400 字 |
| `config/prompts/diagnosis/root_cause.txt` | L2 根因分析 | ~350 字 |
| `config/prompts/diagnosis/pattern_match.txt` | L3 模式匹配 | ~500 字 |
| `config/prompts/orchestrator/route.txt` | 意图路由 | ~300 字 |
| `config/prompts/profiler/update_profile.txt` | 画像校准 | ~400 字 |
| `config/prompts/resource_generator/generate_doc.txt` | 文档生成 | ~350 字 |
| `config/prompts/resource_generator/generate_exercise.txt` | 题目生成 | ~400 字 |
| `config/prompts/resource_generator/generate_code.txt` | 代码生成 | ~300 字 |

### 6.2 知识图谱驱动设计

知识图谱（Knowledge Graph）在系统中承担三重角色：

| 角色 | 具体功能 |
|------|---------|
| 路径规划基础 | 拓扑排序确定学习顺序，前置依赖确保学习路径科学 |
| 诊断增强 | 根因分析时通过知识节点反向遍历定位薄弱点 |
| 检索扩展 | 用户问题命中节点时同步返回前置节点知识 |

**知识图谱加载与查询：**

```python
class KnowledgeGraph:
    def find_missing_prerequisites(
        self, targets: List[str], mastered: Dict[str, float]
    ) -> List[str]:
        """DFS 反向遍历，找出掌握度低于阈值的前置节点"""
        ...

    def topological_sort(self, nodes: List[str]) -> List[str]:
        """Kahn 算法，返回按依赖顺序排列的节点列表"""
        ...
```

### 6.3 协议仿真引擎设计

仿真引擎采用"数据驱动 + Canvas 渲染"分离架构：

**后端（数据层）：** 每个场景定义为 JSON 结构的有序步骤列表

```json
{
  "scene_id": "three_way_handshake",
  "name": "TCP 三次握手",
  "steps": [
    {
      "step": 1,
      "sender": "client",
      "receiver": "server",
      "flags": {"SYN": true},
      "seq": 100,
      "ack": 0,
      "description": "客户端发送SYN报文，seq=100，请求建立连接",
      "state_change": {"client": "SYN_SENT"}
    },
    ...
  ],
  "parameters": {
    "window_size": {"default": 65535, "range": [512, 65535]},
    "rtt_ms": {"default": 100, "range": [1, 1000]}
  }
}
```

**前端（渲染层）：** `SimulatorPlayer.vue` 使用 Canvas 2D API + requestAnimationFrame，根据步骤数据驱动动画：
- 双栏布局：Canvas 动画区（左）+ 状态机面板（右）
- 报文气泡点击弹出字段详情
- 支持步进/播放/暂停/速度调节/进度拖拽

---

## 7 运行设计

### 7.1 运行模块组合

| 模块 | 进程 | 端口 | 依赖 |
|------|------|------|------|
| FastAPI 后端 | uvicorn | 8000 | Python .venv_new |
| Vue 前端开发服务 | Vite | 5173 | Node.js 18+ |
| 前端生产构建 | 静态文件 | 随 nginx | frontend/dist/ |
| SQLite 数据库 | 内嵌 | — | aiosqlite |
| ChromaDB 向量库 | 内嵌（可选） | — | chromadb（可选） |

### 7.2 运行控制

#### 7.2.1 一键启动（Windows）

```bat
:: start.bat
start.bat           -- 正常模式（讯飞 API）
start.bat --mock-mode  -- Mock 模式（无需 API）
```

启动流程：
1. 检测 Python 版本
2. 创建/激活 .venv_new 虚拟环境
3. 按需安装依赖（pip show fastapi）
4. 初始化数据库（scripts/init_db.py）
5. 启动 uvicorn（uvicorn src.loopse.main:app）

#### 7.2.2 环境变量配置

```ini
# .env 文件（不入 Git）
SPARK_APP_ID=your_app_id
SPARK_API_SECRET=your_api_secret
SPARK_API_KEY=your_api_key
MOCK_MODE=0                   # 1=强制 Mock
LOG_LEVEL=INFO                # DEBUG/INFO/WARNING/ERROR
```

### 7.3 性能优化措施

| 优化点 | 实现方式 | 预期收益 |
|--------|---------|---------|
| 检索结果缓存 | 相同查询 5 分钟内复用检索结果 | 检索延迟减少 80% |
| 画像更新去抖 | 连续对话不重复触发全量 LLM 校准 | LLM 调用减少 60% |
| 日志异步写入 | asyncio Task 后台写 agent_logs | 主流程不阻塞 |
| SSE 心跳保活 | 每 20 秒发送 `:keepalive\n\n` | 长连接不断 |

---

## 8 系统出错处理设计

### 8.1 出错信息规范

所有 SSE `error` 事件遵循以下格式（脱敏）：

```json
{
  "agent_name": "orchestrator",
  "timestamp": 1720876800789,
  "data": {
    "error": "LLM服务暂时不可用，已切换Mock模式",
    "code": "LLM_TIMEOUT",
    "fallback": true
  }
}
```

**禁止在 error 事件中出现：** API Key、完整堆栈信息、数据库连接字符串。

### 8.2 补救措施

| 故障场景 | 检测方式 | 补救措施 |
|---------|---------|---------|
| LLM API 超时 | asyncio.wait_for 30s | 切换 MockProvider，发送 fallback=true |
| ChromaDB 不可用 | 启动时 try/except | 降级本地 JSON 索引，记录 WARNING |
| 数据库写入失败 | SQLAlchemy 异常 | 事务回滚，日志记录，不影响主流程 |
| SSE 连接中断 | 前端 EventSource onerror | 前端自动重连（最多 3 次，指数退避） |
| 单 Agent 超时 | asyncio.wait_for | 跳过该 Agent，继续执行后续步骤 |
| 前端构建失败 | npm run build 返回码 | 使用 public/mock/ 目录 Mock 数据离线运行 |

### 8.3 日志与监控

| 日志级别 | 使用场景 |
|---------|---------|
| DEBUG | Agent 入参出参详情（开发环境） |
| INFO | 系统启动、每轮对话开始/结束、Agent 调度 |
| WARNING | 降级切换（Mock/本地索引）、性能超阈 |
| ERROR | 未处理异常、API 调用失败 |

日志格式：`%(asctime)s [%(levelname)s] %(name)s | %(message)s`

---

## 9 附录

### 附录 A 目录结构

```
Socrates-Cube/
├── src/loopse/                 # 后端核心
│   ├── agent/                  # 9 个 Agent 实现
│   │   ├── orchestrator.py     #   总协调器
│   │   ├── coordinator.py      #   意图路由
│   │   ├── profiler.py         #   画像维护
│   │   ├── retriever.py        #   知识检索
│   │   ├── diagnosis.py        #   三层诊断
│   │   ├── resource_generator.py # 资源生成
│   │   ├── path_planner.py     #   路径规划
│   │   ├── challenger.py       #   概念挑战
│   │   └── simulator.py        #   协议仿真
│   ├── api/                    # FastAPI 路由层（20+ 路由文件）
│   ├── core/                   # 核心能力
│   │   ├── llm_client.py       #   LLM 统一入口
│   │   ├── mock_provider.py    #   Mock 响应提供器
│   │   └── trust_mechanism.py  #   可信机制
│   ├── db/                     # 数据访问层
│   ├── kb/                     # 知识库
│   │   ├── vector_store.py     #   ChromaDB/JSON 向量检索
│   │   ├── knowledge_graph.py  #   图谱加载与查询
│   │   ├── misconception_registry.py # 误区库
│   │   └── text_splitter.py    #   文档切分
│   ├── schema/                 # Pydantic 数据模型
│   └── main.py                 # 应用入口
├── config/prompts/             # Prompt 模板（8 类 Agent）
├── frontend/src/               # Vue 3 前端（20+ 视图组件）
├── data/
│   ├── knowledge_graph.json    # 100 节点 82 边知识图谱
│   ├── misconceptions.json     # 150 条误区库
│   └── vector_db/local_index.json  # 本地 JSON 向量索引
├── scripts/                    # 数据工程脚本
├── tests/unit/                 # 单元测试（8 个测试文件）
└── docs/                       # 项目文档
```

### 附录 B 开源组件声明

| 组件 | 版本 | License | 用途 |
|------|------|---------|------|
| FastAPI | 0.111.0 | MIT | Web 框架 |
| Vue 3 | 3.5 | MIT | 前端框架 |
| Pydantic | 2.x | MIT | 数据验证 |
| SQLAlchemy | 2.0.30 | MIT | ORM |
| ECharts | 5.6 | Apache 2.0 | 数据可视化 |
| TailwindCSS | 3.4 | MIT | CSS 工具类 |
| spark-ai-python | ≥0.4.5 | Apache 2.0 | 讯飞星火 SDK |
| marked | 14.x | MIT | Markdown 渲染 |
| highlight.js | — | BSD-3 | 代码高亮 |

AI 工具使用声明：系统核心 AI 能力使用科大讯飞讯飞星火大模型 API（符合 A3 赛题要求）。

### 附录 C 变更历史

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| V1.0 | 2026-05-20 | 初稿 |
| V1.1 | 2026-07-13 | C4 架构图、状态图、接口规格、算法描述 |
| V2.0 | 2026-07-20 | GB/T 8567-2006 全面升级：增加详细 Agent 设计、Prompt 工程、知识图谱设计、出错处理规范 |
