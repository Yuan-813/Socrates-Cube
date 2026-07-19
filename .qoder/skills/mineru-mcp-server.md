# MinerU MCP Server 集成技能

## 描述
MinerU v3.4 (https://github.com/opendatalab/MinerU) 官方提供 MCP Server，可直接集成到 Cursor / Claude Desktop / Windsurf 等 AI 编辑器，实现在对话中直接解析 PDF 文档。

v3.4 核心升级：PP-OCRv6（精度+11%）、OCR速度+100%、hybrid-engine effort=medium/high、自动模型缓存复用。

## 触发场景
- 用户上传 PDF 要求解析（网络协议 RFC/华为认证教材/Cisco 官方指南）
- 需要在 Cursor/Claude Desktop 中直接对 PDF 提问
- 批量处理 `data/raw/external/` 下的多个 PDF 教材

## MinerU MCP Server 配置

### Claude Desktop 配置（claude_desktop_config.json）
```json
{
  "mcpServers": {
    "mineru": {
      "command": "uvx",
      "args": ["mineru-mcp"],
      "env": {
        "MINERU_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Cursor 配置（cursor settings > MCP）
```json
{
  "name": "mineru",
  "command": "uvx mineru-mcp",
  "env": {
    "MINERU_API_KEY": "your-api-key-here"
  }
}
```

### 本地部署版本（无需 API Key）
```powershell
# 安装 MinerU（模型存 D 盘）
pip install magic-pdf[full] --cache-dir D:\pip-cache

# 设置模型存储路径（D 盘，防止 C 盘爆满）
$env:MAGIC_PDF_MODEL_DIR = "D:\models\mineru"

# 启动本地 MCP Server
magic-pdf server --host 0.0.0.0 --port 8765
```

## MinerU v3.4 API 特性

### hybrid-engine effort 参数
```python
# effort=medium（默认）：速度优先
# - Linux OCR 场景：速度提升 ~35%
# - Windows OCR 场景：速度提升 ~45%
# - macOS OCR 场景：速度提升 ~50%
# effort=high：精度优先 + 支持图片分析

import httpx

async def parse_pdf_v34(pdf_bytes: bytes, filename: str, effort: str = "medium"):
    """MinerU v3.4 API 调用示例"""
    async with httpx.AsyncClient() as c:
        r = await c.post(
            "https://mineru.net/api/v4/file/batch_urls",
            headers={"Authorization": f"Bearer {MINERU_API_KEY}"},
            json={
                "enable_formula": True,      # 公式 → LaTeX
                "enable_table": True,         # 表格 → HTML
                "language": "ch",             # ch 模型覆盖中英日文
                "parse_method": "auto",       # 自动选择 hybrid/pipeline
                "effort": effort,             # v3.4 新参数
                "files": [{"name": filename, "is_ocr": True, "data_id": "socrates"}],
            }
        )
    return r.json()
```

## 在 Socrates-Cube 中的集成

### books.py 中的调用
```python
# effort=medium 速度优先（普通教材）
full_text = await _extract_pdf_mineru(pdf_bytes, filename, effort="medium")

# effort=high 精度优先（含公式/图表的 RFC 文档）
full_text = await _extract_pdf_mineru(pdf_bytes, filename, effort="high")
```

### 批量处理 RFC 文档
```powershell
cd d:\git-projects\Socrates-Cube
# 使用 MinerU 批量解析 data/raw/external/ 目录下所有 PDF
python scripts/ingest_pdf.py data/raw/external --use-mineru --mineru-backend hybrid

# 或使用 reingest_with_mineru.py 重建向量库
python scripts/reingest_with_mineru.py --reset
```

## 支持的文档格式
- PDF（含扫描件、手写、多栏布局）
- DOCX / PPTX / XLSX（Office 文档）
- 图片（PNG/JPG/WEBP，含 VLM 理解）
- 网页（URL 直接解析）

## 输出格式
- **Markdown**（默认，最适合 RAG）：保持阅读顺序，自动去除页眉页脚
- **JSON**（结构化，含坐标信息）：用于精确元素定位
- 公式 → LaTeX；表格 → HTML；图片 → base64 或 URL

## 性能对比（PP-OCRv6 vs 上一版本）

| 指标 | 旧版本 | v3.4 (PP-OCRv6) | 提升 |
|------|--------|-----------------|------|
| OmniDocBench 精度 | 基准 | +11% | ↑ |
| OCR 处理速度 | 基准 | +100% | ↑↑ |
| 扫描 PDF（Windows effort=medium） | 基准 | +45% | ↑ |
| 多栏文档支持 | 部分 | 完整 | ↑ |

## 关键文件
- `src/loopse/api/books.py` — `_extract_pdf_mineru()` 函数
- `scripts/ingest_pdf.py` — CLI 批量处理脚本
- `.env` — `MINERU_API_KEY=` 配置项
