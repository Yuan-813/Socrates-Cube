# Phase 1 遗留问题记录

## Phase 1 遗留问题记录

| 问题ID | 问题描述 | 严重度 | 处理状态 |
|--------|---------|--------|---------|
| P1-001 | config/prompts 只有 profiler/extract_profile.txt，其余 7 个 Agent 目录未建立 | High | ✅ 在 Phase 2 补齐所有 prompt 文件 |
| P1-002 | README.md 存在中文编码显示问题 | Medium | ✅ 统一使用 UTF-8 编码保存 |
| P1-003 | SRS_v1.md 仅完成 80%，第 5 章缺失 | High | ✅ 在 Phase 4 补充第 5 章资源与路径规格 |
| P1-004 | 数据库初始化只有最小 4 表，无法支撑演示 | High | ✅ 扩展学生画像、学习资源、学习路径等业务表 |
| P1-005 | 知识库为空，检索 Agent 无法提供证据 | Critical | ✅ 创建 build_knowledge_base.py 一键构建脚本 |
| P1-006 | 星火 API 认证错误导致全链路无法跑通 | Critical | ✅ 完善 Mock 模式作为降级方案 |
| P1-007 | 缺少独立 coordinator.py 文件，逻辑合并进 Orchestrator | High | ✅ 抽离 coordinator.py 独立职责 |

## 清账总结

- **遗留问题总数**：7 个
- **Critical 级别**：2 个（P1-005、P1-006）
- **High 级别**：4 个（P1-001、P1-003、P1-004、P1-007）
- **Medium 级别**：1 个（P1-002）
- **已完成数量**：7 个
- **清账完成率**：100%
# Phase 1 遗留问题清账单

| 问题ID | 问题描述 | 严重度 | 根因分析 | 修复方案 | 验证方式 | 处理状态 | 修复日期 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P1-001 | 早期 Prompt 目录不完整，只有局部 Agent 模板 | High | 项目初期仅实现了核心 Agent，资源生成、路径规划等 Agent 的 Prompt 未同步配置 | 在 `config/prompts/` 下补齐所有 Agent 的 Prompt 模板文件，包含 diagnosis、resource_generator、path_planner、profiler、retriever、orchestrator | 检查 `config/prompts/` 目录文件数量与内容完整性 | 已完成 | 2025-07-10 |
| P1-002 | README 与部分中文注释存在编码显示问题 | Medium | Windows 与 Linux 编码差异导致中文注释乱码 | 统一使用 UTF-8 编码保存所有文档和代码文件，重写 README 确保中文显示正常 | 在 Windows PowerShell 和 Linux 终端分别验证 README 显示 | 已完成 | 2025-07-10 |
| P1-003 | SRS 文档未覆盖资源生成与路径规划 | High | Phase 1 仅完成核心对话和诊断功能，资源生成、路径规划在后续 Phase 实现 | 重构 SRS_v1.md，新增 Phase 3 独立章节（第5章），覆盖资源生成、路径规划、进阶路径规划等需求 | 检查 SRS 文档结构，验证 Phase 3 为独立第五章 | 已完成 | 2025-07-12 |
| P1-004 | 数据库初始化只有最小 4 表，无法支撑演示 | High | 初期仅设计了用户、会话、消息、日志基础表，缺少业务实体表 | 扩展数据库 Schema，新增学生画像、学习资源、学习路径、测评记录、误区库等数据表 | 运行 `scripts/init_db.py` 验证所有表创建成功 | 已完成 | 2025-07-11 |
| P1-005 | 知识库为空，检索 Agent 无法提供证据 | Critical | 新 clone 环境未执行知识库入库脚本，向量库无数据 | 1. 创建 `scripts/build_knowledge_base.py` 一键构建脚本<br>2. 支持 course_docs / protocol_specs / misconceptions 三集合<br>3. README 明确标注知识库入库为必做步骤 | 运行知识库构建脚本，验证三集合计数 > 0；调用检索 API 验证返回结果 | 已完成 | 2025-07-12 |
| P1-006 | 星火 API 认证错误导致全链路无法跑通 | Critical | 讯飞星火 API 凭据未正确配置或账号未完成认证 | 1. 完善 Mock 模式作为降级方案<br>2. `.env.example` 明确标注可选配置<br>3. 前端支持 Mock 模式与真实 SSE 模式切换 | 设置 `USE_MOCK_LLM=true` 验证对话功能正常；配置正确 API Key 验证真实模式 | 已完成 | 2025-07-10 |
| P1-007 | 缺少独立 coordinator.py 文件，逻辑合并进 Orchestrator | High | 初期将意图识别和路由逻辑直接写在 OrchestratorAgent 中，职责不清晰 | 抽离 `src/loopse/agents/coordinator.py`，实现 `AgentCoordinator` 类和 `DispatchPlan` 数据类，Orchestrator 仅调用其 dispatch 方法 | 检查 coordinator.py 是否独立存在；验证 Orchestrator 使用 coordinator.dispatch() | 已完成 | 2025-07-10 |

---

## 清账总结

- **遗留问题总数**：7 个
- **Critical 级别**：2 个（P1-005、P1-006）
- **High 级别**：4 个（P1-001、P1-003、P1-004、P1-007）
- **Medium 级别**：1 个（P1-002）
- **已完成数量**：7 个
- **清账完成率**：100%
