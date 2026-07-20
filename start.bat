@echo off
chcp 65001 >nul 2>&1
title Socrates-Cube — 苏格拉底方块

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║   Socrates-Cube  苏格拉底方块                   ║
echo  ║   多智能体自适应计算机网络学习系统               ║
echo  ║   第十五届中国软件杯  A3 赛项                   ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: ── 解析参数 ────────────────────────────────────────────
set MOCK_MODE_FLAG=0
if /i "%1"=="--mock-mode" set MOCK_MODE_FLAG=1
if /i "%1"=="-m"          set MOCK_MODE_FLAG=1

:: ── 定位项目根目录 ────────────────────────────────────
set "PROJ_DIR=%~dp0"
if "%PROJ_DIR:~-1%"=="\" set "PROJ_DIR=%PROJ_DIR:~0,-1%"
cd /d "%PROJ_DIR%"

:: ── 查找可用 Python（按优先级）────────────────────────
set "PYTHON_EXE="

:: 优先使用项目 venv（若存在且有效）
if exist ".venv\Scripts\python.exe" (
    if exist ".venv\pyvenv.cfg" (
        set "PYTHON_EXE=%PROJ_DIR%\.venv\Scripts\python.exe"
        echo [Python] 使用项目虚拟环境: .venv
        goto :python_found
    )
)

:: 尝试常见 Python 安装路径
for %%P in (
    "D:\Python3.12.7\python.exe"
    "D:\Python3.11\python.exe"
    "D:\Python3.10\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
) do (
    if exist %%P (
        set "PYTHON_EXE=%%~P"
        echo [Python] 使用: %%~P
        goto :python_found
    )
)

:: 最后尝试 PATH 中的 python
python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=python"
    echo [Python] 使用 PATH 中的 python
    goto :python_found
)

echo [错误] 未找到 Python 3.10+，请从 https://python.org/downloads 安装后重试
pause
exit /b 1

:python_found

:: ── 检查 Python 版本（需 3.10+）────────────────────────
for /f "tokens=2 delims= " %%v in ('"%PYTHON_EXE%" --version 2^>^&1') do set PY_VER=%%v
echo [检查] Python 版本: %PY_VER%

:: ── 安装依赖（首次运行）────────────────────────────────
"%PYTHON_EXE%" -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [1/3] 首次安装依赖，请耐心等待（约 3-5 分钟）...
    "%PYTHON_EXE%" -m pip install -r requirements.txt -q -i https://pypi.tuna.tsinghua.edu.cn/simple --no-warn-script-location
    if errorlevel 1 (
        echo       镜像源失败，尝试官方源...
        "%PYTHON_EXE%" -m pip install -r requirements.txt -q --no-warn-script-location
    )
) else (
    echo [1/3] 依赖已就绪
)

:: ── 初始化 .env 配置文件 ────────────────────────────────
if not exist ".env" (
    echo [2/3] 初始化配置文件...
    copy ".env.example" ".env" >nul 2>&1
)

:: ── 初始化数据库 ─────────────────────────────────────────
echo [3/3] 初始化数据库...
"%PYTHON_EXE%" scripts\init_db.py >nul 2>&1

:: ── 设置运行模式 ─────────────────────────────────────────
if "%MOCK_MODE_FLAG%"=="1" (
    echo  [模式] Mock 离线模式（不调用外部 API）
    set "MOCK_MODE=1"
) else (
    echo  [模式] 正常模式（调用讯飞星火 + 豆包 API）
    set "MOCK_MODE=0"
)

:: ── 延迟 4 秒后自动打开浏览器 ─────────────────────────
echo.
echo  ┌─────────────────────────────────────────────────┐
echo  │  系统启动中...                                   │
echo  │  访问地址：http://localhost:8000                 │
echo  │  API 文档：http://localhost:8000/docs            │
echo  │  按 Ctrl+C 停止服务                              │
echo  └─────────────────────────────────────────────────┘
echo.

start /b cmd /c "timeout /t 4 /nobreak >nul && start http://localhost:8000"

:: ── 启动后端（同时托管前端静态文件）─────────────────────
set "PYTHONPATH=%PROJ_DIR%"
"%PYTHON_EXE%" -m uvicorn src.loopse.main:app --host 0.0.0.0 --port 8000 --log-level info

if errorlevel 1 (
    echo.
    echo [错误] 服务启动失败，请检查上方错误信息
    echo        常见问题：
    echo          1) 端口 8000 被占用 → 关闭其他程序后重试
    echo          2) 依赖缺失 → 运行  python -m pip install -r requirements.txt
    echo          3) Python 版本不兼容 → 请使用 Python 3.10-3.12
    pause
)
