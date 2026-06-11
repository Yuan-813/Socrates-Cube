# Prompt 无硬编码合规检查清单

## 检查标准

- 所有可长期维护的 LLM Prompt 应优先放在 `config/prompts/` 下。
- Python 代码中的长 Prompt 只能作为兜底 fallback，并应保持短小、结构化。
- 每个核心 Agent 至少对应一个 prompt 文件或明确说明其规则型逻辑来源。
- Prompt 模板变量必须有 fallback，避免模板字段不一致导致运行时 KeyError。
- Prompt 不得包含 API Key、个人隐私、不可公开的课程资料全文。

## Agent 检查记录

| Agent | Prompt 文件 | 代码兜底 | 状态 |
| --- | --- | --- | --- |
| Orchestrator | `config/prompts/orchestrator/route.txt` | 有短兜底回复模板 | 通过 |
| Retriever | `config/prompts/retriever/search_query.txt` | 有查询扩展兜底 | 通过 |
| Diagnosis | `config/prompts/diagnosis/surface_error.txt`、`root_cause.txt`、`pattern_match.txt` | 已支持缺字段 fallback | 通过 |
| Profiler | `config/prompts/profiler/update_profile.txt` | 已支持 `current_profile_json/new_dialogue` 与旧字段兼容 | 通过 |
| ResourceGenerator | `config/prompts/resource_generator/generate_doc.txt`、`generate_exercise.txt`、`generate_code.txt` | 有短兜底 | 通过 |
| PathPlanner | `config/prompts/path_planner/plan_path.txt` | 当前主要为图谱规则型，无大段硬编码 Prompt | 通过 |
| Challenger | `config/prompts/challenger/challenge.txt` | 待联调 | 待验证 |

## 已修复问题

1. Diagnosis prompt 中存在 `{student_answer}`、`{reference_content}` 与代码字段不一致的问题，已通过格式化 fallback 避免 KeyError。
2. Profiler prompt 中存在 `{current_profile_json}`、`{new_dialogue}` 与旧代码字段不一致的问题，已做兼容。
3. 知识库检索不再依赖单一 ChromaDB，缺包时自动使用本地索引，避免 Prompt 得不到证据。

## 验证命令

```bash
python -m compileall src scripts
python -m pytest -q
python scripts/download_knowledge_sources.py --skip-existing
python scripts/ingest_docs.py --reset
```

## 后续约束

后续新增 Agent 时，必须同步补充三处内容：`config/prompts/<agent>/` 模板、Agent 输入输出字段说明、SSE 或 API 返回结构。超过 300 字的 Prompt 不应直接塞进 Python 代码；如确实需要 fallback，应说明原因并保证模板变量都有默认值。
