# Socrates Cube — 多智能体自适应网络协议学习系统

> 🏆 软件杯 A3 赛道参赛作品 | 基于讯飞星火大模型 | 知识库：谢希仁《计算机网络》第 8 版

## 📌 项目简介

**Socrates Cube** 是面向高校《计算机网络》课程的多智能体自适应学习系统。系统通过构建学生八维认知画像，动态驱动 8 个专业 Agent 协同工作，实现"诊断→检索→生成→规划"全链路个性化辅学闭环。

区别于传统问答系统仅判断"对与错"，Socrates Cube 深入分析"为什么错"——三层认知诊断引擎从表面错误层层穿透到根因与误解模式，结合知识图谱生成可解释的个性化学习路径，并按照学生认知风格偏好自适应生成 5 类多表征学习资源。

系统全程基于 RAG（检索增强生成）架构，以教材原文为权威知识源，配合可信机制（越界拦截 + 引用溯源 + 不确定性声明），有效防止大模型幻觉，确保生成内容的准确性和可追溯性。

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🤖 **8 Agent 智能协同架构** | Orchestrator 调度 + 7 大业务 Agent，SSE 实时可见推理链路 |
| 🔬 **三层认知诊断引擎** | 表面错误识别 → 根因知识节点定位 → 误解模式归类 |
| 📚 **5 类多表征资源自适应生成** | 文档 / 练习题 / 代码示例 / 思维导图 / 教学脚本 |
| 🎮 **协议仿真可视化（7 场景）** | TCP 握手/挥手、滑动窗口、HTTP、DNS、拥塞控制动画 |
| 🗺️ **可解释学习路径规划** | 知识图谱拓扑排序，最短补偿路径，每步附推荐理由 |
| 🛡️ **系统可信机制** | 越界拦截 + 引用溯源 + 不确定性声明 |
| 📊 **八维学习画像动态追踪** | 每轮对话增量更新，雷达图实时展示 |
| ⚡ **SSE 流式输出** | 多 Agent 思考过程实时推送，8 Agent 颜色区分 + 耗时统计 |

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3 + Element Plus)               │
│  ┌───────┬────────┬──────────┬──────────┬─────────┬──────────┐  │
│  │ Chat  │Profile │Diagnosis │Resources │Simulator│  Path    │  │
│  └───┬───┴────┬───┴────┬─────┴────┬─────┴────┬────┴────┬─────┘  │
│      └────────┴────────┴──────────┴──────────┴─────────┘        │
│                          SSE Event Stream                        │
└────────────────────────────────┬────────────────────────────────┘
                                 │ HTTP / SSE
┌────────────────────────────────▼────────────────────────────────┐
│                  FastAPI Backend (Python 3.10)                    │
│                                                                  │
│  ┌────────────── Orchestrator (调度中枢) ─────────────────────┐  │
│  │                                                            │  │
│  │  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌─────────┐  │  │
│  │  │ Profiler │  │Retriever │  │ Diagnosis │  │Generator│  │  │
│  │  │ 画像追踪 │  │ 知识检索 │  │ 三层诊断  │  │资源生成 │  │  │
│  │  └──────────┘  └──────────┘  └───────────┘  └─────────┘  │  │
│  │                                                            │  │
│  │  ┌──────────┐  ┌──────────┐  ┌───────────┐               │  │
│  │  │ Planner  │  │Challenger│  │ Simulator │               │  │
│  │  │ 路径规划 │  │ 概念挑战 │  │ 协议仿真  │               │  │
│  │  └──────────┘  └──────────┘  └───────────┘               │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────┐  ┌─────────────┐  ┌────────────────────────┐    │
│  │  ChromaDB  │  │   SQLite    │  │  Knowledge Graph       │    │
│  │ 三库向量检索│  │  画像持久化  │  │  20节点 × 21条依赖边   │    │
│  └────────────┘  └─────────────┘  └────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
                                 │
                     ┌───────────▼────────────┐
                     │  讯飞星火 Spark v3.5   │
                     │     LLM 推理引擎       │
                     └────────────────────────┘
