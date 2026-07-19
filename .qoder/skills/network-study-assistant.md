# 计算机网络学习助手技能

帮助学生通过 Socrates-Cube 系统深入学习计算机网络协议，触发苏格拉底式追问和三层认知诊断。

## 触发条件

当用户提出以下类型问题时使用本技能：
- 询问网络协议工作原理（TCP/UDP/HTTP/DNS/TLS/QUIC等）
- 对某个概念理解不清或有误解
- 需要学习路径规划
- 想要练习题或代码示例

## 执行步骤

1. **分析用户问题**
   - 识别涉及的协议层次（OSI L1-L7）
   - 判断是概念理解、协议分析还是计算/设计题

2. **触发 AI 对话**
   - 通过 `/api/v1/chat/stream` 发起 SSE 流式对话
   - 使用 `agent_persona=professor` 获得苏格拉底式教学风格

3. **关注诊断结果**
   - 等待 `diagnosis` SSE 事件，分析三层认知诊断
   - 若 `is_correct=false`，关注 `error_type` 和 `intervention_suggestion`

4. **获取学习资源**
   - 等待 `resource` SSE 事件，获取生成的文档/练习/代码/思维导图
   - 可通过 `/api/v1/resources/generate` 单独生成特定类型资源

5. **查看知识图谱**
   - 等待 `kg_nodes` SSE 事件，获取相关知识图谱节点 ID
   - 通过 KGPanel 可视化当前知识点在 OSI 体系中的位置

## 关键 API

| 功能 | 端点 |
|------|------|
| AI 对话（流式） | `POST /api/v1/chat/stream` |
| 生成学习资源 | `POST /api/v1/resources/generate` |
| 生成测验题 | `POST /api/v1/question/batch` |
| 知识路径规划 | `POST /api/v1/path/recommend` |
| 获取学习画像 | `GET /api/v1/profile/{user_id}` |

## 示例用法

```
用户：TCP 三次握手为什么需要第三次 ACK？
→ 触发对话 → 诊断是否理解 ISN 同步目的 → 生成时序图和练习题
```

## 注意事项

- 所有协议讨论应引用具体 RFC 标准（TCP→RFC 9293，HTTP→RFC 9110，DNS→RFC 1034）
- 苏格拉底式教学：不直接给答案，先通过追问引导学生思考
- 诊断错误类型参考：`layer_misplacement`/`flow_omission`/`concept_confusion`/`term_confusion`
