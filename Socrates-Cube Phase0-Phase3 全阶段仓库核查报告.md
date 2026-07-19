# Socrates\-Cube Phase0\-Phase3 全阶段仓库核查报告

## Phase 0 核查结果

已对照 Phase 0 文档和当前仓库 `Socrates-Cube` 逐项核查。结论如下。

---

### 总览

|状态|数量|说明|
|---|---|---|
|✅ 已完成|11 项|核心文档与代码骨架基本到位|
|⚠️ 部分完成 / 有偏差|5 项|能跑但不符合原验收标准|
|❌ 未完成|3 项|验收清单明确缺失|

**Phase 0 不能算“全绿通过”**，主要卡在 README、环境可复现性、`/api/v1/chat/test` 接口。

---

### 5 月 10 日验收清单（逐项）

|验收项|状态|说明|
|---|---|---|
|Git 仓库可 clone|✅|远程 `https://github.com/Yuan-813/Socrates-Cube.git` 存在|
|目录结构 `src/loopse/{agent,prompt,schema,utils}`|⚠️|目录存在，但 `agent/`、`prompt/`、`utils/` 只有空 `__init__.py`；实际 Agent 在 `agents/`|
|README 含简介 \+ 一键启动|❌|当前 README 主要是 Git 规范，无项目简介和启动步骤|
|`.env.example`|✅|已提交，字段齐全|
|`.gitignore`|✅|已过滤 `.env`、`.venv`、`data/`、`chroma_db/` 等|
|`requirements.txt` 安装无报错|❌|Windows 上 `chromadb` 需 MSVC 编译工具，完整安装会失败|
|`api_schema.yaml` 定稿|✅|含六维画像、SSE、Agent 日志三套 Schema|
|六维画像 Pydantic 可 import|✅|`student_profile_schema.py` 可正常导入|
|知识库资料清单 ≥3 章|✅|已覆盖 5 个聚焦章节|
|竞品分析文档（含 3 篇论文）|✅|五节齐全，含 Oak / KAQG / ParLD|
|环境初始化说明可复现|⚠️|文档存在；`verify_env.py` 在当前环境无法通过|
|FastAPI `/health` 返回 200|✅|可正常访问|
|`init_db.py` 建立 4 张表|✅|已演进为 SQLAlchemy 多表（≥4 张），功能上满足|

---

### 按交付物对照（Phase 0 总表）

|文件|负责人|截止|状态|
|---|---|---|---|
|`docs/项目定位说明.md`|A|5/8|✅ 五模块齐全|
|`docs/references/知识库资料清单.md`|B|5/8|✅ 覆盖 5 章|
|`requirements.txt`|C|5/8|⚠️ 有文件，但 Windows 完整安装会失败|
|`.gitignore`|C|5/8|✅|
|`docs/deployment/环境初始化说明.md`|C|5/8|✅|
|`scripts/verify_env.py`|C|5/8|⚠️ 有脚本，但当前环境跑不通|
|`config/api_schema.yaml`|A|5/9|✅|
|`docs/requirements/竞品分析与理论支撑说明.md`|A|5/10|✅|
|`src/loopse/schema/student_profile_schema.py`|B|5/9|✅|
|`tests/test_student_profile_schema.py`|B|5/9|⚠️ 测试文件有，venv 未装 pytest|
|`.env.example`|B|5/9|✅|
|`src/loopse/main.py`|C|5/9|⚠️ 有 FastAPI，缺 `/api/v1/chat/test`|
|`scripts/init_db.py`|C|5/9|✅（已超出 Phase 0 最小版）|
|前端框架初始化|C|5/10|✅ Vue3 \+ TS，`frontend/` 可 `npm run dev`|

---

### 未完成 / 有问题的具体项

#### 1\. ❌ README 缺少启动说明（A，5/10 验收项）

当前 `README.md` 是 Git 操作规范，没有：

- 项目一句话介绍

- `uvicorn` / `npm run dev` 等一键启动步骤

#### 2\. ❌ `/api/v1/chat/test` 接口缺失（C，5/9 任务）

Phase 0 要求：

```Plain Text
@app.get("/api/v1/chat/test")
async def chat_test():
    return {"message": "后端联通成功"}
```

