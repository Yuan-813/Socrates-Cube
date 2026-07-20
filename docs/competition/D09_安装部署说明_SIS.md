# 安装部署说明（SIS）
# Software Installation Specification

| 文档标识 | SC-SIS-001 |
|:---:|:---|
| 项目名称 | Socrates-Cube 多智能体自适应《计算机网络》学习系统 |
| 版本号 | v1.0 |
| 编制日期 | 2026-07-20 |
| 参考标准 | GB/T 8567-2006《计算机软件文档编制规范》 |

---

## 第一章 部署架构概述

Socrates-Cube 支持两种部署方式：

| 方式 | 适用场景 | 说明 |
|---|---|---|
| 本机直接运行 | 开发演示、竞赛答辩 | 前后端分别启动，推荐方式 |
| Docker Compose | 生产部署、快速体验 | 容器化一键启动 |

**服务端口**：
- 后端FastAPI：`http://localhost:8000`
- 前端Vue3 Vite：`http://localhost:5173`（开发）
- API文档：`http://localhost:8000/docs`

---

## 第二章 环境要求

### 2.1 必须满足的环境要求

| 要求 | 版本 | 备注 |
|---|---|---|
| Python | **3.10.*** | **严格锁定**，aiosqlite兼容性要求，3.11+可能不兼容 |
| Node.js | ≥ 18.0 | 前端构建需要 |
| npm | ≥ 9.0 | 随Node.js自动安装 |
| 可用磁盘 | ≥ 2GB | 含Python虚拟环境和Node.js依赖 |
| 内存 | ≥ 4GB | 运行时需要，ChromaDB向量检索建议8GB |

> **注意**：Python版本必须精确为 3.10.x（如3.10.11、3.10.14等均可），使用 `python --version` 验证。

### 2.2 可选环境要求

| 要求 | 说明 |
|---|---|
| 讯飞星火API账号 | LLM功能需要；不配置则自动使用Mock模式 |
| Docker + Docker Compose | 仅容器化部署需要，v20.10+ |
| Git | 源码克隆需要 |

---

## 第三章 安装步骤

### 方式A：Windows一键启动（推荐，最简单）

```batch
# 双击执行 start.bat 或在命令行运行：
cd d:\path\to\Socrates-Cube
start.bat
```

`start.bat` 自动完成：
1. 激活Python虚拟环境（.venv）
2. 安装/验证Python依赖
3. 初始化数据库（scripts/init_db.py）
4. 启动后端Uvicorn服务（port 8000）
5. 启动前端Vite开发服务器（port 5173）

---

### 方式B：手动安装步骤

#### 步骤1：克隆/获取源码

```bash
git clone <repository-url>
cd Socrates-Cube
```

#### 步骤2：配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env
# 编辑 .env 文件，填入讯飞星火API密钥（可选，不填则使用Mock模式）
```

`.env` 关键配置项：

```ini
# 讯飞星火API（可选，不填则使用Mock模式）
XUNFEI_APP_ID=your_app_id_here
XUNFEI_API_KEY=your_api_key_here
XUNFEI_API_SECRET=your_api_secret_here
XUNFEI_SPARK_URL=wss://spark-api.xf-yun.com/v3.5/chat

# 数据库（默认SQLite，无需修改）
DATABASE_URL=sqlite:///./edu_agent.db

# 向量库路径（默认值，无需修改）
CHROMA_DB_PATH=./chroma_db

# 服务配置（默认值，无需修改）
APP_HOST=0.0.0.0
APP_PORT=8000
```

#### 步骤3：创建Python虚拟环境并安装依赖

```bash
# 确保Python版本为3.10.*
python --version
# 输出应为：Python 3.10.x

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 安装Python依赖
pip install -r requirements.txt
```

#### 步骤4：初始化数据库

```bash
python scripts/init_db.py
```

执行成功后，项目根目录下会生成 `edu_agent.db` 文件，包含：
- 10张已创建的数据库表
- 10个核心KP知识节点（TCP/IP/HTTP/DNS/子网等）
- 3000条演示用户数据（用于展示效果）

#### 步骤5：安装前端依赖

```bash
cd frontend
npm install
cd ..
```

#### 步骤6：启动后端服务

```bash
# 确保在项目根目录，虚拟环境已激活
python -m uvicorn src.loopse.main:app --host 0.0.0.0 --port 8000 --reload
```

输出示例：
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     数据库初始化完成
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### 步骤7：启动前端服务

在新的终端窗口：
```bash
cd frontend
npm run dev
```

输出示例：
```
  VITE v5.4.21  ready in 856 ms
  ➜  Local:   http://localhost:5173/
  ➜  Network: http://0.0.0.0:5173/
```

---

### 方式C：Docker Compose部署

```bash
# 构建并启动所有服务
docker-compose up --build

# 后台运行
docker-compose up -d --build

