---
kind: external_dependency
name: 讯飞星火大模型（主LLM引擎）
slug: xunfei-spark
category: external_dependency
category_hints:
    - vendor_identity
    - auth_protocol
scope:
    - '**'
source_files:
    - src/loopse/core/llm_client.py
    - .env.example
---

### 身份与角色
- 本项目的主 LLM 推理引擎，用于对话、诊断、资源生成等所有 Agent 的文本生成能力
- 通过 `spark-ai-python` SDK 集成，支持 SSE 流式输出

### 认证协议
- 使用 HMAC-SHA256 签名：APPID + APIKey + APISecret
- 凭据注入位置：项目根目录 `.env` 文件中的 `XUNFEI_APP_ID` / `API_KEY` / `API_SECRET`
- 前端环境变量：`VITE_XUNFEI_DH_*` 系列（数字人功能）

### 关键集成点
- 自动降级机制：当 `sparkai` 包未安装或凭据无效时，自动回退到 Mock 模式
- SSE 流式处理：通过自定义 `_TokenCollector` 回调收集 token 并实时推送

### 已知约束
- AppID 需要单独开通星火认知大模型服务，否则返回 `AppIdNoAuthError (11200)`
- 不同版本端点（v3.5/v4.0 Ultra等）权限独立，需确认具体开通版本
- Windows 环境下可能需要跳过 SSL 证书验证才能正常连接