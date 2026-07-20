# 软件测试报告（STR）
# Software Test Report

| 文档标识 | SC-STR-001 |
|:---:|:---|
| 项目名称 | Socrates-Cube 多智能体自适应《计算机网络》学习系统 |
| 版本号 | v1.0 |
| 编制日期 | 2026-07-20 |
| 参考标准 | GB/T 8567-2006《计算机软件文档编制规范》 |
| 依赖文档 | SC-SRS-001（验收标准来源）|

---

## 第一章 引言

### 1.1 测试目的

本测试报告记录 Socrates-Cube 系统的测试活动、测试用例设计、测试执行结果和质量评估。测试主要覆盖以下方面：
1. 核心Agent逻辑的单元测试（pytest）
2. API接口的功能验证
3. 数据模型的结构完整性验证
4. 系统在不同降级模式下的可用性验证

### 1.2 测试范围

**测试覆盖范围**：
- DiagnosisAgent 三层诊断逻辑（unit tests）
- ResourceGeneratorAgent 三类资源生成（unit tests）
- StudentProfile Pydantic模型（unit tests）
- API路由层功能（功能验证）
- 前端构建验证（vue-tsc类型检查 + vite build）

**测试范围外**：
- 端到端UI自动化测试（未实现）
- 性能压力测试（未实现）
- 生产环境MySQL的切换验证（手动验证）

---

## 第二章 测试环境

### 2.1 硬件环境

| 环境项 | 配置 |
|---|---|
| 操作系统 | Windows 10/11（测试开发机） |
| CPU | x86-64，≥4核 |
| 内存 | ≥8GB RAM |
| 存储 | SSD，≥20GB可用空间 |

### 2.2 软件环境

| 软件 | 版本 |
|---|---|
| Python | 3.10.* |
| pytest | 8.2.0 |
| pytest-asyncio | 0.23.7 |
| Node.js | ≥18.0 |
| npm | ≥9.0 |
| Vue3 | 3.5.29 |
| TypeScript | 5.9.3 |
| vue-tsc | 2.2.12 |
| Vite | 5.4.21 |

### 2.3 测试数据

测试中使用的固定数据：
- 默认演示账号：`student-001`
- Mock LLM响应：诊断测试使用硬编码JSON字符串（见 test_diagnosis_agent.py fixtures）
- 知识节点ID：`kn_005`（TCP三次握手）、`kn_008`（拥塞控制）
- 误解条目：mc_001~mc_150（data/misconceptions.json）

---

## 第三章 测试策略

### 3.1 单元测试策略

使用 pytest 框架，测试文件位于 `tests/unit/` 和 `tests/` 目录。采用 Mock/Stub 替换外部依赖（LLM客户端、数据库），确保测试可在无LLM API密钥的环境下运行。

**Mock策略**：
```python
# 示例：Mock LLM客户端
agent.llm = MagicMock()
agent.llm.chat = MagicMock(return_value='{"is_correct": false, ...}')
```

### 3.2 AI功能测试策略

对于AI生成类功能（诊断、资源生成），测试不验证LLM生成内容的质量（取决于模型），而是验证：
- 返回数据的结构完整性（必要字段存在）
- 业务逻辑的正确性（如is_correct字段在特定输入下的预期值）
- 降级机制的正确行为（LLM失败时系统行为）

### 3.3 前端构建测试策略

使用 vue-tsc 进行TypeScript类型检查，使用 vite build 验证生产构建可成功完成，确保无编译时错误。

---

## 第四章 测试用例与结果

### 4.1 DiagnosisAgent 测试（tests/unit/test_diagnosis_agent.py）

**测试目标**：验证三层诊断逻辑的正确性

#### TC-DIAG-001：TCP握手次数错误检测

| 测试项 | 详情 |
|---|---|
| 测试类 | TestSurfaceErrorDetection |
| 测试方法 | test_detect_wrong_handshake_count |
| 输入 | student_answer="TCP需要两次握手才能建立连接", knowledge_point="TCP三次握手" |
| 预期结果 | result["has_error"] is True |
| 实际结果 | **PASSED** |

