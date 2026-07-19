---
kind: build_system
name: 构建与部署编排（Python + Vue3 全栈）
category: build_system
scope:
    - '**'
source_files:
    - pyproject.toml
    - requirements.txt
    - start.sh
    - start.bat
    - frontend/package.json
    - frontend/vite.config.ts
    - frontend/nginx.conf
    - frontend/vercel.json
    - tests/conftest.py
---

## 1. 构建系统概览
本项目采用「后端 Python (FastAPI) + 前端 Vue3 (Vite)」的全仓单仓模式，通过顶层启动脚本统一编排前后端开发/演示环境。未引入 Docker、Makefile、CI/CD 流水线或容器化配置，本地一键启动是主要交付入口。

## 2. 关键文件与职责
- `pyproject.toml`：声明包名 `socrates-cube`、版本 `0.1.0`、Python 锁定 `==3.10.*`、setuptools 构建后端；pytest 测试路径与异步模式。
- `requirements.txt`：后端运行时依赖清单（FastAPI/Uvicorn/SSE/Pydantic/SQLAlchemy/JWT 等），向量库为可选依赖（见 `requirements-vector.txt`）。
- `start.sh` / `start.bat`：跨平台一键启动器，负责创建 `.venv`、安装依赖、复制 `.env.example`、以 `--reload` 启动 Uvicorn 并拉起 Vite dev server，支持 `--mock-mode` 离线演示。
- `frontend/package.json`：定义 `dev`/`dev:mock`/`build`/`preview` 四个脚本，区分 mock 与真实 API 模式。
- `frontend/vite.config.ts`：配置 `/api` 代理到 `localhost:8000`、手动分包（vendor/element-plus/echarts）、sourcemap 输出。
- `frontend/nginx.conf`：生产反向代理模板，将 `/api` 转发至 `backend:8000`，并对 SSE 流式端点关闭缓冲与延长超时。
- `frontend/vercel.json`：Vercel 静态站点部署配置，重写路由至 `index.html`，对 `/api/*` 放行 CORS。
- `tests/conftest.py` + `tests/unit/*`：基于 pytest 的单元/集成测试套件，配合 `pyproject.toml` 中的 `[tool.pytest.ini_options]` 自动发现。

## 3. 架构与约定
- **后端**：`src.loopse.main:app` 作为 Uvicorn ASGI 入口，按功能域拆分为 `agent/`、`api/`、`db/`、`kb/`、`rl/`、`schema/` 子包；`config/prompts` 下各 Agent 提示词以文本文件形式热插拔。
- **前端**：Vue3 + TypeScript + Vite，Pinia 状态管理，Axios 请求封装，SSE 通过 `composables/useSSE.ts` 消费后端流式接口。
- **Mock 模式**：通过环境变量 `MOCK_MODE=1` 切换后端 Mock Provider 与前端 `dev:mock` 脚本，实现无 LLM 依赖的离线演示。
- **数据层**：默认使用 SQLite (`data/socrates_cube.db`)，MySQL 通过 `scripts/init_mysql.py` 初始化；向量索引落盘于 `data/vector_db/local_index.json`。
- **构建产物**：前端 `npm run build` 输出至 `frontend/dist`，由 nginx 或 Vercel 托管；后端不打包，直接以源码运行。

## 4. 开发者应遵循的规则
- **Python 版本**：必须使用 `3.10.x`（`requires-python = "==3.10.*"`），否则 `uvicorn`/`aiosqlite` 等依赖可能不兼容。
- **依赖管理**：新增后端依赖请同步更新 `requirements.txt`；可选依赖（如 MinerU、ChromaDB）在注释中说明，避免强制安装。
- **启动方式**：优先使用 `./start.sh --mock-mode` 或 `start.bat --mock-mode` 进行本地联调；生产部署需自行准备 `.env` 并替换 `nginx.conf` 中的 `backend` 主机名。
- **前端模式**：开发时通过 `npm run dev`（真实后端）或 `npm run dev:mock`（离线）切换；构建产物仅用于静态托管，不包含后端代码。
- **测试执行**：在项目根目录运行 `pytest`（或 `python -m pytest`），异步测试由 `pytest-asyncio` 自动处理，无需额外标记。
- **配置扩展**：新 Agent 的提示词放入 `config/prompts/<agent>/` 对应 txt 文件，并在 `agent_personas.json` 中注册人设；API 契约维护在 `config/api_schema.yaml`。
- **无容器化约束**：当前仓库不含 Dockerfile/docker-compose，如需容器化部署，可参考 `frontend/nginx.conf` 的反向代理规则自行编写镜像。