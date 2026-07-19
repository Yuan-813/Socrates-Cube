# OpenMAIC PBL 互动课堂生成技能

## 描述
基于 OpenMAIC v0.3.0 (https://github.com/THU-MAIC/OpenMAIC) 的 PBL（Project-Based Learning）项目式学习场景，在 Socrates-Cube 中生成计算机网络教学互动课程。

OpenMAIC 是清华多智能体互动课堂开源框架，v0.3.0 新增 PBL v2、AI 编辑器 Agent、PPTX/HTML 导出、@openmaic/* npm SDK。

## 触发场景
- 用户要求"生成互动课程"、"PBL 项目式学习"、"制作教学幻灯片"
- 用户说"帮我生成一节关于TCP/DNS/TLS的课"
- 需要生成可导出 .pptx/.html 的交互式课堂内容

## 课程模板列表（计算机网络专用）

| 模板 ID | 主题 | 类型 | 时长 | RFC |
|---------|------|------|------|-----|
| tcp_handshake | TCP三次握手/四次挥手 | 仿真+讲解 | 20min | RFC 9293 |
| dns_resolution | DNS域名解析全流程 | 图解 | 15min | RFC 1034 |
| osi_layers | OSI七层模型与协议栈 | 互动讲解 | 25min | - |
| tcp_congestion | TCP拥塞控制四阶段 | 仿真+讲解 | 30min | RFC 5681 |
| bgp_routing | BGP路径矢量路由 | 讲解 | 35min | RFC 4271 |
| pbl_network_troubleshoot | **PBL: 企业网络故障排查** | PBL项目 | 60min | RFC 2151 |
| pbl_tls_security | **PBL: TLS 1.3安全实践** | PBL项目 | 45min | RFC 8446 |

## API 调用方式

### 生成完整互动课程
```bash
POST /api/v1/lesson/generate
{
  "topic": "TCP 拥塞控制算法",
  "difficulty": 3,
  "slide_count": 6,
  "include_quiz": true,
  "include_simulation": true,
  "language": "zh"
}
```

### 使用预置 PBL 模板
```bash
GET /api/v1/lesson/templates
# 返回所有模板，包含 pbl_type 字段的为 PBL 项目式课程
```

### 生成单页幻灯片
```bash
POST /api/v1/lesson/slide
{
  "topic": "TCP 慢启动算法",
  "slide_type": "protocol",
  "context": "上一页介绍了拥塞窗口的定义..."
}
```

## PBL 课程结构（参考 OpenMAIC v0.3.0 PBL v2）

```json
{
  "lesson_id": "pbl_xxx",
  "type": "pbl",
  "stages": [
    {"stage": 1, "name": "情景引入", "duration_min": 5, "model_hint": "讲解Agent"},
    {"stage": 2, "name": "问题分析", "duration_min": 15, "model_hint": "苏格拉底追问"},
    {"stage": 3, "name": "实践操作", "duration_min": 25, "model_hint": "指导Agent"},
    {"stage": 4, "name": "成果展示", "duration_min": 10, "model_hint": "评价Agent"},
    {"stage": 5, "name": "总结复盘", "duration_min": 5, "model_hint": "总结Agent"}
  ],
  "export_formats": ["html", "pptx"],
  "rfc_refs": ["RFC 2151", "RFC 9293"]
}
```

## OpenMAIC 与 Socrates-Cube 集成点

| OpenMAIC 功能 | Socrates-Cube 对应模块 |
|--------------|----------------------|
| 多 Agent 协同讲解 | OrchestratorAgent + ChatPanel |
| 协议仿真场景 | SimulatorPlayer.vue + simulatorStore |
| AI 苏格拉底追问 | ChallengerAgent |
| 知识测验 | ExamView.vue + question API |
| 学习路径规划 | PathPlannerAgent |
| PPTX 导出 | export API |

## 关键文件
- `src/loopse/api/lesson.py` — 课程生成 API
- `frontend/src/views/LessonView.vue` — 前端展示
- `config/prompts/resource_generator/generate_script.txt` — 视频脚本生成 Prompt

## 注意事项
1. PBL 模板需要 `include_simulation=true` 才能触发仿真场景
2. 课程内容导出通过 `POST /api/v1/export/markdown` 实现（将 slide.content 拼接为 Markdown 后输入）
3. 每阶段可以指定不同的 LLM 模型（OpenMAIC v0.3.0 per-stage model routing）
