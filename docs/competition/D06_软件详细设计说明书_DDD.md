# 软件详细设计说明书（DDD）
# Detailed Design Description

| 文档标识 | SC-DDD-001 |
|:---:|:---|
| 项目名称 | Socrates-Cube 多智能体自适应《计算机网络》学习系统 |
| 版本号 | v1.0 |
| 编制日期 | 2026-07-20 |
| 参考标准 | GB/T 8567-2006《计算机软件文档编制规范》 |
| 依赖文档 | SC-SDD-001；SC-AIARCH-001 |

---

## 第一章 引言

本文档描述 Socrates-Cube 系统关键模块的详细设计，包括核心算法的伪代码、关键数据结构定义、模块接口签名和异常处理机制。重点描述 Agent 层和知识库层，前端部分描述核心交互逻辑。

---

## 第二章 后端详细设计

### 2.1 主入口与应用初始化

**文件**：`src/loopse/main.py`（55行）

```python
app = FastAPI(title="Socrates-Cube", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"])

@app.on_event("startup")
async def _on_startup():
    init_db()  # 自动建表，应用启动时执行

# 注册5个路由模块
app.include_router(chat_router)      # POST /api/v1/chat/stream
app.include_router(profile_router)   # GET/POST /api/v1/profile/{user_id}
app.include_router(logs_router)      # GET /api/v1/logs/session/{session_id}
app.include_router(resources_router) # GET/POST /api/v1/resources/**
app.include_router(path_router)      # GET/POST /api/v1/path/**

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0", "service": "Socrates-Cube"}
```

### 2.2 路由层详细设计

#### 2.2.1 chat.py — SSE流式对话路由

**关键实现细节**：

```python
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    user_id: str = Field(default="student-001")
    session_id: str | None = None

@router.post("/stream")
async def chat_stream(req: ChatRequest):
    # 1. 验证消息非空
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")
    # 2. 确保用户和会话存在
    UserRepository.get_or_create(req.user_id)
    session_id = req.session_id or str(uuid.uuid4())
    SessionRepository.get_or_create(session_id, req.user_id)
    # 3. 创建异步生成器
    async def event_generator():
        async for chunk in _orchestrator.async_stream_reply(session_id, req.user_id, req.message):
            yield chunk
    # 4. 返回SSE响应
    return EventSourceResponse(event_generator(), media_type="text/event-stream")
```

#### 2.2.2 path.py — 学习路径路由

**进度更新逻辑**：
```python
@router.post("/{user_id}/progress")
def update_node_progress(user_id: str, req: ProgressUpdateRequest):
    profile = _profiler.get_profile(user_id)
    mastery_map = profile.get("mastery_map", {})
    if req.mastery is not None:
        mastery_map[req.node_id] = req.mastery
        profile["mastery_map"] = mastery_map
        # 实时重新计算 weak_points 和 strong_points
        profile["weak_points"] = [nid for nid, m in mastery_map.items() if m < 0.5]
        profile["strong_points"] = [nid for nid, m in mastery_map.items() if m >= 0.8]
        ProfileRepository.upsert(user_id, profile)
    return {"user_id": user_id, "node_id": req.node_id, "status": "updated"}
```

### 2.3 Agent层详细设计

#### 2.3.1 OrchestratorAgent — async_stream_reply() 详细流程

**方法签名**：
```python
async def async_stream_reply(
    self,
    session_id: str,
    user_id: str,
    user_message: str
) -> AsyncGenerator[str, None]
```

**执行伪代码**：
```
1. started = current_time()
2. trace = make_trace(user_message)
3. yield SSE("agent_start", "Orchestrator", "开始理解问题")
4. history_text = SessionRepository.get_last_8_messages(session_id)
5. intent = _detect_intent(user_message)  // qa/resource/planning/simulation
6. yield SSE("agent_start", "Retriever", "检索知识库")
7. retrieval = RetrieverAgent.search_all(user_message, history_text, session_id)
8. yield SSE("agent_end", "Retriever", f"命中{len(docs)}条文档")
9. yield SSE("agent_start", "Diagnosis", "三层错误诊断")
10. diag = DiagnosisAgent.diagnose(user_message, docs+protocols, history)
11. yield SSE("diagnosis", "Diagnosis", diag)
12. yield SSE("agent_end", "Diagnosis", diag.is_correct)
13. yield SSE("agent_start", "Orchestrator", "生成主回复")
14. prompt = _build_reply_prompt(user_message, retrieval, diag, history, trace)
15. full_reply = ""
    async for token in llm_client.async_stream_chat(prompt):
        full_reply += token
        yield SSE("token", "Orchestrator", {"token": token})
16. yield SSE("agent_end", "Orchestrator", "主回复完成")
17. yield SSE("agent_start", "Profiler", "更新学习画像")
18. try:
      profile = ProfilerAgent.update_from_dialogue(user_id, user_message, full_reply, diag)
      yield SSE("agent_end", "Profiler", profile.weak_points)
    except: // 降级
      profile = ProfilerAgent.get_profile(user_id)
      yield SSE("agent_end", "Profiler", "画像更新跳过")
19. if intent == "resource":
      yield SSE("agent_start", "ResourceGenerator", "生成学习资源")
      resource = ResourceGeneratorAgent.generate(res_type, knowledge_point, docs)
      yield SSE("resource", "ResourceGenerator", resource)
      yield SSE("agent_end", "ResourceGenerator", "资源生成完成")
20. if intent == "planning":
      yield SSE("agent_start", "PathPlanner", "基于画像和图谱生成路径")
      path = PathPlannerAgent.plan(user_id, profile)
      yield SSE("path_update", "PathPlanner", path)
      yield SSE("agent_end", "PathPlanner", f"{len(path.nodes)}个节点")
21. SessionRepository.append_message(session_id, "user", user_message)
22. SessionRepository.append_message(session_id, "assistant", full_reply)
23. yield SSE("done", "Orchestrator", {session_id, total_time_ms, trace})
```

