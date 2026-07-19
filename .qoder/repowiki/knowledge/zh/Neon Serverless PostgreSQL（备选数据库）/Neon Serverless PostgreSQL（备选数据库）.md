---
kind: external_dependency
name: Neon Serverless PostgreSQL（备选数据库）
slug: neon-postgresql
category: external_dependency
category_hints:
    - vendor_identity
    - migration_status
scope:
    - '**'
source_files:
    - src/loopse/db/connection.py
    - .env.example
---

### 身份与角色
- 作为关系型数据库的备选方案，提供免费的 Serverless PostgreSQL 服务
- 无需信用卡注册，支持 GitHub 账号快速登录

### 迁移状态
- 项目代码已支持 PostgreSQL 切换，但当前生产环境使用腾讯云 TDSQL-C
- 切换方式：修改 `.env` 中的 `DATABASE_URL` 指向 Neon 连接字符串
- 需要安装 `psycopg2-binary` 驱动包

### 连接特性
- 连接字符串格式：`postgresql://用户名:密码@ep-xxx.ap-southeast-1.aws.neon.tech/数据库名?sslmode=require`
- 默认区域选择亚太（新加坡）以获得最低延迟
- 支持零停机扩容和分支管理