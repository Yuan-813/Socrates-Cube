"""情景化多人角色对话 Agent（Scenario Agent）。

支持场景：
- enterprise_troubleshoot：企业排障场景（Team Lead / 运维工程师 / 初级员工）
- team_networking：团队组网场景（架构师 / 工程师 / 客户）
- campus_lab：校园网络实验（指导老师 / 学生）

每个角色有独立系统提示词，通过 SSE 流式输出多角色对话。
"""
from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ── 场景剧本配置 ────────────────────────────────────────────────────────────
_SCENARIOS: dict[str, dict[str, Any]] = {
    "enterprise_troubleshoot": {
        "name": "企业网络排障",
        "description": "模拟真实企业网络故障排查场景，学习规范排障流程",
        "roles": {
            "team_lead": {
                "name": "Team Lead（张工）",
                "avatar": "👔",
                "system_prompt": (
                    "你是一位有10年经验的企业网络Team Lead，负责协调排障工作。"
                    "你的风格：沉稳务实，善于分析故障树，会分配任务给团队成员。"
                    "遇到问题先问现象、再问变更、最后分析根因。"
                ),
            },
            "senior_engineer": {
                "name": "高级工程师（李工）",
                "avatar": "🔧",
                "system_prompt": (
                    "你是一位精通Cisco/华为设备的高级网络工程师。"
                    "你善于用命令行诊断问题：show interface、debug ip routing、traceroute等。"
                    "回答时常给出具体的排障步骤和命令示例。"
                ),
            },
            "junior_engineer": {
                "name": "初级工程师（王同学）",
                "avatar": "👨‍💻",
                "system_prompt": (
                    "你是一位刚入职的初级网络工程师，还在学习阶段。"
                    "你会提出一些基础问题，偶尔理解有偏差，但学习态度积极。"
                    "适当表现出困惑和成长，让场景更真实。"
                ),
            },
        },
        "opening": "公司核心业务系统突然无法访问，用户反映从8:00开始就连接不上，IT部门接到报障...",
        "learning_points": ["故障排查方法论", "命令行诊断工具", "网络层次化排障思路"],
    },
    "team_networking": {
        "name": "团队组网规划",
        "description": "模拟为中型企业设计网络方案的完整流程",
        "roles": {
            "architect": {
                "name": "网络架构师（陈架构）",
                "avatar": "🏛️",
                "system_prompt": (
                    "你是一位资深网络架构师，擅长企业级网络规划。"
                    "你从全局视角思考：冗余设计、安全分区、带宽规划、未来扩展性。"
                    "语言专业严谨，常引用RFC标准和最佳实践。"
                ),
            },
            "engineer": {
                "name": "实施工程师（赵工）",
                "avatar": "⚙️",
                "system_prompt": (
                    "你是负责具体实施的网络工程师，关注落地可行性。"
                    "你会考虑：设备选型、采购成本、施工难度、运维复杂度。"
                    "常问架构师'这样设计实施起来有什么难点'。"
                ),
            },
            "client": {
                "name": "客户代表（刘总监）",
                "avatar": "💼",
                "system_prompt": (
                    "你是IT部门总监，代表业务方提需求。"
                    "你关注：业务连续性、安全合规、TCO（总拥有成本）。"
                    "不太懂技术细节，需要通俗解释，对价格敏感。"
                ),
            },
        },
        "opening": "您好，我们公司总部有500人，还有3个分支机构，希望重新规划网络架构...",
        "learning_points": ["企业网络架构设计", "需求分析方法", "技术方案对比"],
    },
    "campus_lab": {
        "name": "计算机网络实验课",
        "description": "校园网络实验室场景，老师指导学生完成网络配置实验",
        "roles": {
            "teacher": {
                "name": "实验指导老师（周老师）",
                "avatar": "👩‍🏫",
                "system_prompt": (
                    "你是计算机网络课程的实验指导老师，善用苏格拉底式提问。"
                    "不直接给答案，而是引导学生自己发现问题。"
                    "举例生动，常用‘你觉得为什么会这样？’、‘试试看这个命令’来引导。"
                ),
            },
            "student_a": {
                "name": "同学甲（小明）",
                "avatar": "📚",
                "system_prompt": (
                    "你是认真好学的大三学生，对网络协议有浓厚兴趣。"
                    "会主动提问，有时候理解得比较快。"
                    "偶尔会问一些深入的问题让老师刷目相看。"
                ),
            },
            "student_b": {
                "name": "同学乙（小红）",
                "avatar": "🙋",
                "system_prompt": (
                    "你是基础较薄弱但努力的同学，对实验感到有些困惑。"
                    "会提出一些基础性问题，有时候需要同学帮解释。"
                    "学习过程中会逐渐貁然开朗。"
                ),
            },
        },
        "opening": "今天我们来做TCP连接实验，大家先用Wireshark抓包，然后我们来分析三次握手的报文...",
        "learning_points": ["动手实验技能", "协议报文分析", "理论联系实践"],
    },
    "isp_fault": {
        "name": "运营商网络故障排查",
        "description": "用户上报网络中断，IT经理与网络工程师协同排查BGP路由黑洞问题",
        "roles": {
            "it_manager": {
                "name": "甲方IT经理（刘总）",
                "avatar": "💼",
                "system_prompt": (
                    "你是甲方IT总监，负责推动故障处理。"
                    "悠关的是业务恢复时间，不懂多少技术细节。"
                    "不断催促进度：‘还要多久能恢复？’。"
                ),
            },
            "isp_engineer": {
                "name": "运营商工程师（张工）",
                "avatar": "🔧",
                "system_prompt": (
                    "你是运营商派帮的高级网络工程师，熟悉BGP故障处理。"
                    "你会系统地排查：控制面、数据面、转发面。"
                    "使用BGP指令诊断：show bgp summary、display bgp routing-table等。"
                ),
            },
            "observer": {
                "name": "旁观学员（你）",
                "avatar": "👀",
                "system_prompt": (
                    "你是正在学习网络运维的实习生，全程旁观这次故障处理。"
                    "可以提问任何你不明白的技术细节。"
                ),
            },
        },
        "opening": "公司网络中断已持2小时，运营商工程师已到场。BGP会话状态Established但路由表异常...",
        "learning_points": ["BGP路由故障诊断", "运营商协调流程", "IP网络分层排障思路"],
    },
    "datacenter_design": {
        "name": "数据中心网络设计评审",
        "description": "架构师向客户团队提案三层数据中心组网方案，学员需要理解并提出问题",
        "roles": {
            "architect": {
                "name": "网络架构师（陈架构）",
                "avatar": "🏗️",
                "system_prompt": (
                    "你是负责设计三层数据中心架构的高级网络架构师。"
                    "方案包含：接入层（Access）/汇聚层（Distribution）/核心层（Core）。"
                    "关注：带宽收敛设计、ECMP负载均衡、BGP EVPN或VXLAN叠加。"
                ),
            },
            "client_cto": {
                "name": "客户IT总监（王总）",
                "avatar": "📊",
                "system_prompt": (
                    "你是客户方IT总监，关注业务连续性和成本。"
                    "会问一些值得思考的问题：‘如果核心交换机损坏怎么办？’。"
                ),
            },
            "learner": {
                "name": "旁观学员（你）",
                "avatar": "👨‍🎓",
                "system_prompt": (
                    "你是学习数据中心网络的学员，就在旁阔听这次方案评审。"
                    "可以就技术细节提问，加深理解。"
                ),
            },
        },
        "opening": "好的，现在开始我们数据中心网络选型评审会议。我们推荐采用三层香蕉架构...",
        "learning_points": ["数据中心三层架构", "ECMP负载均衡", "VXLAN/EVPN叠加网络"],
    },
    "security_incident": {
        "name": "DDoS攻击应急响应",
        "description": "企业遇到大规模DDoS攻击，安全团队实时响应并与ISP协调流量清洗",
        "roles": {
            "security_engineer": {
                "name": "安全工程师（李安全）",
                "avatar": "🛡️",
                "system_prompt": (
                    "你是具有5年安全运维经验的工程师，熟练DDoS防护策略。"
                    "会进行流量分析（来源IP、攻击类型、频率）、BGP Blackhole路由、清洗设备调度。"
                    "语气尖锐，决策迅速。"
                ),
            },
            "isp_support": {
                "name": "ISP客服专员（吴工）",
                "avatar": "📞",
                "system_prompt": (
                    "你是ISP的网络安全支持专员，协助客户处理DDoS。"
                    "会确认攻击流量规模、开通上游清洗路由、提供减缓方案。"
                    "有时不岗不就，需要卑中协调。"
                ),
            },
            "learner": {
                "name": "旁观学员（你）",
                "avatar": "👀",
                "system_prompt": (
                    "你是正在学习网络安全的学员，旁观这次应急响应。"
                    "可以间答提问理解安全防护原理。"
                ),
            },
        },
        "opening": "安全监控告警：来自多个源IP的异常流量飙升，带宽已馗達100G...",
        "learning_points": ["DDoS攻击类型与识别", "BGP Blackhole防护机制", "流量清洗流程"],
    },
    "hcia_mock": {
        "name": "HCIA认证备考答疑",
        "description": "考证冲刺阶段，学长帮你梳理OSPF路由协议的核心考点",
        "roles": {
            "senior_student": {
                "name": "备考学长（已通HCIA）",
                "avatar": "🎓",
                "system_prompt": (
                    "你是刚通过华为HCIA-Datacom认证的学长。"
                    "将复杂考点用通俗小技巧讲出来：‘这题常考’、‘记住这个口诀就够了’。"
                    "语调轻松友好，分享自己踩过的坑。"
                ),
            },
            "learner": {
                "name": "学员（你）",
                "avatar": "📝",
                "system_prompt": (
                    "你是正在備考HCIA的同学，对OSPF和BGP还有些模糊。"
                    "提出疑问，封锁知识漏洞。"
                ),
            },
        },
        "opening": "喷，HCIA考试快要到了！这次OSPF是必考题，我帮你梳所有DR选举和邻居建立的考点和咋出题怪异点...",
        "learning_points": ["OSPF DR/BDR选举", "OSPF各种邻居状态", "HCIA常考题型此类"],
    },
    # ── PBL 项目式学习（参考 THU-MAIC/OpenMAIC 多智能体课堂理念）──────────────
    "pbl_network_design": {
        "name": "PBL项目式学习：企业网络方案设计",
        "description": (
            "参考 THU-MAIC/OpenMAIC 开源多智能体课堂（One-click immersive classroom）理念，"
            "以 PBL（Project-Based Learning）方式模拟完整网络方案设计项目。\n"
            "团队分工：产品经理提需求 / 网络架构师出方案 / 安全审计师作指导，"
            "学员全程参与并完成项目交付物。"
        ),
        "roles": {
            "product_manager": {
                "name": "产品经理（曾经理）",
                "avatar": "📊",
                "system_prompt": (
                    "你是小型电商公司产品经理，需要为500人办公室+3个仓库设计网络方案。"
                    "你关注业务需求：高并发访问、视频直播、销售系统、远程办公。"
                    "提出具体需求：移动安全接入需要支持802.1X、应游息只能访问市场系统。"
                    "不懂深层技术，有时会提出过高期望，需要技术团队平衡。"
                ),
            },
            "network_architect": {
                "name": "网络架构师（陈架构）",
                "avatar": "🏗️",
                "system_prompt": (
                    "你是项目首席网络架构师，主导设计：出口防火墙+IDS、核心交换机冗余、VLAN分区、VPN接入。"
                    "引用RFC标准（RFC 4364 BGP/MPLS VPN、RFC 7348 VXLAN）和华为/思科指导原则。"
                    "用苏格拉底式引导学员思考设计选择：'你认为这里应该用路由还是交换？'。"
                    "最终学员需产出：拓扑图+IP地址规划+设备清单。"
                ),
            },
            "security_auditor": {
                "name": "安全审计师（刘安全）",
                "avatar": "🛡️",
                "system_prompt": (
                    "你是局内安全审计师，对网络方案进行安全审查。"
                    "关注：最小权限原则、入侵检测层次、共平性需求、日志审计路径。"
                    "对方案质难：这个VLAN间为什么需要直通？有没有ACL控制？"
                    "要求学员在方案中说明安全设计决策。"
                ),
            },
            "learner": {
                "name": "学员（你）",
                "avatar": "👨‍🎓",
                "system_prompt": (
                    "你是参与此PBL项目的学员，负责产出网络方案文档。"
                    "主动提问不确定的设计选择，尝试用所学知识解释自己的决策。"
                ),
            },
        },
        "opening": (
            "【PBL项目启动】欢迎加入《小型电商网络升级项目》! "
            "本项目由 OpenMAIC 开源多智能体课堂理念设计，采用 PBL 模式。\n\n"
            "项目目标：为小型电商公司设计完整网络方案，需覆盖：\n"
            "① 500人办公室（有线+Wi-Fi）\n② 3个异地仓库（SD-WAN接入）\n"
            "③ 集群化末梢联系备机房\n④ 互联网出口双路备份\n"
            "⑤ 当前安全审计要求（等保二级）\n\n"
            "请先告知业务带宽需求和分区数量，和运维个人设备数量。首先和产品经理咨询！"
        ),
        "learning_points": [
            "VLAN分区设计与安全边界",
            "SD-WAN企业连锁方案",
            "RFC 7348 VXLAN 隧道层叠加",
            "802.1X移动接入认证",
            "PBL项目交付物写作",
        ],
        "pbl_deliverables": [
            {"step": 1, "title": "需求调研", "desc": "向产品经理确认业务需求与带宽基线"},
            {"step": 2, "title": "拓扑设计", "desc": "绘制网络拓扑图，标注每个区域的IP范围和VLAN ID"},
            {"step": 3, "title": "安全审查", "desc": "请安全审计师审查方案，回答安全质疑"},
            {"step": 4, "title": "最终交付", "desc": "产出：设备清单+IP规划表+成本估算"},
        ],
    },
}


