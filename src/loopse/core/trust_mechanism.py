"""TrustMechanism：系统可信机制 v1

三层防护：
1. 范围校验层：检测回答是否超出计算机网络范畴
2. 溯源标注层：为生成内容追加参考来源编号
3. 不确定性声明层：置信度低于阈值时自动追加声明
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Optional

from .llm_client import llm_client

logger = logging.getLogger(__name__)

_PROMPT_DIR = Path("config/prompts/trust")


def _load_prompt(name: str) -> str:
    p = _PROMPT_DIR / name
    try:
        return p.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


# 计算机网络领域关键词集合（用于范围校验）
_NETWORK_KEYWORDS = {
    "tcp", "udp", "ip", "http", "https", "dns", "ftp", "smtp", "ssh",
    "osi", "vlan", "arp", "icmp", "dhcp", "nat", "bgp", "ospf", "rip",
    "ethernet", "wi-fi", "wifi", "802.11", "802.3", "mac", "llc",
    "socket", "port", "subnet", "router", "switch", "hub", "gateway",
    "firewall", "proxy", "cdn", "tls", "ssl", "quic", "sctp",
    "拥塞", "握手", "挥手", "滑动窗口", "子网", "路由", "转发",
    "数据包", "报文", "帧", "比特", "协议", "端口", "地址",
    "网络层", "传输层", "应用层", "数据链路层", "物理层",
    "三次握手", "四次挥手", "序列号", "确认号", "窗口大小",
    "计算机网络", "因特网", "互联网", "局域网", "广域网",
}

# 强域外模式：人名社交/生活/娱乐（零容忍，优先匹配）
_STRICT_OFF_TOPIC = [
    r"(你认识|认识|你见过|你知道).{1,15}(吗|嘛|呢|吧)[\s\?？]*$",
    r"[\u4e00-\u9fa5]{2,6}(是谁|是什么人|哪里人|多大了|几岁)",
    r"^(你好|嗨|hello|hi|hey|哈喽|早安|晚安|早上好|晚上好|下午好)[\s！!。，,]*$",
    r"(你叫什么名字|你是谁|你是什么ai|你是哪个模型|你有没有意识|你有感情吗)",
    r"(我.{0,4}(难过|伤心|失恋|分手|暗恋|无聊|焦虑|抑郁)|帮我.{0,4}(写情书|写诗|作诗))",
    r"(推荐|介绍|评价).{0,6}(电影|电视剧|综艺|歌曲|音乐|小说|游戏|餐厅|菜|景点|旅游)",
    r"(今天|明天|后天).{0,4}(天气|几度|下雨|下雪|温度|气温)",
    r"(股票|基金|理财|投资|比特币|加密货币).{0,6}(行情|走势|推荐|分析)",
    r"(语文|物理|化学|历史|地理|生物).{0,6}(题|作业|考试|怎么学)",
    r"(帮我|请你|能不能).{0,8}(写|编).{0,6}(爬虫(?!.*协议)|购物网站|游戏|情书|日记)",
]

# 宽松闲聊模式：仅在0个网络关键词时才触发
_GENERAL_CHAT = [
    r"(你喜欢|你最喜欢|你偏好).{0,15}(吗|呢)[\?？]*$",
    r"(什么是|解释).{2,12}(定律|效应|现象|原理)(?!.*(网络|协议|数据|传输|分层))",
    r"[\u4e00-\u9fa5]{2,4}(是谁|哪里人|年龄|职业)[\?？]?",
]

_REJECT_MSG = (
    "抱歉，这个问题超出了我的服务范围。"
    "我专注于计算机网络课程辅导，可以帮你理解 TCP/IP、HTTP、DNS、路由协议、TLS 等网络知识。\n"
    "试试问我：「什么是 TCP 三次握手？」「HTTP 和 HTTPS 有什么区别？」"
)


class TrustMechanism:
    """系统可信机制，提供范围校验、溯源标注和不确定性声明。"""

    CONFIDENCE_THRESHOLD = 0.6  # 低于此值追加不确定性声明

    def __init__(self):
        self._scope_prompt = _load_prompt("scope_check.txt")
        self._citation_prompt = _load_prompt("source_citation.txt")

    # ------------------------------------------------------------------
    # 1. 范围校验层
    # ------------------------------------------------------------------

    def verify_scope(self, generated_content: str) -> dict[str, Any]:
        """判断回答是否在计算机网络范围内。

        Returns:
            {"in_scope": bool, "reason": str}
        """
        if not generated_content or not generated_content.strip():
            return {"in_scope": True, "reason": "空内容，无需校验"}

        # 快速关键词检测
        text_lower = generated_content.lower()
        hit_count = sum(1 for kw in _NETWORK_KEYWORDS if kw in text_lower)
        if hit_count >= 3:
            return {"in_scope": True, "reason": f"命中 {hit_count} 个网络领域关键词"}

        # LLM 辅助判断（当关键词命中不足时）
        prompt = self._format_scope_prompt(generated_content)
        try:
            raw = llm_client.chat(prompt, max_tokens=120)
            data = self._parse_json(raw, {"in_scope": True, "reason": "LLM 判断"})
            return {
                "in_scope": bool(data.get("in_scope", True)),
                "reason": data.get("reason", "LLM 辅助判断"),
            }
        except Exception as exc:
            logger.warning("[TrustMechanism] scope check LLM failed: %s", exc)
            # 降级为宽松策略
            return {"in_scope": True, "reason": "LLM 不可用，宽松放行"}

    def check_question_scope(self, question: str) -> dict[str, Any]:
        """校验用户问题是否在计算机网络范畴内。

        四层检测策略：
        1. 2+ 网络关键词 → 直接放行
        2. 强域外模式（人名/社交/娱乐/生活）→ 立即拒绝
        3. 1 个关键词 → 宽松放行
        4. 0 个关键词 + 宽松闲聊模式 → 拒绝，否则放行

        Returns:
            {"in_scope": bool, "reject_message": str | None}
        """
        if not question or not question.strip():
            return {"in_scope": False, "reject_message": "请输入有效的问题。"}

        text_lower = question.lower().strip()

        # 第一层：关键词快速放行
        hit_count = sum(1 for kw in _NETWORK_KEYWORDS if kw in text_lower)
        if hit_count >= 2:
            return {"in_scope": True, "reject_message": None}

        # 第二层：强域外模式（零容忍）
        for pattern in _STRICT_OFF_TOPIC:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return {"in_scope": False, "reject_message": _REJECT_MSG}

        # 第三层：1个关键词宽松放行
        if hit_count >= 1:
            return {"in_scope": True, "reject_message": None}

        # 第四层：0个关键词，检查宽松闲聊模式
        for pattern in _GENERAL_CHAT:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return {"in_scope": False, "reject_message": _REJECT_MSG}

        # 兜底放行（短句技术提问可能无关键词）
        return {"in_scope": True, "reject_message": None}

    # ------------------------------------------------------------------
    # 2. 溯源标注层
    # ------------------------------------------------------------------

    def add_source_annotations(
        self,
        content: str,
        sources: Optional[list[dict]] = None,
    ) -> str:
        """给生成内容追加引用来源标注。

        Args:
            content: 原始生成内容
            sources: 检索到的来源列表，每项含 document/text/content 字段

        Returns:
            追加了参考来源的内容
        """
        if not sources:
            return content

        refs = []
        for i, src in enumerate(sources[:5], 1):
            text = src.get("document", src.get("text", src.get("content", "")))
            source_name = src.get("source", src.get("metadata", {}).get("source", f"来源{i}"))
            if text:
                snippet = text[:80].replace("\n", " ").strip()
                refs.append(f"[{i}] {source_name}: {snippet}...")

        if not refs:
            return content

        annotation = "\n\n---\n**参考来源：**\n" + "\n".join(refs)
        return content + annotation

    # ------------------------------------------------------------------
    # 3. 不确定性声明层
    # ------------------------------------------------------------------

    def add_uncertainty_statement(
        self,
        content: str,
        confidence: float = 0.7,
    ) -> str:
        """置信度低于阈值时追加不确定性声明。

        Args:
            content: 原始生成内容
            confidence: 置信度 0-1

        Returns:
            可能追加了声明的内容
        """
        if confidence < self.CONFIDENCE_THRESHOLD:
            statement = (
                "\n\n> ⚠️ **声明**：以上内容仅供参考，"
                "诊断置信度较低（{:.0%}），建议结合教材和课堂笔记进一步确认。"
            ).format(confidence)
            return content + statement
        return content

    # ------------------------------------------------------------------
    # 综合验证入口
    # ------------------------------------------------------------------

    def verify_response(
        self,
        content: str,
        sources: Optional[list[dict]] = None,
        confidence: float = 0.7,
    ) -> dict[str, Any]:
        """对生成的回答执行完整可信验证。

        Returns:
            {
                "content": str,        # 处理后的内容
                "in_scope": bool,      # 是否在范围内
                "has_sources": bool,   # 是否附带来源
                "has_uncertainty": bool,  # 是否追加了不确定性声明
                "confidence": float,
            }
        """
        scope = self.verify_scope(content)
        if not scope["in_scope"]:
            return {
                "content": scope.get("reject_message", "该问题超出本课程范围。"),
                "in_scope": False,
                "has_sources": False,
                "has_uncertainty": False,
                "confidence": confidence,
            }

        annotated = self.add_source_annotations(content, sources)
        final = self.add_uncertainty_statement(annotated, confidence)

        return {
            "content": final,
            "in_scope": True,
            "has_sources": bool(sources),
            "has_uncertainty": confidence < self.CONFIDENCE_THRESHOLD,
            "confidence": confidence,
        }

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    def _format_scope_prompt(self, content: str) -> str:
        if self._scope_prompt:
            try:
                return self._scope_prompt.format(content=content[:500])
            except KeyError:
                pass
        return (
            f"判断以下内容是否属于计算机网络课程范畴（回答yes或no）：\n{content[:300]}\n"
            '返回JSON：{"in_scope": true, "reason": "判断理由"}'
        )

    @staticmethod
    def _parse_json(text: str, default: Any) -> Any:
        try:
            import json
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except Exception:
            pass
        return default


# 单例
trust_mechanism = TrustMechanism()
