# Phase 3 验收用例清单

## AC-01 多 Agent 协作对话

**前置条件：** 后端服务运行，LLM mock 模式开启  
**输入：** 用户发送"TCP 握手只需要两次就够了吧？"  
**预期：**
1. SSE 流中出现 `agent_start` 事件，agentName 包含 Orchestrator
2. 出现 `diagnosis` 事件，`is_correct = false`，`error_type` 非空
3. 出现 `agent_start` 事件，agentName 包含 ResourceGenerator
4. 出现 `resource` 事件，resource_type 为 "doc" 或 "exercise"
5. 最终出现 `done` 事件

---

## AC-02 学习路径生成

**前置条件：** 用户已有对话记录（或 ProfileStore 有数据）  
**操作：** 点击 PathView 页面，调用 POST /api/v1/path/plan  
**预期：**
1. 返回 LearningPath，nodes 数组 ≥ 2
2. 每个 node 包含 recommendation_reason 和 prerequisites
3. PathTimeline 组件正确渲染各节点状态颜色

---

## AC-03 学习画像实时更新

**前置条件：** 初始画像全为 0  
**操作：** 完成 3 轮对话后查看 ProfileRadar  
**预期：**
1. 至少一个维度数值 > 0
2. ECharts 雷达图数据点随 radarScores 更新

---

## AC-04 资源标签页切换

**操作：** 在 ChatView 右侧面板切换"知识文档 / 练习题 / 代码示例"  
**预期：**
1. 各 Tab 正确显示对应类型资源卡片
2. 无数据时显示空状态提示

---

## AC-05 Agent 状态栏动效

**前置条件：** 正在处理 SSE 流  
**预期：** AgentStatusBar 出现并显示运行中 Agent 名称；流结束后自动隐藏

---

## AC-06 路径节点详情弹窗

**操作：** 点击 PathTimeline 中任意节点  
**预期：** PathReasonModal 弹出，显示 recommendation_reason、reason_sources 和前置知识链

---

## AC-07 后端健康检查

**请求：** GET /health  
**预期：** status 200，body `{ "status": "ok" }`

---

## AC-08 知识检索三库联合

**请求：** POST /api/v1/chat/stream（包含知识点相关提问）  
**预期：** 日志中出现 Retriever agent_start/end 事件，tool_call 包含 search_all 调用
