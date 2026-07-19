# 开源组件与 AI 工具说明

> 最后更新：2026-07-19

## 第一部分：后端开源组件清单

| 组件 | 版本 | 开源协议 | 用途 |
|------|------|----------|------|
| Python | 3.10+ | PSF License | 运行时环境 |
| FastAPI | 0.111.0 | MIT | Web 框架，提供 REST API 和 SSE 流式接口 |
| uvicorn | 0.29.0 | BSD | ASGI 服务器，运行 FastAPI 应用 |
| sse-starlette | 2.1.0 | MIT | SSE（Server-Sent Events）推送支持 |
| SQLAlchemy | 2.0.30 | MIT | ORM 框架，数据库操作抽象层 |
| aiosqlite | 0.20.0 | MIT | 异步 SQLite 驱动 |
| ChromaDB | 0.5.0 | Apache 2.0 | 向量数据库，存储和检索课程文档/协议规范/误区库 |
| Pydantic | 2.x | MIT | 数据验证和序列化，API Schema 校验 |
| spark-ai-python | >=0.4.5 | MIT | 讯飞星火大模型 SDK，提供 LLM 能力 |
| httpx | 0.27.0 | BSD | HTTP 客户端，API 调用 |
| python-dotenv | 1.0.1 | BSD | 环境变量管理 |
| pytest | 8.2.0 | MIT | 单元测试框架 |
| pytest-asyncio | 0.23.7 | MIT | 异步测试支持 |
| **magic-pdf (MinerU)** | latest | Apache 2.0 | PDF 高精度解析，支持公式/表格/图文混合。开源：[opendatalab/MinerU](https://github.com/opendatalab/MinerU)。可选，未安装时降级 PyMuPDF |
| **PyMuPDF** | >=1.24.0 | AGPL-3.0 | PDF 标准降级方案（MinerU 未安装时自动使用） |

## 第二部分：前端开源组件清单

| 组件 | 版本 | 开源协议 | 用途 |
|------|------|----------|------|
| Vue.js | 3.x | MIT | UI 框架，组件化开发 |
| TypeScript | 5.x | Apache 2.0 | 类型安全的 JavaScript 超集 |
| Vite | 5.x | MIT | 前端构建工具，HMR 热更新 |
| Pinia | 2.x | MIT | Vue 状态管理（替代 Vuex） |
| TailwindCSS | 3.x | MIT | 原子化 CSS 样式框架 |
| Element Plus | 2.x | MIT | Vue3 UI 组件库（表单/弹窗/标签等） |
| ECharts | 5.x | Apache 2.0 | 数据可视化（画像雷达图） |
| markdown-it | 14.x | MIT | Markdown 渲染（对话消息/文档卡片） |
| Three.js | 0.165+ | MIT | 3D设备可视化（Hardware3DView）|
| openai | 1.x | Apache 2.0 | OpenAI 兼容 SDK，用于接入 GLM-4/Qwen/DeepSeek |
| vue-router | 4.x | MIT | 前端路由管理 |
| @vueuse/core | 10.x | MIT | Vue 组合式工具函数库 |
| highlight.js | 11.x | BSD | 代码高亮（资源卡片代码展示） |

## 第三部分：AI 工具与模型

| 工具/模型 | 提供方 | 用途 | 协议说明 |
|-----------|--------|------|----------|
| 讯飞星火大模型 | 科大讯飞 | 自然语言理解与生成、对话回复、资源生成、诊断分析 | 商业 API，需 Key 认证 |
| ChatGLM3 开源模型 | 清华大学 KEG 实验室 | 理论参考基础，中文理解能力参考。开源地址：https://github.com/THUDM/ChatGLM3 | Apache 2.0 |
| GLM-4 / GLM-4-Flash | 智谱 AI（清华 ChatGLM 商业版） | 多人格对话路由（expert/engineer/interviewer），通过 OpenAI 兼容接口接入 | 商业 API，需 Key；GLM-4-Flash 有免费额度 |
| Qwen-Plus | 阿里云 | 备选多模型路由 | 商业 API，需 Key |
| DeepSeek-Chat | DeepSeek | 备选多模型路由 | 商业 API，需 Key |
| **SenseNova-U1** | 商汤 AI（OpenSenseNova） | 信息图/思维导图/流程图多模态生成，开源参考：[OpenSenseNova/SenseNova-U1](https://github.com/OpenSenseNova/SenseNova-U1) | 商业 API，未配置时自动降级 LLM+SVG |
| Mock LLM | 自研 | 离线降级模式，未配置 API Key 时提供预设回复 | 项目内部实现 |

## 第四部分：知识库数据来源

| 来源 | 类型 | 协议 | 用途 |
|------|------|------|------|
| RFC Editor (rfc-editor.org) | 协议规范 | 公共领域 | protocol_specs 集合 |
| IANA (iana.org) | 协议参数 | 公共领域 | protocol_specs 集合 |
| 谢希仁《计算机网络》第8版 | 教材 | 教学使用 | course_docs 集合 |
| 自研误区库 | 教学数据 | 原创 | misconceptions 集合 |

## 第五部分：架构参考项目

| 项目 | 来源 | 开源协议 | 参考内容 |
|------|------|----------|----------|
| **OpenMAIC** | 清华大学 MAIC 实验室 | MIT | 多智能体协同教学平台。[THU-MAIC/OpenMAIC](https://github.com/THU-MAIC/OpenMAIC)。本项目 Orchestrator+Agent 架构、认知单元（ACU）建模思路参考该项目理念 |
| **opendatalab-pdf** | OpenDataLab（MinerU生态） | Apache 2.0 | PDF 数据加载范式参考。[opendatalab/opendatalab-pdf](https://github.com/opendatalab/opendatalab-pdf) |
| ChatGLM3 | 清华大学 KEG | Apache 2.0 | 中文对话能力参考基线 |

## 第五部分：PDF 解析与知识提取开源工具

| 组件 | 版本 | 开源协议 | 用途 |
|------|------|----------|------|
| MinerU | ≥3.4.0 | AGPL-3.0 | PDF高精度解析引擎，支持公式/表格/OCR，用于教材知识提取 |
| OpenDataLoader PDF | ≥0.3.0 | Apache 2.0 | RAG专用PDF解析器，支持bounding box源定位，引用溯源 |
| PyMuPDF | ≥1.24.0 | AGPL-3.0 | PDF文本提取降级方案，轻量快速 |

### MinerU 详细说明

- **项目地址**：https://github.com/opendatalab/MinerU
- **解析后端**：
  - `pipeline`：CPU 友好，精度 86.2%，适合日常使用
  - `vlm`：GPU 加速，精度 95.39%，适合复杂版面
  - `hybrid`：自动混合，根据页面复杂度选择后端
- **核心能力**：公式→LaTeX、表格→HTML、多列版面、109种语言OCR
- **本项目集成**：`src/loopse/kb/mineru_parser.py` 提供适配层，支持优雅降级（MinerU → PyMuPDF → 报错）

### OpenDataLoader PDF 详细说明

- **项目地址**：https://github.com/opendataloader-project/opendataloader-pdf
- **核心能力**：专为 RAG 场景设计的 PDF 解析器，提供 bounding box 源定位
- **本项目用途**：知识库引用溯源，精确定位回答内容在原文中的位置

## 第六部分：多 Agent 框架与多模态参考

| 组件 | 提供方 | 开源协议 | 用途 |
|------|--------|----------|------|
| OpenMAIC | 清华大学 THU-MAIC | Apache 2.0 | 多 Agent 教学智能体框架，架构参考 |
| SenseNova-U1 | 商汤科技 | MIT | 统一多模态理解与生成模型，可选可视化增强 |

### OpenMAIC 详细说明

- **项目地址**：https://github.com/THU-MAIC/OpenMAIC
- **核心能力**：清华大学多智能体協同教学框架，支持 Agent 角色定义、任务分解、协同调度
- **本项目用途**：Orchestrator 调度与多 Agent 协同架构设计参考，借鉴其 Agent 间通信协议与任务流转机制

### SenseNova-U1 详细说明

- **项目地址**：https://github.com/OpenSenseNova/SenseNova-U1
- **核心能力**：统一多模态理解与生成，支持图像/文本/表格综合理解
- **本项目用途**：可选可视化增强，用于教材图表解析、复杂版面理解等多模态场景

## 声明

本项目所有开源组件均遵循各自原始许可证。知识库资料仅用于教学演示目的，不做商业分发。
