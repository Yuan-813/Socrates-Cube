# API 接口说明书（IDD）
# Interface Design Description

| 文档标识 | SC-IDD-001 |
|:---:|:---|
| 项目名称 | Socrates-Cube 多智能体自适应《计算机网络》学习系统 |
| 版本号 | v1.0 |
| 接口版本 | v1 |
| 编制日期 | 2026-07-20 |
| 参考标准 | GB/T 8567-2006；OpenAPI 3.1.0 |

---

## 第一章 引言

### 1.1 接口概述

本系统提供 **REST + SSE** 混合接口，共10个API端点：
- 9个 REST JSON 接口（标准HTTP请求/响应）
- 1个 SSE 流式接口（`POST /api/v1/chat/stream`，`text/event-stream`响应）

### 1.2 Base URL

| 环境 | Base URL |
|---|---|
| 开发环境 | `http://localhost:8000` |
| Docker部署 | `http://<host>:8000` |

### 1.3 认证方式

当前版本使用用户名（username）字符串作为用户标识，通过 `user_id` 参数传递。生产部署建议增加JWT Bearer Token认证层。

### 1.4 响应格式约定

**REST接口成功响应**：HTTP 200，Content-Type: application/json

**REST接口错误响应**：
```json
{"detail": "错误描述文字"}
```

| HTTP状态码 | 含义 |
|---|---|
| 200 OK | 请求成功 |
| 400 Bad Request | 请求参数无效（如消息为空、不支持的resource_type）|
| 500 Internal Server Error | 服务器内部错误（如数据库异常、Agent运行错误）|

**SSE接口响应**：HTTP 200，Content-Type: text/event-stream，详见第三章。

---

## 第二章 系统接口

### 2.1 GET /health — 健康检查

**功能**：检查服务是否正常运行

**请求**：无参数

**响应示例**：
```json
{
  "status": "ok",
  "version": "1.0.0",
  "service": "Socrates-Cube"
}
```

---

## 第三章 对话接口（chat）

### 3.1 POST /api/v1/chat/stream — SSE流式对话（核心接口）

**功能**：以Server-Sent Events流式方式执行多智能体对话，实时推送Agent执行状态和学习结果。

**请求头**：
- `Content-Type: application/json`

**请求体**（JSON）：
```json
{
  "message": "TCP三次握手的过程是什么？",   // 用户消息，必填，1-2000字符
  "user_id": "student-001",                // 用户ID，可选，默认"student-001"
  "session_id": "uuid-string-optional"    // 会话ID，可选，不填自动创建
}
```

| 字段 | 类型 | 是否必填 | 说明 |
|---|---|---|---|
| message | string | 是 | 用户消息文本，1-2000字符 |
| user_id | string | 否 | 用户标识，默认"student-001" |
| session_id | string \| null | 否 | 会话ID（UUID），不填时自动创建新会话 |

**响应**：`text/event-stream`，格式为 `data: {...}\n\n`

**SSE事件流说明**（按时序）：

---

#### 事件类型1：agent_start

```
data: {"event":"agent_start","agent_name":"Orchestrator","data":{"message":"开始理解问题与规划协作流程"},"timestamp":"2026-07-20T10:00:00.000Z"}

data: {"event":"agent_start","agent_name":"Retriever","data":{"message":"检索知识库、协议片段和知识图谱"},"timestamp":"..."}
```

---

#### 事件类型2：agent_end

```
data: {"event":"agent_end","agent_name":"Retriever","data":{"message":"检索完成，命中文档3条、图谱节点2个"},"timestamp":"..."}
```

---

#### 事件类型3：diagnosis（仅当DiagnosisAgent执行后）

```
data: {"event":"diagnosis","agent_name":"Diagnosis","data":{
  "is_correct": false,
  "confidence": 0.9,
  "surface_error": "把TCP三次握手误认为两次握手",
  "error_type": "flow_omission",
  "root_causes": ["对TCP连接建立机制理解不足"],
  "missing_prerequisites": ["kn_005"],
  "pattern": "握手次数混淆",
  "intervention_suggestion": "通过TCP握手仿真动画演示，观察第三次ACK的作用",
  "related_node_ids": ["kn_005"],
  "agent_trace": {...}
},"timestamp":"..."}
```

---

#### 事件类型4：token（LLM生成的文字片段，多次推送）

```
data: {"event":"token","agent_name":"Orchestrator","data":{"token":"TCP"},"timestamp":"..."}
data: {"event":"token","agent_name":"Orchestrator","data":{"token":"三次"},"timestamp":"..."}
data: {"event":"token","agent_name":"Orchestrator","data":{"token":"握手"},"timestamp":"..."}
```

---

#### 事件类型5：resource（当用户意图为"resource"时）

```
data: {"event":"resource","agent_name":"ResourceGenerator","data":{
  "resource_id": "uuid-xxxx",
  "resource_type": "doc",
  "knowledge_point": "TCP三次握手",
  "title": "【知识文档】TCP三次握手",
  "content": "## TCP三次握手\n...",
  "metadata": {"difficulty": 3},
  "created_at": "2026-07-20T10:00:05Z",
  "quality_score": 0.867
},"timestamp":"..."}
```

---

#### 事件类型6：path_update（当用户意图为"planning"时）

