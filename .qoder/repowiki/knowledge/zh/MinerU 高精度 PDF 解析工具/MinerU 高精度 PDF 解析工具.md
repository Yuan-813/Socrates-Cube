---
kind: external_dependency
name: MinerU 高精度 PDF 解析工具
slug: mineru-pdf-parser
category: external_dependency
category_hints:
    - framework_behavior
    - sdk_real_api
scope:
    - '**'
source_files:
    - scripts/download_knowledge_sources.py
    - requirements.txt
---

### 身份与角色
- 开源的高精度 PDF 解析工具，支持公式、表格、OCR 的高质量提取
- 用于将教材 PDF 转换为结构化 Markdown 内容，构建知识库

### 集成方式
- 可选依赖，未安装时自动降级到 PyMuPDF 轻量级解析
- 通过 `scripts/download_knowledge_sources.py` 脚本调用
- 支持 GPU 加速获得最佳效果

### 关键约束
- 扫描版图片 PDF 无法直接提取文字，需要预置内容或使用 OCR
- 需要 Python 3.10+ 环境和足够的内存空间
- 解析结果质量受 PDF 原始质量影响较大