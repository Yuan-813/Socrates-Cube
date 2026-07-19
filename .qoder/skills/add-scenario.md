# Skill: 向情景化对话系统添加新场景

## 适用场景
- 添加新的计算机网络实战情景（如 SDN 控制器部署、云网络排障等）
- 修改现有场景的角色或剧情
- 调整场景难度和学习目标

## 涉及文件

| 文件 | 作用 |
|------|------|
| `src/loopse/agent/scenario_agent.py` | 后端场景定义（`_SCENARIOS` 字典） |
| `frontend/src/views/ScenarioView.vue` | 前端场景卡片展示（`SCENARIOS` 数组） |

## 当前已有场景（7个）

| ID | 名称 | 难度 |
|----|------|------|
| `enterprise_troubleshoot` | 企业网络排障 | 中级 |
| `team_networking` | 团队组网规划 | 中级 |
| `campus_lab` | 计算机网络实验课 | 入门 |
| `isp_fault` | 运营商网络故障排查（BGP黑洞） | 中级 |
| `datacenter_design` | 数据中心网络设计评审 | 进阶 |
| `security_incident` | DDoS 攻击应急响应 | 进阶 |
| `hcia_mock` | HCIA 认证备考答疑 | 入门 |

## 步骤一：在后端 `_SCENARIOS` 字典中添加新场景

位置：`src/loopse/agent/scenario_agent.py` → `_SCENARIOS` 字典（约第 22 行）

模板：
```python
"sdn_deployment": {
    "name": "SDN 控制器部署演练",
    "description": "模拟企业从传统网络迁移到 SDN 架构的全过程，学习 OpenFlow 协议和控制平面分离原理",
    "roles": {
        "network_architect": {
            "name": "网络架构师（林工）",
            "avatar": "🏛️",
            "system_prompt": (
                "你是负责 SDN 迁移方案设计的高级架构师，熟悉 OpenFlow 1.3/1.5 协议。"
                "讲解时强调控制平面与数据平面分离的核心价值，引用 RFC 7426（SDN layers）。"
                "会提到 ONOS/OpenDaylight 控制器的选型对比。"
            ),
        },
        "ops_engineer": {
            "name": "运维工程师（何工）",
            "avatar": "⚙️",
            "system_prompt": (
                "你是负责日常运维的工程师，对 SDN 迁移有些担忧。"
                "会提出实际运维问题：'控制器挂了怎么办？'、'现有设备支持 OpenFlow 吗？'。"
                "关注迁移期间的业务连续性和回滚方案。"
            ),
        },
        "learner": {
            "name": "旁观学员（你）",
            "avatar": "👨‍🎓",
            "system_prompt": (
                "你是正在学习 SDN 技术的学员，对 OpenFlow 和控制平面概念还不熟悉。"
                "可以随时提问，加深对 SDN 架构的理解。"
            ),
        },
    },
    "opening": "好的，我们今天讨论公司从传统三层架构向 SDN 架构迁移的方案...",
    "learning_points": [
        "SDN 控制平面与数据平面分离原理",
        "OpenFlow 协议消息类型（Packet-In/Packet-Out/Flow-Mod）",
        "ONOS vs OpenDaylight 控制器选型",
        "SDN 迁移策略与回滚方案",
    ],
},
```

## 步骤二：在前端 `SCENARIOS` 数组中添加对应卡片

位置：`frontend/src/views/ScenarioView.vue` → `const SCENARIOS = [...]` 数组（约第 8 行）

```typescript
{
  id: 'sdn_deployment',
  title: 'SDN 控制器部署演练',
  description: '从传统三层架构迁移到 SDN，学习 OpenFlow 协议和控制平面分离原理',
  roles: ['网络架构师', '运维工程师', '旁观学员（你）'],
  topic: 'SDN/OpenFlow 架构迁移',
  difficulty: '进阶',
  icon: '🌐',
  color: 'from-violet-500 to-purple-600',
},
```

> **关键**：`id` 字段必须与后端 `_SCENARIOS` 字典的 key 完全一致！

## 场景设计原则

1. **三角色设计**（推荐）：专家 + 质疑者 + 学员/旁观者，形成自然对话张力
2. **Learning Points 完整**：至少 3 个具体可测量的学习目标
3. **Opening 有钩子**：第一句话要引出主要矛盾或问题
4. **角色 system_prompt 分化**：各角色立场/关注点明显不同，避免同质化
5. **引用权威来源**：尽量在 system_prompt 中引用 RFC、华为白皮书、Cisco Design Guide

## 验证

添加后运行语法检查：
```powershell
python -c "import ast; ast.parse(open('src/loopse/agent/scenario_agent.py',encoding='utf-8').read()); print('OK')"
```

重启后端验证 API 返回新场景：
```bash
curl http://localhost:8000/api/v1/scenario/list | python -m json.tool
```
