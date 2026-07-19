---
kind: external_dependency
name: 腾讯云 TDSQL-C Serverless 数据库
slug: tencentcloud-tdsql-c
category: external_dependency
category_hints:
    - vendor_identity
    - client_constraint
scope:
    - '**'
source_files:
    - src/loopse/db/connection.py
    - scripts/init_mysql.py
---

### 身份与角色
- 项目的云端关系型数据库，替代本地 SQLite 实现多用户协作
- Serverless 架构，按实际用量计费，适合竞赛短期项目

### 连接配置
- 连接字符串格式：`mysql+pymysql://用户名:密码@外网地址:端口/数据库名?charset=utf8mb4`
- 默认字符集必须为 `utf8mb4` 以支持中文内容
- 端口号通常不是标准 3306，而是 60000+ 的高端口

### 关键约束
- Serverless 实例空闲时会暂停，首次连接有唤醒延迟
- 需要开启外网访问权限才能从本地开发环境连接
- 免费体验版不支持按量付费，需要使用独立的 TDSQL-C 实例
- MySQL 驱动需要额外安装 `pymysql` 和 `cryptography` 包