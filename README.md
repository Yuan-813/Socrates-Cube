# Socrates Cube Git 操作规范详解

# Socrates\-Cube

Education Agent AI

## 一、项目目录结构规范

```Plain Text
Socrates-Cube/
├── src/                      # 所有核心源代码（必须上传Git）
│   └── loopse/
│       ├── agent/            # 智能体核心模块
│       ├── prompt/           # 提示词模板归档
│       ├── schema/           # 数据结构定义
│       └── utils/            # 通用工具函数（含防幻觉、内容过滤）
├── scripts/                  # 启动脚本、工具脚本（必须上传Git）
├── config/                   # 系统配置文件（不含密钥，必须上传Git）
│   └── prompts/              # 配置文件子目录
├── tests/                    # 单元测试、集成测试用例（必须上传Git）
├── docs/                     # 全套项目文档、关键结果（必须上传Git）
│   ├── requirements/         # 系统需求规格说明书
│   ├── architecture/         # 系统架构与设计说明书
│   ├── test/                 # 软件质量保证与测试报告
│   ├── deployment/           # 部署与使用手册
│   ├── results/              # 项目成果归档(包括关键演示结果)
│   ├── references/           # 参考资料
│   └── 项目定位说明.md       # 核心项目定位文档
├── data/                     # 原始数据、知识库（不上传Git，关键演示结果）
├── outputs/                  # 临时输出文件（不上传Git）
├── .venv/                  # 虚拟环境（不上传Git）
├── .gitignore                # Git忽略规则（必须上传Git）
├── .env.example              # 环境变量模板（必须上传Git）
├── .env                    # API key等敏感信息（不上传Git，所有的密钥（AppID, API Secret）必须写在本地的 .env 文件里，并且让 .gitignore 忽略它。代码库里只允许提交一个空白的 .env.example 模板）
├── requirements.txt          # 项目依赖清单（必须上传Git）
├── pyproject.toml            # 项目配置文件（必须上传Git）
├── LICENSE*                  # 开源协议文件（必须上传Git）
└── README.md                 # 项目说明文档（必须上传Git）
```

## 二、Git 操作全流程规范

### 2\.1 每日开始工作（必做，杜绝代码冲突）

执行前确认：当前操作目录为项目根目录

```bash
# 1. 切换到开发主分支 dev
git checkout dev

# 2. 拉取远程仓库最新代码（同步团队修改）
git pull --rebase origin dev
```

### 2\.2 开发新功能 / 文档（分支创建规范）

**基于 dev 分支创建独立功能分支**（禁止直接在 dev 分支开发）

```bash
# 示例：创建学生智能体开发分支（命名规范：feature/功能名称）
git checkout -b feature/student-agent
```

### 2\.3 完成开发后提交代码（暂存与提交规范）

仅提交**必须纳入 Git**的目录 / 文件（src/scripts/config/tests/docs 及核心配置文件）

```bash
# 1. 查看文件修改状态
git status

# 2. 暂存项目核心文件（严格匹配目录规范）
git add src/ scripts/ config/ tests/ docs/
git add .gitignore .env.example requirements.txt pyproject.toml README.md LICENSE*

# 3. 本地提交（语义化提交信息）
git commit -m "feat: 完成学生智能体核心代码开发"
```

#### 2\.3\.1 commit 前缀规范（必做，评委查看 Git 历史加分项）

每次执行 `git commit \-m` 时，必须带上以下前缀，后缀说明清晰、简洁，贴合项目实际修改内容：

- `feat: `新功能（示例：`feat: 增加苏格拉底提问Agent（src/loopse/agent/）`、`feat: 开发学生6维画像抽取功能`）

- `fix: `修复问题（示例：`fix: 修复模型回复超时断连`、`fix: 修正docs/项目定位说明\.md格式错误`）

- `refactor: `代码重构（不改变功能，示例：`refactor: 重构多智能体协调器逻辑（src/loopse/agent/coordinator\.py）`）

- `docs: `文档更新（示例：`docs: 更新API接口说明文档（docs/requirements/）`、`docs: 完善项目定位说明\.md内容`）

- `test: `测试相关（示例：`test: 添加学生画像模块单元测试（tests/目录下）`）

- `chore: `配置、脚本等杂项（示例：`chore: 更新requirements\.txt依赖`、`chore: 完善\.gitignore规则`）

### 2\.4 推送分支到远程 GitHub

```bash
# 首次推送绑定远程分支
git push -u origin feature/student-agent

# 后续推送
git push origin feature/student-agent
```

### 2\.5 合并到 dev 分支前（必做，解决冲突）

```bash
# 1. 切回 dev 分支并同步最新代码
git checkout dev
git pull --rebase origin dev

# 2. 切回功能分支，合并 dev 最新代码
git checkout feature/student-agent
git rebase dev

# 3. 解决冲突后（如有），完成rebase并推送
git add .
git rebase --continue
git push -f origin feature/student-agent
```

