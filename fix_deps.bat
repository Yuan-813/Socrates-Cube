@echo off
chcp 65001 >nul 2>&1
echo === 修复 pydantic 版本冲突 ===
.venv\Scripts\pip.exe install --upgrade pydantic pydantic-core -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.
echo === 验证 fastapi 可导入 ===
.venv\Scripts\python.exe -c "import fastapi; print('fastapi ok: ' + fastapi.__version__)"
pause
