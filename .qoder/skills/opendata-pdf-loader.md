# OpenDataloader-PDF 数据加载技能

## 描述
OpenDataloader-PDF (https://github.com/opendataloader-project/opendataloader-pdf) 是一款 AI-ready PDF 解析框架，基准测试综合排名 **#1**（0.907 overall），比 MinerU / docling / marker 更快，支持复杂表格、公式、OCR（80+语言），适合在 Socrates-Cube 中作为 RAG 数据管道的补充解析方案。

**核心指标（200个真实 PDF 基准测试）**：
- 整体精度：0.907（#1）
- 表格提取精度：0.928（#1）
- 阅读顺序准确率：0.934
- 速度：0.463 秒/页（hybrid 模式）
- 许可证：Apache-2.0

## 触发场景
- 需要快速（无需 GPU）解析普通数字 PDF 并构建 RAG 知识库
- MinerU 模型文件太大或显存不足时的替代方案
- 需要处理带边界框坐标的结构化 JSON 输出（用于引用溯源）
- 生成符合无障碍规范（Tagged PDF）的文档时

## 安装

```powershell
# 标准版（速度最快，适合普通数字 PDF）
pip install -U opendataloader-pdf --cache-dir D:\pip-cache

# Hybrid 版（复杂表格 / 扫描件 / 公式 - 需要 Java 11+）
pip install -U "opendataloader-pdf[hybrid]" --cache-dir D:\pip-cache

# 验证 Java 版本（Hybrid 模式依赖）
java -version
# 如未安装：从 https://adoptium.net/ 下载 JDK 17+
```

## 使用方式

### 方式一：Python API（推荐 Socrates-Cube 集成）

```python
import opendataloader_pdf

# 批量转换（推荐：一次调用处理所有文件，避免重复启动 JVM）
opendataloader_pdf.convert(
    input_path=["data/raw/external/rfc9293_tcp.pdf", "data/raw/external/"],
    output_dir="data/cleaned/",
    format="markdown,json"   # markdown 适合 RAG 分块，json 含坐标信息
)
```

### 方式二：Hybrid 模式（复杂 RFC 文档 / 扫描件）

```powershell
# 终端1：启动 Hybrid 后端服务
opendataloader-pdf-hybrid --port 5002

# 终端2：处理文档
opendataloader-pdf --hybrid docling-fast data/raw/external/
```

### 方式三：CLI 快速使用

```powershell
cd d:\git-projects\Socrates-Cube

# 处理单个文件
opendataloader-pdf data/raw/external/rfc8446_tls.pdf --output-dir data/cleaned/

# 处理目录下所有 PDF（标准模式）
opendataloader-pdf data/raw/external/ --output-dir data/cleaned/ --format markdown

# 生成无障碍 Tagged PDF
opendataloader-pdf data/raw/external/ --format tagged-pdf --output-dir data/tagged/
```

## 与 MinerU 的选择建议

| 场景 | 推荐工具 | 原因 |
|------|---------|------|
| 普通数字 PDF（教材/标准文档） | OpenDataloader-PDF | 速度快（0.015s/页），无需模型文件 |
| 扫描 PDF / 手写文字 | MinerU v3.4 (effort=high) | PP-OCRv6 精度更高 |
| 含大量公式的 RFC 文档 | MinerU v3.4 (effort=high) | LaTeX 公式识别更准确 |
| 需要边界框坐标（引用溯源） | OpenDataloader-PDF | 原生 JSON 含 bounding boxes |
| 批量快速处理（速度优先） | OpenDataloader-PDF | 比 MinerU 快 ~13x |
| GPU 不可用 | OpenDataloader-PDF | 完全无需 GPU |

## 在 Socrates-Cube 中的集成点

### 集成到 books.py（降级方案）

```python
# src/loopse/api/books.py 中的降级逻辑
async def _extract_pdf_fallback(pdf_bytes: bytes, filename: str) -> str:
    """当 MinerU API 不可用时，使用 OpenDataloader-PDF 本地解析"""
    import tempfile, opendataloader_pdf, pathlib
    
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = pathlib.Path(tmp) / filename
        pdf_path.write_bytes(pdf_bytes)
        out_dir = pathlib.Path(tmp) / "out"
        opendataloader_pdf.convert(
            input_path=[str(pdf_path)],
            output_dir=str(out_dir),
            format="markdown"
        )
        md_file = next(out_dir.glob("**/*.md"), None)
        return md_file.read_text(encoding="utf-8") if md_file else ""
```

### 集成到 scripts/ingest_pdf.py

```powershell
# 方案A：先用 OpenDataloader-PDF CLI 生成 Markdown，再用 ingest_docs.py 入库
opendataloader-pdf data/raw/external/ --output-dir data/cleaned/ --format markdown
python scripts/ingest_docs.py

# 方案B：使用 ingest_pdf.py 传入目录（不启用 MinerU，使用 PyMuPDF 降级）
python scripts/ingest_pdf.py data/raw/external
```

## 输出格式说明

| 格式 | 用途 | 特点 |
|------|------|------|
| `markdown` | RAG 分块（默认）| 保持阅读顺序，去除页眉页脚 |
| `json` | 引用溯源 | 含每个元素的 bounding boxes 坐标 |
| `html` | 网页展示 | 保留样式结构 |
| `tagged-pdf` | 无障碍合规 | 满足 EAA/ADA/Section 508 要求 |

## 支持的复杂元素

- 复杂/无边框表格（hybrid 模式，精度 0.928）
- LaTeX 公式提取（`--enrich-formula` 选项）
- 扫描件 OCR（80+ 语言，`--force-ocr`）
- 图表 AI 描述（`--enrich-picture-description`）
- 多栏布局（XY-Cut++ 阅读顺序算法）
- AI 安全过滤（自动过滤 prompt injection）

## 关键文件
- `src/loopse/api/books.py` — PDF 解析入口（MinerU 优先，OpenDataloader 降级）
- `scripts/ingest_pdf.py` — CLI 批量处理脚本
- `scripts/reingest_with_mineru.py` — 批量清洗 + 向量库重建
- `data/raw/external/` — 原始 PDF 存放目录
- `data/cleaned/` — 解析后的 Markdown 输出目录

## 注意事项
1. **Hybrid 模式需要 Java 11+**：运行前先执行 `java -version` 确认
2. **批量调用**：每次 `convert()` 会启动 JVM 进程，建议一次调用传入所有文件
3. **公式识别**：默认关闭，需要 `--enrich-formula` 或 `--hybrid-mode full`
4. **与 MinerU 共存**：两者都安装时，优先使用 MinerU（精度更高），OpenDataloader 作为降级方案