```
data: {"event":"path_update","agent_name":"PathPlanner","data":{
  "path_id": "uuid-xxxx",
  "user_id": "student-001",
  "title": "计算机网络个性化学习路径（5个节点）",
  "total_estimated_time": 150,
  "nodes": [
    {
      "node_id": "kn_001",
      "node_name": "TCP/IP分层模型",
      "status": "completed",
      "current_mastery": 0.85,
      "recommendation_reason": "TCP/IP分层模型是本课程基础，掌握度良好",
      "suggested_resources": ["doc", "exercise"],
      "is_target": false
    },
    ...
  ],
  "quality_score": 0.867
},"timestamp":"..."}
```

---

#### 事件类型7：done（工作流最终完成）

```
data: {"event":"done","agent_name":"Orchestrator","data":{
  "session_id": "session-uuid-xxxx",
  "total_time_ms": 3241,
  "trace": {
    "goal": "TCP三次握手的过程是什么？",
    "steps": [...],
    "tool_calls": [...]
  }
},"timestamp":"..."}
```

---

#### 事件类型8：error（发生未处理异常时）

```
data: {"event":"error","agent_name":"Orchestrator","data":{"error":"LLM调用超时"},"timestamp":"..."}
```

**错误码**：HTTP 400（消息为空）；HTTP 500（服务端错误推送为error事件）

---

## 第四章 学习画像接口（profile）

### 4.1 GET /api/v1/profile/{user_id} — 获取学生画像

**路径参数**：`user_id`（string）

**响应示例**：
```json
{
  "user_id": "student-001",
  "profile": {
    "conceptual_understanding": 0.65,
    "protocol_analysis": 0.50,
    "calculation_ability": 0.45,
    "error_diagnosis": 0.55,
    "system_design": 0.40,
    "knowledge_connection": 0.60,
    "expression_clarity": 0.70,
    "self_correction": 0.50,
    "mastery_map": {"kn_005": 0.72, "kn_008": 0.43},
    "weak_points": ["kn_008"],
    "strong_points": [],
    "turn_count": 12
  }
}
```

---

### 4.2 POST /api/v1/profile/{user_id} — 更新学生画像

**路径参数**：`user_id`（string）

**请求体**：
```json
{
  "profile": {
    "conceptual_understanding": 0.70,
    "mastery_map": {"kn_005": 0.80}
  }
}
```

**响应**：
```json
{"user_id": "student-001", "status": "ok"}
```

---

## 第五章 学习路径接口（path）

### 5.1 GET /api/v1/path/{user_id} — 获取学习路径

**功能**：基于当前画像自动规划学习路径并返回

**路径参数**：`user_id`（string）

**响应**：LearningPath对象（结构同3.1中path_update事件的data字段）

---

### 5.2 POST /api/v1/path/plan — 规划学习路径

**请求体**：
```json
{
  "target_node_ids": ["kn_005", "kn_008"],  // 目标节点ID，可选
  "max_nodes": 10                            // 最大节点数，1-20，默认10
}
```

**Query参数**：`user_id`（string，默认"student-001"）

**响应**：LearningPath对象

---

### 5.3 POST /api/v1/path/{user_id}/progress — 更新节点学习进度

**路径参数**：`user_id`（string）

**请求体**：
```json
{
  "node_id": "kn_005",
  "status": "completed",      // completed | in_progress | pending
  "mastery": 0.85             // 掌握度 0.0-1.0，可选
}
```

**响应**：
```json
{"user_id": "student-001", "node_id": "kn_005", "status": "updated"}
```

---

## 第六章 学习资源接口（resources）

### 6.1 GET /api/v1/resources/ — 获取最近资源列表

**Query参数**：`limit`（integer，默认20）

**响应**：
```json
{
  "items": [
    {
      "resource_id": "uuid-xxxx",
      "resource_type": "doc",
      "knowledge_point": "TCP三次握手",
      "title": "【知识文档】TCP三次握手",
      "content": "...",
      "quality_score": 0.867,
      "created_at": "2026-07-20T10:00:00Z"
    }
  ]
}
```

---

### 6.2 POST /api/v1/resources/generate — 生成学习资源

**请求体**：
```json
{
  "knowledge_point": "TCP三次握手",   // 知识点名称，1-100字符
  "resource_type": "doc",             // doc | exercise | code
  "difficulty": 3,                    // 难度1-5，默认3
  "session_id": null                  // 会话ID，可选
}
```

**响应**：LearningResource对象

**错误**：
- 400：不支持的resource_type
- 500：生成失败

---

## 第七章 日志接口（logs）

### 7.1 GET /api/v1/logs/session/{session_id} — 查询Agent执行日志

**路径参数**：`session_id`（string）

**响应**：
```json
{
  "session_id": "session-uuid-xxxx",
  "logs": [
    {
      "log_id": "uuid-xxxx",
      "agent_name": "Retriever",
      "action": "search_all",
      "state": {"input": {...}, "output": {...}, "duration_ms": 342},
      "result": {...},
      "timestamp": "2026-07-20T10:00:01Z"
    }
  ]
}
```

日志按 `timestamp` 升序排列。

---

## 第八章 接口变更记录

| 版本 | 变更内容 |
|---|---|
| v1.0（2026-07-20）| 初始版本，包含10个端点 |

---

*本文档基于 config/api_schema.yaml（OpenAPI 3.1.0）和实际代码实现编制。*
