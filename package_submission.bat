@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo  Socrates-Cube 软件杯提交打包脚本
echo  使用方法：package_submission.bat [团队编号]
echo  示例：package_submission.bat 26001234
echo ============================================================
echo.

set TEAM_ID=%1
if "%TEAM_ID%"=="" (
    set /p TEAM_ID="请输入你的团队编号（如 26001234）："
)

if "%TEAM_ID%"=="" (
    echo 错误：未提供团队编号，退出。
    pause
    exit /b 1
)

echo 团队编号：%TEAM_ID%
echo.

set ROOT=d:\git-projects\Socrates-Cube
set OUT=%ROOT%\submission_packages
if not exist "%OUT%" mkdir "%OUT%"

REM ============================================================
REM 包1：作品安装/可执行文件  ->  [团队编号]作品.zip
REM ============================================================
echo [1/4] 正在打包 作品安装/可执行文件 (%TEAM_ID%作品.zip) ...

set PKG1_DIR=%OUT%\pkg1_work
if exist "%PKG1_DIR%" rmdir /s /q "%PKG1_DIR%"
mkdir "%PKG1_DIR%"

REM 复制后端核心
xcopy "%ROOT%\src"           "%PKG1_DIR%\src\"            /E /I /Q
xcopy "%ROOT%\config"        "%PKG1_DIR%\config\"         /E /I /Q
xcopy "%ROOT%\scripts\init_db.py"      "%PKG1_DIR%\scripts\" /I /Q
xcopy "%ROOT%\scripts\demo_warmup.py"  "%PKG1_DIR%\scripts\" /I /Q
xcopy "%ROOT%\scripts\ingest_docs.py"  "%PKG1_DIR%\scripts\" /I /Q
xcopy "%ROOT%\scripts\verify_env.py"   "%PKG1_DIR%\scripts\" /I /Q

REM 复制前端构建产物
xcopy "%ROOT%\frontend\dist"  "%PKG1_DIR%\frontend\dist\" /E /I /Q

REM 复制关键数据文件
mkdir "%PKG1_DIR%\data"
if exist "%ROOT%\data\knowledge_graph.json"          copy "%ROOT%\data\knowledge_graph.json"          "%PKG1_DIR%\data\" >nul
if exist "%ROOT%\data\misconceptions.json"           copy "%ROOT%\data\misconceptions.json"           "%PKG1_DIR%\data\" >nul
if exist "%ROOT%\data\certificate_exams.json"        copy "%ROOT%\data\certificate_exams.json"        "%PKG1_DIR%\data\" >nul
if exist "%ROOT%\data\demo_cases.json"               copy "%ROOT%\data\demo_cases.json"               "%PKG1_DIR%\data\" >nul
mkdir "%PKG1_DIR%\data\vector_db"
if exist "%ROOT%\data\vector_db\local_index.json"    copy "%ROOT%\data\vector_db\local_index.json"    "%PKG1_DIR%\data\vector_db\" >nul

REM 复制根文件
copy "%ROOT%\requirements.txt"   "%PKG1_DIR%\" >nul
copy "%ROOT%\.env.example"        "%PKG1_DIR%\" >nul
copy "%ROOT%\start.bat"           "%PKG1_DIR%\" >nul
copy "%ROOT%\start.sh"            "%PKG1_DIR%\" >nul
copy "%ROOT%\README.md"           "%PKG1_DIR%\" >nul
copy "%ROOT%\pyproject.toml"      "%PKG1_DIR%\" >nul
if exist "%ROOT%\docker-compose.yml" copy "%ROOT%\docker-compose.yml" "%PKG1_DIR%\" >nul
if exist "%ROOT%\Dockerfile"         copy "%ROOT%\Dockerfile"         "%PKG1_DIR%\" >nul

powershell -Command "Compress-Archive -Path '%PKG1_DIR%\*' -DestinationPath '%OUT%\%TEAM_ID%作品.zip' -Force"
echo    完成：%OUT%\%TEAM_ID%作品.zip
echo.

REM ============================================================
REM 包2：作品源码  ->  [团队编号]源码.zip
REM ============================================================
echo [2/4] 正在打包 作品源码 (%TEAM_ID%源码.zip) ...