# 停止服务
docker-compose down
```

Docker Compose配置说明（docker-compose.yml）：
- `backend` 服务：基于 `Dockerfile`，映射8000端口
- `frontend` 服务：基于 `frontend/Dockerfile`，映射80端口（nginx）

---

## 第四章 环境变量详细说明

| 变量名 | 是否必填 | 默认值 | 说明 |
|---|---|---|---|
| XUNFEI_APP_ID | 否 | 无 | 讯飞星火应用ID，不填则Mock模式 |
| XUNFEI_API_KEY | 否 | 无 | 讯飞星火API密钥 |
| XUNFEI_API_SECRET | 否 | 无 | 讯飞星火API密钥 |
| XUNFEI_SPARK_URL | 否 | wss://spark-api.xf-yun.com/v3.5/chat | 星火WebSocket端点 |
| DATABASE_URL | 否 | sqlite:///./edu_agent.db | 数据库连接字符串 |
| CHROMA_DB_PATH | 否 | ./chroma_db | ChromaDB持久化目录 |
| APP_HOST | 否 | 0.0.0.0 | 服务监听地址 |
| APP_PORT | 否 | 8000 | 服务监听端口 |
| APP_DEBUG | 否 | true | 是否开启调试模式 |
| CORS_ORIGINS | 否 | ["http://localhost:5173"] | CORS允许的来源 |

**Mock模式说明**：当 XUNFEI_APP_ID / XUNFEI_API_KEY / XUNFEI_API_SECRET 任意一项未配置时，系统自动切换至Mock模式，使用预设模板回复。Mock模式下所有功能可用，但AI回复内容为固定预设文本。

---

## 第五章 验证安装

### 5.1 后端健康检查

```bash
curl http://localhost:8000/health
# 预期响应：{"status":"ok","version":"1.0.0","service":"Socrates-Cube"}
```

### 5.2 API文档访问

浏览器打开：`http://localhost:8000/docs`

应显示 FastAPI 自动生成的 Swagger UI，包含所有10个API端点。

### 5.3 前端访问

浏览器打开：`http://localhost:5173`

应显示 Socrates-Cube 系统首页（HomeView）。

### 5.4 演示账号验证

使用默认演示账号发起对话：
- 用户ID：`student-001`（系统内置，无需注册）
- 在首页点击"智能对话"或直接访问 `http://localhost:5173/chat`
- 输入任意问题（如"TCP三次握手是什么"）
- 应看到SSE事件流推送（agent_start/token等事件）

---

## 第六章 向量知识库初始化（可选）

ChromaDB向量知识库可选初始化（不初始化则降级至TF-IDF本地索引）：

```bash
# 向量化课程文档和RFC规范
python scripts/ingest_docs.py

# 重新注入误解库向量
python scripts/reingest_misconceptions.py

# 验证知识库状态
python scripts/verify_env.py
```

> **注意**：ChromaDB向量化需要联网下载 sentence-transformers 模型，首次运行约需下载 500MB 模型文件。离线演示时可跳过此步骤，系统自动使用TF-IDF降级检索。

---

## 第七章 故障排除

### 问题1：Python版本不匹配

**症状**：`pip install` 报 `aiosqlite` 安装失败或兼容性错误

**解决方案**：
```bash
python --version  # 确认为3.10.x
# 若版本不匹配，下载安装 Python 3.10.x
# Windows: 从 python.org 下载3.10.14
# 注意：不要使用系统Python，建议用pyenv管理多版本
```

### 问题2：端口冲突

**症状**：`Address already in use: ('0.0.0.0', 8000)` 或 Vite端口5173被占用

**解决方案**：
```bash
# 查找并终止占用端口的进程（Windows PowerShell）
netstat -ano | findstr :8000
taskkill /PID <PID号> /F

# 或修改启动端口
python -m uvicorn src.loopse.main:app --port 8001
# 同时修改前端 frontend/.env 中的 VITE_API_BASE_URL
```

### 问题3：ChromaDB初始化失败

**症状**：日志出现 `ChromaDB unavailable; local KB index will be used`

**说明**：这是**预期的降级行为**，不影响系统运行。系统会自动使用 `data/vector_db/local_index.json` 进行TF-IDF检索。

**若希望启用ChromaDB**：检查 `requirements-vector.txt` 中的依赖，确保 numpy 版本兼容：
```bash
pip install -r requirements-vector.txt
python -c "import chromadb; print(chromadb.__version__)"
```

### 问题4：LLM API连接失败

**症状**：对话返回内容为固定预设文本，或日志出现 `LLM client Mock mode`

**说明**：这是**正常的Mock模式行为**。确认 `.env` 文件中已正确填写讯飞星火API三个密钥参数。

**验证**：
```bash
python scripts/verify_env.py
# 查看是否显示 "LLM API 配置: 已配置"
```

### 问题5：数据库初始化失败

**症状**：启动时报 `数据库初始化失败（非致命）`

**解决方案**：
```bash
# 手动重新初始化
python scripts/init_db.py

# 若edu_agent.db文件损坏，删除后重新初始化
del edu_agent.db  # Windows
python scripts/init_db.py
```

---

*本文档描述的所有命令均经过测试，适用于 Windows 10/11 环境。Linux/macOS 环境命令基本相同，路径分隔符使用 `/`。*
