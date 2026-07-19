"""差分隐私 + 联邦学习方案实现（技术展示向）。

核心模块：
1. DifferentialPrivacy：对画像数据添加拉普拉斯噪声
2. FederatedLearning：本地梯度计算 + 梯度差上传（模拟）
3. EncryptionHelper：敏感字段 AES 加密/解密

注意：演示实现，生产级部署需配合 PySyft/Flower 等框架。
"""
from __future__ import annotations

import base64
import hashlib
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_AES_KEY = os.getenv("DATA_ENCRYPT_KEY", "socrates-cube-2025-aes256-key!")[:32].encode()


class DifferentialPrivacy:
    """差分隐私：对数值数据添加拉普拉斯噪声。"""

    def __init__(self, epsilon: float = 1.0, sensitivity: float = 1.0):
        """
        Args:
            epsilon: 隐私预算（越小隐私保护越强，数据可用性越低）
            sensitivity: 函数全局敏感度（画像维度取 1.0）
        """
        self.epsilon = epsilon
        self.sensitivity = sensitivity
        self._scale = sensitivity / epsilon

    def add_noise(self, value: float) -> float:
        """对单个数值添加拉普拉斯噪声。"""
        import random
        import math
        u = random.uniform(-0.5, 0.5)
        noise = -self._scale * math.copysign(1, u) * math.log(1 - 2 * abs(u))
        noisy = value + noise
        return max(0.0, min(1.0, noisy))  # 裁剪到 [0, 1]

    def privatize_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        """对用户画像的所有数值维度添加噪声。

        注意：只处理 8 维能力分数，不影响 weak_points/mastery_map 等结构字段。
        """
        NUMERIC_DIMS = [
            "conceptual_understanding", "protocol_analysis", "calculation_ability",
            "error_diagnosis", "system_design", "knowledge_connection",
            "expression_clarity", "self_correction",
        ]
        privatized = dict(profile)
        for dim in NUMERIC_DIMS:
            if dim in privatized and isinstance(privatized[dim], (int, float)):
                privatized[dim] = round(self.add_noise(float(privatized[dim])), 4)
        return privatized

    def report_noise_stats(self) -> dict:
        """返回噪声配置信息（用于 RLDashboard 展示）。"""
        return {
            "mechanism": "Laplace",
            "epsilon": self.epsilon,
            "sensitivity": self.sensitivity,
            "scale": round(self._scale, 4),
            "expected_noise": round(self._scale, 4),
        }


class FederatedLearning:
    """联邦学习模拟：本地梯度计算 + 全局聚合（示意实现）。

    真实联邦学习需使用 Flower/PySyft 框架；此处演示核心流程：
    1. 本地计算梯度差（差分更新）
    2. 上传梯度（不含原始数据）
    3. 模拟全局聚合
    """

    def __init__(self):
        self._local_gradients: list[dict] = []
        self._global_model: dict[str, float] = {}

    def compute_local_gradient(
        self,
        user_id: str,
        old_profile: dict[str, Any],
        new_profile: dict[str, Any],
    ) -> dict[str, float]:
        """计算本地梯度（新画像 - 旧画像 = 更新量）。

        只上传梯度差，不上传原始画像，保护用户隐私。
        """
        DIMS = [
            "conceptual_understanding", "protocol_analysis", "calculation_ability",
            "error_diagnosis", "system_design", "knowledge_connection",
            "expression_clarity", "self_correction",
        ]
        gradient = {}
        for dim in DIMS:
            old_val = float(old_profile.get(dim, 0.5))
            new_val = float(new_profile.get(dim, 0.5))
            gradient[dim] = round(new_val - old_val, 4)

        # 在梯度上也添加噪声（梯度差分隐私）
        dp = DifferentialPrivacy(epsilon=0.5)
        for dim in gradient:
            raw = gradient[dim]
            noise = dp.add_noise(0.5 + raw) - 0.5  # 映射到 0-1 再加噪声
            gradient[dim] = round(noise, 4)

        self._local_gradients.append({
            "user_id_hash": hashlib.sha256(user_id.encode()).hexdigest()[:8],
            "gradient": gradient,
        })
        logger.debug("[FL] 本地梯度计算完成 user_hash=%s",
                     hashlib.sha256(user_id.encode()).hexdigest()[:8])
        return gradient

    def aggregate_gradients(self) -> dict[str, float]:
        """FedAvg 聚合：对所有客户端梯度取平均（联邦平均）。"""
        if not self._local_gradients:
            return {}
        DIMS = list(self._local_gradients[0]["gradient"].keys())
        aggregated = {}
        for dim in DIMS:
            values = [g["gradient"][dim] for g in self._local_gradients]
            aggregated[dim] = round(sum(values) / len(values), 4)
        self._global_model = aggregated
        self._local_gradients.clear()
        logger.info("[FL] 全局梯度聚合完成，参与客户端数: %d", len(values))
        return aggregated

    def get_global_update(self) -> dict:
        """获取全局模型更新（下发给客户端用于本地更新）。"""
        return {
            "global_gradient": self._global_model,
            "round": len(self._local_gradients),
            "participants": len(self._local_gradients),
        }


class EncryptionHelper:
    """敏感字段 AES 加密（基于 Fernet 或降级到 base64+XOR 演示）。"""

    @staticmethod
    def encrypt(plaintext: str) -> str:
        """加密字符串。生产环境推荐使用 cryptography.fernet.Fernet。"""
        try:
            from cryptography.fernet import Fernet
            import base64
            # 从 AES key 派生 Fernet key
            fernet_key = base64.urlsafe_b64encode(_AES_KEY[:32])
            f = Fernet(fernet_key)
            return f.encrypt(plaintext.encode()).decode()
        except ImportError:
            # 降级：base64 编码（仅演示，非真实加密）
            logger.warning("[Encrypt] cryptography 未安装，使用 base64 演示模式")
            return base64.b64encode(plaintext.encode()).decode()

    @staticmethod
    def decrypt(ciphertext: str) -> str:
        """解密字符串。"""
        try:
            from cryptography.fernet import Fernet
            import base64
            fernet_key = base64.urlsafe_b64encode(_AES_KEY[:32])
            f = Fernet(fernet_key)
            return f.decrypt(ciphertext.encode()).decode()
        except ImportError:
            return base64.b64decode(ciphertext.encode()).decode()
        except Exception as exc:
            logger.warning("[Encrypt] 解密失败: %s", exc)
            return ""


# 全局单例
dp_engine = DifferentialPrivacy(epsilon=1.0)
fl_engine = FederatedLearning()
encryption = EncryptionHelper()