```

---

## 🛠️ 技术栈

### 后端

| 类别 | 技术 | 版本 |
|------|------|------|
| Web 框架 | FastAPI + Uvicorn | 0.111 / 0.29 |
| 数据验证 | Pydantic v2 | 2.7 |
| 数据库 | SQLAlchemy + aiosqlite | 2.0 / 0.20 |
| 向量数据库 | ChromaDB（支持本地 JSON 降级） | — |
| LLM 引擎 | 讯飞星火 spark-ai-python | ≥0.4.5 |
| 流式推送 | sse-starlette | 2.1 |
| 测试 | pytest + pytest-asyncio | 8.2 / 0.23 |
| Python | 严格锁定 3.10.* | — |

### PDF 解析与知识提取

| 类别 | 技术 | 用途 |
|------|------|------|
| 高精度解析 | [MinerU](https://github.com/opendatalab/MinerU) ≥3.4 | 公式/表格/OCR 高质量提取，教材知识入库 |
| RAG 解析 | [OpenDataLoader PDF](https://github.com/opendataloader-project/opendataloader-pdf) | bounding box 源定位，引用溯源 |
| 降级方案 | PyMuPDF | 轻量级文本提取 |

### 多 Agent 与多模态参考

| 类别 | 技术 | 用途 |
|------|------|------|
| 多 Agent 框架 | [OpenMAIC](https://github.com/THU-MAIC/OpenMAIC) (清华大学) | 多智能体协同教学架构参考 |
| 多模态模型 | [SenseNova-U1](https://github.com/OpenSenseNova/SenseNova-U1) | 统一多模态理解与生成，可选可视化增强 |

### 前端

| 类别 | 技术 | 版本 |
|------|------|------|
| 框架 | Vue 3 + TypeScript | 3.5 / 5.9 |
| 构建 | Vite | 5.4 |
| 状态管理 | Pinia + 持久化插件 | 2.3 |
| UI 组件 | Element Plus | 2.13 |
| 数据可视化 | ECharts + vue-echarts | 5.6 |
| CSS | TailwindCSS | 3.4 |
| Markdown | marked + highlight.js | — |
| 图表 | Mermaid | 11.x |

---

## 🚀 快速启动

> 环境要求：Python 3.10、Node.js ≥ 18、Git

### 方式一：一键启动（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/Yuan-813/Socrates-Cube.git
cd Socrates-Cube

# 2. 后端一键启动（Windows 双击 start.bat 或命令行执行）
start.bat
# macOS/Linux:
# bash start.sh

# 3. 前端启动（新终端）
cd frontend
npm install
npm run dev
```

`start.bat` / `start.sh` 将自动完成：创建虚拟环境 → 安装依赖 → 配置 `.env` → 启动后端服务。

### 方式二：手动启动

```bash
# 后端
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows
# source .venv/bin/activate         # macOS/Linux
pip install -r requirements.txt
copy .env.example .env              # 填入讯飞 API Key（可选，未填则 Mock 模式）
python scripts/verify_env.py

# 知识库构建（首次必做）
python scripts/download_knowledge_sources.py
python scripts/ingest_docs.py --reset
python scripts/init_db.py

# 启动后端
uvicorn src.loopse.main:app --reload --host 0.0.0.0 --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev
```

### 知识库構建（首次必做）

```bash
python scripts/download_knowledge_sources.py
python scripts/ingest_docs.py --reset
```

成功输出示例：`Index counts: course_docs>=30 protocol_specs>=200 misconceptions=24`

> 若提示 `ChromaDB unavailable`，系统自动使用 `data/vector_db/local_index.json` 本地索引，不影响使用。

### 服务地址

| 服务 | 地址 |
|------|------|
| 后端 API | http://localhost:8000 |
| 健康检查 | http://localhost:8000/health |
| 前端界面 | http://localhost:5173 |
| API 文档 | http://localhost:8000/docs |

> 💡 未配置讯飞 API Key 时系统自动进入 Mock 演示模式，所有功能均可正常体验。

---

## 📁 目录结构