set PKG2_DIR=%OUT%\pkg2_src
if exist "%PKG2_DIR%" rmdir /s /q "%PKG2_DIR%"
mkdir "%PKG2_DIR%"

REM 复制源码（排除大型构建产物和依赖）
xcopy "%ROOT%\src"        "%PKG2_DIR%\src\"       /E /I /Q
xcopy "%ROOT%\frontend\src"     "%PKG2_DIR%\frontend\src\"     /E /I /Q
xcopy "%ROOT%\frontend\public"  "%PKG2_DIR%\frontend\public\"  /E /I /Q
copy "%ROOT%\frontend\package.json"      "%PKG2_DIR%\frontend\" >nul
copy "%ROOT%\frontend\package-lock.json" "%PKG2_DIR%\frontend\" >nul
copy "%ROOT%\frontend\vite.config.ts"    "%PKG2_DIR%\frontend\" >nul
copy "%ROOT%\frontend\tsconfig.json"     "%PKG2_DIR%\frontend\" >nul
copy "%ROOT%\frontend\index.html"        "%PKG2_DIR%\frontend\" >nul
copy "%ROOT%\frontend\tailwind.config.js" "%PKG2_DIR%\frontend\" >nul
copy "%ROOT%\frontend\postcss.config.js"  "%PKG2_DIR%\frontend\" >nul

xcopy "%ROOT%\config"     "%PKG2_DIR%\config\"    /E /I /Q
xcopy "%ROOT%\scripts"    "%PKG2_DIR%\scripts\"   /E /I /Q
xcopy "%ROOT%\tests"      "%PKG2_DIR%\tests\"     /E /I /Q
xcopy "%ROOT%\docs"       "%PKG2_DIR%\docs\"      /E /I /Q

mkdir "%PKG2_DIR%\data"
if exist "%ROOT%\data\knowledge_graph.json"   copy "%ROOT%\data\knowledge_graph.json"   "%PKG2_DIR%\data\" >nul
if exist "%ROOT%\data\misconceptions.json"    copy "%ROOT%\data\misconceptions.json"    "%PKG2_DIR%\data\" >nul
if exist "%ROOT%\data\certificate_exams.json" copy "%ROOT%\data\certificate_exams.json" "%PKG2_DIR%\data\" >nul
if exist "%ROOT%\data\demo_cases.json"        copy "%ROOT%\data\demo_cases.json"        "%PKG2_DIR%\data\" >nul
mkdir "%PKG2_DIR%\data\vector_db"
if exist "%ROOT%\data\vector_db\local_index.json" copy "%ROOT%\data\vector_db\local_index.json" "%PKG2_DIR%\data\vector_db\" >nul

copy "%ROOT%\requirements.txt"    "%PKG2_DIR%\" >nul
copy "%ROOT%\.env.example"         "%PKG2_DIR%\" >nul
copy "%ROOT%\start.bat"            "%PKG2_DIR%\" >nul
copy "%ROOT%\start.sh"             "%PKG2_DIR%\" >nul
copy "%ROOT%\README.md"            "%PKG2_DIR%\" >nul
copy "%ROOT%\pyproject.toml"       "%PKG2_DIR%\" >nul
copy "%ROOT%\.gitignore"           "%PKG2_DIR%\" >nul
if exist "%ROOT%\docker-compose.yml" copy "%ROOT%\docker-compose.yml" "%PKG2_DIR%\" >nul
if exist "%ROOT%\Dockerfile"         copy "%ROOT%\Dockerfile"         "%PKG2_DIR%\" >nul

powershell -Command "Compress-Archive -Path '%PKG2_DIR%\*' -DestinationPath '%OUT%\%TEAM_ID%源码.zip' -Force"
echo    完成：%OUT%\%TEAM_ID%源码.zip
echo.

REM ============================================================
REM 包3：介绍PPT/演示视频和文档  ->  [团队编号]介绍.zip
REM ============================================================
echo [3/4] 正在打包 介绍材料 (%TEAM_ID%介绍.zip) ...

set PKG3_DIR=%OUT%\pkg3_intro
if exist "%PKG3_DIR%" rmdir /s /q "%PKG3_DIR%"
mkdir "%PKG3_DIR%"
mkdir "%PKG3_DIR%\docs"