#### TC-DIAG-002：正确答案不触发错误

| 测试项 | 详情 |
|---|---|
| 测试类 | TestSurfaceErrorDetection |
| 测试方法 | test_correct_answer_passes |
| 输入 | student_answer="TCP通过三次握手建立连接，确保双方收发能力正常" |
| 预期结果 | result["has_error"] is False |
| 实际结果 | **PASSED** |

#### TC-DIAG-003：L2根因分析返回前置知识

| 测试项 | 详情 |
|---|---|
| 测试类 | TestRootCauseAnalysis |
| 测试方法 | test_returns_missing_prerequisites |
| 输入 | 错误类型"factual"，错误描述"握手次数错误" |
| 预期结果 | result包含"missing_prerequisites"键，值为list |
| 实际结果 | **PASSED** |

#### TC-DIAG-004：L3误区模式匹配

| 测试项 | 详情 |
|---|---|
| 测试类 | TestMisconceptionPatternMatch |
| 测试方法 | test_match_known_pattern |
| 输入 | error_type="factual", root_causes=["协议流程记忆不准确"] |
| 预期结果 | result为None或string类型 |
| 实际结果 | **PASSED** |

#### TC-DIAG-005：完整诊断流程集成测试

| 测试项 | 详情 |
|---|---|
| 测试方法 | test_full_diagnose_pipeline（异步，@pytest.mark.asyncio）|
| 输入 | student_answer="TCP两次握手就够了" |
| 预期结果 | 结果包含 is_correct / confidence / surface_error / root_causes（list）|
| 实际结果 | **PASSED** |

**小计**：5/5 PASSED

---

### 4.2 ResourceGeneratorAgent 测试（tests/unit/test_resource_generator.py）

**测试目标**：验证三类资源生成的结构完整性

#### TC-RES-001：知识文档生成

| 测试方法 | test_generate_doc（async）|
|---|---|
| 预期结果 | resource_type=="doc"，knowledge_point正确，len(content)>0，存在resource_id和created_at |
| 实际结果 | **PASSED** |

#### TC-RES-002：练习题生成

| 测试方法 | test_generate_exercise（async）|
|---|---|
| 预期结果 | resource_type=="exercise"，len(content)>0 |
| 实际结果 | **PASSED** |

#### TC-RES-003：代码示例生成

| 测试方法 | test_generate_code（async）|
|---|---|
| 预期结果 | resource_type=="code"，len(content)>0 |
| 实际结果 | **PASSED** |

#### TC-RES-004：资源结构完整性

| 测试方法 | test_result_schema（async）|
|---|---|
| 预期结果 | 返回值包含 resource_id/resource_type/knowledge_point/title/content/metadata/created_at 7个必填字段 |
| 实际结果 | **PASSED** |

**小计**：4/4 PASSED

---

### 4.3 StudentProfile Pydantic模型测试（tests/test_student_profile_schema.py）

**测试目标**：验证Pydantic模型的字段校验、边界值处理和序列化

#### TestKnowledgeDimension（4个测试）

| 测试方法 | 预期 | 实际 |
|---|---|---|
| test_default_instantiation | level默认3，desc默认"" | PASSED |
| test_level_boundary_valid | level=1/5均有效 | PASSED |
| test_level_boundary_invalid_low | level=0抛出异常 | PASSED |
| test_level_boundary_invalid_high | level=6抛出异常 | PASSED |

#### TestLearningProgress（3个测试）

| 测试方法 | 预期 | 实际 |
|---|---|---|
| test_default_instantiation | completed_topics=[]，completion_rate=0.0 | PASSED |
| test_with_data | 正常数据实例化成功 | PASSED |
| test_completion_rate_boundary_invalid | completion_rate=1.5抛出异常 | PASSED |

#### TestCommonMistakes（2个测试）

| 测试方法 | 预期 | 实际 |
|---|---|---|
| test_default_instantiation | types=[]，frequency={} | PASSED |
| test_with_data | 正常数据实例化成功 | PASSED |

#### TestStudentProfile（8个测试）

