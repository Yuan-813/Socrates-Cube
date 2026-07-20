@echo off
chcp 65001 >nul 2>&1
title Socrates-Cube — Mock 离线演示模式
echo.
echo  [离线演示模式] 不调用外部 API，适合无网络答辩现场
echo.
call "%~dp0start.bat" --mock-mode