```
Socrates-Cube/
├── src/loopse/                # 核心后端源码
│   ├── agent/                 # 8 个智能体实现
│   │   ├── orchestrator.py    #   调度中枢
│   │   ├── profiler.py        #   画像追踪
│   │   ├── retriever.py       #   知识检索
│   │   ├── diagnosis.py       #   三层诊断
│   │   ├── resource_generator.py  # 资源生成
│   │   ├── path_planner.py    #   路径规划
│   │   ├── challenger.py      #   概念挑战
│   │   └── simulator.py       #   协议仿真
│   ├── api/                   # FastAPI 路由层
│   ├── core/                  # 信任机制、LLM 客户端
│   ├── db/                    # SQLAlchemy 模型与会话
│   ├── kb/                    # 知识库（向量检索 + 知识图谱）
│   ├── schema/                # Pydantic 数据结构
│   └── prompt/                # Prompt 加载器
├── frontend/src/              # Vue 3 前端
│   ├── views/                 # 9 个页面视图
│   ├── components/            # 可复用组件
│   ├── stores/                # Pinia 状态管理
│   ├── composables/           # SSE 等组合式函数
│   └── api/                   # 后端接口封装
├── config/prompts/            # Agent Prompt 模板（8 类）
├── data/                      # 知识库数据（运行时生成）
├── scripts/                   # 构建与初始化脚本
├── tests/                     # 单元测试
└── docs/                      # 完整项目文档
```

---

## 🎯 核心功能展示

| 功能模块 | 说明 | 路由 | 后端接口 |
|----------|------|------|----------|
| **智能对话** | 多 Agent 协同，SSE 流式输出，实时推理链路 | `/chat` | `POST /api/v1/chat/stream` |
| **能力画像** | 八维雷达图实时展示认知全貌 | `/profile` | `GET /api/v1/profile/{uid}` |
| **认知诊断** | 三层诊断：表面错误→根因→误解模式 | `/diagnosis` | `POST /api/v1/diagnosis` |
| **学习资源** | 5 类资源一键生成 | `/resources` | `POST /api/v1/resources/generate-all` |
| **协议仿真** | 7 个交互式协议动画场景 | `/simulator` | `GET /api/v1/simulator/{scene}` |
| **学习路径** | 知识图谱驱动的个性化路径 | `/path` | `POST /api/v1/path/plan` |
| **概念挑战** | 苏格拉底式追问，引导深度思考 | `/challenger` | `POST /api/v1/challenge` |
| **Agent 日志** | 8 Agent 运行日志，颜色区分 + 耗时 | `/logs` | `GET /api/v1/logs` |

---

## 🔬 三大创新点

### 1. 三层认知诊断引擎

传统问答系统只判断对错，缺乏对"为什么答错"的深层分析。本系统参考教育心理学中的认知负荷理论与错误分析框架，将诊断分为三层递进：

```
学生错误答案
    │
    ▼
┌─────────────────┐
│ L1: 表面错误层   │  ← LLM 提示 + 关键词规则
│   识别具体错误类型（概念混淆/计算错误/逻辑断裂）
├─────────────────┤
│ L2: 根因分析层   │  ← 知识图谱反向遍历 + LLM 推理
│   定位缺失的前置知识节点
├─────────────────┤
│ L3: 误解模式层   │  ← 误解库向量检索 + 模式匹配
│   归类认知模式（24种常见误解模式库）
└─────────────────┘
    │
    ▼
结构化诊断报告 → 驱动资源生成与路径规划
```

### 2. 多表征自适应资源生成

根据学生八维画像中的认知风格偏好，自动匹配最优表征形式：

| 资源类型 | 适配学习者 | 生成方式 |
|----------|-----------|----------|
| 📖 文档讲解 | 概念型学习者 | LLM + RAG 知识增强 |
| ✏️ 练习题 | 实践型学习者 | 难度自适应 + 知识点关联 |
| 💻 代码示例 | 工程型学习者 | 协议实现代码 + 注释 |
| 🧠 思维导图 | 结构型学习者 | Mermaid 图谱自动生成 |
| 🎬 教学脚本 | 视听型学习者 | 分步讲解 + 场景化 |

### 3. 可解释学习路径规划

基于 20 节点 × 21 条有向边的知识图谱，采用拓扑排序（Kahn 算法）+ DFS 前置依赖搜索，生成"最短补偿路径"——先补弱项前置知识，再推进目标知识点，每步均给出可追溯的推荐理由。

```
示例路径：目标「TCP拥塞控制」
  Step 1: IP数据报格式（前置依赖）  理由：理解网络层承载关系
  Step 2: TCP连接管理（前置依赖）   理由：拥塞控制建立在连接之上
  Step 3: 滑动窗口机制（前置依赖）  理由：拥塞窗口与发送窗口耦合
  Step 4: TCP拥塞控制（目标）       理由：慢启动→拥塞避免→快恢复
```

---

## 📊 八维学习画像