当前 `main.py` 只有 `/health`，没有该测试接口。

#### 3\. ❌ `requirements.txt` 无法在所有环境无报错安装（C，5/8）

- `chromadb` 在 Windows 需 **Microsoft C\+\+ Build Tools**

- 文档要求 Python **3\.10**，当前 venv 是 **3\.12**

- 因此“按说明安装后无报错”在现状下不成立

#### 4\. ⚠️ `verify_env.py`无法打出「环境检查通过 ✅」

当前会失败的原因：

- Python 不是 3\.10

- `chromadb` 未安装

- `.env` 里是占位 API Key

- Windows 控制台还有 emoji 编码问题（GBK）

#### 5\. ⚠️ 目录结构与 Phase 0 规划不一致

|Phase 0 规划|现状|
|---|---|
|`src/loopse/agent/`|空目录|
|`src/loopse/agents/`|实际 Agent 代码在这里|
|`src/loopse/prompt/`|空目录（提示词在 `config/prompts/`）|
|`src/loopse/utils/`|空目录（竞品文档写了 Oak 护栏要放这里，但未实现）|

#### 6\. ⚠️ Schema 与接口规范不完全一致（B）

- `api_schema.yaml`：`profile` 嵌套结构，`cognitive_style` 为 `{type, desc}` 对象

- `student_profile_schema.py`：扁平结构，`cognitive_style` 直接是枚举值

不影响 import，但“A 定稿、B/C 确认无异议”这一条可能有争议。

#### 7\. ⚠️ 无法从仓库验证的流程类任务

这些在文档里有，但代码里看不出来是否做过：

- 5/8 四人线上对齐会（知识库版本、Vue3、SQLite 等拍板）

- B：讯飞 API 本地联调（`outputs/test_spark.py`，不应提交 Git）

- C：在**另一个目录**按文档完整复现环境

- A：5/10 主持 Phase 0 验收例会

---

### 已完成较好的部分

- **A**：`项目定位说明.md`、`api_schema.yaml`、竞品分析文档均完整

- **B**：资料清单覆盖 5 章；六维画像 Schema \+ 单元测试文件齐全

- **C**：FastAPI 脚手架、前端 Vue3、环境文档、`init_db.py` 均已超出 Phase 0 最低要求

---

### 建议优先补救（按优先级）

1. **补 README**：加项目简介 \+ 后端/前端启动三步

2. **`/api/v1/chat/test`****补 **：满足 5/9 C 的交付检查点

3. **修环境可复现性**：
        

    - 安装 Python 3\.10，或放宽 `verify_env.py` 的版本检查

    - 解决 `chromadb` 安装（装 MSVC 或文档注明 Windows 替代方案）

    - 填入真实讯飞 API Key 后跑通 `verify_env.py`

4. **统一目录命名**：决定用 `agent/` 还是 `agents/`，避免两套空目录

5. **对齐 Schema**：让 Pydantic 模型与 `api_schema.yaml` 结构一致

---

## Phase 1 核查结果

已对照 **Phase 1（5/11–5/17）** 文档和当前仓库逐项核查。结论：**代码骨架远超 Phase 1 最低要求，但按当时验收标准不能算“全绿通过”**——主要卡在知识库数据、星火 API 真联通、目录对齐和 README/SRS 形态。

---

### 总览

|状态|数量|说明|
|---|---|---|
|✅ 已完成 / 超额完成|9 项|后端、前端、Agent、仿真等已演进到 Phase 2\+ 水平|
|⚠️ 部分完成 / 有偏差|8 项|有实现但与 Phase 1 规格不一致|
|❌ 未完成|6 项|验收硬性项或交付物缺失|

**Phase 1 硬性验收（5/17）预估：4/4 项中仅 2 项可算通过。**

---

### 5/17 硬性验收清单（最重要）

