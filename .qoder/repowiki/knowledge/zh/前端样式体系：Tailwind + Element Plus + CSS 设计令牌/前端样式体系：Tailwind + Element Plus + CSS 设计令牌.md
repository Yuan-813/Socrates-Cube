---
kind: frontend_style
name: 前端样式体系：Tailwind + Element Plus + CSS 设计令牌
category: frontend_style
scope:
    - '**'
source_files:
    - frontend/tailwind.config.js
    - frontend/postcss.config.js
    - frontend/src/assets/styles/main.css
    - frontend/package.json
    - frontend/src/App.vue
---

## 1. 采用的样式系统与方法论
- 原子化 CSS：以 Tailwind CSS 3.4 为核心，通过 postcss.config.js 启用 tailwindcss 与 autoprefixer，在 src/assets/styles/main.css 中注入 @tailwind base/components/utilities。
- UI 组件库：Element Plus 2.13（含 @element-plus/icons-vue）作为表单、按钮、标签、对话框等基础交互组件来源，并在 main.css 中对 .el-button、.el-input__wrapper、.el-tag、.el-dialog 等进行统一圆角、阴影、聚焦态微调，使其与整体视觉一致。
- CSS 自定义属性（Design Tokens）：在 :root 下集中定义颜色、字体、字号、圆角、阴影、间距以及 8 个 Agent 主题色，形成 EduBright 明亮教育科技风的视觉基线，供全局与组件复用。
- 构建工具链：Vite 5 + Vue SFC + TypeScript，样式经 PostCSS → Tailwind → Autoprefixer 流水线处理。

## 2. 关键文件与包
- 配置层
  - frontend/tailwind.config.js：扩展 primary/secondary/slate 及品牌色 ai-blue/ai-teal/ai-purple 完整色板。
  - frontend/postcss.config.js：注册 tailwindcss、autoprefixer 插件。
  - frontend/package.json：声明 vue、pinia、vue-router、axios、echarts、mermaid、three、page-flip、highlight.js、marked、element-plus 等依赖。
- 样式层
  - frontend/src/assets/styles/main.css：全局 Design Tokens、滚动条、通用卡片/标题类、Element Plus 覆盖、Agent 标签色、渐变工具类、移动端适配。
- 使用层（示例）
  - frontend/src/App.vue：大量使用 <el-icon>、<el-tag> 等 Element Plus 组件。
  - frontend/src/views/ExamView.vue、ResourcesView.vue、ScenarioView.vue 等视图广泛采用 Tailwind 原子类组合布局与配色。

## 3. 架构与约定
- Token 分层：main.css 中的 CSS 变量是单一事实源；Tailwind 扩展色板与其一一对应（如 --color-primary 对应 primary.*），新增主题时两端同步维护。
- 组件风格策略：业务 UI 优先用 Tailwind 原子类拼装，复杂交互控件走 Element Plus，并通过 main.css 中的覆盖规则统一圆角、阴影、焦点环，避免各组件风格割裂。
- Agent 主题映射：为 orchestrator/retriever/diagnosis/profiler/resource/path-planner/simulator/challenger 分别定义 --agent-* 变量，并配套 .agent-tag-* 类，使日志面板、状态栏等能按 Agent 类型着色。
- 响应式策略：基于 Tailwind 断点 + main.css 中 @media (max-width: 640px) 的兜底调整，兼顾桌面端与平板/手机阅读体验。

## 4. 开发者应遵循的规则
- 优先使用 Token：颜色、圆角、阴影、间距一律引用 var(--color-*) / var(--radius-*) / var(--shadow-*) / var(--spacing-*)，禁止在组件内硬编码十六进制值。
- Tailwind 原子类为主：布局、间距、背景、文字大小等尽量用 Tailwind 类名组合；仅在需要跨页面复用的块级样式时才新建 CSS 类。
- Element Plus 覆盖要收敛：对 .el-* 的覆盖集中在 main.css，不要在各组件内写局部 style 覆盖，保持覆盖可审计。
- 新增主题色需双端更新：若引入新语义色，需在 tailwind.config.js 的 theme.extend.colors 与 :root 的 CSS 变量两处同时添加，保证一致性。
- Agent 色规范：新增 Agent 时，先在 :root 增加 --agent-xxx 变量，再补充 .agent-tag-xxx 类，并在日志/状态相关组件中按此命名消费。
- 移动端适配：优先使用 Tailwind 响应式前缀（sm/md/lg/xl），必要时在 main.css 中补充最小化媒体查询，避免在组件内写死固定尺寸。