# Phase 3 遗留问题记录

| 问题ID | 问题描述 | 严重度 | 处理状态 |
| --- | --- | --- | --- |
| P3-001 | `data/knowledge_graph.json` 未确认可用 | Critical | 当前图谱为 20 节点、21 边，满足 Phase 4 最小验收 |
| P3-002 | `/health` 路由需要确认 | Critical | 当前 `src/loopse/main.py` 提供 `/health` |
| P3-003 | `PathTimeline` 与 `PathReasonModal` 缺少联动 | High | 已在时间线中接入弹窗 |
| P3-004 | `AgentStatusBar` 状态读取错误 | High | 已改为读取 `activeAgents` 数组 |
| P3-005 | `chat_mock.json` 缺失完整 SSE 事件流 | Medium | 已新增 `frontend/public/mock/chat_mock.json` |
| P3-006 | 知识库资料不足，ChromaDB 入库未验证 | High | 已下载 RFC/IANA 资料，本地索引入库 366 条以上 |
| P3-007 | 路径规划推荐理由不够可解释 | High | 已重写 PathPlanner，输出推理轨迹、质量分和推荐理由 |
