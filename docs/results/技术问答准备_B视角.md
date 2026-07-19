# Socrates-Cube 技术问答准备（B 视角）

> 面向技术评委的深度问答，聚焦算法实现、工程决策、性能与可靠性

---

## 一、三层诊断算法细节

### T1：三层诊断的调用链是怎样的？每层的输入输出是什么？

**答**：调用链是串行的，每层输出作为下层输入：

```
学生回答 + 检索结果
    │
    ▼
┌─────────────────────────────────┐
│ Layer 1: surface_error          │
│ Input:  student_answer, question │
│ Output: { is_correct, error_type,│
│   confidence, error_description }│
└──────────────┬──────────────────┘
               │ error_type + 检索上下文
    ▼
┌─────────────────────────────────┐
│ Layer 2: root_cause              │
│ Input:  student_answer, error,   │
│         knowledge_context        │
│ Output: { root_causes[],         │
│   missing_prerequisites[],       │
│   confidence }                   │
└──────────────┬──────────────────┘
               │ root_causes + error_type
    ▼
┌─────────────────────────────────┐
│ Layer 3: pattern_match           │
│ Input:  error_type, root_causes  │
│ Output: { pattern: {name,         │
│   intervention_suggestion},       │
│   matched_misconception_id }      │
└─────────────────────────────────┘
```

每层独立 prompt 文件在 `config/prompts/diagnosis/` 下，JSON 解析有类型兜底。

---

### T2：诊断的 7 种错误类型和 7 种误区模式分别是什么？

**答**：

**7 种错误类型**（Layer 1 输出）：

| 类型 | 说明 | 典型案例 |
|------|------|---------|
| flow_omission | 流程遗漏 | "TCP 两次握手就够了" |
| hierarchy_error | 层级错位 | "HTTP 直接基于 IP" |
| concept_confusion | 概念混淆 | "TCP 和 UDP 一样" |
| calculation_error | 计算错误 | 滑动窗口大小算错 |
| state_error | 状态错误 | "SYN_SENT 可以发数据" |
| semantic_error | 语义错误 | "ACK 就是确认收到数据" |
| other | 其他 | 不属于以上类型 |

**7 种误区模式**（Layer 3 输出）：

| 模式 | 说明 | 干预建议 |
|------|------|---------|
| flow_simplification | 流程简化 | 仿真纠偏 |
| layer_conflation | 层级混淆 | 对比题练习 |
| concept_equivalence | 概念等价化 | 概念边界题 |
| state_misunderstanding | 状态误解 | 状态机可视化 |
| direction_confusion | 方向混淆 | 报文流向图 |
| range_error | 范围错误 | 边界值计算 |
| oversimplification | 过度简化 | 反例分析 |

---

### T3：如果 LLM 返回的 JSON 格式不对怎么办？

**答**：三级容错策略：

1. **直接解析**：`json.loads(text)` 尝试直接解析。
2. **正则提取**：如果直接解析失败，用正则 `r'\{[\s\S]*\}'` 提取 JSON 片段再解析。
3. **类型兜底**：解析成功后做类型检查和修正：

```python
# pattern 可能是 str，包装为 dict
if isinstance(pattern, str):
    pattern = {"pattern": pattern, "intervention_suggestion": "建议先用对比题澄清概念边界。"}
if not isinstance(pattern, dict):
    pattern = {}

# root_causes 可能不是 list
if not isinstance(root_causes, list):
    root_causes = [str(root_causes)] if root_causes else []

# missing_prerequisites 同理
if not isinstance(missing_prereqs, list):
    missing_prereqs = []
```

这样保证下游消费者（Profiler、ResourceGenerator）拿到的始终是正确类型的结构化数据。

---

## 二、知识图谱与向量检索

### T4：知识图谱的数据结构是怎样的？

**答**：`KnowledgeGraph` 类管理节点和边：

```python
@dataclass
class KnowledgeNode:
    id: str            # "kn_001" ~ "kn_020"
    name: str          # "TCP 三次握手"
    type: str           # "concept" | "protocol" | "mechanism"
    chapter: int       # 1, 3, 4, 5, 6
    difficulty: int    # 1-5
    estimated_time: int # 分钟
    prerequisites: list[str]  # 前置节点 ID 列表
```

数据存储在 `data/knowledge_graph.json`，包含 20 个节点和 21 条依赖边。核心操作：

- `get_prerequisites(node_id)`：递归获取所有前置依赖
- `topological_sort(node_ids)`：拓扑排序，返回合理学习顺序
- `find_weak_prerequisites(targets, mastery_map, threshold)`：找出掌握度不达标的前置节点
- `estimate_mastery(node_id, mastery_map)`：估算知识点掌握度
- `search_by_keyword(query)`：关键词检索节点

---

### T5：向量检索和知识图谱检索是怎么结合的？

**答**：Retriever 的 `search_all()` 方法做三路检索：

1. **向量库检索**（3 个集合）：
   - `course_docs`：课程文档片段（教材章节）
   - `protocol_specs`：RFC 协议规范片段
   - `misconceptions`：常见误区库

