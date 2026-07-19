"""
环境验证脚本
运行方式：python scripts/verify_env.py
成功输出：环境检查通过 [OK]
失败输出：列出所有缺失依赖和未配置的环境变量
"""

from __future__ import annotations

import os
import sys

# 确保从项目根目录运行时路径正确
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

errors: list[str] = []
warnings: list[str] = []

# Windows 控制台默认 GBK，避免 emoji 导致 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ─────────────────────────────────────────
# 1. Python 版本检查
# ─────────────────────────────────────────
_major, _minor = sys.version_info[:2]
if _major == 3 and _minor == 10:
    pass
elif _major == 3 and _minor >= 10:
    warnings.append(f"当前 Python {_major}.{_minor}，项目推荐 3.10，但通常可继续运行")
else:
    errors.append(f"Python 版本错误：当前 {_major}.{_minor}，需要 Python 3.10+")

# ─────────────────────────────────────────
# 2. 依赖包检查
# ─────────────────────────────────────────
_core_packages = {
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "pydantic": "pydantic",
    "dotenv": "python-dotenv",
    "sqlalchemy": "sqlalchemy",
    "aiosqlite": "aiosqlite",
    "httpx": "httpx",
    "sse_starlette": "sse-starlette",
}

_optional_packages = {
    "chromadb": "chromadb",
    "langchain": "langchain",
}

_missing_core: list[str] = []
for import_name, pip_name in _core_packages.items():
    try:
        __import__(import_name)
    except ImportError:
        _missing_core.append(pip_name)

if _missing_core:
    errors.append(
        "缺少以下核心依赖（执行 pip install -r requirements.txt 安装）：\n"
        + "\n".join(f"    - {p}" for p in _missing_core)
    )

_missing_optional: list[str] = []
for import_name, pip_name in _optional_packages.items():
    try:
        __import__(import_name)
    except ImportError:
        _missing_optional.append(pip_name)

if _missing_optional:
    warnings.append(
        "以下可选依赖未安装（将使用本地 JSON 索引兜底，不影响基本检索）： "
        + ", ".join(_missing_optional)
    )

# ─────────────────────────────────────────
# 3. 环境变量检查
# ─────────────────────────────────────────
_env_file = os.path.join(_project_root, ".env")
if os.path.exists(_env_file):
    try:
        from dotenv import load_dotenv

        load_dotenv(_env_file)
    except ImportError:
        pass

_xunfei_vars = ["XUNFEI_APP_ID", "XUNFEI_API_KEY", "XUNFEI_API_SECRET"]
_spark_vars = ["SPARK_APP_ID", "SPARK_API_KEY", "SPARK_API_SECRET"]

def _configured(var: str) -> bool:
    val = os.getenv(var, "")
    return bool(val) and not val.endswith("_here")


_xunfei_ok = all(_configured(v) for v in _xunfei_vars)
_spark_ok = all(_configured(v) for v in _spark_vars)

if not (_xunfei_ok or _spark_ok):
    warnings.append(
        "讯飞 API Key 未配置，系统将使用 Mock LLM 模式。"
        "请编辑 .env 填入 XUNFEI_* 或 SPARK_* 变量。"
    )

if not os.path.exists(_env_file):
    warnings.append(".env 文件不存在，请执行：copy .env.example .env")

# ─────────────────────────────────────────
# 4. 知识库索引检查
# ─────────────────────────────────────────
_local_index = os.path.join(_project_root, "data", "vector_db", "local_index.json")
_misconceptions = os.path.join(_project_root, "data", "raw", "misconceptions.json")
_cleaned_dir = os.path.join(_project_root, "data", "cleaned")

_kb_counts: dict[str, int] = {}
try:
    from src.loopse.kb.vector_store import vector_store

    _kb_counts = {
        "course_docs": vector_store.count("course_docs"),
        "protocol_specs": vector_store.count("protocol_specs"),
        "misconceptions": vector_store.count("misconceptions"),
    }
except Exception as exc:
    warnings.append(f"知识库模块加载失败：{exc}")

    if _kb_counts:
        if _kb_counts.get("course_docs", 0) < 30 or _kb_counts.get("misconceptions", 0) < 20:
            errors.append(
                "知识库未入库或数据不足（course_docs 需 >=30，misconceptions 需 >=20）。\n"
                "    请依次执行：\n"
                "    python scripts/download_knowledge_sources.py\n"
                "    python scripts/ingest_docs.py --reset"
            )
else:
    if not os.path.exists(_local_index):
        if not os.path.isdir(_cleaned_dir) or not os.path.exists(_misconceptions):
            errors.append(
                "知识库尚未初始化。请依次执行：\n"
                "    python scripts/download_knowledge_sources.py\n"
                "    python scripts/ingest_docs.py --reset"
            )
        else:
            errors.append(
                "已找到原始资料，但尚未建立检索索引。请执行：\n"
                "    python scripts/ingest_docs.py --reset"
            )

# ─────────────────────────────────────────
# 5. 输出结果
# ─────────────────────────────────────────
print("=" * 50)
print("  Socrates-Cube 环境检查")
print("=" * 50)

if warnings:
    print("\n[WARN] 提示（不影响基本运行）：")
    for w in warnings:
        print(f"  - {w}")

if errors:
    print("\n[FAIL] 发现以下问题，请修复后重新运行：\n")
    for i, e in enumerate(errors, 1):
        print(f"  [{i}] {e}\n")
    print("=" * 50)
    sys.exit(1)

print("\n环境检查通过 [OK]")
print(f"  Python: {sys.version.split()[0]}")
print(f"  项目根目录: {_project_root}")
if _kb_counts:
    print(
        "  知识库索引: "
        f"course_docs={_kb_counts.get('course_docs', 0)}, "
        f"protocol_specs={_kb_counts.get('protocol_specs', 0)}, "
        f"misconceptions={_kb_counts.get('misconceptions', 0)}"
    )
print("=" * 50)
