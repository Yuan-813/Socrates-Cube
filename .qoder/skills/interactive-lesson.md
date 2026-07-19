# 互动课程生成技能（OpenMAIC 风格）

基于 OpenMAIC 多智能体互动课堂设计理念，为 Socrates-Cube 用户生成结构化网络协议互动课程。
OpenMAIC GitHub: https://github.com/THU-MAIC/OpenMAIC

## 触发条件

- 用户想系统学习某个网络协议或概念
- 用户需要准备授课材料或演示幻灯片
- 用户想要包含测验题的完整学习单元
- 参考预置课程模板开始学习

## 执行步骤

### 方式1：从预置模板开始
1. 调用 `GET /api/v1/lesson/templates`
2. 选择合适的模板（TCP握手、DNS解析、OSI模型等）
3. 基于模板向学生展示课程结构

### 方式2：自定义生成课程
1. 调用 `POST /api/v1/lesson/generate`
   ```json
   {
     "topic": "HTTP/2 多路复用原理",
     "difficulty": 2,
     "slide_count": 6,
     "include_quiz": true,
     "target_audience": "计算机网络课程学生"
   }
   ```
2. 系统生成包含以下内容的结构化课程：
   - **幻灯片组**：标题页+概念讲解+协议分析+图示+测验+总结
   - **测验题**：选择题（含答案和解析）
   - **RFC 引用**：每页关联标准文档
   - **视觉提示**：建议前端渲染的图形类型

### 方式3：生成单页幻灯片
1. 调用 `POST /api/v1/lesson/slide`
   ```json
   {
     "topic": "TCP 滑动窗口",
     "slide_type": "protocol",
     "context": "前一页介绍了流量控制概念"
   }
   ```

## 课程幻灯片类型

| 类型 | 说明 |
|------|------|
| `title` | 封面：标题+学习目标+重要性 |
| `concept` | 概念：定义+要点列表+类比 |
| `protocol` | 协议：报文格式+字段说明+流程 |
| `diagram` | 图示：时序图/状态机/拓扑图描述 |
| `quiz` | 测验：1-2道思考题 |
| `summary` | 总结：回顾+拓展+预告 |

## 预置课程模板

| ID | 标题 | 难度 | 预计时长 |
|----|------|------|---------|
| tcp_handshake | TCP三次握手与四次挥手 | 基础 | 20min |
| dns_resolution | DNS域名解析全流程 | 基础 | 15min |
| osi_layers | OSI七层模型与协议栈 | 入门 | 25min |
| tcp_congestion | TCP拥塞控制算法 | 进阶 | 30min |
| bgp_routing | BGP路径矢量路由协议 | 进阶 | 35min |

## 与 OpenMAIC 的关系

Socrates-Cube 借鉴了 OpenMAIC 的核心设计理念：
- **结构化课程生成**：从主题到完整幻灯片序列
- **多类型内容**：讲解+图示+测验的组合
- **RFC 标准引用**：每个知识点关联权威来源
- **难度分级**：1-5级覆盖入门到专家

区别：Socrates-Cube 专注计算机网络领域，集成了三层认知诊断和个性化学习路径。
