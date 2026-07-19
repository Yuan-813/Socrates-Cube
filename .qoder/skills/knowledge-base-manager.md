---
name: knowledge-base-manager
description: 知识库管理技能：重建向量库、更新知识图谱、检查ACU质量、扩充误解库
---

# 知识库管理技能

## 描述
帮助开发者快速执行 Socrates-Cube 知识库相关操作，包括向量库重建、知识图谱扩展、ACU认知单元质量检查、误解库管理等。所有命令均在项目根目录 `d:\git-projects\Socrates-Cube` 下执行。

## 使用场景
- 新增或修改了 `data/cleaned/` 下的课程文档或RFC文档后，需要重建向量索引
- 需要检查知识图谱中 ACU 认知单元的数量和质量
- 需要扩充误解库（misconceptions）或知识图谱节点
- 项目初始化时需要一次性构建完整知识库
- 排查知识检索不准确的问题

## 操作指南

### 1. 完整知识库重建（从零开始）

按顺序执行以下步骤：

```powershell
# Step 1: 下载外部知识源（RFC文档、IANA协议号等）
.venv\Scripts\python.exe scripts/download_knowledge_sources.py

# Step 2: 重建向量索引（--reset 清除旧数据）
.venv\Scripts\python.exe scripts/ingest_docs.py --reset

# Step 3: 初始化数据库（生成演示数据）
.venv\Scripts\python.exe scripts/init_db.py --db data/demo.db --rows 3000
```

### 2. 仅更新向量索引（文档有变更时）

```powershell
# 增量更新（不清除旧数据）
.venv\Scripts\python.exe scripts/ingest_docs.py

# 完全重建（清除旧数据后重新索引）
.venv\Scripts\python.exe scripts/ingest_docs.py --reset
```

向量索引文件位置：`data/vector_db/local_index.json`

### 3. 检查 ACU 认知单元质量

```powershell
# 查看 ACU 节点数量和采样
.venv\Scripts\python.exe scripts/check_acu.py

# 全量验证（包括人格、API、图谱、误解库等）
.venv\Scripts\python.exe scripts/verify_all.py
```

**ACU 质量指标：**
- 目标数量：≥60 个 ACU 认知单元
- 每个 ACU 应包含：id、name、chapter、difficulty、prerequisites
- ACU 之间应有 prerequisite 边连接

### 4. 扩展知识图谱

```powershell
# 扩展知识图谱（添加技能/认证/岗位节点）
.venv\Scripts\python.exe scripts/expand_knowledge_graph.py

# 扩展 ACU 认知单元
.venv\Scripts\python.exe scripts/expand_acu.py
```

知识图谱文件：`data/knowledge_graph.json`
- `nodes`：KP知识点节点（kp_001~kp_0xx）
- `cognitive_nodes`：ACU认知单元（acu_001~acu_0xx）
- `edges`：节点间的关联边（prerequisite、contains、maps_to等）

### 5. 扩充误解库

```powershell
# 追加新误解条目
.venv\Scripts\python.exe scripts/expand_misconceptions.py

# 检查误解库状态
.venv\Scripts\python.exe scripts/check_misconceptions.py

# 将误解数据重新导入向量库
.venv\Scripts\python.exe scripts/reingest_misconceptions.py
```

误解库文件：`data/misconceptions.json`
每条误解包含：id、knowledge_point、misconception、error_type、correct_answer、interventions

### 6. 知识库构建（替代方案）

```powershell
# 使用 build_knowledge_base.py 一次性构建向量库
.venv\Scripts\python.exe scripts/build_knowledge_base.py
```

## 关键文件清单

| 文件路径 | 说明 |
|---------|------|
| `data/knowledge_graph.json` | 知识图谱主文件（KP节点 + ACU + 边） |
| `data/misconceptions.json` | 误解库（诊断Agent使用） |
| `data/vector_db/local_index.json` | 向量索引文件 |
| `data/cleaned/*.md` | 已清洗的课程/RFC文档 |
| `data/raw/misconceptions.json` | 原始误解数据 |
| `data/raw/external/` | 下载的外部RFC原文 |
| `src/loopse/kb/vector_store.py` | 向量存储引擎 |
| `src/loopse/kb/text_splitter.py` | 文本切片器 |

## 常见问题

### Q: 向量索引重建后检索结果不准确？
A: 检查 `data/cleaned/` 下的文档是否完整，确认 `--reset` 参数已使用。可通过 API `/api/v1/search` 测试检索效果。

### Q: ACU 数量不足怎么办？
A: 运行 `scripts/expand_acu.py` 扩展。检查 `data/knowledge_graph.json` 中 `cognitive_nodes` 数组长度。

### Q: 新增的误解条目未生效？
A: 添加到 `data/misconceptions.json` 后，需运行 `scripts/reingest_misconceptions.py` 将其导入向量库。

### Q: 下载外部知识源超时？
A: `download_knowledge_sources.py` 支持 `--skip-existing` 参数跳过已下载的文件。检查网络连接或使用代理。

### Q: 知识图谱节点类型有哪些？
A: 主要类型包括：
- `kp_xxx`：知识点节点（KnowledgePoint）
- `acu_xxx`：认知单元（Atomic Cognitive Unit）
- `skill_xxx`：实践技能节点
- `cert_xxx`：认证考试节点
- `job_xxx`：岗位需求节点