#### 2.3.2 DiagnosisAgent — 三层诊断详细算法

**_detect_surface_error() 伪代码**：
```
输入: message, docs, history
1. context = format_docs(docs[:4])
2. prompt = surface_error_template.format(student_message=message, reference_docs=context)
3. raw = llm_client.chat(prompt, max_tokens=300)
4. data = parse_json(raw, default={})
5. result = normalize_surface(data, message)
   // 硬规则：
   if "两次握手" in message or "二次握手" in message:
       result.is_correct = False
       result.error_type = "factual"
       result.surface_error = "把TCP三次握手误认为两次握手"
6. return AwaitableDict(result)
```

**_analyze_root_cause() 伪代码**：
```
输入: message, surface_error_str, docs
1. context = format_docs(docs)
2. prompt = root_cause_template.format(
       student_message=message,
       surface_error=surface_error_str,
       reference_docs=context
   )
3. data = parse_json(llm_client.chat(prompt, max_tokens=300), default={})
4. // 兼容数组格式和对象格式：
   if isinstance(data, list):
       causes = [item["reason"] for item in data]
       missing = [item["knowledge_node_id"] for item in data]
   else:
       causes = data.get("root_causes", ["概念边界不清"])
       missing = data.get("missing_prerequisites", [])
5. return AwaitableDict({"root_causes": causes, "missing_prerequisites": missing})
```

**_match_pattern() 伪代码**：
```
输入: surface_error, root_causes
1. prompt = pattern_template.format(
       surface_error=surface_error,
       root_causes="；".join(root_causes)
   )
2. data = parse_json(llm_client.chat(prompt, max_tokens=220), default={})
3. return AwaitableDict({
       "pattern": data.get("pattern", "无明确模式"),
       "intervention_suggestion": data.get("intervention_suggestion", "用反例和追问引导")
   })
```

#### 2.3.3 ProfilerAgent — 画像更新详细算法

**_parse_delta() 详细逻辑**：
```
输入: LLM返回的JSON文本
1. 提取JSON字符串（find("{")到rfind("}")）
2. json.loads(json_str)
3. for dim in PROFILE_DIMENSIONS:
       value = data.get(dim)
       if value > 1:  // 兼容LLM返回1-5的scale
           value = (value - 3.0) / 10.0
       delta[dim] = clamp(value, -0.2, 0.2)
4. return delta
```

**_apply_delta() 详细逻辑**：
```
输入: current_profile, delta, diagnosis_result
1. for dim in PROFILE_DIMENSIONS:
       if dim in delta:
           profile[dim] = clamp(profile[dim] + delta[dim], 0.1, 1.0)
2. if diagnosis_result is not None:
       mastery_map = dict(profile["mastery_map"])
       for node_id in diagnosis_result["related_node_ids"]:
           old = mastery_map.get(node_id, 0.5)
           change = +0.05 if diagnosis_result["is_correct"] else -0.07
           mastery_map[node_id] = clamp(old + change, 0.0, 1.0)
       profile["mastery_map"] = mastery_map
       profile["weak_points"] = [nid for nid, score in mastery_map.items() if score < 0.5]
       profile["strong_points"] = [nid for nid, score in mastery_map.items() if score >= 0.8]
3. return profile
```

#### 2.3.4 PathPlannerAgent — Kahn拓扑排序详细算法

