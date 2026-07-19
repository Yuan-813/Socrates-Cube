# PDF 知识库管理技能

使用 MinerU 高精度PDF解析引擎管理 Socrates-Cube 的 PDF 书架知识库。
MinerU GitHub: https://github.com/opendatalab/MinerU

## 触发条件

- 用户上传 PDF 文档（教材、RFC、论文等）
- 用户想搜索知识库中的特定内容
- 用户想基于上传资料进行 RAG 问答
- 查看知识库统计信息

## MinerU 解析引擎

**有 MINERU_API_KEY 时（高精度模式）：**
- VLM+OCR 双引擎，自动识别扫描件/手写内容
- 公式自动转 LaTeX，表格转 HTML 保留结构
- 支持多栏布局、跨页表格合并
- 中英文混排、109种语言支持
- 输出标准 Markdown，适合 RAG 切块

**无 API Key 时（基础模式）：**
- 使用 pypdf 提取纯文本
- 不支持扫描件 OCR
- 适合数字原生 PDF（已有文本层）

## 执行步骤

### 上传 PDF
1. 调用 `POST /api/v1/books/upload`
   - `file`: PDF 文件（multipart/form-data）
   - `title`: 书籍标题
   - `author`: 作者（可选）
2. 检查返回的 `parse_engine` 字段（`mineru`/`pypdf`）
3. 返回 `chunk_count` 确认解析成功

### RAG 问答
1. 调用 `POST /api/v1/books/ask`
   - `book_id`: 书籍 ID
   - `question`: 问题
   - `top_k`: 检索段落数（默认5）
2. 系统自动 BM25 检索 → LLM 综合回答
3. 返回 `answer` 和 `sources`（参考段落）

### 知识库搜索
1. 调用 `POST /api/v1/kb/search`
   - `query`: 搜索词
   - `collection`: `user_uploads`/`course_docs`/`protocol_specs`
   - `n_results`: 结果数量

## 预置书目

| ID | 书名 | 特点 |
|----|------|------|
| preset_001 | 计算机网络：自顶向下方法 | 最广泛使用的入门教材 |
| preset_002 | TCP/IP详解 卷1：协议 | 协议深度参考权威书 |
| preset_003 | 路由与交换技术 | HCIA/HCIP认证备考 |
| preset_004 | HCIA-Datacom学习指南 | 华为官方认证指南 |
| preset_005 | Cisco CCNA 200-301 | 思科认证官方教材 |

## 注意事项

- 文件大小限制：50MB
- 仅支持 PDF 格式
- MinerU 解析需要网络访问 mineru.net API
- 预置书籍无 PDF，需用户上传后才能问答
- BM25 为关键词匹配，语义搜索使用 /api/v1/kb/search