|验收项|状态|核查结果|
|---|---|---|
|输入「什么是TCP三次握手」→ 星火 API → 前端 SSE 流式显示|⚠️|后端 `/api/v1/chat/stream` 可返回 JSON SSE；当前走 **Mock 模式**（`llm_client.py` 读 `SPARK_*`，`.env.example` 是 `XUNFEI_*`，变量名不一致）；`async_stream_chat` 是**伪流式**（先 `generate`整段再切块 yield），不是文档要求的真异步流式|
|Chroma 检索 TCP 知识点 ≥3 条|❌|本地 `data/cleaned/`、`data/vector_db/local_index.json` 均不存在；实测 `search_all('TCP三次握手')` → **docs=0**|
|Chroma 检索常见误解 ≥3 条|❌|`data/raw/misconceptions.json` 不存在；实测 **misconceptions=0**（`download_knowledge_sources.py` 可生成，但未执行入库）|
|协议仿真：两主机 \+ SYN 一帧动画|✅|`SimulatorPlayer.vue` 已实现，且超出要求（三次握手/四次挥手/滑动窗口/HTTP 等）|
|`/health` 返回 200|✅|正常：`{"status":"ok","version":"1.0.0"}`|
|数据库 4 张表可读写|✅|`users`、`student_profiles`、`chat_sessions`、`agent_logs` 均存在且有数据（另有扩展表）|

---

### 按交付物对照（Phase 1 总表）

|交付物|负责人|截止|状态|说明|
|---|---|---|---|---|
|目录结构对齐|C|5/11|⚠️|`core/`、`db/`、`kb/`、`agents/` 已有；但 Git 仍跟踪 `src/agents/student/.gitkeep`；`src/loopse/agent/` 空目录仍在；`data/raw`、`data/cleaned` 本地未建|
|README 更新|A|5/11|❌|仍是 Git 规范文档，无项目定位、无快速启动|
|`llm_client.py`（真异步流式）|B|5/12|⚠️|文件存在，有 Mock 降级；**非真流式**；环境变量与 `.env.example` 不一致|
|FastAPI 路由（统一 JSON SSE）|C|5/12|✅|已演进为多 Agent Orchestrator \+ `EventSourceResponse`，SSE 格式符合 `api_schema`|
|数据库模型 \+ 连接|C|5/13|✅|SQLAlchemy ORM \+ Repository，远超 4 表最小版|
|`text_splitter.py`|B|5/13|⚠️|无独立文件；切分逻辑内联在 `ingest_docs.py`|
|向量库封装|B|5/13|✅|`vector_store.py` 有 Chroma \+ 本地 JSON 降级|
|知识库入库脚本|B|5/13|⚠️|`ingest_docs.py`、`download_knowledge_sources.py` 有，但**本地未跑通/无数据**|
|误解库 JSON（≥20 条）|B|5/14|⚠️|脚本内嵌 24 条可生成；`data/raw/misconceptions.json`**本地缺失**|
|Profiler Agent|B|5/14|⚠️|有 `update_from_dialogue`；缺 `extract_profile()`；缺 `extract_profile.txt`；8 维字段名与 Phase 1 规格不同|
|前端 SSE 类型 \+ 封装|C|5/14|⚠️|`types/index.ts` 有 `SSEPayload`；`useSSE.ts` 有实现；未用 `@microsoft/fetch-event-source`|
|对话界面|C|5/14|⚠️|`ChatPanel.vue` 默认 **Mock 流式**；需配置 `VITE_SSE_ENDPOINT` 才连真实后端|
|Retriever Agent|B|5/15|✅|`search_all` 已实现，且含协议库 \+ 知识图谱|
|协议仿真组件|C|5/15|✅|超额完成|
|全链路联调|三人|5/16|⚠️|`phase1_issues.md` 有记录，多项标为后续 Phase 补救|
|SRS v1 初稿|A|5/17|⚠️|有 `SRS_v1.md`，但是**合并版**（偏 Phase 4），不是文档要求的第 1–4 章结构|
|联调问题记录|A|5/17|✅|`docs/results/phase1_issues.md` 存在|
|`test_llm_client.py`|B|5/12|❌|不存在|
|`health.py` 独立路由|C|5/12|⚠️|`/health` 在 `main.py`，无 `api/health.py`|
|`schema/profile.py`迁移|C|5/11|❌|仍为 `student_profile_schema.py`|

---

### 按日期任务核查

#### 5/11（周一）— 工程对齐