**完整算法（topological_sort）**：
```
输入: target_ids（节点ID集合）
1. target_ids = {nid for nid in node_ids if nid in self._nodes}
2. // 仅计算目标子图内的入度
   in_degree = {nid: 0 for nid in target_ids}
   for nid in target_ids:
       for pred in self._predecessors.get(nid, set()):
           if pred in target_ids:
               in_degree[nid] += 1
3. // 初始化队列（入度0的节点，按chapter/difficulty/id排序）
   queue = sorted([nid for nid, d in in_degree.items() if d == 0],
                  key=lambda n: (nodes[n].chapter, nodes[n].difficulty, n))
4. sorted_nodes = []
   while queue:
       current = queue.pop(0)
       sorted_nodes.append(nodes[current])
       for succ in self._successors.get(current, set()):
           if succ not in in_degree: continue
           in_degree[succ] -= 1
           if in_degree[succ] == 0:
               queue.append(succ)
       queue.sort(key=lambda n: (nodes[n].chapter, nodes[n].difficulty, n))
5. return sorted_nodes
// 时间复杂度：O((V+E) log V)（因每步重新排序）
```

#### 2.3.5 ResourceGeneratorAgent — 质量评估机制

**质量评分计算**：
```python
checks = {
    "has_content": len(content) >= 30,       # 内容长度检查
    "has_title": bool(title),                  # 标题存在检查
    "type_matched": res_type == resource_type  # 类型匹配检查
}
reflection = self.reflect(trace, checks)
# reflection["confidence"] = passed_count / total_checks ∈ {0.33, 0.67, 1.0}
quality_score = round(0.6 + 0.4 * reflection["confidence"], 3)
# quality_score ∈ {0.733, 0.867, 1.0}（三检查均通过时1.0，其中一项失败时0.867）
```

### 2.4 知识库层详细设计

#### 2.4.1 VectorStore — TF-IDF降级搜索

**_tokenize() 分词算法**：
```python
def _tokenize(text: str) -> list[str]:
    text = text.lower()
    latin = re.findall(r"[a-z0-9][a-z0-9_\-./]{1,}", text)  # 英文词
    cjk = re.findall(r"[\u4e00-\u9fff]{2,}", text)           # 中文词（≥2字）
    return latin + cjk
```

**TF-IDF评分公式**：
\[
score = \sum_{t \in query} (1 + \log tf_t) \cdot \left(\log\frac{N+1}{df_t+1} + 1\right)
\]

其中 N 为文档总数，\(tf_t\) 为词 t 在文档中的频次，\(df_t\) 为包含词 t 的文档数。

#### 2.4.2 KnowledgeGraph — estimate_mastery() 算法

```python
def estimate_mastery(node_id, mastery_map) -> float:
    direct = mastery_map.get(node_id)        # 直接掌握度记录
    prereqs = self.get_prerequisites(node_id)  # 直接前置节点
    
    if direct is not None:
        if not prereqs:
            return round(float(direct), 3)
        prereq_avg = mean([mastery_map.get(p.id, 0.35) for p in prereqs])
        return round(0.75 * direct + 0.25 * prereq_avg, 3)  # 加权估算
    
    if not prereqs:
        return 0.35   # 无记录、无前置 → 中低估值
    return round(mean([mastery_map.get(p.id, 0.35) for p in prereqs]) * 0.85, 3)
```

---

## 第三章 前端详细设计

### 3.1 SSE事件消费逻辑

前端通过 EventSource API 或 fetch-SSE 接收事件流，核心处理逻辑：

```typescript
// composables/useSSE.ts（概念性描述）
async function startChat(message: string, userId: string) {
  const response = await fetch('/api/v1/chat/stream', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({message, user_id: userId})
  })
  const reader = response.body!.getReader()
  // 读取SSE流
  while (true) {
    const {done, value} = await reader.read()
    if (done) break
    const text = decoder.decode(value)
    // 解析 "data: {...}\n\n" 格式
    for (const line of text.split('\n\n')) {
      if (line.startsWith('data: ')) {
        const payload = JSON.parse(line.slice(6))
        dispatchEvent(payload)  // 分发到对应处理器
      }
    }
  }
}

function dispatchEvent(payload) {
  switch(payload.event) {
    case 'token':    // 追加到聊天消息
      chatStore.appendToken(payload.data.token)
      break
    case 'diagnosis': // 更新诊断面板
      diagnosisStore.setResult(payload.data)
      break
    case 'path_update': // 更新学习路径
      pathStore.setPath(payload.data)
      break
    case 'done':     // 标记完成
      chatStore.setLoading(false)
      break
  }
}
```

### 3.2 核心页面交互

**ChatView**：接收token事件逐字拼接消息；接收diagnosis事件展示诊断折叠面板；显示Agent执行时间线（agent_start/agent_end事件）。

