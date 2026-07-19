---
name: agent-debugger
description: 多Agent系统调试技能：查看通信日志、检查状态机转换、分析SSE事件流、排查Agent协同问题
---

# Agent调试技能

## 描述
帮助开发者调试 Socrates-Cube 多Agent系统，包括查看 Agent 通信日志、检查 Orchestrator 状态机转换、分析 SSE 事件流、排查 Agent 协同问题。系统由 Orchestrator + 5个业务 Agent（Diagnosis、PathPlanner、ResourceGenerator、Challenger、Simulator）组成。

## 使用场景
- AI对话返回异常或不完整时，需要追踪 Agent 调用链路
- SSE 流式响应中断或超时
- 诊断 Agent 未正确触发认知诊断
- Orchestrator 路由到错误的 Agent
- 需要了解某次对话的完整 Agent 协作过程
- Agent 人格化响应风格不符预期

## 操作指南

### 1. 查看 Agent 通信日志

**通过 API 查询会话日志：**
```powershell
# 查询某个 session 的所有 Agent 日志
curl http://localhost:8000/api/v1/logs/session/{session_id}
```

**通过后端日志直接查看：**
```powershell
# 启动后端时开启 DEBUG 日志
$env:LOG_LEVEL="DEBUG"; .venv\Scripts\python.exe -m uvicorn src.loopse.main:app --port 8000
```

日志关键字过滤：
- `orchestrator` — Orchestrator 路由决策
- `diagnosis` — 诊断 Agent 触发
- `chat request` — 入站请求
- `SSE` — 流式事件

### 2. 检查 Orchestrator 状态机转换

Orchestrator 是多Agent协作的中枢，通过 GraphState 管理会话状态。

**核心文件：**
- `src/loopse/agent/orchestrator.py` — Orchestrator 主逻辑
- `src/loopse/agent/state.py` — GraphState 定义
- `docs/architecture/Agent通信State设计.md` — 状态机设计文档

**状态流转调试：**
```powershell
# 在 DEBUG 模式下，Orchestrator 会打印每次状态转换
$env:LOG_LEVEL="DEBUG"
.venv\Scripts\python.exe -m uvicorn src.loopse.main:app --port 8000

# 观察日志中的关键模式：
# "routing to agent: diagnosis" — 路由到诊断Agent
# "routing to agent: path_planner" — 路由到路径规划Agent
# "agent response complete" — Agent响应完成
```

**Agent 路由规则检查：**
查看 `config/prompts/orchestrator/system.md` 了解路由 prompt 策略。

### 3. 分析 SSE 事件流

**手动测试 SSE 流：**
```powershell
# 发送聊天请求并观察 SSE 事件流
curl -X POST http://localhost:8000/api/v1/chat/stream `
  -H "Content-Type: application/json" `
  -d '{"message": "什么是TCP三次握手", "user_id": "test-001"}'
```

**SSE 事件格式：**
```
data: {"type": "token", "content": "..."}
data: {"type": "agent_switch", "agent": "diagnosis"}
data: {"type": "done"}
```

**SSE 心跳机制：**
- 心跳间隔：15秒（`_HEARTBEAT_INTERVAL`）
- 心跳格式：`data: {"type": "heartbeat"}`
- 若超过15秒无数据，检查 Agent 是否阻塞

### 4. 各 Agent 独立调试

**诊断 Agent（三层递进式）：**
```powershell
# 运行诊断准确性测试
.venv\Scripts\python.exe scripts/run_diagnosis_accuracy_test.py
```
- 配置文件：`config/prompts/diagnosis/`
- 核心逻辑：`src/loopse/agent/diagnosis_agent.py`

**资源生成 Agent：**
- 配置文件：`config/prompts/resource_generator/`（6个子prompt）
- 核心逻辑：`src/loopse/agent/resource_generator.py`
- 支持类型：文本/图表/动画/infographic/视频/交互

**路径规划 Agent：**
- 配置文件：`config/prompts/path_planner/`
- 核心逻辑：`src/loopse/agent/path_planner.py`

**挑战者 Agent：**
- 配置文件：`config/prompts/challenger/`
- 核心逻辑：`src/loopse/agent/challenger_agent.py`

**协议仿真 Agent：**
- 配置文件：`config/prompts/simulator/`
- 核心逻辑：`src/loopse/agent/simulator_agent.py`

### 5. Agent 人格化调试

```powershell
# 查看人格配置
type config\agent_personas.json
```

人格模式：`professor`（教授）、`peer`（同伴）、`expert`（专家）

测试不同人格响应：
```powershell
# 以 peer 人格发送请求
curl -X POST http://localhost:8000/api/v1/chat/stream `
  -H "Content-Type: application/json" `
  -d '{"message": "解释DNS", "user_id": "test-001", "agent_persona": "peer"}'
```

### 6. Mock 模式快速调试

```powershell
# Mock 模式启动（无需 LLM API Key）
$env:MOCK_MODE="true"; .venv\Scripts\python.exe -m uvicorn src.loopse.main:app --port 8000

# 或通过命令行参数
.venv\Scripts\python.exe -m uvicorn src.loopse.main:app --port 8000 -- --mock-mode
```

Mock 模式下 Agent 返回预设响应，用于：
- 前后端联调
- UI 流程验证
- SSE 流机制测试

## 关键文件清单

| 文件路径 | 说明 |
|---------|------|
| `src/loopse/agent/orchestrator.py` | Orchestrator 中枢（路由+状态管理） |
| `src/loopse/agent/state.py` | GraphState 状态定义 |
| `src/loopse/agent/diagnosis_agent.py` | 诊断Agent（三层递进） |
| `src/loopse/agent/path_planner.py` | 路径规划Agent |
| `src/loopse/agent/resource_generator.py` | 资源生成Agent |
| `src/loopse/agent/challenger_agent.py` | 挑战者Agent |
| `src/loopse/agent/simulator_agent.py` | 协议仿真Agent |
| `src/loopse/api/chat.py` | SSE 流式聊天接口 |
| `src/loopse/api/logs.py` | Agent日志查询接口 |
| `config/agent_personas.json` | Agent人格配置 |
| `config/prompts/` | 各Agent的prompt模板 |

## 常见问题

### Q: SSE 流中断，前端收不到完整响应？
A: 检查后端日志是否有异常。常见原因：
1. LLM API 超时 → 检查 `.env` 中 API Key 配置
2. Agent 内部异常 → 开启 `LOG_LEVEL=DEBUG` 查看堆栈
3. 代理/网关超时 → 心跳机制应每15秒发送 heartbeat

### Q: Orchestrator 路由到错误的 Agent？
A: 检查 `config/prompts/orchestrator/system.md` 中的路由规则。用户意图关键词映射可能需要调整。

### Q: 诊断 Agent 未触发三层递进？
A: 三层递进需要：
1. 第一层：知识点识别
2. 第二层：误解检测
3. 第三层：认知根因分析
检查 `config/prompts/diagnosis/` 下的 prompt 是否完整。

### Q: Mock 模式下行为与在线模式差异大？
A: Mock Provider 返回固定文本，不会触发真实的 Agent 协作链路。Mock 适合 UI 联调，不适合 Agent 逻辑调试。

### Q: 如何增加新的 Agent？
A: 步骤：
1. 在 `src/loopse/agent/` 下创建新 Agent 文件
2. 在 `config/prompts/` 下添加对应 prompt
3. 在 Orchestrator 中注册路由规则
4. 在 `src/loopse/main.py` 中注册 API 路由（如需独立接口）