系统为每位学习者维护实时更新的八维认知画像，每轮对话后 Profiler Agent 提取增量 delta 叠加更新：

| 维度 | 字段 | 数据来源 |
|------|------|----------|
| 知识储备 | knowledge_depth | 对话分析 |
| 认知风格 | cognitive_style | 对话偏好 |
| 学习进度 | learning_progress | 路径跟踪 |
| 协议理解 | protocol_understanding | 诊断结果 |
| 动手能力 | practical_skill | 代码类资源交互 |
| 常见错误 | common_mistakes | 三层诊断积累 |
| 学习偏好 | learning_preference | 资源选择 |
| 综合水平 | overall_level | 综合评估 |

画像数据通过前端雷达图实时可视化，驱动所有 Agent 的个性化决策。

---

## ✅ 赛题硬指标达成

| 指标 | 状态 | 说明 |
|------|:----:|------|
| ≥6 维学生画像 | ✅ | 实际 8 维，超额完成 |
| 多智能体协同 | ✅ | 8 Agent 流水线架构 |
| ≥5 类个性化资源 | ✅ | doc/exercise/code/mindmap/script |
| 个性化学习路径 | ✅ | 知识图谱驱动 + 可解释推荐 |
| 防幻觉/可信机制 | ✅ | 越界拦截 + 引用溯源 + 不确定性声明 |
| 自建课程知识库 | ✅ | ChromaDB 三库：course_docs / protocol_specs / misconceptions |
| 智能辅导答疑 | ✅ | 多 Agent 协同 + Challenger 追问引导 |
| 学习效果评估 | ✅ | 三层诊断引擎 |
| 流式输出 | ✅ | SSE + AgentStatusBar + GenerationProgress |
| 协议仿真可视化 | ✅ | 7 个交互式仿真场景 |

---

## 📖 开发指南

### Git 分支规范

| 分支 | 用途 | 规则 |
|------|------|------|
| `main` | 稳定发布版 | 仅通过 dev 合并，禁止直推 |
| `dev` | 日常集成 | 禁止直接开发，通过 PR 合入 |
| `feature/*` | 功能开发 | 基于 dev 创建，命名：`feature/功能名` |
| `fix/*` | Bug 修复 | 命名：`fix/问题描述` |

### Commit 规范

```
feat: 新功能       fix: 修复问题       refactor: 重构
docs: 文档更新     test: 测试相关      chore: 配置杂项
```

### 开发工作流

```bash
# 1. 同步最新代码
git checkout dev && git pull --rebase origin dev

# 2. 创建功能分支
git checkout -b feature/xxx

# 3. 开发完成后提交
git add src/ scripts/ config/ tests/ docs/
git commit -m "feat: 功能描述"

# 4. 合并前同步
git checkout dev && git pull --rebase origin dev
git checkout feature/xxx && git rebase dev

# 5. 推送并提交 PR
git push -u origin feature/xxx
```

### 依赖管理

- 新增 Python 依赖后执行 `pip freeze > requirements.txt` 并提交
- 前端依赖通过 `package.json` 管理，提交 `package-lock.json`

---

## 👥 团队

| 角色 | 职责 |
|------|------|
| 系统架构师 | 多智能体框架设计、Git 主分支维护、防幻觉与内容安全机制 |
| 算法工程师 | Agent 核心算法、知识库 Embedding/检索、5 类资源生成 |
| 全栈工程师 | AI 交互 UI（流式输出/Markdown 渲染/仿真动画）、前后端联调部署 |

---

## 📄 License

本项目为软件杯竞赛参赛作品，仅供学术交流使用。

---

## 📚 相关文档

| 文档 | 路径 |
|------|------|
| 项目定位说明 | [`docs/项目定位说明.md`](docs/项目定位说明.md) |
| 系统架构设计 | [`docs/architecture/系统开发说明书_v1.md`](docs/architecture/系统开发说明书_v1.md) |
| 核心创新点方案 | [`docs/requirements/核心创新点落地方案.md`](docs/requirements/核心创新点落地方案.md) |
| 部署与操作手册 | [`docs/deployment/操作手册_v1.md`](docs/deployment/操作手册_v1.md) |
| 测试说明书 | [`docs/test/测试说明书_v1.md`](docs/test/测试说明书_v1.md) |

---

<p align="center">
  <b>Socrates Cube</b> — 让每一位学习者都拥有自己的苏格拉底
</p>