**ProfileView**：调用 `GET /api/v1/profile/{user_id}`，将8维分数渲染为ECharts雷达图；mastery_map渲染为知识点条形图。

**PathView**：调用 `GET /api/v1/path/{user_id}` 或接收SSE path_update事件；节点状态（completed/in_progress/pending/locked）对应不同颜色/图标；点击节点可更新进度（POST /api/v1/path/{user_id}/progress）。

---

## 第四章 关键数据结构定义

### 4.1 DiagnosisResult（诊断报告）

```python
DiagnosisResult = TypedDict("DiagnosisResult", {
    "is_correct": bool,
    "confidence": float,           # [0, 1]
    "surface_error": Optional[str],
    "error_type": str,             # 23种错误类型之一或"none"
    "root_causes": list[str],
    "missing_prerequisites": list[str],  # 知识节点ID列表
    "pattern": Optional[str],
    "intervention_suggestion": str,
    "related_node_ids": list[str],
    "agent_trace": dict
})
```

### 4.2 StudentProfile（学生画像）

```python
_DEFAULT_PROFILE = {
    "conceptual_understanding": 0.5,
    "protocol_analysis": 0.5,
    "calculation_ability": 0.5,
    "error_diagnosis": 0.5,
    "system_design": 0.5,
    "knowledge_connection": 0.5,
    "expression_clarity": 0.5,
    "self_correction": 0.5,
    "mastery_map": {},       # Dict[str, float] 知识节点掌握度
    "weak_points": [],       # List[str] 掌握度<0.5的节点ID
    "strong_points": [],     # List[str] 掌握度≥0.8的节点ID
    "turn_count": 0          # int 累计对话轮次
}
```

### 4.3 LearningPath（学习路径）

```python
LearningPath = {
    "path_id": str,             # UUID
    "user_id": str,
    "title": str,               # 自动生成标题
    "description": str,
    "total_estimated_time": int, # 分钟
    "nodes": list[PathNode],    # 有序路径节点列表
    "generated_at": str,        # ISO 8601时间
    "agent_trace": dict,
    "quality_score": float      # PathPlanner的self-reflection置信度
}

PathNode = {
    "node_id": str,
    "node_name": str,
    "type": str,                 # concept/skill/protocol
    "chapter": str,
    "difficulty": int,           # 1-5
    "estimated_time": int,       # 分钟
    "recommendation_reason": str, # ≥12字符的推荐理由
    "reason_sources": list[str], # ["知识图谱前置依赖", "学生画像掌握度", "薄弱点优先级"]
    "suggested_resources": list[str], # ["doc", "exercise"] 或 + ["code"]
    "prerequisites": list[str],
    "prerequisites_met": bool,
    "status": str,               # completed/in_progress/pending/locked
    "current_mastery": float,    # estimate_mastery()的估算值
    "is_target": bool            # 是否为目标节点
}
```

---

## 第五章 错误处理与异常设计

### 5.1 LLM调用失败的降级策略

| 场景 | 处理方式 |
|---|---|
| `llm_client.chat()` 超时或网络错误 | LLM客户端内部捕获，返回Mock预设内容 |
| 诊断Prompt调用失败 | `DiagnosisAgent` catch Exception → 返回低置信度空诊断结果 |
| 画像Prompt调用失败 | `ProfilerAgent` catch Exception → delta为{}，仅执行确定性更新 |
| 资源生成Prompt调用失败 | `ResourceGeneratorAgent` 不捕获，会触发路由500 |

### 5.2 ChromaDB不可用时的降级流程

```python
class VectorStore:
    def __init__(self):
        try:
            import chromadb
            self.client = chromadb.PersistentClient(...)
            self.available = True
        except Exception as exc:
            logger.warning("ChromaDB unavailable; local KB index will be used: %s", exc)
            self.available = False  # 降级标记
    
    def search(self, collection_name, query, n_results):
        col = self._collections.get(collection_name)
        if col is not None:
            try:
                result = col.query(...)
                if result: return result
            except Exception:
                pass
        return self._search_local(...)  # 自动路由到TF-IDF
```

### 5.3 全局异常处理

FastAPI使用 `HTTPException` 处理可预期的业务错误：
- `400 Bad Request`：消息为空（chat.py）、不支持的resource_type（resources.py）
- `500 Internal Server Error`：数据库操作失败、Agent运行时异常

对于SSE流式响应中的未捕获异常：
```python
try:
    # ... 主流程 ...
except Exception as exc:
    logger.exception("[Orchestrator] fatal error: %s", exc)
    yield self._sse("error", "Orchestrator", {"error": str(exc)})
    # 不再yield done事件，前端需处理仅有error事件的情况
```

---

*本文档遵循 GB/T 8567-2006 规范，伪代码描述基于实际代码实现，不含未开发功能。*
