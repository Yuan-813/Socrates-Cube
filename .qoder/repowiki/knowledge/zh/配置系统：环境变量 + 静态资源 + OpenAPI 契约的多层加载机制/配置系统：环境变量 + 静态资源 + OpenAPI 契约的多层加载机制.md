---
kind: configuration_system
name: 配置系统：环境变量 + 静态资源 + OpenAPI 契约的多层加载机制
category: configuration_system
scope:
    - '**'
source_files:
    - src/loopse/main.py
    - src/loopse/core/llm_client.py
    - src/loopse/db/connection.py
    - scripts/verify_env.py
    - config/agent_personas.json
    - config/api_schema.yaml
    - frontend/.env.example
    - pyproject.toml
---

## 1. 采用的系统与工具

- **环境变量管理**：`python-dotenv`（`load_dotenv()`）在模块导入时自动加载根目录 `.env`，配合 `os.getenv` 读取运行时参数。
- **启动期配置**：`src/loopse/main.py` 通过 `argparse` 解析 `--mock-mode` 并读 `MOCK_MODE`、`LOG_LEVEL` 等环境变量，控制 FastAPI 应用行为。
- **静态资源配置**：`config/agent_personas.json` 与 `config/prompts/<agent>/<prompt>.txt` 作为可热插拔的提示词与人设文件；`config/api_schema.yaml` 作为前后端共享的 OpenAPI 3.1 接口契约。
- **前端配置**：`frontend/.env.example` 提供 Vite 构建期变量模板（`VITE_API_BASE_URL`、`VITE_SSE_ENDPOINT`、`VITE_MOCK_MODE`）。

## 2. 关键文件与包

- 后端入口与运行模式：`src/loopse/main.py`
- LLM 客户端与多模型路由：`src/loopse/core/llm_client.py`
- 数据库连接与多后端切换：`src/loopse/db/connection.py`
- 环境自检脚本：`scripts/verify_env.py`
- Agent 人设与 Prompt 模板：`config/agent_personas.json`、`config/prompts/**/*.txt`
- API 契约：`config/api_schema.yaml`
- 前端环境变量模板：`frontend/.env.example`
- 项目元数据与 pytest 配置：`pyproject.toml`

## 3. 架构与设计约定

### 3.1 环境变量分层与默认值
- 所有运行时参数统一通过 `os.getenv(key, default)` 获取，并在代码中给出合理默认值（如 `LLM_TIMEOUT=30`、`LLM_STREAM_TIMEOUT=60`、`DB_PATH=edu_agent.db`、`SQL_ECHO=0`）。
- 敏感凭据（讯飞星火、OpenAI 兼容接口）支持多变量名回退：`XUNFEI_*` → `SPARK_*` → `SPARKAI_*`，由 `_first_env` 函数按优先级取第一个非空且不以 `_here` 结尾的值，便于本地占位与 CI 注入。
- 当凭据缺失或依赖包未安装时，`llm_client.py` 自动降级到 Mock 模式，保证离线演示可用。

### 3.2 启动期配置与中间件
- `main.py` 在进程启动阶段解析 `--mock-mode` / `MOCK_MODE`、设置日志级别，随后注册 CORS 中间件并一次性 include 所有业务路由。
- 数据库初始化放在 `@app.on_event("startup")` 钩子中，确保首次请求前完成表结构创建。

### 3.3 静态资源驱动的配置
- **Agent 人设**：`config/agent_personas.json` 以 JSON 描述每个角色的 id/name/style/avatar/description/prompt_prefix，供 Persona 路由动态返回。
- **Prompt 模板**：`config/prompts/<agent>/<name>.txt` 按 Agent 域拆分，便于非开发者编辑提示词而不改动代码。
- **API 契约**：`config/api_schema.yaml` 定义 `StudentProfile`、`SSEPayload`、`AgentLog` 三大公共 Schema 及 `/health`、`/api/v1/chat`、`/api/v1/profile/{user_id}` 路径，作为前后端联调的单一事实来源。

### 3.4 数据库后端选择策略
- `connection.py` 优先读取 `DATABASE_URL`；若为空或以 `sqlite` 开头则使用本地 SQLite（`DB_PATH` 可配），否则走 MySQL/PostgreSQL 云端连接，并通过 `pool_pre_ping`、`pool_recycle` 增强健壮性。

### 3.5 前端构建期配置
- 通过 Vite 的 `import.meta.env.VITE_*` 注入 `VITE_API_BASE_URL`、`VITE_SSE_ENDPOINT`、`VITE_MOCK_MODE`，开发时可留空走 Vite 代理，生产替换为真实地址。

## 4. 开发者应遵循的规则

1. **新增运行时参数**一律通过 `os.getenv(key, default)` 暴露，并在 `.env.example` 和 `scripts/verify_env.py` 中同步声明。
2. **敏感凭据**采用多变量名回退策略，避免硬编码服务厂商前缀；新接入第三方 API 时沿用 `_first_env` 模式。
3. **提示词与人设**修改只动 `config/prompts/*` 与 `config/agent_personas.json`，不直接改 Python 字符串常量。
4. **接口变更**先更新 `config/api_schema.yaml`，再同步实现后端 Pydantic 模型与前端类型，保持契约先行。
5. **数据库后端切换**仅改 `.env` 中的 `DATABASE_URL`，不要修改 `connection.py` 逻辑。
6. **前端环境变量**新增 `VITE_*` 变量后，记得更新 `frontend/.env.example` 并告知团队。
7. **Mock 模式**通过 `--mock-mode` 或 `MOCK_MODE=true` 全局开启，无需单独维护两套代码分支。
