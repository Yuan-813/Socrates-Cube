# Agent 通信 State 设计文档 v1.0

## 一、State 数据结构定义

Socrates-Cube 的多智能体协作以 `AgentState` 为逻辑中心。运行时不要求所有字段都落成一个 Python 类，但所有 Agent 的输入输出都按同一份状态契约组织。`AgentState` 的核心字段定义如下：

```python
class AgentState:
    session_id: str          # 当前会话唯一标识
    user_id: str             # 学习者唯一标识
    user_message: str        # 本轮学生输入
    history: list[dict]      # 最近多轮对话上下文
    intent: dict             # Orchestrator 识别的意图与下游 Agent 激活计划
    retrieval: dict          # 课程文档、协议规范、误区库和知识图谱命中结果
    diagnosis: dict          # 三层认知诊断结果
    user_profile: dict       # 八维画像与知识点掌握度 mastery_map
    resources: list[dict]    # 本轮生成或推荐的学习资源
    learning_path: dict      # 路径规划结果
    agent_trace: list[dict]  # 各 Agent 的推理步骤、工具调用和自反检查
    created_at: str          # ISO 格式时间戳
    updated_at: str          # ISO 格式时间戳
```

状态中的每个结构都必须可 JSON 序列化，方便写入 `agent_logs`、经 SSE 推送给前端或用于离线 Demo 回放。`session_id` 标识会话，`user_id` 标识学习者，`user_message` 保存当前轮输入，`history` 保存最近多轮上下文，`intent` 保存 Orchestrator 的任务判断，`retrieval` 保存课程文档、协议规范、误区库和知识图谱命中结果，`diagnosis` 保存三层认知诊断，`user_profile` 保存八维画像与知识点掌握度，`resources` 保存本轮生成或推荐的学习资源，`learning_path` 保存路径规划结果，`agent_trace` 保存各 Agent 的推理步骤、工具调用和自反检查。该结构在 `src/loopse/agent/orchestrator.py` 中以字典形式流转，在 `config/api_schema.yaml` 中以 Schema 形式约束，确保前后端对 State 的理解一致。

## 二、各 Agent 读写权限矩阵

权限原则是“单点写入，多方只读”。例如画像只能由 Profiler 更新，路径只能由 PathPlanner 写入，Orchestrator 负责合并和持久化，而不是替代子 Agent 的专业判断。下表明确了每个 Agent 对每个 State 字段的读写权限：

| 字段名 | Orchestrator | Profiler | Diagnosis | Retriever | Generator | Planner |
|--------|-------------|---------|-----------|---------|---------|---------|
| session_id | R/W | R | R | R | R | R |
| user_id | R/W | R | R | R | R | R |
| user_message | R/W | R | R | R | R | R |
| history | R/W | R | R | R | R | R |
| intent | R/W | R | R | R | R | R |
| retrieval | R/W | R | W | R | R | R |
| diagnosis | R/W | R | W | R | R | R |
| user_profile | R/W | W | R | R | R | R |
| resources | R/W | R | R | R | W | R |
| learning_path | R/W | R | R | R | R | W |
| agent_trace | R/W | W | W | W | W | W |

Orchestrator 作为总调度器，拥有所有字段的读取权限和大部分字段的写入权限，但它不直接生成诊断、资源或路径的专业结果，而是调用对应 Agent 并将结果合并到 State。Profiler 只写入 `user_profile`，确保画像更新逻辑集中。Diagnosis 只写入 `diagnosis`，Retriever 只写入 `retrieval`，ResourceGenerator 只写入 `resources`，PathPlanner 只写入 `learning_path`。每个 Agent 在自己的 `agent_trace` 中追加推理步骤，便于后续可解释展示。

## 三、SSE 事件包格式规范

所有 SSE 事件统一为 `data: {...}\n\n`，JSON 包含 `event`、`agent_name`、`data`、`timestamp` 四个字段。事件类型与含义如下：

- `agent_start`：某个 Agent 开始工作，前端 AgentStatusBar 进入运行态。
- `agent_end`：该 Agent 完成，前端清理当前 Agent 状态。
- `tool_call`：用于展示检索、图谱查询等工具调用。
- `token`：用于主回复流式输出。
- `diagnosis`：推送认知诊断结果。
- `resource`：推送学习资源卡片。
- `path_update`：推送学习路径。
- `done`：表示整轮结束。
- `error`：表示可恢复或不可恢复异常。

事件命名必须稳定，新增事件应先更新 `frontend/src/types/index.ts` 和 `config/api_schema.yaml`。`agent_name` 使用英文类名，如 `Orchestrator`、`DiagnosisAgent`、`ResourceGenerator`，前端通过映射表显示中文名称。`data` 字段根据事件类型携带不同结构：`token` 事件为 `{ token: string }`；`diagnosis` 事件为 `DiagnosisResult` 对象；`resource` 事件为 `LearningResource` 对象；`path_update` 事件为 `LearningPath` 对象。`timestamp` 统一使用 UTC ISO 字符串，便于前端排序和日志回放。

## 四、State 生命周期

一次对话的生命周期为：接收请求，Orchestrator 创建初始 State；读取历史和画像；Retriever 写入检索证据；Diagnosis 基于证据写入诊断；Orchestrator 生成主回复并流式输出；Profiler 更新画像；根据 intent 触发 ResourceGenerator 或 PathPlanner；最后写入消息、资源、路径和 AgentLog。生命周期中任何 Agent 都不直接修改其他 Agent 的私有结果，只能通过 State 添加自己的输出。

该生命周期可以用以下流程图表示：

