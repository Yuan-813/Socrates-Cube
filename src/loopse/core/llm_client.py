"""
讯飞星火大模型统一调用封装
支持：流式输出（SSE）、非流式调用、异步调用
"""
import os
import asyncio
import queue
import threading
from typing import AsyncGenerator, Optional
from dotenv import load_dotenv

load_dotenv()

# 尝试导入真实 sparkai，不可用时降级 Mock
try:
    from sparkai.llm.llm import ChatSparkLLM
    from sparkai.core.messages import ChatMessage, SystemMessage
    _SPARKAI_AVAILABLE = True
except ImportError:
    _SPARKAI_AVAILABLE = False


class SparkLLMClient:
    """讯飞星火大模型客户端"""

    def __init__(self):
        self.app_id = os.environ.get("XUNFEI_APP_ID")
        self.api_key = os.environ.get("XUNFEI_API_KEY")
        self.api_secret = os.environ.get("XUNFEI_API_SECRET")
        self.spark_url = os.environ.get(
            "XUNFEI_SPARK_URL",
            "wss://spark-api.xf-yun.com/v3.5/chat"
        )

        if not _SPARKAI_AVAILABLE:
            print("⚠ sparkai 未安装，将使用 Mock 模式运行")
            self.mock_mode = True
        elif not all([self.app_id, self.api_key, self.api_secret]):
            print("⚠ 缺少讯飞 API 配置，请检查 .env 文件，将使用 Mock 模式运行")
            self.mock_mode = True
        else:
            self.mock_mode = False

    def _build_client(self, streaming: bool = False) -> "ChatSparkLLM":
        return ChatSparkLLM(
            spark_api_url=self.spark_url,
            spark_app_id=self.app_id,
            spark_api_key=self.api_key,
            spark_api_secret=self.api_secret,
            spark_llm_domain="generalv3.5",
            streaming=streaming,
            max_tokens=2048,
            temperature=0.7,
        )

    def chat(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        history: Optional[list] = None
    ) -> str:
        """同步非流式调用"""
        if self.mock_mode:
            return '{"network_layer_cognition": 3, "protocol_flow_memory": 4, "packet_format_understanding": 3, "protocol_relationship": 4, "fault_diagnosis_logic": 3, "hands_on_ability": 2, "cognitive_style": "logical", "misconception_patterns": []}'
        client = self._build_client(streaming=False)
        messages = self._build_messages(user_message, system_prompt, history)
        result = client.generate([messages])
        return result.generations[0][0].text

    async def async_stream_chat(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        history: Optional[list] = None
    ) -> AsyncGenerator[str, None]:
        """
        真正的异步流式输出
        原理：用 queue 桥接 sparkai 的同步回调和 FastAPI 的异步生成器
        """
        if self.mock_mode:
            mock_text = "这是 Mock 回复：TCP 三次握手的目的是让双方确认彼此的收发能力正常，防止建立无效连接。"
            for char in mock_text:
                await asyncio.sleep(0.03)
                yield char
            return

        token_queue: queue.Queue = queue.Queue()
        SENTINEL = object()  # 结束哨兵

        class AsyncTokenCollector:
            def on_llm_new_token(self, token: str, **kwargs):
                token_queue.put(token)

            def on_llm_end(self, *args, **kwargs):
                token_queue.put(SENTINEL)

            def on_llm_error(self, error, **kwargs):
                token_queue.put(Exception(str(error)))

        def _run_spark():
            """在独立线程中运行同步的 sparkai 调用"""
            client = self._build_client(streaming=True)
            messages = self._build_messages(user_message, system_prompt, history)
            try:
                client.generate([messages], callbacks=[AsyncTokenCollector()])
            except Exception as e:
                token_queue.put(e)

        thread = threading.Thread(target=_run_spark, daemon=True)
        thread.start()

        loop = asyncio.get_event_loop()
        while True:
            token = await loop.run_in_executor(None, token_queue.get)
            if token is SENTINEL:
                break
            if isinstance(token, Exception):
                raise token
            yield token

    def _build_messages(
        self,
        user_message: str,
        system_prompt: Optional[str],
        history: Optional[list]
    ) -> list:
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        if history:
            messages.extend(history)
        messages.append(ChatMessage(role="user", content=user_message))
        return messages


# 全局单例
llm_client = SparkLLMClient()
