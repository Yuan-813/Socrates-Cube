---
kind: logging_system
name: 基于 Python logging 的进程内日志与 Agent 行为持久化系统
category: logging_system
scope:
    - '**'
source_files:
    - src/loopse/main.py
    - src/loopse/api/logs.py
    - src/loopse/db/repositories.py
    - src/loopse/agent/orchestrator.py
---

## 1. 使用的系统与框架
- **标准库 `logging`**：项目未引入第三方日志框架（如 loguru、structlog），全部使用 Python 标准库 `logging`。
- **无集中式日志收集**：没有接入 ELK/Fluentd/Filebeat 等外部 sink，日志输出到控制台（Uvicorn/FastAPI 进程 stdout）。
- **Agent 行为日志持久化**：通过 SQLite 表 `agent_logs` 记录多智能体编排过程中的结构化事件，由 `/api/v1/logs/session/{session_id}` 暴露查询接口供前端 LogsView 展示。

## 2. 关键文件与包
- `src/loopse/main.py` — 应用入口，统一调用 `logging.basicConfig` 初始化根 logger，格式为 `%(asctime)s [%(levelname)s] %(name)s | %(message)s`，级别由环境变量 `LOG_LEVEL` 控制（默认 INFO）。
- `src/loopse/api/logs.py` — 提供 GET `/api/v1/logs/session/{session_id}` 路由，封装对 `AgentLogRepository.get_session_logs` 的调用。
- `src/loopse/db/repositories.py` — `AgentLogRepository` 类实现同步 `write` 与异步 `write_async`（后台线程写入），以及按 session 查询；模型定义在 `db/models.py` 的 `AgentLog` 表。
- `src/loopse/agent/orchestrator.py` — Orchestrator 在每个 Agent 步骤前后调用 `_log(session_id, agent_name, action, input_state, result)`，最终落盘到 `agent_logs` 表。
- `scripts/*.py`（ingest_docs、ingest_pdf、reingest_with_mineru、seed_resources 等）— 一次性脚本各自独立 `logging.basicConfig`，格式多为 `%(levelname)s %(message)s`，用于数据导入与种子注入。

## 3. 架构与约定
- **日志级别策略**：
  - 运行时服务：`LOG_LEVEL` 环境变量控制，默认 `INFO`，调试时设为 `DEBUG`。
  - 运维脚本：固定 `INFO`，仅打印关键进度。
- **Logger 命名空间**：各模块以 `logger = logging.getLogger(__name__)` 获取子 logger，形成 `loopse.agent.xxx`、`loopse.api.xxx` 等层级结构，便于按模块过滤。
- **结构化 Agent 日志**：`AgentLogRepository.write` 将 `input_state`、`output_state`、`duration_ms` 序列化为 JSON 存入 `state`、`result` 字段，并附带 `session_id`、`agent_name`、`action`、`timestamp`，构成可回溯的多智能体执行轨迹。
- **非阻塞写入**：`write_async` 使用 daemon 线程执行 DB 写入，异常仅 `logger.warning` 不抛出，保证主流程不受日志落盘影响。
- **前端可视化**：LogsView 组件通过 SSE + `/api/v1/logs/session/{session_id}` 拉取并渲染 Agent 执行日志，配合 AgentLogPanel 实时展示。

## 4. 开发者应遵循的规则
1. **不要重复配置 basicConfig**：仅在 `main.py` 中调用一次 `logging.basicConfig`，其他模块直接使用 `logging.getLogger(__name__)`。
2. **通过环境变量控制级别**：使用 `LOG_LEVEL=DEBUG|INFO|WARNING|ERROR` 切换，不要在代码中硬编码级别。
3. **记录结构化上下文**：在 Agent 关键路径上调用 `AgentLogRepository.write/write_async`，传入清晰的 `agent_name`、`action`、`input_state`、`output_state`，以便后续分析诊断准确率与性能。
4. **避免在热路径阻塞**：高频日志写入优先使用 `write_async`，确保不影响 SSE 流式响应延迟。
5. **脚本独立配置**：一次性脚本可各自 `basicConfig`，但建议统一格式并与服务端保持一致，便于对比排查。