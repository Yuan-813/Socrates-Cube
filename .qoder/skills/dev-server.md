# Socrates-Cube 开发服务器启动技能

## 描述
一键启动 Socrates-Cube 前后端开发服务器，包含端口检查、环境预检、Mock 模式切换。

## 触发场景
- 用户说"启动项目"、"开发模式"、"跑起来"、"start server"
- 需要调试前后端联调

## 快速启动

### Windows PowerShell（推荐）
```powershell
# 一键启动（后端+前端）
cd d:\git-projects\Socrates-Cube
.\start.bat

# 或手动分步启动
# 后端（虚拟环境）
.venv\Scripts\python.exe -m uvicorn src.loopse.main:app --host 0.0.0.0 --port 8000 --reload

# 前端（新终端）
cd frontend
npm run dev
```

### Mock 模式（无需 API Key）
```powershell
# 设置 Mock 模式，无需真实 LLM API
$env:MOCK_LLM = "true"
.venv\Scripts\python.exe -m uvicorn src.loopse.main:app --port 8000 --reload
```

### 前端 Mock 模式
```powershell
cd frontend
$env:VITE_USE_MOCK = "true"
npm run dev -- --mode mock
```

## 服务端口
| 服务 | 地址 | 说明 |
|------|------|------|
| 后端 API | http://localhost:8000 | FastAPI + uvicorn |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| 前端 | http://localhost:5173 | Vite dev server |
| 前端(构建) | http://localhost:4173 | vite preview |

## 环境检查
```powershell
# 运行环境预检脚本
python scripts/verify_env.py

# 检查数据库初始化状态
.venv\Scripts\python.exe scripts/init_db.py

# 验证知识图谱加载
python -c "from src.loopse.kb.knowledge_graph import knowledge_graph; print(f'图谱节点: {len(knowledge_graph.get_all_nodes())}')"
```

## 常见问题
- `pymysql not found` → 正常，本地使用 SQLite，云端才需要 MySQL
- `No module named numpy` → ChromaDB 降级到本地 JSON 索引，不影响核心功能
- 端口占用 → 改 uvicorn 的 `--port` 参数
- 前端代理 → `frontend/vite.config.ts` 中 proxy 指向后端端口

## 构建生产版本
```powershell
cd frontend
npm run build          # 输出到 dist/
# 或
npx vite build --mode development  # 开发构建（含 sourcemap）
```

## OpenMAIC 灵感：多Agent教学课堂模式
参考 THU-MAIC/OpenMAIC 的多Agent课堂理念，Socrates-Cube 提供：
- `/scenario` 路由 → 多角色情景对话（教授/工程师/学长/面试官）
- `/simulator` 路由 → 协议仿真（TCP/DNS/HTTP 流程可视化）
- `/hardware3d` 路由 → 3D 硬件设备可视化（Three.js）
