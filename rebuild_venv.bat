@echo off
chcp 65001 >nul 2>&1
echo === [1/4] 删除旧虚拟环境 ===
if exist .venv (
    rmdir /s /q .venv
    echo 旧虚拟环境已删除
) else (
    echo 无旧虚拟环境
)

echo === [2/4] 创建新虚拟环境 ===
D:\Python3.12.7\python.exe -m venv .venv
if errorlevel 1 (
    echo [错误] 虚拟环境创建失败
    pause
    exit /b 1
)
echo 虚拟环境创建成功

echo === [3/4] 升级 pip ===
.venv\Scripts\python.exe -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple -q

echo === [4/4] 安装项目依赖（约需3-5分钟）===
.venv\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [警告] 镜像源安装失败，尝试官方源...
    .venv\Scripts\python.exe -m pip install -r requirements.txt
)

echo.
echo === 验证核心依赖 ===
.venv\Scripts\python.exe -c "from fastapi import FastAPI; print('FastAPI OK')"
.venv\Scripts\python.exe -c "import pydantic; print('Pydantic OK:', pydantic.VERSION)"
echo.
echo === 依赖安装完成！===
pause
