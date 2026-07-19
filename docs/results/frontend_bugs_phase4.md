# Phase 4 前端走查 Bug 清单

> 日期：2026-06-07 | 走查人：C

## 走查范围

| 页面 | 走查项 | 状态 |
|------|--------|:----:|
| 首页 (HomeView) | 系统介绍、入口按钮 | ✅ 正常 |
| 对话页 (ChatView) | SSE 流式输出、Agent 状态栏、消息渲染 | ✅ 正常 |
| 画像页 (ProfileView) | 雷达图渲染、八维数据展示 | ✅ 正常 |
| 路径页 (PathView) | 时间线展示、节点详情弹窗 | ✅ 正常 |
| 资源页 (ResourcesView) | 5 Tab 切换、资源卡片渲染 | ✅ 正常 |
| 仿真页 (SimulatorView) | 7 场景选择、动画播放 | ✅ 正常 |
| 诊断页 (DiagnosisView) | 三层诊断结果展示 | ✅ 正常 |
| 日志页 (LogsView) | Agent 日志面板、筛选、展开 | ✅ 正常 |

## 已修复 Bug

| Bug ID | 严重级 | 描述 | 修复方式 |
|--------|:------:|------|----------|
| FB-01 | P0 | resourceStore.ts 文件重复导致 TypeScript 编译失败 | 删除旧版重复内容 |
| FB-02 | P0 | resource.ts ResourceType 重复声明 | 删除旧版 3 类声明 |
| FB-03 | P0 | AgentLogPanel.vue 双 script 块导致编译错误 | 删除旧版重复 script+template |
| FB-04 | P0 | ResourceTabBar.vue 双 template 导致编译错误 | 删除旧版 3-tab 重复内容 |
| FB-05 | P1 | MindmapCard.vue mermaid 模块类型缺失 | 安装 mermaid + 添加 env.d.ts 类型声明 |

## 已知限制

| 编号 | 描述 | 影响 | 处理计划 |
|------|------|------|----------|
| L-01 | mermaid 库体积较大（~628KB gzip ~149KB） | 首屏加载变慢 | Phase 5 做按需加载优化 |
| L-02 | MindmapCard 在 mermaid 不可用时降级为 pre 标签 | 视觉效果下降 | Phase 5 增加 SVG fallback |

## 构建验证

```
vue-tsc: 0 errors
vite build: ✓ 3781 modules transformed, built in 23.02s
```
