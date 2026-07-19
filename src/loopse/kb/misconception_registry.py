"""误解库注册表：提供按 ID / 知识节点 / 错误类型 / 诊断输出的查询能力。"""
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class MisconceptionRegistry:
    """加载 misconceptions.json 并构建多维索引，支持快速查询。"""

    def __init__(self, json_path: str | Path | None = None):
        # 默认路径：项目根/data/misconceptions.json
        # 使用相对路径从项目根目录查找
        if json_path is None:
            # 尝试多种路径策略
            candidates = [
                Path("data/misconceptions.json"),
                Path(__file__).resolve().parents[3] / "data" / "misconceptions.json",
            ]
            for p in candidates:
                if p.exists():
                    json_path = p
                    break

        self._data: list[dict] = []
        self._by_id: dict[str, dict] = {}
        self._by_node: dict[str, list[dict]] = {}  # node_id -> [misconceptions]
        self._by_error_type: dict[str, list[dict]] = {}  # error_type -> [misconceptions]

        self._load(json_path)

    def _load(self, json_path):
        """加载JSON并构建索引"""
        try:
            path = Path(json_path) if json_path else None
            if path and path.exists():
                self._data = json.loads(path.read_text(encoding="utf-8"))
                self._build_indexes()
                logger.info("[MisconceptionRegistry] 加载 %d 条误解记录", len(self._data))
            else:
                logger.warning("[MisconceptionRegistry] 未找到 misconceptions.json: %s", json_path)
        except Exception as exc:
            logger.error("[MisconceptionRegistry] 加载失败: %s", exc)

    def _build_indexes(self):
        """构建倒排索引"""
        for mc in self._data:
            mc_id = mc.get("id", "")
            self._by_id[mc_id] = mc

            # 按知识节点索引
            for node_id in mc.get("knowledge_node_ids", []):
                self._by_node.setdefault(node_id, []).append(mc)

            # 按错误类型索引
            error_type = mc.get("error_type", "")
            if error_type:
                self._by_error_type.setdefault(error_type, []).append(mc)

    def get_by_id(self, mc_id: str) -> Optional[dict]:
        """精确查询：按误解ID"""
        return self._by_id.get(mc_id)

    def find_by_node(self, node_id: str) -> list[dict]:
        """反向查询：该知识节点关联的所有常见误解"""
        return self._by_node.get(node_id, [])

    def find_by_error_type(self, error_type: str) -> list[dict]:
        """按错误类型查询"""
        return self._by_error_type.get(error_type, [])

    def match_from_diagnosis(self, error_type: str, knowledge_point: str) -> Optional[dict]:
        """
        根据诊断输出匹配最佳误解条目。
        策略：
        1. 在同 error_type 的误解中，找 knowledge_point 关键词匹配度最高的
        2. 如果无匹配，扩大到全量搜索
        3. 仍无匹配返回 None
        """
        candidates = self._by_error_type.get(error_type, [])
        if not candidates:
            candidates = self._data

        if not knowledge_point:
            return candidates[0] if candidates else None

        # 关键词匹配打分
        best_match = None
        best_score = 0
        kp_lower = knowledge_point.lower()

        for mc in candidates:
            mc_kp = mc.get("knowledge_point", "").lower()
            # 精确匹配
            if mc_kp == kp_lower:
                return mc
            # 包含匹配
            score = 0
            if mc_kp in kp_lower or kp_lower in mc_kp:
                score = 3
            else:
                # 分词匹配
                for word in kp_lower.split():
                    if len(word) >= 2 and word in mc_kp:
                        score += 1

            if score > best_score:
                best_score = score
                best_match = mc

        return best_match if best_score > 0 else (candidates[0] if candidates else None)

    @property
    def count(self) -> int:
        return len(self._data)

    @property
    def all_misconceptions(self) -> list[dict]:
        return self._data


# 模块级单例
misconception_registry = MisconceptionRegistry()
