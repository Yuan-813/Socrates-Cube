# Skill: 使用 MinerU v3.4 高精度解析 PDF 并入库知识库

> MinerU v3.4 核心升级：PP-OCRv6（精度+11%，OCR速度+100%）、hybrid-engine（effort=medium/high）、MCP Server（Cursor/Claude Desktop/Windsurf）
> 官方仓库：https://github.com/opendatalab/MinerU

## 适用场景
- 用户上传网络协议 RFC/华为认证教材/任意计算机网络 PDF
- 需要将 PDF 内容（含公式/表格/图文）解析并写入向量知识库
- 批量清洗 `data/raw/external/` 下的 PDF 教材
- effort=high 模式精度优先（复杂 RFC 文档、含公式教材）

## 工具链
- **MinerU v3.4 (magic-pdf)**：PP-OCRv6，hybrid-engine，https://github.com/opendatalab/MinerU
- **OpenDataloader-PDF**：配套高精度数据加载框架（基准#1，0.907分），https://github.com/opendataloader-project/opendataloader-pdf
- **PyMuPDF**：降级方案（MinerU 未安装时自动使用）
- **ChromaDB**：向量存储后端

## 安装依赖（D 盘优先，禁止 C 盘爆满）

```powershell
# MinerU v3.4 完整版（PP-OCRv6 + hybrid-engine）
pip install magic-pdf[full] --cache-dir D:\pip-cache

# 模型文件必须存到 D 盘，在 .env 中设置：
# MAGIC_PDF_MODEL_DIR=D:\models\mineru

# PyMuPDF 降级方案
pip install PyMuPDF --cache-dir D:\pip-cache
```

## MinerU v3.4 新特性说明

### hybrid-engine effort 参数
| effort 值 | 适用场景 | 速度提升（Windows） |
|-----------|---------|--------------------|
| `medium`（默认）| 普通教材、速度优先 | OCR +45% |
| `high` | 含公式/图表 RFC 文档 | 精度最高，支持图片分析 |

```python
# books.py 中 effort 用法
full_text = await _extract_pdf_mineru(pdf_bytes, filename, effort="medium")  # 速度优先
full_text = await _extract_pdf_mineru(pdf_bytes, filename, effort="high")    # 精度优先（RFC 文档）
```

### PP-OCRv6 性能对比
| 指标 | 旧版 | v3.4 (PP-OCRv6) |
|------|------|-----------------|
| OmniDocBench 精度 | 基准 | +11% |
| OCR 处理速度 | 基准 | +100% |
| 多栏支持 | 部分 | 完整 |
| 中英日文覆盖 | 分模型 | `language=ch` 统一 |

## 使用方式

### 方式一：批量重新清洗所有教材（推荐）

```powershell
cd d:\git-projects\Socrates-Cube
python scripts/reingest_with_mineru.py --reset
```

- `--reset`：清空向量库重建（默认增量追加）
- `--clean-only`：仅生成 Markdown，不重建向量库
- `--file path/to/file.pdf`：处理单个文件

### 方式二：REST API 上传单个 PDF

```bash
curl -X POST http://localhost:8000/api/v1/kb/upload-pdf \
  -F "file=@/path/to/rfc9293_tcp.pdf" \
  -F "source_name=RFC9293-TCP" \
  -F "use_mineru=true"
```

响应示例：
```json
{
  "success": true,
  "source": "RFC9293-TCP",
  "chunks_added": 42,
  "char_count": 18500,
  "message": "「RFC9293-TCP」已解析为 42 个知识块并入库"
}
```

### 方式三：Python 脚本调用

```python
from scripts.ingest_pdf import extract_text, chunk_and_ingest
text = extract_text("path/to/book.pdf", use_mineru=True)
chunk_and_ingest(text, collection="course_docs", source="新版教材")
```

## 关键文件路径

| 文件 | 作用 |
|------|------|
| `scripts/ingest_pdf.py` | CLI 脚本：单文件/批量 PDF 入库 |
| `scripts/reingest_with_mineru.py` | 批量清洗 + 向量库重建 |
| `src/loopse/api/knowledge_base.py` | REST API：`POST /upload-pdf` |
| `src/loopse/kb/document_processor.py` | 文本切块核心逻辑 |
| `data/raw/external/` | 原始 PDF/TXT 存放目录 |
| `data/cleaned/` | 清洗后的 Markdown 输出目录 |

## 注意事项

1. **模型文件必须存 D 盘**：运行前确认 `.env` 中 `MAGIC_PDF_MODEL_DIR=D:\models\mineru`
2. **首次运行**：MinerU 会自动下载模型，约 2GB，确保 D 盘剩余空间 > 5GB
3. **降级透明**：MinerU 解析失败时自动切换 PyMuPDF，无需手动干预
4. **幂等安全**：重复运行不会产生重复的向量条目（基于 MD5 ID 去重）
