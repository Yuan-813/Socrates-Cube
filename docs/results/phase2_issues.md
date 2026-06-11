# Phase 2 遗留问题记录

| 问题ID | 问题描述 | 严重度 | 处理状态 |
| --- | --- | --- | --- |
| P2-001 | Agent 通信 State 设计缺失，导致各 Agent 输入输出边界不清 | Critical | 已新增 `docs/architecture/Agent通信State设计.md` |
| P2-002 | Orchestrator 早期只是串行调用，缺少推理轨迹和自反检查 | High | 已引入 `cognitive_engine.py` 并写入 agent_trace |
| P2-003 | Prompt 模板变量与代码字段不一致，容易运行时报错 | High | Diagnosis 与 Profiler 已做兼容 fallback |
| P2-004 | 向量库缺包时全链路检索为空 | High | 已实现本地 JSON 索引兜底 |
| P2-005 | 单元测试与新实现接口存在同步/异步不一致 | Medium | 已通过 AwaitableDict 兼容旧测试 |
