"""联邦学习模块（Federated Learning）。

在 Socrates-Cube 中，联邦学习用于：
1. 多机构协同优化 LinUCB 资源推荐模型（不共享原始用户数据）
2. 聚合来自不同虚拟"教育机构"的模型梯度，提升推荐精度
3. 完全在本地模拟联邦轮次（无需网络通信），演示联邦学习思想

架构设计：
  - FederatedServer：聚合各客户端上传的模型参数（FedAvg 算法）
  - FederatedClient：基于本地数据计算梯度更新（模拟一个教育机构）
  - FederatedRound：管理一轮联邦训练的完整流程
"""
from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# 模拟机构数（在实际部署中每个机构是独立服务器）
DEFAULT_NUM_CLIENTS = 5
DEFAULT_ROUNDS = 10
FEATURE_DIM = 8  # 对应 8 维用户画像特征


@dataclass
class ClientModel:
    """单个客户端（教育机构）持有的本地模型参数。"""
    client_id: str
    weights: list[float]          # 模型权重向量
    bias: float = 0.0
    local_samples: int = 0        # 本地样本数（用于加权聚合）
    training_loss: float = 1.0    # 本轮训练损失


@dataclass
class FederatedRoundResult:
    """一轮联邦训练的结果摘要。"""
    round_num: int
    num_clients: int
    global_weights: list[float]
    global_bias: float
    avg_loss: float
    accuracy_gain: float          # 相比上轮的精度提升估算
    privacy_budget_used: float    # 已使用的隐私预算（ε）


class FederatedClient:
    """模拟单个客户端（教育机构）的本地训练。"""

    def __init__(self, client_id: str, num_local_samples: int = 100):
        self.client_id = client_id
        self.num_local_samples = num_local_samples
        # 初始化随机权重（模拟未训练状态）
        self.weights = [random.gauss(0, 0.1) for _ in range(FEATURE_DIM)]
        self.bias = random.gauss(0, 0.01)

    def local_train(
        self,
        global_weights: list[float],
        global_bias: float,
        learning_rate: float = 0.01,
        local_epochs: int = 3,
        add_dp_noise: bool = True,
        noise_scale: float = 0.05,
    ) -> ClientModel:
        """基于全局模型执行本地训练（梯度下降模拟）。

        Args:
            global_weights: 全局模型权重（来自服务器）
            global_bias: 全局偏置
            learning_rate: 学习率
            local_epochs: 本地训练轮数
            add_dp_noise: 是否添加差分隐私噪声
            noise_scale: 高斯噪声标准差（差分隐私）

        Returns:
            训练后的本地模型参数
        """
        # 从全局模型开始本地训练
        w = list(global_weights)
        b = global_bias

        # 模拟本地数据梯度（简化为随机扰动表示真实数据影响）
        loss = 1.0
        for epoch in range(local_epochs):
            # 模拟梯度：基于本地数据的方向性更新
            grad_w = [
                random.gauss(0, 0.02) + 0.01 * (1 - abs(w[i]))
                for i in range(FEATURE_DIM)
            ]
            grad_b = random.gauss(0, 0.01)

            # 梯度更新
            w = [w[i] - learning_rate * grad_w[i] for i in range(FEATURE_DIM)]
            b = b - learning_rate * grad_b

            # 损失衰减模拟
            loss *= (1 - learning_rate * 0.3 * (1 + random.uniform(-0.1, 0.1)))

        # 差分隐私：在上传前添加高斯噪声（保护本地数据不被反推）
        if add_dp_noise:
            w = [w[i] + random.gauss(0, noise_scale) for i in range(FEATURE_DIM)]
            b += random.gauss(0, noise_scale * 0.5)

        return ClientModel(
            client_id=self.client_id,
            weights=w,
            bias=b,
            local_samples=self.num_local_samples,
            training_loss=max(0.01, loss),
        )