2. **知识图谱检索**：
   - `search_by_keyword(query)` 做关键词匹配
   - 返回前 5 个最相关节点

3. **兜底机制**：
   - 如果三路检索全部返回空，使用 `_FALLBACK_DOCS` 预设数据
   - 确保 Orchestrator 总能拿到上下文

向量检索结果中的 `source` 字段用于可信溯源标注。

---

### T6：为什么不直接用 Neo4j 做知识图谱？

**答**：工程权衡：

1. **部署复杂度**：Neo4j 需要 JVM + 独立服务进程，竞赛环境部署成本高。
2. **数据规模**：20 节点 21 边的规模，用 JSON 文件 + 内存加载完全够用，启动即加载。
3. **查询性能**：拓扑排序和前置依赖查询在内存中 <1ms，无需图数据库索引。
4. **可维护性**：JSON 文件可直接版本控制，团队协作编辑方便。

如果后续扩展到 100+ 节点或多课程图谱，再迁移到 Neo4j 或 TigerGraph。

---

## 三、多智能体协调机制

### T7：Orchestrator 的状态机有几个状态？转换条件是什么？

**答**：三个状态：

```
         新会话
            │
            ▼
     ┌─── idle ───┐
     │             │
  用户提问      5轮学习后
     │             │
     ▼             ▼
  learning ◄─── consolidation
     │             │
     │     Challenger 检验完成
     │             │
     └─────────────┘
          回到 idle
```

- `idle → learning`：用户发送第一条消息
- `learning → consolidation`：学习轮次累计达到 5 轮
- `consolidation → idle`：Challenger 完成概念挑战检验

状态变化通过 SSE `state_change` 事件推送到前端，UI 同步更新。

---

### T8：Agent 之间是怎么传递数据的？有没有用消息队列？

**答**：没有使用消息队列（如 Redis/Celery），采用同步函数调用 + 结构化字典传递：

```python
# Orchestrator 中的调用链
retrieval = retriever.search_all(question, history, session_id)
diagnosis = diagnosis_agent.diagnose(question, answer, retrieval)
profiler.update(session_id, diagnosis, question)
resources = resource_gen.generate_all(diagnosis, profile)
path = path_planner.plan(user_id, profile)
```

原因：
1. **延迟敏感**：SSE 流式推送要求低延迟，消息队列引入额外网络开销。
2. **数据一致性**：同步调用保证数据顺序，无需处理消息乱序问题。
3. **部署简单**：无需额外中间件，SQLite + 内存即可运行。

代价是 Agent 之间有隐式耦合（前一个 Agent 失败会影响后续），但通过异常降级和默认值兜底来缓解。

---

### T9：CognitiveAgentMixin 的作用是什么？

**答**：提供所有 Agent 共享的认知引擎原语：

1. **`make_trace(goal)`**：创建 AgentTrace 对象，记录推理步骤和工具调用。
2. **`reflect(trace, quality_checks)`**：自反思，根据质量检查项计算置信度，决定 accept 还是 revise。
3. **`use_tool(trace, name, fn, *args)`**：包装工具调用，自动记录到 trace。

这使每个 Agent 都有统一的 plan-act-reflect 行为模式，且 trace 可序列化为 JSON 存入 `agent_logs` 表，支持全链路调试。

---

## 四、可信机制与安全性

### T10：范围校验的具体实现是什么？

**答**：`trust_mechanism.py` 实现双层判断：

1. **快速关键词层**（<1ms）：
   ```python
   _OUT_OF_SCOPE_KEYWORDS = ["数学题", "物理公式", "化学方程式", "英语翻译", ...]
   ```
   命中任一关键词直接返回 `{"in_scope": False, "reason": "keyword_match"}`。

2. **LLM 判断层**（~2s）：
   如果关键词层未命中，调用 LLM 判断问题是否属于计算机网络课程范围。返回：
   ```json
   {"in_scope": true/false, "scope_type": "transport|network|application|..."}
   ```

越界时 Orchestrator 返回友好提示："抱歉，我专注于计算机网络协议学习，暂时无法回答其他领域的问题。" 同时通过 SSE `state_change` 事件通知前端显示 ScopeNotice 组件。

---

### T11：来源溯源是怎么实现的？

**答**：Retriever 返回的每条文档都带 `source` 字段：

```python
{"document": "TCP 三次握手是...", "source": "谢希仁《计算机网络》第8版 第5章"}
```

Orchestrator 在流式回复完成后，将检索来源整理为编号列表追加到回复末尾：

```
参考来源：
[1] 谢希仁《计算机网络》第8版 第5章
[2] RFC 9293 - TCP Specification
```

前端 ChatMessage 组件将来源标注渲染为可点击的引用标记。

---

## 五、性能与可靠性

### T12：检索缓存是怎么实现的？缓存策略是什么？

**答**：Retriever 模块级 TTL 缓存：

