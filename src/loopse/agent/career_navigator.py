"""Career Navigator Agent（职业导航代理）。

分析用户当前能力画像与目标岗位之间的技能差距（GAP Analysis），
并结合知识图谱中的职业链路节点生成个性化职业学习路径。

主要能力：
1. 从知识图谱获取目标岗位的前置技能链
2. 对比用户 mastery_map 计算每个技能节点的 GAP
3. 调用 PathPlannerAgent 生成以职业为导向的学习路径
4. 输出可解释的 GAP 报告（含优先级排序）
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from ..kb.knowledge_graph import knowledge_graph, KnowledgeNode
from .path_planner import PathPlannerAgent

logger = logging.getLogger(__name__)

# 预定义岗位与核心前置技能链映射
# 用于快速 GAP 分析（无需完整遍历图谱）
JOB_SKILL_MAP: dict[str, dict[str, Any]] = {
    "job_001": {
        "name": "网络工程师",
        "core_kp_ids": ["kp_007", "kp_008", "kp_009", "kp_010", "kp_013", "kp_014", "kp_015"],
        "core_skill_ids": ["skill_001", "skill_002", "skill_003", "skill_006", "skill_007"],
        "recommended_cert": "cert_001",
        "description": "负责企业网络规划、部署与运维",
        "avg_salary": "15-30K/月",
        "key_skills": ["OSPF/BGP路由", "VLAN配置", "防火墙策略", "故障排查", "Wireshark分析"],
    },
    "job_002": {
        "name": "云计算网络工程师",
        "core_kp_ids": ["kp_007", "kp_010", "kp_015", "kp_019"],
        "core_skill_ids": ["skill_005", "skill_008", "skill_009", "skill_010"],
        "recommended_cert": "cert_002",
        "description": "负责云平台网络架构设计与运维",
        "avg_salary": "20-40K/月",
        "key_skills": ["SDN", "容器网络", "VPN/隧道", "Linux网络", "性能调优"],
    },
    "job_003": {
        "name": "网络安全工程师",
        "core_kp_ids": ["kp_014", "kp_018", "kp_019"],
        "core_skill_ids": ["skill_004", "skill_007", "skill_008"],
        "recommended_cert": "cert_003",
        "description": "负责企业网络安全防护与应急响应",
        "avg_salary": "18-35K/月",
        "key_skills": ["防火墙策略", "网络故障排查", "TLS/加密", "安全审计"],
    },
    "job_004": {
        "name": "DevOps工程师",
        "core_kp_ids": ["kp_015", "kp_018", "kp_019"],
        "core_skill_ids": ["skill_005", "skill_009"],
        "recommended_cert": "cert_005",
        "description": "负责软件交付与基础设施自动化",
        "avg_salary": "18-35K/月",
        "key_skills": ["容器网络", "Linux配置", "HTTP/HTTPS", "TCP调优"],
    },
    "job_005": {
        "name": "后端开发工程师",
        "core_kp_ids": ["kp_013", "kp_014", "kp_015", "kp_017", "kp_018"],
        "core_skill_ids": ["skill_001"],
        "recommended_cert": None,
        "description": "开发高性能后端服务，需深入理解网络协议",
        "avg_salary": "15-30K/月",
        "key_skills": ["TCP/IP原理", "HTTP协议", "DNS解析", "网络性能", "抓包调试"],
    },
}


class CareerNavigatorAgent:
    """职业导航代理：分析技能GAP并生成职业导向学习路径。"""

    def __init__(self):
        self._path_planner = PathPlannerAgent()

    def list_jobs(self) -> list[dict]:
        """返回所有支持的目标岗位列表。"""
        return [
            {
                "job_id": jid,
                "name": info["name"],
                "description": info.get("description", ""),
                "avg_salary": info.get("avg_salary", ""),
                "key_skills": info.get("key_skills", []),
                "recommended_cert": info.get("recommended_cert"),
            }
            for jid, info in JOB_SKILL_MAP.items()
        ]

    def analyze_gap(
        self,
        user_profile: dict[str, Any],
        target_job_id: str,
    ) -> dict[str, Any]:
        """分析用户当前画像与目标岗位的技能差距。

        Args:
            user_profile: 学生8维画像字典（含 mastery_map）
            target_job_id: 目标岗位 ID（如 job_001）

        Returns:
            GAP 报告字典
        """
        job_info = JOB_SKILL_MAP.get(target_job_id)
        if not job_info:
            return {"error": f"未知岗位 ID: {target_job_id}"}

        mastery_map: dict[str, float] = user_profile.get("mastery_map", {})
        core_kp_ids = job_info.get("core_kp_ids", [])
        core_skill_ids = job_info.get("core_skill_ids", [])

        # 计算 KP 节点的 GAP
        kp_gaps = []
        for nid in core_kp_ids:
            node = knowledge_graph.get_node(nid)
            if not node:
                continue
            mastery = knowledge_graph.estimate_mastery(nid, mastery_map)
            required = 0.65  # 岗位要求最低掌握度
            gap = max(0.0, required - mastery)
            kp_gaps.append({
                "node_id": nid,
                "node_name": node.name,
                "node_type": node.type,
                "current_mastery": round(mastery, 3),
                "required_mastery": required,
                "gap": round(gap, 3),
                "priority": self._calc_priority(gap, node.difficulty),
            })

        # 计算技能节点 GAP（技能节点没有 mastery_map 数据，默认 0）
        skill_gaps = []
        for sid in core_skill_ids:
            node = knowledge_graph.get_node(sid)
            if not node:
                continue
            mastery = float(mastery_map.get(sid, 0.0))
            gap = max(0.0, 0.6 - mastery)
            skill_gaps.append({
                "node_id": sid,
                "node_name": node.name,
                "node_type": "skill",
                "current_mastery": round(mastery, 3),
                "required_mastery": 0.6,
                "gap": round(gap, 3),
                "priority": self._calc_priority(gap, node.difficulty),
            })

        all_gaps = sorted(kp_gaps + skill_gaps, key=lambda x: x["gap"], reverse=True)
        total_gap = sum(g["gap"] for g in all_gaps)
        max_possible = len(all_gaps) * 0.65
        gap_score = round(1 - (total_gap / max_possible), 3) if max_possible > 0 else 1.0

        # 估算学习周数（每个 gap 单元约需 1-2 天）
        estimated_hours = sum(
            knowledge_graph.get_node(g["node_id"]).estimated_time / 60  # 小时
            for g in all_gaps
            if g["gap"] > 0.1 and knowledge_graph.get_node(g["node_id"])
        )
        estimated_weeks = max(1, round(estimated_hours / 10))  # 假设每周学10小时

        priority_gaps = [g for g in all_gaps if g["gap"] > 0.1]

        logger.info(
            "[CareerNavigator] GAP分析 job=%s gap_score=%.2f gap_nodes=%d",
            target_job_id, gap_score, len(priority_gaps)
        )

        return {
            "job_id": target_job_id,
            "job_name": job_info["name"],
            "gap_score": gap_score,
            "gap_level": self._gap_level(gap_score),
            "estimated_weeks": estimated_weeks,
            "total_gaps": len(priority_gaps),
            "priority_skills": [g for g in priority_gaps[:5]],
            "all_gaps": all_gaps,
            "recommended_cert": job_info.get("recommended_cert"),
            "current_strengths": [
                g for g in all_gaps if g["current_mastery"] >= 0.65
            ][:3],
        }

    def recommend_learning_path(
        self,
        user_id: str,
        user_profile: dict[str, Any],
        target_job_id: str,
        gap_report: Optional[dict] = None,
    ) -> dict[str, Any]:
        """根据 GAP 报告生成职业导向学习路径。

        Args:
            user_id: 用户 ID
            user_profile: 学生画像
            target_job_id: 目标岗位 ID
            gap_report: 预先生成的 GAP 报告（可选，省略则自动生成）

        Returns:
            学习路径字典（PathPlannerAgent.plan 格式）
        """
        if gap_report is None:
            gap_report = self.analyze_gap(user_profile, target_job_id)

        # 提取高优先级 GAP 节点作为路径目标
        priority_gaps = gap_report.get("priority_skills", [])
        target_node_ids = [g["node_id"] for g in priority_gaps if g["gap"] > 0.1]

        if not target_node_ids:
            # 无明显 GAP，使用岗位核心节点
            job_info = JOB_SKILL_MAP.get(target_job_id, {})
            target_node_ids = job_info.get("core_kp_ids", [])[:3]

        path = self._path_planner.plan(
            user_id=user_id,
            profile=user_profile,
            target_node_ids=target_node_ids,
            max_nodes=10,
        )

        # 附加职业导向元数据
        path["career_context"] = {
            "target_job_id": target_job_id,
            "target_job_name": gap_report.get("job_name", ""),
            "gap_score": gap_report.get("gap_score", 0),
            "estimated_weeks": gap_report.get("estimated_weeks", 4),
            "recommended_cert": gap_report.get("recommended_cert"),
        }

        logger.info(
            "[CareerNavigator] 职业路径生成完成 job=%s nodes=%d",
            target_job_id, len(path.get("nodes", []))
        )
        return path

    @staticmethod
    def _calc_priority(gap: float, difficulty: int) -> str:
        """计算优先级。"""
        score = gap * 2 + difficulty * 0.1
        if score > 0.8:
            return "high"
        elif score > 0.4:
            return "medium"
        else:
            return "low"

    @staticmethod
    def _gap_level(gap_score: float) -> str:
        """将 GAP 分数转换为文字等级。"""
        if gap_score >= 0.8:
            return "基础扎实，距目标岗位要求接近"
        elif gap_score >= 0.6:
            return "有一定基础，需重点补充核心技能"
        elif gap_score >= 0.4:
            return "基础薄弱，需系统学习多个模块"
        else:
            return "差距较大，建议从基础课程开始"


career_navigator = CareerNavigatorAgent()