|任务|状态|
|---|---|
|C：目录对齐 PR|⚠️ 部分完成，遗留 `src/agents/`|
|A：README 更新|❌|
|A：SRS 第一章|⚠️ SRS 有内容，但非「第一章 项目概述」结构|
|B：讯飞 API 跑通|⚠️ 无法从仓库验证；代码侧默认 Mock|
|C：Vue3 前端初始化|✅ `frontend/` 可 `npm run dev`|
|C：Tailwind \+ Vite proxy|✅ proxy 已配；依赖与文档不完全一致（用 `marked` 而非 `markdown-it`，无 `d3`/`mermaid`）|

#### 5/12（周二）

|任务|状态|
|---|---|
|A：SRS 第二、三章|⚠️ 功能/非功能需求有表格化描述，缺原文档的 F01–F08 详表和三层诊断专节|
|B：`llm_client.py` \+ 单测|⚠️ / ❌|
|C：chat 流式路由|✅ 已超出（Orchestrator 全链路）|

#### 5/13（周三）

|任务|状态|
|---|---|
|A：SRS 第四章 \+ Prompt 初始化|⚠️ Prompt 目录有 12 个文件，缺 `profiler/extract_profile.txt`|
|B：文档清洗 \+ Chroma 向量化|❌ 本地无 `data/cleaned/`|
|C：数据库层|✅|

#### 5/14（周四）

|任务|状态|
|---|---|
|B：误解库 ≥20 条|⚠️ 脚本有，文件未落盘|
|B：Profiler v1|⚠️|
|C：对话界面 \+ SSE|⚠️ 界面有，默认 Mock|

#### 5/15（周五）

|任务|状态|
|---|---|
|B：误解入库 \+ Retriever|⚠️ Retriever ✅；入库 ❌|
|C：仿真 Canvas|✅|

#### 5/16–5/17（联调 \+ 验收）

|任务|状态|
|---|---|
|全链路联调|⚠️ 后端可跑，知识库空、前端默认 Mock|
|验收例会 13 项清单|约 **6/13 通过**|

---

### 5/17 验收清单逐项

|\#|验收项|状态|
|---|---|---|
|1|星火 API 真异步流式|❌|
|2|course\_docs 检索 TCP ≥3|❌|
|3|misconceptions 检索 ≥3|❌|
|4|`/health` 200|✅|
|5|`/api/v1/chat/stream` 统一 JSON SSE|✅|
|6|数据库 4 表读写|✅|
|7|前端 Vue3 启动 \+ 流式效果|⚠️ 能启动；默认 Mock 流式|
|8|仿真组件渲染 \+ 动画|✅|
|9|Profiler 8 维画像提取|⚠️ 有更新逻辑，无 `extract_profile`|
|10|Retriever `search_all`|✅ 代码有；无数据时结果为空|
|11|SRS v1 初稿|⚠️ 有文档，形态不符|
|12|`.env` 密钥未提交 Git|✅ `.gitignore` 已忽略|
|13|Prompt 统一存放、无硬编码|⚠️ 大部分外置；Retriever 仍有内联 `_SEARCH_PROMPT_TEMPLATE`|

---

### 已完成较好的部分（相对 Phase 1）

项目在 Phase 1 之后已明显演进：

- **多 Agent 编排**：`orchestrator.py` 串联 Retriever → Diagnosis → LLM → Profiler → Resource/Path

- **前端**：完整 Chat \+ 画像雷达 \+ 资源/路径/日志侧栏

- **仿真器**：远超 Phase 1「SYN 一帧」最低要求

- **数据库**：10 张表 \+ Repository 层

- **知识图谱**：`data/knowledge_graph.json` 已入库（Git 跟踪）

- **问题追踪**：`phase1_issues.md` 记录了 P1\-001 \~ P1\-005 及后续处理状态

---

## 优先补救项（若要让 Phase 1 验收全绿）

1. 跑通知识库流水线（最关键）

2. python scripts/download\_knowledge\_sources\.py

3. python scripts/ingest\_docs\.py

4. 统一讯飞环境变量：`llm_client.py` 与 `.env.example` 对齐为 `XUNFEI_*` 或反之

5. 修复真流式：按 Phase 1 文档用 queue \+ threading 实现 `async_stream_chat`

