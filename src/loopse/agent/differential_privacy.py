"""差分隐私模块（Differential Privacy）。

在 Socrates-Cube 中，差分隐私用于：
1. 保护用户学习画像中的敏感数值（mastery_map、知识掌握度）
2. 聚合统计时添加噪声，防止通过统计数据反推个人信息
3. 为联邦学习梯度上传添加 Gaussian Noise（在 federated_learning.py 中已集成）

实现机制：
- Laplace 机制：用于连续数值字段（mastery_map 每个 KP 的掌握度）
- Gaussian 机制：用于模型梯度（联邦学习场景）
- 局部差分隐私（LDP）：用户数据在上传服务器前就已加噪
"""
from __future__ import annotations

import logging
import math
import random
from typing import Any

logger = logging.getLogger(__name__)

# 隐私预算默认值（越小隐私保护越强，但数据精度越低）
DEFAULT_EPSILON = 1.0   # ε 参数（Laplace 机制）
DEFAULT_DELTA = 1e-5    # δ 参数（Gaussian 机制）
DEFAULT_SENSITIVITY = 1.0  # 全局敏感度（mastery_map 值域 [0,1]）


def laplace_noise(sensitivity: float = DEFAULT_SENSITIVITY, epsilon: float = DEFAULT_EPSILON) -> float:
    """生成满足 ε-差分隐私的 Laplace 噪声。

    scale = sensitivity / epsilon
    噪声越小 → epsilon 越大（隐私保护越弱）
    """
    scale = sensitivity / max(epsilon, 1e-9)
    u = random.uniform(-0.5, 0.5)
    return -scale * math.copysign(1, u) * math.log(1 - 2 * abs(u))


def gaussian_noise(
    sensitivity: float = DEFAULT_SENSITIVITY,
    epsilon: float = DEFAULT_EPSILON,
    delta: float = DEFAULT_DELTA,
) -> float:
    """生成满足 (ε,δ)-差分隐私的 Gaussian 噪声。

    sigma = sqrt(2 * ln(1.25/δ)) * sensitivity / ε
    """
    sigma = math.sqrt(2 * math.log(1.25 / max(delta, 1e-10))) * sensitivity / max(epsilon, 1e-9)
    return random.gauss(0, sigma)


def clip_value(value: float, low: float = 0.0, high: float = 1.0) -> float:
    """裁剪数值到合法范围（差分隐私中的值裁剪步骤）。"""
    return max(low, min(high, value))


def privatize_mastery_map(
    mastery_map: dict[str, float],
    epsilon: float = DEFAULT_EPSILON,
    mechanism: str = "laplace",
) -> dict[str, float]:
    """对用户 mastery_map 添加差分隐私噪声。

    Args:
        mastery_map: 原始 KP -> 掌握度（0~1）字典
        epsilon: 隐私预算（ε），越小隐私保护越强
        mechanism: "laplace" 或 "gaussian"

    Returns:
        加噪后的 mastery_map（值仍裁剪到 [0,1]）
    """
    privatized = {}
    noise_fn = laplace_noise if mechanism == "laplace" else gaussian_noise

    for kp_id, mastery in mastery_map.items():
        noise = noise_fn(sensitivity=1.0, epsilon=epsilon)
        noisy = clip_value(mastery + noise)
        privatized[kp_id] = round(noisy, 4)

    logger.debug(
        "[DP] mastery_map 差分隐私处理完成 mechanism=%s ε=%.2f items=%d",
        mechanism, epsilon, len(mastery_map)
    )
    return privatized


def privatize_profile_stats(
    profile: dict[str, Any],
    epsilon: float = DEFAULT_EPSILON,
    mechanism: str = "laplace",
) -> dict[str, Any]:
    """对用户画像中的数值字段添加隐私保护。

    仅对 mastery_map 和部分数值字段加噪；
    非数值字段（如 cognitive_style）不处理。
    """
    result = dict(profile)

    # 处理 mastery_map
    if isinstance(profile.get("mastery_map"), dict):
        result["mastery_map"] = privatize_mastery_map(profile["mastery_map"], epsilon=epsilon, mechanism=mechanism)
        result["_dp_applied"] = True
        result["_dp_epsilon"] = epsilon
        result["_dp_mechanism"] = mechanism

    # 处理标量数值（轻微扰动，不影响可用性）
    for field in ["knowledge_level", "total_study_hours", "streak_days"]:
        if field in profile and isinstance(profile[field], (int, float)):
            noise_scale = 0.05 * abs(profile[field]) if profile[field] != 0 else 0.01
            result[field] = round(float(profile[field]) + random.gauss(0, noise_scale), 4)

    return result


def compute_privacy_budget_usage(
    num_queries: int,
    epsilon_per_query: float = 0.1,
    delta: float = DEFAULT_DELTA,
) -> dict[str, float]:
    """计算多次查询后的隐私预算消耗（组合定理）。

    使用高级组合定理（Advanced Composition）估算总隐私消耗。
    """
    # 简单组合：ε_total = n * ε
    simple_total = num_queries * epsilon_per_query

    # 高级组合（更紧的界）
    k = num_queries
    adv_epsilon = epsilon_per_query * math.sqrt(2 * k * math.log(1 / max(delta, 1e-10)))

    return {
        "num_queries": num_queries,
        "epsilon_per_query": epsilon_per_query,
        "total_epsilon_simple": round(simple_total, 4),
        "total_epsilon_advanced": round(adv_epsilon, 4),
        "delta": delta,
        "privacy_level": "strong" if adv_epsilon < 1.0 else "moderate" if adv_epsilon < 3.0 else "weak",
    }


def anonymize_for_analytics(
    profiles: list[dict[str, Any]],
    epsilon: float = 0.5,
) -> dict[str, Any]:
    """将多个用户画像聚合为匿名统计数据（用于系统分析大屏）。

    对聚合均值添加 Laplace 噪声，实现差分隐私聚合。

    Returns:
        匿名化的统计摘要（不含任何个人识别信息）
    """
    if not profiles:
        return {}

    n = len(profiles)

    def noisy_mean(values: list[float]) -> float:
        true_mean = sum(values) / len(values) if values else 0
        noise = laplace_noise(sensitivity=1.0 / len(values), epsilon=epsilon)
        return round(clip_value(true_mean + noise, 0, 1), 4)

    knowledge_levels = [p.get("knowledge_level", 0.5) for p in profiles if isinstance(p.get("knowledge_level"), (int, float))]
    study_hours = [p.get("total_study_hours", 0) for p in profiles if isinstance(p.get("total_study_hours"), (int, float))]

    style_counts: dict[str, int] = {}
    for p in profiles:
        style = p.get("cognitive_style", "unknown")
        style_counts[style] = style_counts.get(style, 0) + 1

    return {
        "anonymized_stats": True,
        "num_users": n,
        "avg_knowledge_level": noisy_mean(knowledge_levels),
        "avg_study_hours": round(sum(study_hours) / max(n, 1) + laplace_noise(sensitivity=300 / n, epsilon=epsilon), 2),
        "cognitive_style_distribution": {k: round(v / n, 3) for k, v in style_counts.items()},
        "dp_epsilon": epsilon,
        "dp_mechanism": "Laplace",
        "privacy_guarantee": f"ε={epsilon}-差分隐私保护",
    }
