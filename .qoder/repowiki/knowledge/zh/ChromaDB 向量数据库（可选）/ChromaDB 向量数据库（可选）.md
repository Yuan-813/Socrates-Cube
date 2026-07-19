---
kind: external_dependency
name: ChromaDB 向量数据库（可选）
slug: chromadb-vector-db
category: external_dependency
category_hints:
    - migration_status
    - client_constraint
scope:
    - '**'
source_files:
    - src/loopse/kb/vector_store.py
    - requirements-vector.txt
---

### 身份与角色
- 可选的向量数据库，用于知识检索和语义搜索
- 支持本地 JSON 索引作为降级方案

### 迁移状态
- 核心功能不依赖 ChromaDB，缺失时使用 `data/vector_db/local_index.json` 本地索引
- 安装后可提升检索性能和质量
- 通过 `requirements-vector.txt` 管理相关依赖

### 关键约束
- 缺少 numpy 依赖时会发出警告但仍可运行
- 本地模式数据持久化在 JSON 文件中
- 分布式部署需要额外的配置