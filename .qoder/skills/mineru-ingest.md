# MinerU PDF 知识库入库技能

## 描述
使用 MinerU（opendatalab/MinerU）高精度解析 PDF，并将内容分块入库到 Socrates-Cube 知识库。
MinerU 支持 VLM+OCR 双引擎、109种语言、公式→LaTeX、表格→HTML，是 LLM/RAG 领域最佳 PDF 解析方案。

## 触发场景
- 用户说"解析PDF"、"PDF入库"、"添加教材"、"导入文档"
- 需要将计算机网络教材/RFC文档/论文入库向量数据库

## 执行步骤

### 方案一：使用本地 MinerU（magic-pdf 已安装）
```bash
# 安装 MinerU（确保模型下载到 D 盘）
$env:MAGIC_PDF_MODEL_DIR = "D:\models\magic-pdf"
pip install --cache-dir D:\pip-cache magic-pdf[full]

# 解析单个PDF并入库
python scripts/ingest_pdf.py <pdf_path> --use-mineru --backend hybrid

# 批量处理目录
python scripts/ingest_pdf.py data/raw/pdfs/ --pattern "*.pdf" --use-mineru
```

### 方案二：使用 MinerU REST API（无需本地安装）
```bash
# 通过 REST API 调用 MinerU 云端服务
curl -X POST /api/v1/kb/upload-pdf \
  -F "file=@path/to/book.pdf" \
  -F "source_name=谢希仁计算机网络第8版" \
  -F "use_mineru=true"
```

### 方案三：MinerU MCP Server（Cursor/Claude Desktop）
```json
// 添加到 claude_desktop_config.json 或 cursor settings
{
  "mcpServers": {
    "mineru": {
      "command": "uvx",
      "args": ["mineru-mcp"],
      "env": {
        "MINERU_MODEL_DIR": "D:\\models\\magic-pdf"
      }
    }
  }
}
```

## 关键参数说明
| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `--backend pipeline` | 快速稳定，CPU可跑 | 日常使用 |
| `--backend hybrid` | 高精度，支持图像分析 | 重要文档 |
| `--backend vlm` | 最高精度，需GPU | 学术PDF |
| `--chunk-size` | 文本切块大小 | 800 |
| `--collection` | ChromaDB集合名 | course_docs |

## 注意事项
- 模型文件较大（~2GB），必须下载到 D 盘：`$env:MAGIC_PDF_MODEL_DIR = "D:\models\magic-pdf"`
- 首次运行会自动选择最佳模型源（国内优先华为云/阿里云镜像）
- Windows 下推荐使用 `hybrid` 后端（比 pipeline 快 90%）
- 向量库数据自动保存至 `D:\git-projects\Socrates-Cube\chroma_db`
