"""
LLM Client — 统一调用星火API / OpenAI兼容接口
支持同步chat和异步流式stream_chat
"""
import os
import json
import httpx
from typing import AsyncIterator, Optional

# 从环境变量读取配置
LLM_API_URL = os.getenv("LLM_API_URL", "https://spark-api-open.xf-yun.com/v1/chat/completions")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "4.0Ultra")


class LLMClient:
    """统一LLM调用客户端"""

    def __init__(self):
        self.api_url = LLM_API_URL
        self.api_key = LLM_API_KEY
        self.model = LLM_MODEL

    def chat(
        self,
        user_message: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """同步调用，返回完整文本"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(self.api_url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[LLMClient] chat调用失败: {e}")
            return f"[LLM调用失败] {e}"

    async def async_stream_chat(
        self,
        user_message: str,
        system_prompt: str = "",
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """异步流式调用，逐token返回"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST", self.api_url, headers=headers, json=payload
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        data_str = line[len("data:"):].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"[LLMClient] stream调用失败: {e}")
            yield f"[流式调用失败] {e}"


llm_client = LLMClient()
