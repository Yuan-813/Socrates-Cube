---
kind: dependency_management
name: Python/Node 双栈依赖管理策略
category: dependency_management
scope:
    - '**'
source_files:
    - pyproject.toml
    - requirements.txt
    - requirements-vector.txt
    - frontend/package.json
    - frontend/package-lock.json
    - start.sh
---

本项目为 Python + Vue3 全栈仓库，采用后端 requirements.txt + 前端 package.json + 虚拟环境的双栈依赖管理模式，并通过顶层启动脚本统一编排安装与运行。

## 1. 使用的系统与工具
- Python 侧：pip + requirements.txt 声明运行时依赖；使用 venv 创建本地虚拟环境 .venv；通过 pyproject.toml 声明构建系统（setuptools）与项目元信息（name、version、requires-python）。
- 可选向量库依赖：单独维护 requirements-vector.txt，包含 ChromaDB、LangChain、MinerU 等可选组件，默认不随核心包安装，需显式 pip install -r requirements-vector.txt。
- 前端侧：npm + package.json 声明依赖，配合 frontend/package-lock.json 锁定精确版本；提供 dev / dev:mock / build / preview 脚本。
- 一键启动：start.sh 自动检测并创建 .venv、激活虚拟环境、安装 Python 依赖、复制 .env.example -> .env、并行启动 Uvicorn 后端与 Vite 前端。

## 2. 关键文件与位置
- pyproject.toml：项目元数据、构建后端、pytest 配置、包发现规则（include = ["src*"]）。
- requirements.txt：核心 Python 依赖清单（FastAPI、Pydantic v2、SQLAlchemy、JWT、PDF 解析、Spark AI SDK、pytest 等），全部使用 == 或 >= 固定版本。
- requirements-vector.txt：可选向量数据库与高精度 PDF 解析依赖（ChromaDB、LangChain、magic-pdf[full]、PyMuPDF）。
- frontend/package.json：前端依赖与开发脚本。
- frontend/package-lock.json：npm 锁文件，记录完整依赖树与 sha512 integrity。
- start.sh：虚拟环境初始化、依赖安装、前后端服务编排入口。
- .env.example / .env：环境变量模板与实际配置（由启动脚本自动复制）。

## 3. 架构与约定
- 分层依赖：核心功能仅依赖 requirements.txt，向量检索、RAG、高精度 PDF 解析等能力通过 requirements-vector.txt 按需启用，保证最小可用安装路径。
- 严格版本锁定：Python 侧对主要依赖使用 == 精确锁定（如 fastapi==0.111.0、uvicorn[standard]==0.29.0、pydantic==2.7.1、pytest==8.2.0），降低环境漂移风险；部分第三方库允许小范围兼容（>=）。
- 前端锁文件入仓：package-lock.json 提交至版本控制，确保 CI/CD 与协作开发时依赖树一致。
- 虚拟环境隔离：所有 Python 依赖安装到 .venv，不在全局环境污染；start.sh 在首次运行时自动创建并激活。
- 构建系统声明：pyproject.toml 指定 setuptools.backends.legacy:legacy 作为 build-backend，避免隐式 PEP 517 行为差异。

## 4. 开发者应遵循的规则
- 新增 Python 依赖：一律写入根目录 requirements.txt，优先使用 == 精确版本；若为可选能力（如向量库、MinerU），追加到 requirements-vector.txt 并在代码中做条件导入。
- 新增前端依赖：在 frontend/package.json 的 dependencies 或 devDependencies 中添加，然后执行 npm install 生成/更新 frontend/package-lock.json，并将 lock 文件提交。
- 不要手动编辑 lock 文件：始终通过 pip install / npm install 驱动变更，保持 lock 与声明一致。
- 依赖升级流程：先修改对应 manifest（requirements.txt 或 package.json），再运行 pip install -r requirements.txt / npm install 验证，最后提交变更。
- 可选依赖安装：需要 RAG/向量检索或 MinerU 时，在已激活的虚拟环境中执行 pip install -r requirements-vector.txt；Windows 用户按注释提示设置 --cache-dir。
- 环境初始化：新克隆仓库后直接运行 ./start.sh [--mock-mode]，脚本会自动完成 .venv 创建、依赖安装与环境变量复制，无需手工操作。