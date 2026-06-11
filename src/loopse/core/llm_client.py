"""
LLM 调用客户端 —— 封装讯飞星火 API
同步聊天 / 异步流式两种模式，对外统一接口
"""
import os
import json
import asyncio
from typing import AsyncIterator, Optional
from dotenv import load_dotenv

load_dotenv()

SPARK_APP_ID  = os.getenv("SPARK_APP_ID", "")
SPARK_API_KEY = os.getenv("SPARK_API_KEY", "")
SPARK_API_SECRET = os.getenv("SPARK_API_SECRET", "")
SPARK_DOMAIN  = os.getenv("SPARK_DOMAIN", "generalv3.5")
SPARK_URL     = os.getenv("SPARK_URL", "wss://spark-api.xf-yun.com/v3.5/chat")

# 是否启用 Mock 模式（API Key 未配置时自动启用）
_MOCK_MODE = not (SPARK_APP_ID and SPARK_API_KEY and SPARK_API_SECRET)


class SparkLLMClient:
    """讯飞星火大模型客户端，支持同步聊天和异步流式输出"""

    def chat(
        self,
        user_message: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """同步调用，等待完整结果返回"""
        if _MOCK_MODE:
            return self._mock_response(user_message)

        try:
            from sparkai.llm.llm import ChatSparkLLM
            from sparkai.core.messages import ChatMessage as SparkMessage

            spark = ChatSparkLLM(
                spark_api_url=SPARK_URL,
                spark_app_id=SPARK_APP_ID,
                spark_api_key=SPARK_API_KEY,
                spark_api_secret=SPARK_API_SECRET,
                spark_llm_domain=SPARK_DOMAIN,
                streaming=False,
            )
            messages = []
            if system_prompt:
                messages.append(SparkMessage(role="system", content=system_prompt))
            messages.append(SparkMessage(role="user", content=user_message))

            resp = spark.generate([messages])
            return resp.generations[0][0].text
        except Exception as e:
            return f"[LLM调用失败: {e}]"

    async def async_stream_chat(
        self,
        user_message: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """异步流式输出，逐 token 产生"""
        if _MOCK_MODE:
            async for token in self._mock_stream(user_message):
                yield token
            return

        try:
            from sparkai.llm.llm import ChatSparkLLM
            from sparkai.core.messages import ChatMessage as SparkMessage

            spark = ChatSparkLLM(
                spark_api_url=SPARK_URL,
                spark_app_id=SPARK_APP_ID,
                spark_api_key=SPARK_API_KEY,
                spark_api_secret=SPARK_API_SECRET,
                spark_llm_domain=SPARK_DOMAIN,
                streaming=True,
            )
            messages = []
            if system_prompt:
                messages.append(SparkMessage(role="system", content=system_prompt))
            messages.append(SparkMessage(role="user", content=user_message))

            # sparkai 流式通过回调实现，此处用队列桥接
            queue: asyncio.Queue[Optional[str]] = asyncio.Queue()

            def on_token(token_str: str):
                asyncio.get_event_loop().call_soon_threadsafe(queue.put_nowait, token_str)

            def on_done():
                asyncio.get_event_loop().call_soon_threadsafe(queue.put_nowait, None)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: spark.stream([messages])
            )
            # 简化处理：收集完整响应后分批 yield
            result = spark.generate([messages])
            full_text = result.generations[0][0].text
            chunk_size = 8
            for i in range(0, len(full_text), chunk_size):
                yield full_text[i:i + chunk_size]
                await asyncio.sleep(0.02)

        except Exception as e:
            yield f"[流式调用失败: {e}]"

    @staticmethod
    def _mock_response(user_message: str) -> str:
        """Mock 模式下的规则回复，覆盖常见知识点"""
        msg_lower = user_message.lower()

        if "三次握手" in user_message or "three-way handshake" in msg_lower:
            return (
                "## TCP 三次握手\n\n"
                "TCP建立连接需要三次握手：\n"
                "1. **第一次**：客户端发送 SYN 报文（SYN=1, seq=x），进入 SYN-SENT 状态。\n"
                "2. **第二次**：服务端回复 SYN-ACK 报文（SYN=1, ACK=1, seq=y, ack=x+1），进入 SYN-RCVD 状态。\n"
                "3. **第三次**：客户端发送 ACK 报文（ACK=1, ack=y+1），双方进入 ESTABLISHED 状态。\n\n"
                "> 来源：第5章 TCP/UDP协议"
            )

        if "四次挥手" in user_message:
            return (
                "## TCP 四次挥手\n\n"
                "TCP断开连接需要四次挥手，因为 TCP 是全双工协议，每个方向需要独立关闭：\n"
                "1. 主动方发送 FIN，进入 FIN-WAIT-1 状态。\n"
                "2. 被动方回 ACK，进入 CLOSE-WAIT。主动方进入 FIN-WAIT-2。\n"
                "3. 被动方发送 FIN，进入 LAST-ACK 状态。\n"
                "4. 主动方回 ACK，进入 TIME-WAIT（等待 2MSL 后关闭）。\n\n"
                "> 来源：第5章 TCP/UDP协议"
            )

        if "http" in msg_lower and "tcp" in msg_lower:
            return (
                "HTTP 是应用层协议，**必须基于传输层的 TCP 协议**。\n"
                "HTTP 不能直接基于 IP，因为 IP 是网络层协议，不提供可靠传输和端口寻址。\n"
                "正确的协议层次：HTTP → TCP → IP → 数据链路层\n\n"
                "> 来源：第1章 TCP/IP分层模型"
            )

        if "滑动窗口" in user_message or "流量控制" in user_message:
            return (
                "## TCP 流量控制（滑动窗口）\n\n"
                "发送方维护一个发送窗口，大小由接收方的 **rwnd（接收窗口）** 决定。\n"
                "- 接收方在 ACK 中携带 `window` 字段通告当前可用缓冲区大小\n"
                "- 当 rwnd=0 时，发送方停止发送，启动持续定时器探测\n\n"
                "> 来源：第5章 TCP流量控制"
            )

        return (
            f"关于「{user_message[:30]}」的回复（Mock模式）：\n"
            "这是测试响应，真实环境需配置讯飞星火 API Key。\n"
            "请在 `.env` 文件中设置 SPARK_APP_ID / SPARK_API_KEY / SPARK_API_SECRET。"
        )

    @staticmethod
    async def _mock_stream(user_message: str) -> AsyncIterator[str]:
        """Mock 流式输出"""
        text = SparkLLMClient._mock_response(user_message)
        chunk_size = 6
        for i in range(0, len(text), chunk_size):
            yield text[i:i + chunk_size]
            await asyncio.sleep(0.05)


# 全局单例
llm_client = SparkLLMClient()
