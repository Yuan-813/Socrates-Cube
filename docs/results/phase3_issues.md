# Phase 3 遗留问题记录

## Phase 3 遗留问题记录

| 问题ID | 问题描述 | 严重度 | 处理状态 |
|--------|---------|--------|---------|
| P3-001 | `data/knowledge_graph.json` 未确认可用 | Critical | ✅ Phase 4 已生成并提交 20 节点 21 边 |
| P3-002 | `/health` 路由需要确认 | Critical | ✅ 当前 `src/loopse/main.py` 通过 `api/health.py` 提供 `/health` |
| P3-003 | `SRS_v1.md` 被 C 分支删除 | Critical | ✅ Phase 4 已恢复并补充第 5 章 |
| P3-004 | `PathTimeline` 与 `PathReasonModal` 缺少联动 | High | ✅ 已在时间线中接入弹窗 |
| P3-005 | `AgentStatusBar` 所有分支均缺失 | High | ✅ Phase 4 已实现并接入 ChatView |
| P3-006 | `feature/C-role` 的 pycache 污染 | Medium | ✅ Phase 4 已清理并统一目录为 `src/loopse/agent/` |
| P3-007 | `knowledge_graph.py` 两套实现冲突 | High | ✅ Phase 4 保留 `_estimate_mastery` 兼容能力 |

## 清账总结

- **遗留问题总数**：7 个
- **Critical 级别**：3 个（P3-001、P3-002、P3-003）
- **High 级别**：3 个（P3-004、P3-005、P3-007）
- **Medium 级别**：1 个（P3-006）
- **已完成数量**：7 个
- **清账完成率**：100%
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