```python
_CACHE_TTL = 300  # 5 分钟
_cache: dict[str, tuple[float, dict[str, Any]]] = {}

def _get_cached(query: str) -> Optional[dict]:
    entry = _cache.get(query)
    if entry and (time.time() - entry[0]) < _CACHE_TTL:
        return entry[1]
    return None
```

策略：
- **Key**：LLM 扩展后的查询词（不是原始问题）
- **TTL**：5 分钟，超时自动失效
- **容量限制**：超过 200 条时清理过期条目，避免内存泄漏
- **粒度**：缓存整个 `search_all` 结果（含 docs + protocols + misconceptions + graph_nodes）

---

### T13：SSE 连接断线了怎么处理？

**答**：三层保障：

1. **心跳保活**：后端每 15 秒发送 `: ping\n\n` 注释行，保持连接活跃。
2. **前端重连**：EventSource 原生支持自动重连（默认 3 秒），重连时携带 `Last-Event-ID` 请求头。
3. **会话恢复**：后端在 `sessions` 表中维护消息序号，重连后从断点继续推送未完成的事件。

如果 Orchestrator 在断线期间已完成回复，重连后前端通过 REST API `GET /api/chat/{session_id}/messages` 拉取完整消息历史。

---

### T14：数据库写入会不会阻塞 SSE 流式推送？

**答**：不会。数据库写入采用异步策略：

1. **消息持久化**：在 SSE `done` 事件发送后才写入 `messages` 表，不阻塞流式 token 推送。
2. **画像更新**：`profiler.update()` 的 DB 写入在后台执行，Orchestrator 不等待写入完成。
3. **Agent 日志**：`agent_logs` 表的写入在 `agent_end` 事件发送后异步执行，失败时仅记日志不报错。

使用 SQLAlchemy + `aiosqlite` 异步驱动，数据库操作不阻塞事件循环。

---

### T15：系统在什么情况下会完全降级到 Mock？

**答**：三种触发条件：

1. **启动参数**：`--mock-mode` 或 `MOCK_MODE=true` 环境变量，全局使用 MockProvider。
2. **LLM 连续超时**：Orchestrator 内部计数器，连续 3 次 LLM 调用超时后自动切换到 Mock 响应（当前会话内生效）。
3. **前端独立 Mock**：前端 `VITE_USE_MOCK=true` 时，`mockInterceptor.ts` 拦截所有请求，不依赖后端。适用于后端完全不可用时的演示场景。

Mock 响应数据在 `frontend/public/mock/` 目录下，包含完整的对话、诊断、资源、路径、画像、仿真 JSON 文件。

---

## 六、测试与验证

### T16：你们的测试覆盖了哪些场景？

**答**：测试文件在 `tests/` 目录：

| 测试文件 | 覆盖场景 |
|---------|---------|
| `test_diagnosis_agent.py` | 三层诊断输出结构、错误类型分类、JSON 解析容错 |
| `test_diagnosis_layer3.py` | 第三层模式匹配的边界情况 |
| `test_llm_client.py` | LLM 抽象层调用、超时处理、Mock 回退 |
| `test_resource_generator.py` | 5 类资源生成、fallback_content 兜底 |
| `test_resource_generator_all_types.py` | 所有资源类型的完整覆盖 |
| `test_student_profile_schema.py` | 画像 8 维字段验证、增量更新逻辑 |

测试框架：pytest + pytest-asyncio，运行命令 `pytest tests/ -v`。

---

### T17：如何验证诊断结果的准确性？

**答**：三层验证：

1. **单元测试**：用预置的误解数据（`data/raw/misconceptions.json`）作为输入，验证诊断输出是否匹配预期误区模式。
2. **人工标注对照**：选取 20 个典型案例，人工标注正确诊断结果，与系统输出做对比，统计准确率。
3. **演示验证**：`docs/results/diagnosis_accuracy_phase4.md` 记录了 Phase 4 验收时的诊断准确率数据。

当前诊断准确率在典型案例上 >85%，边界情况（如混合型误区）约 70%。

---

### T18：前端构建有没有类型检查？如何保证代码质量？

**答**：TypeScript 严格模式：

1. **tsconfig.json**：`"strict": true`，启用严格类型检查。
2. **类型定义**：`frontend/src/types/` 目录下 8 个类型文件，覆盖 API 响应、组件 Props、Store 状态。
3. **构建验证**：`npm run build` 执行 `vue-tsc` 类型检查 + Vite 构建，类型错误会导致构建失败。
4. **ESLint**：配置了 Vue + TypeScript 规则集，代码风格统一。

前端代码在 Phase 6 中已完成代码清理，移除了所有 `console.log`（替换为 `console.info`），修复了所有类型错误，构建零警告（除 chunk size 提示）。

---

**总结**：以上 18 个技术问题覆盖了算法实现（T1-T3）、数据检索（T4-T6）、架构设计（T7-T9）、安全可信（T10-T11）、性能可靠性（T12-T15）、测试验证（T16-T18）六个维度。重点准备 T1（诊断调用链）、T3（JSON 容错）、T7（状态机）、T8（Agent 数据传递）、T10（范围校验）、T14（DB 异步写入），这些是技术评委最可能深挖的点。