6. 前端默认连真实 SSE：配置 `frontend/.env` 的 `VITE_SSE_ENDPOINT=/api/v1/chat/stream`，或让 `ChatPanel` 默认走 `useChatSSE`

7. 清理目录：删除 `src/agents/student/`，决定 `agent/` vs `agents/`

8. 补 README \+ SRS 第一章结构（若需严格对齐文档）

9. 补 `extract_profile.txt` \+ Profiler\.extract\_profile\(\)

---

## 与 Phase 0 的延续关系

Phase 0 遗留的 README、环境可复现、`chromadb` 安装问题，在 Phase 1 验收时仍未解决，并直接影响了：

- 向量库检索（硬性验收 \#2、\#3）

- 星火 API 真联通（硬性验收 \#1）

- 环境一键复现

已对照 **Phase 2（5/18–5/24）** 和 **Phase 3（5/25–5/31）** 任务文档，结合当前仓库逐项核查。结论如下。

## Phase 2 完成情况

### 总览

|状态|数量|说明|
|---|---|---|
|✅ 已完成 / 超额完成|14 项|Agent、API、前端骨架已大幅超出 Phase 2 最低要求|
|⚠️ 部分完成 / 有偏差|10 项|有实现，但与文档规格或验收标准不一致|
|❌ 未完成|8 项|硬性验收项或 Phase 1 遗留仍未解决|

**Phase 2 Hard 验收预估：约 12/21 项通过，不能算“全绿通过”。**

### 5/24 Hard 验收清单（逐项）

#### Phase 1 遗留清账（6 项）

|验收项|状态|说明|
|---|---|---|
|星火 API 真流式已实测|❌|`llm_client.py` 仍为伪流式 \+ Mock；环境变量 `SPARK_*` 与 `.env.example` 的 `XUNFEI_*` 不一致|
|Chroma `course_docs` ≥30 块|❌|本地 `vector_store.count()` 全为 **0**；`data/cleaned/` 不存在|
|`misconceptions` ≥20 条|❌|本地索引为 **0**；`data/raw/misconceptions.json` 不存在|
|数据库 4 表可读写|✅|`users/student_profiles/chat_sessions/agent_logs` 均存在且有数据|
|`config/prompts/` 8 目录有内容|✅|12 个 prompt 文件，覆盖 8 个目录|
|`phase1_issues.md` 已填写清账|⚠️|文件存在，但是问题追踪表，**不是**文档要求的“5/19 验证通过”格式|

#### Orchestrator（4 项）

|验收项|状态|说明|
|---|---|---|
|输入 TCP 问题可见 Orchestrator→Retriever 调用链|✅|`orchestrator.py`已实现；实测 SSE 有 `agent_start(Orchestrator/Retriever)`|
|`agent_logs` 有调度记录|✅|实测对话后 `agent_logs` 有 3 条记录|
|SSE 含 `agent_start/tool_call/token/done`|⚠️|有 `agent_start/agent_end/token/diagnosis`，**`tool_call`****无 **，**`done`****无 **（用 `agent_end` 代替）|
|`/api/v1/logs/session/{id}` 正常|✅|路由已实现（`logs.py`）|

#### Diagnosis Agent（4 项）

|验收项|状态|说明|
|---|---|---|
|“HTTP 不需要 TCP”识别 `layer_misplacement`|⚠️|`diagnosis.py` 三层结构完整，依赖 LLM/Mock，**未在本地实测该用例**|
|返回 surface/root/pattern 三层结构|✅|`diagnose()` 返回完整结构|
|`test_diagnosis_agent.py` 全通过|⚠️|**4 通过 / 1 失败**（`test_full_diagnose_pipeline` 缺 `pytest-asyncio`）|
|前端 DiagnosisPanel 显示诊断标签|⚠️|`DiagnosisPanel.vue` 存在，但 `ChatPanel`**未接入**诊断标签展示|

#### 前端画像联动（3 项）

|验收项|状态|说明|
|---|---|---|
|ProfileRadar 雷达图渲染|✅|`ProfileRadar.vue` \+ ECharts 已实现（8 维，非文档写的 6 维）|
|从 `/api/v1/profile/{id}` 拉取数据|✅|`userStore.fetchProfile()` \+ `profile.py` 已实现|
|AgentLogPanel 从 logs API 拉取|❌|**仍为硬编码 Mock 数据**，未调用`/api/v1/logs`|

