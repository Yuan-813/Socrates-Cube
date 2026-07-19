---
kind: external_dependency
name: 字节火山引擎 ARK 平台（备用LLM+视频生成）
slug: volcengine-ark
category: external_dependency
category_hints:
    - vendor_identity
    - sdk_real_api
scope:
    - '**'
source_files:
    - src/loopse/core/llm_client.py
    - .env.example
---

### 身份与角色
- 作为讯飞星火的备用 LLM 方案，通过 OpenAI 兼容接口接入
- 同时提供 Seedance 视频生成能力，用于 AI 教学视频制作

### 双用途集成
**文本生成（OpenAI兼容）**：
- BASE_URL: `https://ark.cn-beijing.volces.com/api/v3`
- 需要创建推理接入点（Endpoint），格式为 `ep-xxxxxxxx` 的接入点 ID
- 环境变量：`OPENAI_COMPAT_BASE_URL` / `OPENAI_COMPAT_API_KEY` / `OPENAI_COMPAT_MODEL`

**视频生成（Seedance）**：
- 专用 API Key 和模型 ID（如 `seedance-1-lite`）
- 环境变量：`ARK_VIDEO_API_KEY` / `ARK_VIDEO_MODEL`
- 用于生成同一个人物的动态教学视频

### 关键约束
- Doubao 模型需要先开通模型再创建推理接入点，不能直接使用模型名
- Seedance 视频模型在控制台"模型广场"的"视频生成"分类下查找
- 两个功能的 API Key 格式相同但用途不同，需要分别配置