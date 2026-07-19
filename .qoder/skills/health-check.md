---
name: health-check
description: 项目运行与健康检查：一键启动、端口检测、API验证、测试运行、质量报告生成
---

# 项目运行与健康检查技能

## 描述
一键启动 Socrates-Cube 项目、检查后端/前端健康状态、运行测试套件、生成质量报告。涵盖开发环境初始化、服务启动、端口验证、API 可用性检测等完整工作流。

## 使用场景
- 首次克隆项目后需要快速启动完整开发环境
- 确认后端/前端服务是否正常运行
- 代码修改后需要快速验证系统健康状态
- 提交前运行测试套件确保质量
- 生成项目质量度量报告

## 操作指南

### 1. 一键启动（推荐）

**使用 start.bat（Windows CMD）：**
```cmd
start.bat
start.bat --mock-mode
```

**PowerShell 分步启动：**
```powershell
# 后端启动（正常模式，端口 8000）
.venv\Scripts\python.exe -m uvicorn src.loopse.main:app --reload --host 0.0.0.0 --port 8000

# 后端启动（Mock 模式，无需 API Key）
$env:MOCK_MODE="true"; .venv\Scripts\python.exe -m uvicorn src.loopse.main:app --host 0.0.0.0 --port 8000

# 前端启动（另开终端，端口 5173）
cd frontend; npm run dev

# 前端 Mock 模式
cd frontend; npm run dev:mock
```

### 2. 环境验证（启动前）

```powershell
# 全面环境检查（Python版本、依赖、.env、知识库状态）
.venv\Scripts\python.exe scripts/verify_env.py
```

验证项目包括：
- Python 版本 ≥ 3.10
- `requirements.txt` 中所有依赖已安装
- `.env` 文件存在且关键变量已配置
- 知识库文件（knowledge_graph.json、misconceptions.json）存在
- 向量索引文件可用

### 3. 端口检查

```powershell
# 检查后端端口 8000
Test-NetConnection -ComputerName localhost -Port 8000

# 检查前端端口 5173
Test-NetConnection -ComputerName localhost -Port 5173

# 查看端口占用进程
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object OwningProcess
Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | Select-Object OwningProcess
```

### 4. API 健康验证

```powershell
# 基础健康检查
curl http://localhost:8000/health
# 预期返回：{"status":"ok","version":"1.0.0","service":"Socrates-Cube"}

# 聊天接口联通测试
curl http://localhost:8000/api/v1/chat/test
# 预期返回：{"message":"后端联通成功"}

# Swagger API 文档
# 浏览器访问：http://localhost:8000/docs
```

**完整 API 端点检查清单：**
| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 系统健康状态 |
| `/api/v1/chat/test` | GET | 聊天联通测试 |
| `/api/v1/chat/stream` | POST | SSE 流式对话 |
| `/api/v1/profile/{user_id}` | GET | 用户画像 |
| `/api/v1/path/{user_id}` | GET | 学习路径 |
| `/api/v1/resources` | GET | 资源列表 |
| `/api/v1/simulator/protocols` | GET | 协议仿真列表 |

### 5. 运行测试套件

```powershell
# 运行全部单元测试
.venv\Scripts\python.exe -m pytest tests/ -v

# 运行特定测试文件
.venv\Scripts\python.exe -m pytest tests/unit/test_diagnosis_agent.py -v

# 运行诊断准确性测试
.venv\Scripts\python.exe scripts/run_diagnosis_accuracy_test.py

# 运行认知闭环验证
.venv\Scripts\python.exe scripts/verify_cognitive_loop.py
```

**测试文件：**
- `tests/unit/test_diagnosis_agent.py` — 诊断Agent单测
- `tests/unit/test_orchestrator_integration.py` — Orchestrator集成测试
- `tests/unit/test_resource_generator.py` — 资源生成测试
- `tests/unit/test_challenger_agent.py` — 挑战者Agent测试
- `tests/unit/test_misconception_registry.py` — 误解库测试

### 6. 生成质量报告

```powershell
# 生成项目度量指标
.venv\Scripts\python.exe generate_metrics.py

# 生成 ACU 质量报告
.venv\Scripts\python.exe generate_acu_report.py

# 全量验证报告
.venv\Scripts\python.exe scripts/verify_all.py
```

质量报告输出：`outputs/metrics.json`

### 7. 数据库初始化/重置

```powershell
# SQLite 本地数据库初始化
.venv\Scripts\python.exe scripts/init_db.py

# 指定数据库文件和数据量
.venv\Scripts\python.exe scripts/init_db.py --db data/demo.db --rows 3000

# MySQL 云端数据库初始化
.venv\Scripts\python.exe scripts/init_mysql.py

# 同步到云端
.venv\Scripts\python.exe scripts/sync_cloud_db.py
```

### 8. 前端构建检查

```powershell
# TypeScript 类型检查
cd frontend; npx vue-tsc --noEmit

# 生产构建
cd frontend; npm run build

# 构建产物位于 frontend/dist/
```

## 服务地址速查

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:5173 | Vue3 开发服务器 |
| 后端 | http://localhost:8000 | FastAPI 服务 |
| API文档 | http://localhost:8000/docs | Swagger UI |
| ReDoc | http://localhost:8000/redoc | ReDoc 文档 |

## 常见问题

### Q: 后端启动报 "Address already in use"？
A: 端口被占用。查找并终止占用进程：
```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
```

### Q: 前端启动后页面空白？
A: 检查：
1. `frontend/.env` 中 `VITE_API_BASE_URL` 是否指向 `http://localhost:8000`
2. 后端是否已启动且 CORS 已启用
3. 浏览器控制台是否有网络错误

### Q: verify_env.py 报依赖缺失？
A: 重新安装依赖：
```powershell
.venv\Scripts\pip.exe install -r requirements.txt
```

### Q: 测试运行失败提示数据库不存在？
A: 先初始化数据库：
```powershell
$env:DATABASE_URL="sqlite:///data/socrates_cube.db"; .venv\Scripts\python.exe scripts/init_db.py
```

### Q: Mock 模式和正常模式有什么区别？
A: Mock 模式（`MOCK_MODE=true`）：
- 不连接 LLM API，使用预设响应
- 适合前端开发、UI 联调、离线演示
- 所有 Agent 返回固定文本

正常模式：
- 需要在 `.env` 配置讯飞星火 API Key
- 完整多Agent协作链路
- 实时 LLM 推理响应
