"""
环境验证脚本
运行方式：python scripts/verify_env.py
成功输出：环境检查通过 ✅
失败输出：列出所有缺失依赖和未配置的环境变量
"""

import sys
import os

# 确保从项目根目录运行时路径正确
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

errors: list[str] = []
warnings: list[str] = []

# ─────────────────────────────────────────
# 1. Python 版本检查
# ─────────────────────────────────────────
_major, _minor = sys.version_info[:2]
if not (_major == 3 and _minor == 10):
    errors.append(f"Python 版本错误：当前 {_major}.{_minor}，需要 Python 3.10")

# ─────────────────────────────────────────
# 2. 依赖包检查
# ─────────────────────────────────────────
_required_packages = {
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "pydantic": "pydantic",
    "dotenv": "python-dotenv",
    "sqlalchemy": "sqlalchemy",
    "aiosqlite": "aiosqlite",
    "chromadb": "chromadb",
    "langchain": "langchain",
    "httpx": "httpx",
    "sse_starlette": "sse-starlette",
}

_missing_packages: list[str] = []
for import_name, pip_name in _required_packages.items():
    try:
        __import__(import_name)
    except ImportError:
        _missing_packages.append(pip_name)

if _missing_packages:
    errors.append(
        f"缺少以下依赖包（执行 pip install -r requirements.txt 安装）：\n"
        + "\n".join(f"    - {p}" for p in _missing_packages)
    )

# ─────────────────────────────────────────
# 3. 环境变量检查
# ─────────────────────────────────────────
# 加载 .env 文件（如果存在）
_env_file = os.path.join(_project_root, ".env")
if os.path.exists(_env_file):
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        pass  # dotenv 未安装，已在上方捕获

_required_env_vars = [
    "XUNFEI_APP_ID",
    "XUNFEI_API_KEY",
    "XUNFEI_API_SECRET",
    "XUNFEI_SPARK_URL",
]

_optional_env_vars = [
    "DATABASE_URL",
    "CHROMA_DB_PATH",
]

_missing_env: list[str] = []
for var in _required_env_vars:
    val = os.getenv(var, "")
    if not val or val.endswith("_here"):
        _missing_env.append(var)

if _missing_env:
    errors.append(
        f"以下必填环境变量未配置（请编辑 .env 文件填入真实值）：\n"
        + "\n".join(f"    - {v}" for v in _missing_env)
    )

for var in _optional_env_vars:
    if not os.getenv(var):
        warnings.append(f"可选环境变量 {var} 未设置，将使用默认值")

# ─────────────────────────────────────────
# 4. .env 文件存在性检查
# ─────────────────────────────────────────
if not os.path.exists(_env_file):
    errors.append(
        ".env 文件不存在，请执行：cp .env.example .env  然后填入 API Key"
    )

# ─────────────────────────────────────────
# 5. 输出结果
# ─────────────────────────────────────────
print("=" * 50)
print("  Socrates-Cube 环境检查")
print("=" * 50)

if warnings:
    print("\n⚠️  提示（不影响运行）：")
    for w in warnings:
        print(f"  • {w}")

if errors:
    print("\n❌ 发现以下问题，请修复后重新运行：\n")
    for i, e in enumerate(errors, 1):
        print(f"  [{i}] {e}\n")
    print("=" * 50)
    sys.exit(1)
else:
    print("\n环境检查通过 ✅")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  项目根目录: {_project_root}")
    print(f"  已配置环境变量: {', '.join(_required_env_vars)}")
    print("=" * 50)
