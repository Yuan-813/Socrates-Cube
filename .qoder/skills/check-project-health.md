# Skill: 项目健康度全面自检

## 适用场景
- 每次开发前快速验证环境
- CI/CD 部署前的预检查
- 排查某个功能不工作时的诊断入口

## 一键全量验证脚本

```powershell
cd d:\git-projects\Socrates-Cube
python scripts/verify_all.py
```

或逐步运行：

```powershell
# Step 1: 环境依赖检查
python scripts/verify_env.py

# Step 2: 向量库状态
python -c "
import sys,io; sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
sys.path.insert(0,'src')
from loopse.kb.vector_store import vector_store
for col in ['course_docs','protocol_specs','misconceptions','user_uploads']:
    print(f'{col}: {vector_store.count(col)} 条')
"

# Step 3: 题库完整性
python -c "
import json,sys,io; sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
data=json.load(open('data/certificate_exams.json',encoding='utf-8'))
for eid,exam in data['exams'].items():
    q=len(exam['questions']); m=exam.get('question_count',0)
    print(f'{eid}: {q}题 [meta={m}]', 'OK' if q==m else 'MISMATCH!')
"

# Step 4: Python 语法验证（核心文件）
python -c "
import ast,sys,io; sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
files=['src/loopse/main.py','src/loopse/core/llm_client.py',
       'src/loopse/agent/scenario_agent.py','src/loopse/agent/challenger.py',
       'src/loopse/agent/federated_learning.py','src/loopse/api/exam.py']
[print('OK:',f) or None for f in files if ast.parse(open(f,encoding='utf-8').read()) or True]
print('All syntax OK')
"

# Step 5: 知识图谱统计
python -c "
import json,sys,io; sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
kg=json.load(open('data/knowledge_graph.json',encoding='utf-8'))
print('KP节点:', len(kg.get('nodes',[])))
print('ACU节点:', len(kg.get('cognitive_nodes',[])))
print('知识边:', len(kg.get('edges',[])))
mc=json.load(open('data/misconceptions.json',encoding='utf-8'))
print('误解条目:', len(mc))
"
```

## 关键指标基准值

| 指标 | 健康值 |
|------|--------|
| `course_docs` 向量条目 | ≥ 60 |
| `protocol_specs` 向量条目 | ≥ 290 |
| `misconceptions` 向量条目 | ≥ 150 |
| KP 节点数 | 40 |
| ACU 节点数 | 60 |
| 知识边数 | ≥ 60 |
| 误解条目数 | 150 |
| 题库（HCIA） | 30 题 |
| 题库（CCNA） | 30 题 |

## 后端启动验证

```powershell
# 启动后端（Mock模式，无需API Key）
python -m uvicorn src.loopse.main:app --reload --port 8000 --mock-mode

# 或用 start.bat
.\start.bat
```

健康检查接口：
```
GET http://localhost:8000/api/v1/health
```

期望响应：
```json
{"status": "ok", "version": "1.0.0", "mock_mode": false}
```

## 前端构建验证

```powershell
cd frontend
npm run build
```

无报错则输出到 `frontend/dist/`，可用 nginx 或 `npm run preview` 预览。

## 常见问题快速定位

| 症状 | 检查命令 | 可能原因 |
|------|---------|---------|
| 向量检索返回空 | `vector_store.count('course_docs')` | 向量库未初始化，运行 `python scripts/ingest_docs.py --reset` |
| 考试题目数为 0 | 检查 `certificate_exams.json` | JSON 格式错误 |
| LLM 返回 Mock 响应 | `.env` 中查看 `XUNFEI_APP_ID` | API Key 未配置 |
| SenseNova 信息图无图片 | `.env` 中查看 `SENSENOVA_API_KEY` | Key 未配置，会自动降级为 SVG |
| MinerU 未工作 | `python -c "import magic_pdf; print('OK')"` | 运行 `pip install magic-pdf[full] --cache-dir D:\pip-cache` |
| 路由 404 | 查看 `src/loopse/main.py` 最后几行 | 新路由未注册 `app.include_router(xxx)` |

## 磁盘空间检查（防 C 盘爆满）

```powershell
# 检查关键目录大小
Get-ChildItem d:\git-projects\Socrates-Cube\chroma_db -ErrorAction SilentlyContinue | Measure-Object -Sum Length
Get-ChildItem d:\models\mineru -ErrorAction SilentlyContinue | Measure-Object -Sum Length
```

所有大文件（模型、向量库、数据库）必须在 D 盘，严禁占用 C 盘！
