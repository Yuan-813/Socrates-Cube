@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║   Socrates-Cube 多智能体自适应学习系统  一键启动   ║
echo  ║   用法: start.bat [--mock-mode]                      ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

:: 解析参数
set MOCK_MODE=0
if "%~1"=="--mock-mode" set MOCK_MODE=1

:: ============ 1. 后端启动 ============
echo [1/5] 检查 Python 环境...
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

if not exist .venv_new (
    echo [2/5] 创建虚拟环境...
    python -m venv .venv_new
) else (
    echo [2/5] 虚拟环境已存在
)

echo [3/5] 激活虚拟环境并安装依赖...
call .venv_new\Scripts\activate.bat
pip install -r requirements.txt -q 2>nul

if not exist .env (
    echo [提示] 复制环境配置文件...
    copy .env.example .env >nul
)

echo [4/5] 启动后端服务...
if %MOCK_MODE%==1 (
    echo       → 后端 Mock 模式启动中 ^(端口 8000^)
    start "Socrates-Backend" /min cmd /c ".venv_new\Scripts\activate.bat && set MOCK_MODE=1 && uvicorn src.loopse.main:app --host 0.0.0.0 --port 8000"
) else (
    echo       → 后端正常模式启动中 ^(端口 8000^)
    start "Socrates-Backend" /min cmd /c ".venv_new\Scripts\activate.bat && uvicorn src.loopse.main:app --reload --host 0.0.0.0 --port 8000"
)

:: 等待后端启动
echo       等待后端就绪...
timeout /t 3 /nobreak >nul

:: ============ 2. 前端启动 ============
echo [5/5] 启动前端服务...
cd frontend

if not exist node_modules (
    echo       安装前端依赖...
    call npm install --silent
)

if %MOCK_MODE%==1 (
    echo       → 前端 Mock 模式启动中 ^(端口 5173^)
    start "Socrates-Frontend" /min cmd /c "cd /d %~dp0frontend && npm run dev:mock"
) else (
    echo       → 前端正常模式启动中 ^(端口 5173^)
    start "Socrates-Frontend" /min cmd /c "cd /d %~dp0frontend && npm run dev"
)

cd ..

:: ============ 3. 显示启动信息 ============
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║                ✅ 启动完成！                         ║
echo  ╠══════════════════════════════════════════════════════╣
echo  ║  前端地址:  http://localhost:5173                    ║
echo  ║  后端地址:  http://localhost:8000                    ║
echo  ║  API 文档:  http://localhost:8000/docs               ║
if %MOCK_MODE%==1 (
echo  ║  运行模式:  Mock 模式（离线演示）                   ║
) else (
echo  ║  运行模式:  正常模式                                 ║
)
echo  ╠══════════════════════════════════════════════════════╣
echo  ║  按任意键停止所有服务                               ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

:: 健康检查
timeout /t 2 /nobreak >nul
curl -s http://localhost:8000/health >nul 2>&1
if %ERRORLEVEL%==0 (
    echo  [✓] 后端健康检查通过
) else (
    echo  [!] 后端尚未就绪，请稍后重试访问
)

echo.
echo  按任意键停止所有服务...
pause >nul

:: 清理
taskkill /fi "WINDOWTITLE eq Socrates-Backend*" /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq Socrates-Frontend*" /f >nul 2>&1
echo  服务已停止