### 2\.6 最终合并操作（PR 提交规范）

在 GitHub 仓库页面提交 **Pull Request \(PR\)**，申请将自己的 feature/fix 分支（均为 Git 开发分支，非项目目录）合并到 `dev` 分支，审核通过后完成合并，合并后可删除对应的 feature/fix 分支。

### 2\.7 Git 历史查看与导出规范

在项目根目录终端输入以下命令，即可查看所有人的改动历史：

```bash
# 简洁查看历史（每行一条记录，含commit id和说明）
git log --oneline

# 图形化查看历史（清晰展示分支合并记录）
git log --graph

# 导出完整提交历史(初赛提交用，证明原创性)
git log --pretty=format: "%h | %an | %ad | %s" --date=iso > git-commit-history.txt
```

导出的文件可以附在最终提交的文档中，向评委展示团队完整的开发过程。

也可直接登录 GitHub 网页端的 \&\#34;Commits\&\#34; 页面，以图形化方式清晰查看每一条提交记录和分支变动。

## 三、分支管理规范

项目分支严格按以下规则管理，杜绝违规操作导致代码混乱，所有分支操作均基于项目根目录执行：

- **main 分支：极其神圣**。仅存放随时可以打包展示的稳定版本，日常绝对不要直接往这里推代码、修改代码，仅通过 dev 分支合并更新。

- **dev 分支：日常集成分支**。我们三人的开发代码最终都在此分支进行联调、修复和集成，是日常开发的核心分支，禁止直接在该分支开发新功能。

- \**feature/* 分支：个人开发专属分支（Git 分支规范，非项目目录）\\*\\*。命名规范：`feature/姓名\-功能名`，例如开发路由功能，执行命令`git checkout \-b feature/张三\-router`；开发学生智能体功能，执行 `git checkout \-b feature/张三\-学生智能体`，所有新功能开发均在此类分支完成。

- **fix / 问题描述分支：bug 修复分支（Git 分支规范，非项目目录）**。当发现 dev 分支或 feature 分支存在 bug 时，基于对应分支创建此类分支，命名规范：`fix/问题描述`，例如 `fix/模型回复超时断连`，修复完成后合并回对应分支。

严格遵循分支命名规范，基于最新 dev 分支创建个人功能分支，禁止直接在 dev 或 main 分支开发。

### 3\.1 分支创建示例

```bash
# 示例1：开发学生智能体功能（替换为自己的姓名和功能名）
git checkout -b feature/张三-学生智能体

# 示例2：开发API接口文档（替换为自己的姓名和功能名）
git checkout -b feature/张三-API文档编写
```

## 四、补充规范

### 4\.1 新依赖添加规范

添加新依赖流程：谁安装了新的第三方包，必须立即执行 pip freeze \&gt; requirements\.txt 并提交 Git，确保所有人的依赖版本一致。

### 4\.2 代码、数据与结果分层管理规范

1. 代码和配置文件（如 src/, config/）全部上 Git。

2. 大体积数据（去哪存？）： 原始数据集、大模型权重等绝对不要放进 Git。对于大文件，建议存放在高性能台式机的本地硬盘中，同时在云端使用阿里云盘、百度网盘或团队自建 NAS 进行备份同步。

3. 结果产物： 用于论文、答辩或展示的关键结果（如架构图、测试报告），整理后必须存入项目的 docs/ 目录。

### 4\.3 团队角色规范

1. 系统架构及主要文档编写（维护 Git 主分支稳定；搭建微服务 / 多智能体框架；解决大模型防幻觉与内容安全过滤机制（赛题硬性非功能需求）。）

2. 智能体算法工程师、（负责构建 6 维度画像的 Prompt 流；开发多个协作 Agent；处理知识库数据的 Embedding 和检索；跑通 5 类多模态资源的生成。）

3. 前后端部署工程师（开发符合 AI 交互规范的 UI 界面（必须实现流式输出、Markdown 渲染、多模态卡片展示、生成进度追踪，绝不能让用户白屏等待）。）

### 4\.4 Git/GitHub 远程仓库使用规范

参考群里链接（远程地址在 Gitee 或 GitHub 上新建空仓库后，平台生成的一个 \.git 结尾的链接（[https://github\.com/Yuan\-813/Socrates\-Cube\.git](https://github.com/Yuan-813/Socrates-Cube.git) ）。这是我们所有人同步代码的 “中央服务器”。）

### 4\.5 重大改动通知规范

如果要修改核心接口（如 src/loopse/schema/ 下的数据结构）、重构架构（如多智能体协调逻辑）或删除公共模块（如 src/loopse/utils/ 下的通用工具函数），必须提前在群里说明，避免打断其他人的工作进度。

> （注：文档部分内容可能由 AI 生成）