| 测试方法 | 预期 | 实际 |
|---|---|---|
| test_minimal_instantiation | 仅user_id即可实例化 | PASSED |
| test_default_dimensions | 6个维度有合理默认值 | PASSED |
| test_cognitive_style_default | 默认cognitive_style="textual" | PASSED |
| test_cognitive_style_enum_values | visual/textual/practical均有效 | PASSED |
| test_cognitive_style_invalid | unknown_style抛出异常 | PASSED |
| test_full_profile_instantiation | 完整字段实例化成功 | PASSED |
| test_json_serialization | model_dump_json()返回合法JSON | PASSED |
| test_dict_serialization | model_dump()包含所有必要键 | PASSED |

**小计**：17/17 PASSED

---

## 第五章 AI诊断功能专项测试

### 5.1 三层诊断准确率

**测试设计**：选取计算机网络领域常见错误类型，构建典型错误答案，验证DiagnosisAgent能否正确识别。

**验证项目**：

| 测试场景 | 输入 | 预期L1结果 | 验证方式 |
|---|---|---|---|
| TCP握手次数错误 | "两次握手就够了" | is_correct=False, error_type=factual | 硬规则保证零漏判 |
| 正确理解TCP握手 | "三次握手建立双向通道" | is_correct=True | Mock LLM测试 |
| L2前置知识定位 | 任意错误答案 | missing_prerequisites为列表 | 结构验证 |
| L3模式匹配输出 | 已知错误模式 | 返回pattern和intervention | 结构验证 |

### 5.2 Mock模式降级测试

**验证项目**：在LLM API密钥未配置的情况下（Mock模式），验证系统基础功能可用性。

| 验证项 | 结果 |
|---|---|
| GET /health 返回正常 | ✅ |
| POST /api/v1/chat/stream 推送token事件 | ✅（使用Mock预设内容）|
| POST /api/v1/resources/generate 返回资源 | ✅（使用Mock内容）|
| GET /api/v1/profile/{user_id} 返回画像 | ✅ |

---

## 第六章 测试结果统计

### 6.1 单元测试汇总

| 测试文件 | 测试数 | 通过 | 失败 | 错误 |
|---|---|---|---|---|
| test_diagnosis_agent.py | 5 | **5** | 0 | 0 |
| test_resource_generator.py | 4 | **4** | 0 | 0 |
| test_student_profile_schema.py | 17 | **17** | 0 | 0 |
| **合计** | **26** | **26** | **0** | **0** |

> **pytest 26 passed, 0 failed, 0 error**

### 6.2 前端构建测试

| 验证项 | 工具 | 结果 |
|---|---|---|
| TypeScript类型检查 | vue-tsc 2.2.12 | **0 errors** |
| 生产构建 | vite build 5.4.21 | **成功** |
| 构建输出 | frontend/dist/ | **正常生成** |

---

## 第七章 遗留问题与改进建议

### 7.1 已知测试覆盖不足项

| 问题 | 说明 |
|---|---|
| 端到端API测试缺失 | 未对 `/api/v1/chat/stream` 进行完整的端到端SSE流测试 |
| PathPlannerAgent测试缺失 | 路径规划算法（Kahn排序、掌握度估算）未有独立单元测试文件 |
| RetrieverAgent测试缺失 | 向量检索和TF-IDF降级未有独立测试 |
| ChromaDB集成测试缺失 | 向量库初始化和搜索仅通过手动验证 |
| 并发压力测试缺失 | 未进行多用户并发SSE请求的压力测试 |

### 7.2 改进建议

1. **增加端到端测试**：使用 httpx.AsyncClient 对FastAPI应用进行端到端API测试
2. **增加PathPlanner测试**：针对Kahn算法和mastery估算的单元测试
3. **增加RetrieverAgent测试**：TF-IDF降级路径的单元测试
4. **Mock ChromaDB**：在CI环境中Mock ChromaDB，避免依赖本地持久化文件

---

*本测试报告如实记录已执行的测试活动，所有PASSED结论均基于实际测试执行。未覆盖项已在第七章明确标注。*
