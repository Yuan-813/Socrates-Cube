"""pytest 全局配置：将项目根目录的 src/ 加入导入路径，配置 pytest-asyncio。"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))