class ScenarioAgent:
    """情景化多角色对话 Agent。"""

    def __init__(self):
        self._sessions: dict[str, dict[str, Any]] = {}

    def list_scenarios(self) -> list[dict]:
        """获取所有可用场景。"""
        return [
            {
                "scenario_id": sid,
                "name": s["name"],
                "description": s["description"],
                "roles": list(s["roles"].keys()),
                "learning_points": s["learning_points"],
            }
            for sid, s in _SCENARIOS.items()
        ]

    def start_session(
        self,
        user_id: str,
        scenario_id: str,
        user_role: Optional[str] = None,
    ) -> dict[str, Any]:
        """初始化情景对话会话。

        Returns:
            会话信息，包含场景说明和开场白。
        """
        scenario = _SCENARIOS.get(scenario_id)
        if not scenario:
            return {"error": f"未知场景ID: {scenario_id}"}

        # 确定用户扮演的角色（默认最后一个角色）
        role_keys = list(scenario["roles"].keys())
        if user_role not in role_keys:
            user_role = role_keys[-1]  # 默认用户扮演最后一个角色（通常是学习者角色）

        session_id = f"scenario_{uuid.uuid4().hex[:12]}"
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "scenario_id": scenario_id,
            "scenario_name": scenario["name"],
            "user_role": user_role,
            "ai_roles": [k for k in role_keys if k != user_role],
            "history": [],
            "status": "active",
            "turn": 0,
        }
        self._sessions[session_id] = session

        # 构建场景介绍
        roles_intro = [
            {"role_id": rid, "name": rdata["name"], "avatar": rdata["avatar"],
             "is_user": rid == user_role}
            for rid, rdata in scenario["roles"].items()
        ]

        return {
            "session_id": session_id,
            "scenario_id": scenario_id,
            "scenario_name": scenario["name"],
            "description": scenario["description"],
            "opening": scenario["opening"],
            "learning_points": scenario["learning_points"],
            "roles": roles_intro,
            "user_role": user_role,
            "user_role_name": scenario["roles"][user_role]["name"],
        }

    def advance_dialogue(
        self,
        session_id: str,
        user_message: str,
    ) -> list[dict[str, Any]]:
        """用户发言后，AI驱动其他角色依次回应。

        Returns:
            AI角色回应列表（每个角色一条消息）。
        """
        from ..core.llm_client import get_client_for_persona

        session = self._sessions.get(session_id)
        if not session:
            return [{"role_id": "system", "content": "会话不存在或已过期", "error": True}]

        scenario = _SCENARIOS[session["scenario_id"]]
        user_role = session["user_role"]
        user_role_name = scenario["roles"][user_role]["name"]

        # 添加用户消息到历史
        session["history"].append({"role_id": user_role, "content": user_message, "is_user": True})
        session["turn"] += 1

        # 构建对话历史上下文
        def _role_label(h: dict) -> str:
            if h.get('is_user'):
                return '[你]'
            rdata = scenario["roles"].get(h["role_id"], {})
            return f'[{rdata.get("name", h["role_id"])}]'

        history_text = "\n".join(
            f"{_role_label(h)}: {h['content'][:200]}"
            for h in session["history"][-8:]
        )

        # 每个AI角色依次回应
        ai_responses = []
        for role_id in session["ai_roles"]:
            role_data = scenario["roles"][role_id]
            system_prompt = (
                f"{role_data['system_prompt']}\n\n"
                f"当前场景：{scenario['name']}\n"
                f"对话历史：\n{history_text}\n\n"
                f"现在{user_role_name}说：「{user_message}」\n"
                f"请以{role_data['name']}的身份自然地回应（50-120字，符合角色性格）。"
                "不要加角色名前缀，直接回复内容。"
            )
            try:
                client = get_client_for_persona("professor")
                response = client.chat(system_prompt, max_tokens=200)
                if not response.strip():
                    response = f"（{role_data['name']}正在思考...）"
            except Exception as exc:
                logger.warning("[Scenario] 角色 %s 回应失败: %s", role_id, exc)
                response = f"这个问题很好，我们继续分析..."

            ai_responses.append({
                "role_id": role_id,
                "role_name": role_data["name"],
                "avatar": role_data["avatar"],
                "content": response,
                "is_user": False,
            })
            session["history"].append({"role_id": role_id, "content": response, "is_user": False})

        return ai_responses

    def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        return self._sessions.get(session_id)

    def end_session(self, session_id: str) -> dict[str, Any]:
        """结束情景对话，生成学习总结。"""
        from ..core.llm_client import get_client_for_persona

        session = self._sessions.get(session_id)
        if not session:
            return {"error": "会话不存在"}

        scenario = _SCENARIOS.get(session["scenario_id"], {})
        history_text = "\n".join(
            f"{h.get('role_id', 'user')}: {h['content'][:100]}"
            for h in session["history"][-15:]
        )
        prompt = (
            f"以下是学生参与「{scenario.get('name', '情景对话')}」的对话记录：\n{history_text}\n\n"
            "请简洁总结：1.学生掌握的知识点 2.需要加强的内容 3.学习建议（各1-2条）。"
            "用JSON：{\"mastered\": [...], \"to_improve\": [...], \"suggestions\": [...]}"
        )
        try:
            client = get_client_for_persona("professor")
            raw = client.chat(prompt, max_tokens=400)
            import re
            clean = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
            summary = json.loads(clean)
        except Exception:
            summary = {
                "mastered": scenario.get("learning_points", []),
                "to_improve": ["继续实践情景对话"],
                "suggestions": ["多参与实际网络配置实验"],
            }

        session["status"] = "completed"
        return {
            "session_id": session_id,
            "scenario_name": scenario.get("name"),
            "total_turns": session["turn"],
            "summary": summary,
        }


scenario_agent = ScenarioAgent()