#### 工程质量（4 项）

|验收项|状态|说明|
|---|---|---|
|`repositories.py` 已提交|✅|完整 Repository 层|
|Prompt 无硬编码|⚠️|大部分外置；`retriever.py` 仍有内联 `_SEARCH_PROMPT_TEMPLATE`|
|`.env` 未提交 Git|✅|`.gitignore` 已忽略|
|新终端 clone 后按 README 启动无报错|❌|README 仍无启动说明；环境/Chroma 问题未解决|

### Phase 2 交付物对照

|交付物|截止|状态|
|---|---|---|
|Phase 1 遗留清账|5/19|❌ 知识库、星火 API、全链路仍有问题|
|`config/prompts/` 8 目录|5/19|✅|
|`repositories.py`|5/19|✅|
|`系统开发说明书_v1.md` 1–3 章|5/19–23|⚠️ 有文档，但是「技术栈\+目录结构」形态，**非**文档要求的 C4/State/接口三章|
|`coordinator.py` 骨架|5/20|❌ **不存在**；逻辑合并进 `orchestrator.py`|
|`Agent通信State设计.md`|5/21|✅|
|`diagnosis.py` \+ 单测|5/20|⚠️ 代码 ✅，单测未全绿|
|`orchestrator.py` 真实调度|5/21|✅ 已演进为完整多 Agent 编排|
|`profile.py` / `logs.py`|5/20|✅|
|ProfileRadar 接通数据|5/21|✅|
|`data/cleaned` \+ Chroma ≥30 \+ 误解 ≥20|5/23|❌ 本地未入库|
|AgentLogPanel 接 API|5/22|❌|
|前端 SSE 多事件解析|5/23|⚠️ `useSSE.ts` 有完整分发；`ChatPanel` 默认仍 Mock|
|`prompt_compliance_check.md`|5/23|✅|
|`phase2_issues.md`|5/24|✅ 5 条遗留已记录处理状态|

### Phase 2 做得好的部分

- **Orchestrator** 已超出 Phase 2 规格：串联 Retriever → Diagnosis → LLM → Profiler → Resource/Path

- **Diagnosis** 三层诊断 \+ Prompt 外置 \+ 认知引擎 trace

- **Repository \+ API** 层完整

- **Prompt 合规清单** 已建立

- 项目已演进到 Phase 3/4 水平，Phase 2 的“骨架任务”大多被覆盖

## Phase 3 完成情况

### 总览

|状态|数量|说明|
|---|---|---|
|✅ 已完成 / 超额完成|22 项|知识图谱、资源生成、路径规划、前端组件链较完整|
|⚠️ 部分完成 / 有偏差|9 项|结构或运行时与验收有差距|
|❌ 未完成|4 项|知识库数据、部分测试、全链路实测|

**Phase 3 Hard 验收预估：约 18/25 项通过；知识库与端到端实测是主要短板。**

### 5/31 Hard 验收清单（逐项）

#### 知识图谱（3 项）

|验收项|状态|说明|
|---|---|---|
|`knowledge_graph.json` ≥20 节点、≥18 边、覆盖 5 章|✅|**20 节点、21 边**，Git 已跟踪|
|`knowledge_graph.py` 可 import，`get_all_prerequisites("kn_008")` 非空|✅|返回 `['kn_007','kn_006','kn_003','kn_001']`|
|`topological_sort(["kn_006","kn_007","kn_008"])` 顺序正确|✅|顺序为 `kn_006 → kn_007 → kn_008`|

#### Resource Generator（5 项）

|验收项|状态|说明|
|---|---|---|
|`POST /api/v1/resources/generate` 返回 doc/exercise/code|⚠️|API 每次生成 **1 种**资源；Orchestrator 按意图生成单类，**非**一次返回 3 类|
|doc 含 Markdown \+ 来源|✅|代码逻辑支持|
|exercise 含 question/options/answer/explanation|✅|代码逻辑支持|
|code 含 code/explanation/expected\_output|✅|代码逻辑支持|
|`test_resource_generator.py` 全通过|❌|**5 个 async 测试全失败**（未装 `pytest-asyncio`）|

