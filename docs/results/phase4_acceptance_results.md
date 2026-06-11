# Phase 4 验收测试结果

## 测试环境

- 日期：2026-06-11
- 后端：`uvicorn src.loopse.main:app --reload --port 8000`
- 前端：`npm run dev` 或 `npm run build`
- LLM：未配置 Spark Key 时自动 Mock
- 知识库：公开 RFC/IANA 文档 + 本地 JSON 检索索引；ChromaDB 可选

## 验收结果

| 用例ID | 用例名称 | 状态 | 备注 |
| --- | --- | --- | --- |
| AC-01 | 多 Agent 协作对话 | 通过 | Orchestrator 串联 Retriever、Diagnosis、Profiler、Resource/Path |
| AC-02 | 学习路径生成 | 通过 | PathPlanner 基于图谱拓扑和 mastery_map 生成 |
| AC-03 | 学习画像实时更新 | 通过 | Profiler 通过 SSE 后台更新，失败时保留旧画像 |
| AC-04 | 资源标签页切换 | 待人工 UI 验证 | ResourceStore 可接收 SSE resource |
| AC-05 | Agent 状态栏动效 | 通过 | AgentStatusBar 已接入 ChatView |
| AC-06 | 路径节点详情弹窗 | 通过 | PathTimeline 点击节点打开 PathReasonModal |
| AC-07 | 后端健康检查 | 通过 | `/health` 返回服务状态 |
| AC-08 | 知识检索三库联合 | 通过 | course_docs/protocol_specs/misconceptions 均可检索 |

## 知识库计数

- `course_docs`: 43 chunks
- `protocol_specs`: 299 chunks
- `misconceptions`: 24 entries
- 数据来源：RFC Editor、IANA、本地课程 cleaned 文档、误区库

## 已知风险

当前 ChromaDB 已可用并完成入库，但运行时会输出第三方 telemetry 兼容警告：`capture() takes 1 positional argument but 3 were given`。该警告不影响 collection 创建、计数和查询。系统仍保留本地 JSON 索引作为兜底，避免向量库损坏或依赖冲突时知识检索为空。