REM 演示视频（如已录制，放在 docs/results/ 或项目根目录）
if exist "%ROOT%\docs\results\演示视频.mp4" (
    copy "%ROOT%\docs\results\演示视频.mp4" "%PKG3_DIR%\" >nul
    echo    找到演示视频：docs/results/演示视频.mp4
) else if exist "%ROOT%\演示视频.mp4" (
    copy "%ROOT%\演示视频.mp4" "%PKG3_DIR%\" >nul
    echo    找到演示视频：演示视频.mp4
) else (
    echo    警告：未找到演示视频！请手动将演示视频.mp4 复制到 %PKG3_DIR%\
)

REM 答辩PPT（如已制作）
if exist "%ROOT%\docs\results\答辩PPT.pptx" (
    copy "%ROOT%\docs\results\答辩PPT.pptx" "%PKG3_DIR%\" >nul
) else if exist "%ROOT%\答辩PPT.pptx" (
    copy "%ROOT%\答辩PPT.pptx" "%PKG3_DIR%\" >nul
) else (
    echo    警告：未找到答辩PPT！请手动将答辩PPT.pptx 复制到 %PKG3_DIR%\
)

REM 核心文档
if exist "%ROOT%\docs\requirements\SRS_final.md"              copy "%ROOT%\docs\requirements\SRS_final.md"              "%PKG3_DIR%\docs\需求规格说明书.md" >nul
if exist "%ROOT%\docs\architecture\系统开发说明书_final.md"    copy "%ROOT%\docs\architecture\系统开发说明书_final.md"    "%PKG3_DIR%\docs\" >nul
if exist "%ROOT%\docs\test\测试说明书_v1.md"                  copy "%ROOT%\docs\test\测试说明书_v1.md"                  "%PKG3_DIR%\docs\" >nul
if exist "%ROOT%\docs\deployment\操作手册_v1.md"              copy "%ROOT%\docs\deployment\操作手册_v1.md"              "%PKG3_DIR%\docs\" >nul
if exist "%ROOT%\docs\deployment\开源组件与AI工具说明.md"       copy "%ROOT%\docs\deployment\开源组件与AI工具说明.md"       "%PKG3_DIR%\docs\" >nul
copy "%ROOT%\README.md" "%PKG3_DIR%\docs\" >nul

powershell -Command "Compress-Archive -Path '%PKG3_DIR%\*' -DestinationPath '%OUT%\%TEAM_ID%介绍.zip' -Force"
echo    完成：%OUT%\%TEAM_ID%介绍.zip
echo.

REM ============================================================
REM 包4：报名表和学生证  ->  [团队编号]报名.zip
REM ============================================================
echo [4/4] 检查 报名材料 目录...
set PKG4_DIR=%OUT%\pkg4_registration
if not exist "%PKG4_DIR%" (
    mkdir "%PKG4_DIR%"
    echo    已创建目录：%PKG4_DIR%
    echo    请手动将以下文件放入该目录：
    echo      - 报名表.docx （从软件杯官网下载填写）
    echo      - 队长学生证.jpg
    echo      - 队员1学生证.jpg
    echo      - 队员2学生证.jpg（如有）
    echo    然后运行以下命令压缩：
    echo    powershell Compress-Archive -Path '%PKG4_DIR%\*' -DestinationPath '%OUT%\%TEAM_ID%报名.zip' -Force
) else (
    set /p PACK4_NOW="报名材料目录已存在，是否立即压缩？(y/n) "
    if /i "!PACK4_NOW!"=="y" (
        powershell -Command "Compress-Archive -Path '%PKG4_DIR%\*' -DestinationPath '%OUT%\%TEAM_ID%报名.zip' -Force"
        echo    完成：%OUT%\%TEAM_ID%报名.zip
    )
)

echo.
echo ============================================================
echo  打包完成！请检查以下文件：
echo  输出目录：%OUT%
echo ============================================================
dir "%OUT%\*.zip" 2>nul
echo.
echo 下一步：
echo   1. 将演示视频.mp4 和答辩PPT.pptx 放入 %PKG3_DIR%\ 后重新运行
echo   2. 将报名表和学生证放入 %PKG4_DIR%\ 后重新运行
echo   3. 登录 www.cnsoftbei.com 上传4个ZIP文件（截止：今天15:00）
echo.
pause
