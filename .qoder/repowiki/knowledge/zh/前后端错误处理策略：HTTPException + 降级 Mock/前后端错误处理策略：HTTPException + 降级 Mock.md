---
kind: error_handling
name: 前后端错误处理策略：HTTPException + 降级 Mock
category: error_handling
scope:
    - '**'
source_files:
    - src/loopse/main.py
    - src/loopse/api/auth.py
    - src/loopse/api/books.py
    - src/loopse/core/llm_client.py
    - frontend/src/api/client.ts
    - frontend/src/composables/useApi.ts
    - frontend/src/composables/useSSE.ts
    - frontend/src/api/mockInterceptor.ts
    - frontend/src/components/AppError.vue
---

## 1. 系统/方法概述

本仓库采用“后端显式抛出 HTTP 异常 + 前端统一拦截 + 流式 SSE 自动降级”的三层错误处理体系，没有统一的自定义异常类或全局异常处理器。

- **后端（FastAPI）**：各 API 路由直接 `raise HTTPException(status_code, detail)`；LLM 客户端层将网络/超时异常捕获并返回友好提示字符串，避免上层崩溃。
- **前端（Vue3 + Axios）**：全局响应拦截器打印错误日志，业务侧通过 `useApi` composable 暴露 loading/error 状态；SSE 连接失败时自动回退到本地 Mock 数据。
- **无全局异常中间件**：未在 `main.py` 中注册 `@app.exception_handler`，所有错误均由各路由自行 raise。

## 2. 关键文件与位置

| 层次 | 文件 | 作用 |
|------|------|------|
| 应用入口 | `src/loopse/main.py` | 注册 CORS、启动时 init_db（异常仅记录不中断） |
| 认证 API | `src/loopse/api/auth.py` | 大量 `HTTPException(401/409/400/404/500)` 示例 |
| 书籍 API | `src/loopse/api/books.py` | 文件上传校验、400/413/404 错误 |
| LLM 客户端 | `src/loopse/core/llm_client.py` | 同步/异步调用均 try-except，返回降级文本 |
| 前端 Axios 实例 | `frontend/src/api/client.ts` | 全局 response 拦截器打印 `[API Error]` |
| 通用请求封装 | `frontend/src/composables/useApi.ts` | 暴露 data/loading/error，供组件消费 |
| SSE 会话 | `frontend/src/composables/useSSE.ts` | 断线重试 + 超时降级 Mock |
| 离线 Mock 拦截 | `frontend/src/api/mockInterceptor.ts` | 环境变量驱动的全局 Mock 响应 |
| 错误 UI 组件 | `frontend/src/components/AppError.vue` | 通用“出错了 + 重新加载”占位 |

## 3. 架构与约定

### 3.1 后端异常模式

- **业务异常**：在路由函数内直接 `raise HTTPException(status_code=..., detail="...")`，detail 使用中文用户可读文案。
- **外部依赖异常**：`core/llm_client.py` 对 Spark/OpenAI 调用做 try-except，捕获后记录日志并返回“抱歉，AI 服务暂时不可用…”等降级字符串，保证上层稳定。
- **启动期异常**：`main.py` 的 `_on_startup` 中 `init_db()` 被 try-except 包裹，失败仅记录 error 日志，不阻断进程。
- **未覆盖场景**：未发现全局 `@app.exception_handler(Exception)`，因此未被显式捕获的异常会走 FastAPI 默认 JSON 错误响应。

### 3.2 前端错误处理模式

- **Axios 全局拦截**：`client.ts` 的 response interceptor 对所有非 `/health` 请求打印 `[API Error]`，并将错误 Promise.reject 给调用方。
- **Composable 封装**：`useApi.ts` 提供 `{data, loading, error, execute}`，内部 try-catch 后将错误写入 `error.value` 并触发 `onError` 回调。
- **SSE 容错**：`useSSE.ts` 实现指数退避重试（最多 3 次），8s 超时后主动 abort 并降级为本地 Mock 回复，确保演示可用。
- **Mock 开关**：`mockInterceptor.ts` 在 `VITE_MOCK_MODE=true` 时拦截所有已知接口返回静态数据，配合 `AppError.vue` 展示错误态。

### 3.3 设计决策

- **以用户体验为中心**：LLM 调用失败不抛异常，而是返回可理解的降级文案；SSE 断线自动回退 Mock，保证离线演示流畅。
- **简单直接**：未引入统一异常基类或全局中间件，降低学习成本，适合教学演示项目规模。
- **前后端解耦**：后端只负责返回 HTTP 语义正确的状态码和 detail，前端自行决定如何呈现。

## 4. 开发者应遵循的规则

1. **新增 API 的错误路径**：在路由函数内直接 `raise HTTPException(status_code, detail="中文说明")`，保持 detail 对用户友好。
2. **外部调用必须兜底**：任何第三方 API（LLM、OAuth、短信等）调用需 try-except，记录日志并返回降级结果，禁止让异常冒泡到 FastAPI 默认处理器。
3. **前端统一消费**：优先使用 `useApi` composable 获取 loading/error 状态；需要流式交互时使用 `useChatSSE`，不要自行裸写 fetch。
4. **Mock 模式兼容**：开发时可通过 `VITE_MOCK_MODE=true` 启用前端 Mock，确保在无后端环境下仍可演示完整流程。
5. **避免裸 `raise Exception`**：如需自定义领域异常，应在对应模块定义具体类型并在路由层转换为 `HTTPException`，不建议在业务逻辑中直接 raise 裸异常。
