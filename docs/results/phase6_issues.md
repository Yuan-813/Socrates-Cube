# Phase 6 体验打磨问题记录

> 日期：2026-07-13 | 阶段：Code Freeze 后体验打磨

## 后端修复

| 问题 ID | 严重级 | 描述 | 修复方式 | 状态 |
|---------|:------:|------|----------|:----:|
| P6-B01 | P0 | diagnosis.py 中 `pattern` 字段可能返回 str 而非 dict，导致下游消费者崩溃 | 增加类型检查：`isinstance(pattern, str)` 时包装为 dict | ✅ |
| P6-B02 | P0 | diagnosis.py 中 `root_causes` 可能不是 list，导致 for 循环报错 | 增加类型兜底：`not isinstance(root_causes, list)` 时转换为 list | ✅ |
| P6-B03 | P1 | resource_generator.py 生成失败时无兜底，返回空数据导致前端空白 | 新增 `_fallback_content()` 静态方法，为 5 种资源类型提供结构化备选 | ✅ |
| P6-B04 | P1 | profiler.py 中 `cognitive_style` 在 `_DEFAULT_PROFILE` 中缺失，导致下游 KeyError | 在 `_DEFAULT_PROFILE` 和 `_load_profile()` 中统一设置默认值 `"textual"` | ✅ |
| P6-B05 | P2 | orchestrator.py 缺少完成耗时日志，无法分析性能瓶颈 | 在 `stream_chat()` 末尾增加 `total_time_ms` 日志 | ✅ |
| P6-B06 | P2 | diagnosis.py、resource_generator.py 缺少计时日志 | 在 `diagnose()` 和 `generate()` 方法中增加入参/耗时/结果日志 | ✅ |
| P6-B07 | P2 | main.py 缺少 LOG_LEVEL 环境变量支持 | 增加 `LOG_LEVEL` 环境变量配置，默认 INFO | ✅ |
| P6-B08 | P2 | 5 个 Agent 文件缺少模块级 docstring | 为 diagnosis/orchestrator/profiler/path_planner/main 补充中文 docstring | ✅ |

## 前端修复

| 问题 ID | 严重级 | 描述 | 修复方式 | 状态 |
|---------|:------:|------|----------|:----:|
| P6-F01 | P0 | DiagnosisPanel.vue 末尾存在重复的 `<script setup>` 块，导致 vite build 失败 | 删除重复的 script+template 块 | ✅ |
| P6-F02 | P1 | HomeView.vue 被追加旧内容（768行），包含未使用的 `backendVersion`/`stats`/`quickActions` 变量导致 TS 报错 | 完整重写文件覆盖 | ✅ |
| P6-F03 | P1 | LearningPathNode 类型定义缺少 `reason_sources` 字段和 `pending`/`in_progress` 状态 | 更新 `frontend/src/types/path.ts` 接口定义 | ✅ |
| P6-F04 | P1 | App.vue 引用 `userStore.demoMode` 但 store 中未定义 | 在 `userStore.ts` 中增加 `demoMode` ref | ✅ |
| P6-F05 | P2 | mockInterceptor.ts 中 `console.log` 残留 | 替换为 `console.info` | ✅ |
| P6-F06 | P2 | mockStreamChat 类型从 `any` 改为 `Record<string, unknown>` 导致 chat.ts 类型不兼容 | 回退为 `any` 类型 | ✅ |
| P6-F07 | P2 | HomeView.vue 重写后保留了未使用的 `goTo` 函数 | 删除 `goTo` 函数 | ✅ |

## 前端增强

| 增强项 | 说明 | 状态 |
|--------|------|:----:|
| AppLoading 三变体 | 新增 `spinner`/`dots`/`progress` 三种加载样式 | ✅ |
| AppEmpty 操作引导 | 新增 `actionText` prop 和 `@action` 事件 | ✅ |
| ScopeNotice 组件 | 新增超出服务范围提示卡片 | ✅ |
| ChatMessage 滑入动画 | 消息出现时 `msg-slide-in` 动画 | ✅ |
| App 过渡动效 | 页面切换从 `fade` 改为 `fade-slide`（translateY） | ✅ |
| 演示模式快捷键 | Ctrl+Shift+D 切换 + Ctrl+Shift+C 清空 | ✅ |
| 首页改版 | Hero 区域 + 三大能力卡片 + 快速开始 + Footer | ✅ |
| 响应式适配 | 1280px 断点媒体查询 | ✅ |
| 视觉微调 | 阴影优化、card-hover 类、CSS 变量统一 | ✅ |
| Mock SSE 增强 | mockStreamChat 覆盖全部 10 种 SSE 事件类型 | ✅ |

## 后端增强

| 增强项 | 说明 | 状态 |
|--------|------|:----:|
| 检索 TTL 缓存 | 5 分钟缓存 + 容量限制 200 条 + 自动清理过期 | ✅ |
| 画像去抖 | 10 秒去抖窗口 + 每 5 轮 LLM 校准 | ✅ |
| 演示账号预置 | 3 个不同认知风格学生 + --demo-only 参数 | ✅ |
| 资源生成兜底 | _fallback_content() 为 5 种资源类型提供结构化备选 | ✅ |

## 构建验证

```
# 后端测试
pytest tests/ -v
59 passed, 0 failed, 2 warnings

# 前端构建
cd frontend && npm run build
vue-tsc: 0 errors
vite build: ✓ built successfully (仅 chunk size 警告)
```

## 待跟进

| 编号 | 描述 | 优先级 | 计划 |
|------|------|:------:|------|
| — | 无 P0/P1 遗留问题 | — | — |
