================================================================
  Socrates-Cube（苏格拉底方块）运行说明
  第十五届中国软件杯 A3 赛项 — 基于大模型的个性化资源生成与学习多智能体系统开发
  出题企业：科大讯飞股份有限公司
================================================================

【环境要求】
  Python 3.10 或以上版本
  下载地址：https://www.python.org/downloads/
  安装时请勾选 "Add Python to PATH"

【三步启动（Windows）】

  第一步：解压本压缩包到任意目录（路径不含中文和空格）

  第二步：双击运行 start.bat
          ——首次运行会自动安装依赖（约 3-5 分钟，请耐心等待）
          ——看到 "Uvicorn running on http://0.0.0.0:8000" 即表示启动成功

  第三步：打开浏览器，访问
          http://localhost:8000

【三步启动（Linux / macOS）】

  chmod +x start.sh
  ./start.sh
  # 访问 http://localhost:8000

【离线演示（无网络环境）】

  Windows：双击 start_mock.bat
  或执行：  start.bat --mock-mode

  Linux：   ./start.sh --mock-mode

  离线模式使用预置 Mock 数据，全部功能可完整演示，无需连接外网。

【系统访问地址】

  前端界面：http://localhost:8000
  API 文档：http://localhost:8000/docs
  健康检查：http://localhost:8000/health

【演示建议（答辩用）】

  1. 启动后按 Ctrl+Shift+D 切换到演示模式（隐藏调试信息）
  2. 演示顺序：登录 → 对话提问 → 查看诊断 → 查看画像 → 学习路径 → 协议仿真 → 资源生成
  3. 按 Ctrl+Shift+C 可快速清空对话

【常见问题】

  Q: 端口 8000 被占用？
  A: 关闭占用进程，或修改 .env 中 APP_PORT=8001，然后重启

  Q: pip 安装超时？
  A: 脚本已自动切换清华镜像源；如仍超时，手动执行：
     pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

  Q: PowerShell 报"禁止执行脚本"？
  A: 改用 CMD 运行 start.bat，或执行：
     Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

  Q: 页面加载空白？
  A: 确认后端已正常启动（命令行无报错），刷新浏览器即可

【技术栈】

  后端：Python 3.10 + FastAPI + Uvicorn + SQLite
  前端：Vue3 + Vite + TypeScript + Element Plus + ECharts
  AI：  讯飞星火 X + 豆包（ARK）大模型
  多智能体框架：自研 Orchestrator + 8 专业 Agent 协同架构

================================================================
  如有问题，请参阅 docs/deployment/操作手册_v1.md
================================================================