#### Path Planner（4 项）

|验收项|状态|说明|
|---|---|---|
|`POST /api/v1/path/plan` 返回 ≥3 节点|✅|空画像实测 **6 个节点**|
|每节点 `recommendation_reason` ≥20 字|✅|实测首节点理由 37 字|
|空画像用户不报错|✅|实测通过|
|满分画像返回进阶路径|⚠️|有 `_plan_advanced` 逻辑，**未实测满分画像**|

#### 全链路端到端（4 项）

|验收项|状态|说明|
|---|---|---|
|“什么是 TCP 三次握手”→ 完整 SSE \+ 流式显示|⚠️|后端 SSE 可跑；前端 `ChatPanel`**默认 Mock**，需配 `VITE_SSE_ENDPOINT`|
|“HTTP 不需要 TCP”→ diagnosis \+ 3 类 resource|⚠️|Orchestrator 有诊断\+资源逻辑；**知识库为空**，检索证据不足|
|“我该先学什么”→ path\_update \+ 时间线|⚠️|`useSSE.ts` 支持 `path_update`；`ChatView` 右侧面板已整合|
|Agent 日志 ≥4 条不同 Agent|⚠️|实测约 3 条；`AgentLogPanel` 仍用 Mock，未接 API|

#### 前端展示（6 项）

|验收项|状态|说明|
|---|---|---|
|DocCard 展开/Markdown|✅|`DocCard.vue` \+ `marked`|
|ExerciseCard 选项/解析高亮|✅|`ExerciseCard.vue`|
|CodeCard 显示/复制|✅|`CodeCard.vue`|
|PathTimeline 状态色|✅|`path/PathTimeline.vue`|
|PathReasonModal 弹窗|✅|`path/PathReasonModal.vue`|
|AgentStatusBar 动画|✅|读取 `chatStore.activeAgents`，有 pulse 动画|

#### 工程质量（3 项）

|验收项|状态|说明|
|---|---|---|
|新增 Prompt 文件加载|✅|`resource_generator` 3 个 prompt 齐全|
|新 API 已注册到 `main.py`|✅|chat/profile/logs/resources/path 均已注册|
|`npm run build` 无 TS 错误|✅|**构建成功**|

## Phase 3 交付物对照

---

## 两阶段共同遗留（跨 Phase 2/3）

这些问题在 Phase 1 就出现，Phase 2/3 文档要求清账，但当前环境仍未解决：

1. 知识库未入库：`course_docs` / `misconceptions` 本地计数为 0

2. 星火 API 未真联通：Mock 模式 \+ 环境变量命名不一致

3. 前端默认不走真实 SSE：`ChatPanel` 需配置 `VITE_SSE_ENDPOINT`

4. AgentLogPanel 未接后端：仍显示静态 Mock

5. 单元测试环境不完整：缺 `pytest-asyncio`，async 测试失败

6. `coordinator.py` 未按文档拆分：已合并进 Orchestrator（功能有，结构不符）

7. README 仍缺一键启动：影响“新环境可复现”验收

`phase2_issues.md` / `phase3_issues.md` 中多条标为“已修复”，但本机实测知识库计数仍为 0，说明修复可能只在部分成员环境完成，或未在本仓库工作区执行 `download_knowledge_sources.py` \+ `ingest_docs.py`。

---

## 三阶段进度对比

---

## 若要让 Phase 2/3 验收尽量全绿，优先做这 5 件事

*\# 1\. 下载并入库知识库*

python scripts/download\_knowledge\_sources\.py

python scripts/ingest\_docs\.py \-\-reset

*\# 2\. 安装测试依赖*

pip install pytest\-asyncio numpy

*\# 3\. 统一讯飞环境变量（\.env 与 llm\_client\.py 对齐）*

*\# 4\. 前端启用真实 SSE（frontend/\.env）*

*\# VITE\_SSE\_ENDPOINT=/api/v1/chat/stream*

*\# 5\. 将 AgentLogPanel 改为调用 /api/v1/logs/session/\{id\}*

> （注：部分内容可能由 AI 生成）