class FederatedServer:
    """联邦学习服务器：聚合客户端模型（FedAvg 算法）。"""

    def __init__(self, feature_dim: int = FEATURE_DIM):
        self.feature_dim = feature_dim
        self.global_weights = [0.0] * feature_dim
        self.global_bias = 0.0
        self.round_history: list[FederatedRoundResult] = []

    def aggregate(
        self,
        client_models: list[ClientModel],
        round_num: int = 1,
    ) -> FederatedRoundResult:
        """FedAvg 加权聚合：样本数越多权重越高。

        Args:
            client_models: 各客户端训练结果
            round_num: 当前联邦轮次

        Returns:
            本轮聚合结果
        """
        if not client_models:
            raise ValueError("No client models to aggregate")

        total_samples = sum(m.local_samples for m in client_models)
        if total_samples == 0:
            total_samples = len(client_models)

        # 加权平均（FedAvg）
        new_weights = [0.0] * self.feature_dim
        new_bias = 0.0
        for model in client_models:
            ratio = model.local_samples / total_samples
            for i in range(self.feature_dim):
                new_weights[i] += ratio * model.weights[i]
            new_bias += ratio * model.bias

        avg_loss = sum(m.training_loss for m in client_models) / len(client_models)

        # 估算精度提升（基于损失下降）
        prev_loss = self.round_history[-1].avg_loss if self.round_history else 1.0
        accuracy_gain = max(0.0, (prev_loss - avg_loss) / max(prev_loss, 0.001) * 100)

        # 更新全局模型
        self.global_weights = new_weights
        self.global_bias = new_bias

        result = FederatedRoundResult(
            round_num=round_num,
            num_clients=len(client_models),
            global_weights=[round(w, 6) for w in new_weights],
            global_bias=round(new_bias, 6),
            avg_loss=round(avg_loss, 4),
            accuracy_gain=round(accuracy_gain, 2),
            privacy_budget_used=round(0.1 * round_num, 2),  # ε 随轮次累积
        )
        self.round_history.append(result)

        logger.info(
            "[FedLearning] Round %d complete: clients=%d avg_loss=%.4f accuracy_gain=+%.2f%%",
            round_num, len(client_models), avg_loss, accuracy_gain
        )
        return result

    def get_training_summary(self) -> dict[str, Any]:
        """返回完整训练过程摘要。"""
        if not self.round_history:
            return {"status": "not_started"}

        initial_loss = self.round_history[0].avg_loss
        final_loss = self.round_history[-1].avg_loss
        total_improvement = round((initial_loss - final_loss) / max(initial_loss, 0.001) * 100, 2)

        return {
            "total_rounds": len(self.round_history),
            "num_clients": self.round_history[-1].num_clients,
            "initial_loss": initial_loss,
            "final_loss": final_loss,
            "total_improvement_pct": total_improvement,
            "final_weights": self.global_weights,
            "privacy_budget_total": self.round_history[-1].privacy_budget_used,
            "rounds": [
                {
                    "round": r.round_num,
                    "loss": r.avg_loss,
                    "gain_pct": r.accuracy_gain,
                    "privacy_budget": r.privacy_budget_used,
                }
                for r in self.round_history
            ],
        }


class FederatedLearningOrchestrator:
    """联邦学习完整流程编排器。"""

    def __init__(
        self,
        num_clients: int = DEFAULT_NUM_CLIENTS,
        num_rounds: int = DEFAULT_ROUNDS,
        add_dp_noise: bool = True,
    ):
        self.num_clients = num_clients
        self.num_rounds = num_rounds
        self.add_dp_noise = add_dp_noise

        # 创建虚拟教育机构客户端
        self.clients = [
            FederatedClient(
                client_id=f"institution_{i+1:02d}",
                num_local_samples=random.randint(50, 500),
            )
            for i in range(num_clients)
        ]
        self.server = FederatedServer()

    def run(self, learning_rate: float = 0.01, local_epochs: int = 3) -> dict[str, Any]:
        """执行完整联邦学习训练。

        Returns:
            完整训练摘要（含每轮loss曲线、最终精度提升等）
        """
        logger.info(
            "[FedLearning] 开始联邦训练: clients=%d rounds=%d dp=%s",
            self.num_clients, self.num_rounds, self.add_dp_noise
        )

        for round_num in range(1, self.num_rounds + 1):
            # 各客户端本地训练
            client_models = [
                client.local_train(
                    global_weights=self.server.global_weights,
                    global_bias=self.server.global_bias,
                    learning_rate=learning_rate,
                    local_epochs=local_epochs,
                    add_dp_noise=self.add_dp_noise,
                )
                for client in self.clients
            ]

            # 服务器聚合
            self.server.aggregate(client_models, round_num=round_num)

        return self.server.get_training_summary()

    def simulate_personalization(self, user_profile: dict[str, Any]) -> dict[str, Any]:
        """使用联邦模型对单个用户进行个性化资源推荐评分。

        基于全局模型对用户特征向量进行线性评分，
        模拟联邦学习在个性化推荐中的应用。
        """
        # 提取用户特征向量（8维画像）
        features = [
            user_profile.get("knowledge_level", 0.5),
            1.0 if user_profile.get("cognitive_style") == "practical" else 0.0,
            1.0 if user_profile.get("cognitive_style") == "visual" else 0.0,
            len(user_profile.get("weak_points", [])) / 20.0,  # 归一化
            user_profile.get("total_study_hours", 0) / 300.0,
            user_profile.get("streak_days", 0) / 60.0,
            1.0 if user_profile.get("learning_style") == "deep" else 0.0,
            random.uniform(0.3, 0.7),  # 实时特征（模拟）
        ]

        # 线性评分
        score = sum(w * f for w, f in zip(self.server.global_weights, features))
        score += self.server.global_bias
        # Sigmoid 映射到 [0, 1]
        score_normalized = 1 / (1 + math.exp(-score))

        return {
            "personalization_score": round(score_normalized, 4),
            "recommendation_confidence": round(0.6 + score_normalized * 0.3, 3),
            "model_trained_rounds": len(self.server.round_history),
            "contributing_institutions": self.num_clients,
        }


# 全局单例（懒加载）
_fl_instance: FederatedLearningOrchestrator | None = None


def get_federated_orchestrator() -> FederatedLearningOrchestrator:
    global _fl_instance
    if _fl_instance is None:
        _fl_instance = FederatedLearningOrchestrator()
        # 启动时自动运行一次训练（后台预热）
        try:
            _fl_instance.run()
        except Exception as e:
            logger.warning("[FedLearning] 预热训练失败: %s", e)
    return _fl_instance
