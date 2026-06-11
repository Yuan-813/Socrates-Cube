# Socrates-Cube 软件需求规格说明书 v1.0

## 1. 项目范围

Socrates-Cube 是面向《计算机网络》课程的智能学习系统。系统通过多智能体协作，为学生提供苏格拉底式问答、认知诊断、学习资源生成、个性化路径规划、学习画像维护和运行日志追踪。系统必须支持在线 LLM 模式和离线 Mock 模式，保证答辩或课堂演示时不会因为外部 API 不可用而完全失效。

## 2. 用户与场景

主要用户为学习计算机网络的高校学生、助教和课程教师。学生使用对话界面提出概念、协议流程、计算题和代码实践问题；助教关注诊断结果与路径推荐是否可解释；教师关注知识库来源、误区库质量、验收记录和系统稳定性。

## 3. 功能性需求

| 编号 | 需求 |
| --- | --- |
| FR-CHAT-01 | 系统应提供 `/api/v1/chat/stream` SSE 接口，支持 token 流式输出。 |
| FR-CHAT-02 | SSE 必须覆盖 `agent_start`、`agent_end`、`token`、`diagnosis`、`resource`、`path_update`、`done`、`error`。 |
| FR-DIAG-01 | 系统应提供三层诊断：表层错误、根因分析、误区模式匹配。 |
| FR-PROF-01 | 系统应维护八维学生画像与知识点 mastery_map。 |
| FR-LOG-01 | 每轮关键 Agent 调用应写入 `agent_logs`，便于回放和审计。 |

## 4. 数据与知识库需求

| 编号 | 需求 |
| --- | --- |
| FR-KB-01 | 知识库应包含课程文档、协议规范和常见误区三类集合。 |
| FR-KB-02 | 协议规范可使用 RFC Editor、IANA 等公开资料来源。 |
| FR-KB-03 | ChromaDB 不可用时，系统必须降级到本地索引检索。 |
| FR-KG-01 | `data/knowledge_graph.json` 应包含 `nodes` 和 `edges`，最小规模不少于 20 节点、18 边。 |
| FR-KG-02 | 知识点节点字段包括 `id`、`name`、`chapter`、`type`、`difficulty`、`estimated_time`、`keywords`、`description`。 |
| FR-KG-03 | 知识图谱应支持前置依赖查询、拓扑排序、薄弱前置知识筛选和关键词检索。 |

## 5. 资源生成与路径规划规格

### 5.1 资源生成

- FR-RG-01：系统应支持生成三类资源：知识文档 `doc`、练习题 `exercise`、代码示例 `code`。
- FR-RG-02：资源生成应基于检索证据、当前知识点、难度和诊断结果。
- FR-RG-03：生成结果应包含 `resource_id`、`resource_type`、`knowledge_point`、`title`、`content`、`metadata`、`created_at`。
- FR-RG-04：资源生成应写入数据库或资源仓储，前端资源标签页可即时展示。

### 5.2 学习路径规划

- FR-PP-01：路径规划应使用知识图谱前置依赖和拓扑排序。
- FR-PP-02：每个路径节点必须包含推荐理由 `recommendation_reason`。
- FR-PP-03：路径节点应包含 `status`、`current_mastery`、`prerequisites`、`prerequisites_met`、`suggested_resources`。
- FR-PP-04：默认路径节点数不超过 10，可通过 API 参数配置。
- FR-PP-05：路径规划结果应可通过 `PathTimeline` 和 `PathReasonModal` 展示。

## 6. 非功能性需求

- NFR-01：后端 `/health` 必须返回 200。
- NFR-02：单元测试应可在本地虚拟环境运行。
- NFR-03：外部依赖缺失时，应提供明确降级路径。
- NFR-04：不得把 `.env`、数据库文件、向量库文件、`__pycache__`、`.pyc` 提交到 Git。
- NFR-05：演示模式下，系统必须支持 Mock LLM 和 mock SSE 数据。

## 7. 验收标准

Phase 4 验收至少覆盖：多 Agent 协作对话、学习路径生成、画像更新、资源展示、Agent 状态栏、路径详情弹窗、后端健康检查、知识库三集合检索。具体验收结果记录在 `docs/results/phase4_acceptance_results.md`。