```
[接收请求] -> [Orchestrator 创建 State] -> [读取历史与画像]
    -> [Retriever 检索] -> [Diagnosis 诊断] -> [Orchestrator 生成回复]
    -> [Profiler 更新画像] -> [ResourceGenerator/PathPlanner 增强]
    -> [持久化消息/资源/路径/日志] -> [SSE done]
```

这种设计可以在 Demo 时展示清楚的因果链：问题如何被理解、证据来自哪里、诊断为什么成立、路径为什么推荐。每个阶段失败都有独立的降级策略，确保系统尽可能给出可继续学习的答复。

## 五、异常处理规范

Agent 调用失败时不得中断整个系统。Retriever 失败时返回空列表并保留知识图谱检索；ChromaDB 不可用时使用本地 JSON 索引；LLM 失败时使用规则兜底；Profiler 失败时保留旧画像；ResourceGenerator 和 PathPlanner 失败时只跳过对应增强事件。所有异常都写入 `agent_trace` 或日志，SSE 推送 `error` 时应包含可读 message，但不能泄露 API Key、路径敏感信息或完整堆栈。

Orchestrator 的最终职责是尽可能给学生一个可继续学习的答复，而不是把内部错误暴露给用户。当某个 Agent 失败时，Orchestrator 会在 `agent_trace` 中记录失败原因和降级措施，并继续执行后续步骤。如果关键 Agent（如 Diagnosis）失败，Orchestrator 会跳过诊断增强，直接基于检索证据生成通用回复。State 本身不会回滚到上一版本，但失败 Agent 的写入结果会被忽略或清空，确保下游 Agent 不会基于错误数据继续推理。
# Agent 通信 State 设计 v1.0

## 一、State 数据结构定义

Socrates-Cube 的多智能体协作以 `AgentState` 为逻辑中心。运行时不要求所有字段都落成一个 Python 类，但所有 Agent 的输入输出都按同一份状态契约组织：`session_id` 标识会话，`user_id` 标识学习者，`user_message` 保存当前轮输入，`history` 保存最近多轮上下文，`intent` 保存 Orchestrator 的任务判断，`retrieval` 保存课程文档、协议规范、误区库和知识图谱命中结果，`diagnosis` 保存三层认知诊断，`user_profile` 保存八维画像与知识点掌握度，`resources` 保存本轮生成或推荐的学习资源，`learning_path` 保存路径规划结果，`agent_trace` 保存各 Agent 的推理步骤、工具调用和自反检查。状态中的每个结构都必须可 JSON 序列化，方便写入 `agent_logs`、经 SSE 推送给前端或用于离线 Demo 回放。

## 二、各 Agent 读写权限矩阵

| 字段 | Orchestrator | Retriever | Diagnosis | Profiler | ResourceGenerator | PathPlanner |
| --- | --- | --- | --- | --- | --- | --- |
| session_id/user_id | R/W | R | R | R | R | R |
| user_message | R/W | R | R | R | R | R |
| history | R/W | R | R | R | R | R |
| intent | R/W | R | R | R | R | R |
| retrieval | R/W | W | R | R | R | R |
| diagnosis | R/W | R | W | R | R | R |
| user_profile | R/W | R | R | W | R | R |
| resources | R/W | R | R | R | W | R |
| learning_path | R/W | R | R | R | R | W |
| agent_trace | R/W | W | W | W | W | W |

权限原则是“单点写入，多方只读”。例如画像只能由 Profiler 更新，路径只能由 PathPlanner 写入，Orchestrator 负责合并和持久化，而不是替代子 Agent 的专业判断。

## 三、SSE 事件包格式规范

所有 SSE 事件统一为 `data: {...}\n\n`，JSON 包含 `event`、`agent_name`、`data`、`timestamp` 四个字段。`agent_start` 表示某个 Agent 开始工作，前端 AgentStatusBar 进入运行态；`agent_end` 表示该 Agent 完成，前端清理状态；`tool_call` 用于展示检索、图谱查询等工具调用；`token` 用于主回复流式输出；`diagnosis` 推送认知诊断结果；`resource` 推送学习资源卡片；`path_update` 推送学习路径；`done` 表示整轮结束；`error` 表示可恢复或不可恢复异常。事件命名必须稳定，新增事件应先更新 `frontend/src/types/index.ts` 和 `config/api_schema.yaml`。

## 四、State 生命周期

一次对话的生命周期为：接收请求，Orchestrator 创建初始 State；读取历史和画像；Retriever 写入检索证据；Diagnosis 基于证据写入诊断；Orchestrator 生成主回复并流式输出；Profiler 更新画像；根据 intent 触发 ResourceGenerator 或 PathPlanner；最后写入消息、资源、路径和 AgentLog。生命周期中任何 Agent 都不直接修改其他 Agent 的私有结果，只能通过 State 添加自己的输出。这样可以在 Demo 时展示清楚的因果链：问题如何被理解、证据来自哪里、诊断为什么成立、路径为什么推荐。

## 五、异常处理规范

Agent 调用失败时不得中断整个系统。Retriever 失败时返回空列表并保留知识图谱检索；ChromaDB 不可用时使用本地 JSON 索引；LLM 失败时使用规则兜底；Profiler 失败时保留旧画像；ResourceGenerator 和 PathPlanner 失败时只跳过对应增强事件。所有异常都写入 `agent_trace` 或日志，SSE 推送 `error` 时应包含可读 message，但不能泄露 API Key、路径敏感信息或完整堆栈。Orchestrator 的最终职责是尽可能给学生一个可继续学习的答复，而不是把内部错误暴露给用户。
