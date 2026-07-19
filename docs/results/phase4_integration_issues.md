# Phase 4 联调问题记录

> 日期：2026-06-07 | 主持人：A

## 联调链路验证

| 链路 | 验证内容 | 状态 | 备注 |
|------|----------|:----:|------|
| 画像构建 | 3-5 轮对话 → 8 维画像更新 → 雷达图同步 | ✅ | Profiler SSE 后台更新 |
| 知识问答 | "TCP 三次握手" → SSE 流式 → 引用来源 | ✅ | TrustMechanism 自动附加引用 |
| 诊断链路 | "HTTP直接基于IP" → 三层诊断返回 → DiagnosisPanel | ✅ | 关键词兜底 + MockLLM |
| 仿真链路 | "滑动窗口" → 自动触发仿真 → SimulatorPlayer | ✅ | 7 场景全部可播放 |
| 资源生成 | 5 类资源全部生成 → ResourceTabBar 5 Tab 切换 | ✅ | doc/exercise/code/mindmap/script |
| 路径规划 | "我接下来该学什么" → 路径节点 + 推荐理由 | ✅ | PathTimeline 展示 |
| 可信机制 | "怎么写 Python 爬虫" → 系统拒答 | ✅ | scope_check 越界拦截 |
| Agent 日志 | 全程 AgentLogPanel 实时更新 | ✅ | 8 Agent 颜色区分 + 筛选 |

## 已修复问题

| 问题 ID | 严重级 | 描述 | 分配 | 状态 |
|---------|:------:|------|:----:|:----:|
| INT-01 | P0 | resource_generator.py 文件被追加旧版内容导致 SyntaxError | B | ✅ 已修复 |
| INT-02 | P0 | 多个前端文件（store/type/component）被追加旧版重复代码 | C | ✅ 已修复 |
| INT-03 | P1 | exercise/code Prompt 的 JSON 花括号与 Python .format() 冲突 | B | ✅ 改用 .replace() |
| INT-04 | P1 | 诊断 Agent MockLLM 模式无法识别错误回答 | B | ✅ 增加关键词兜底 |
| INT-05 | P1 | mermaid 未安装导致前端构建失败 | C | ✅ npm install mermaid |
| INT-06 | P2 | 旧测试断言 3 类资源，新版已扩展到 5 类 | B | ✅ 更新测试断言 |

## 待跟进

| 编号 | 描述 | 优先级 | 计划 |
|------|------|:------:|------|
| — | 无 P0/P1 遗留问题 | — | — |

## pytest 验证

```
59 passed, 0 failed, 2 warnings
```

## npm build 验证

```
vue-tsc: 0 errors
vite build: ✓ 3781 modules, built in 23.02s
```
