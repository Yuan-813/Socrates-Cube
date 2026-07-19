"""
LLM 调用客户端 —— 封装讲飞星火 API 与多模型路由
同步聊天 / 异步流式两种模式，对外统一接口

多模型支持（通过 LLM_PROVIDER 环境变量或人格路由）：
- spark    ：讲飞星火（默认）
- openai   ： OpenAI 兄容接口（SkyClaw / Qwen / DeepSeek 等）
- qwen     ：默认路向 openai-compat（需配置 QWEN_API_KEY）

异常处理策略：
- 超时控制：同步调用默认 30s，流式调用 60s，可通过 LLM_TIMEOUT 环境变量配置
- 网络异常：捕获后返回友好提示字符串，不抛异常给上层
- Mock 降级：API Key 未配置时自动启用 Mock 模式
"""
from __future__ import annotations

import asyncio
import logging
import os
import queue
import threading
from typing import AsyncIterator

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_SENTINEL = object()

# 超时配置（秒）
_LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))
_LLM_STREAM_TIMEOUT = int(os.getenv("LLM_STREAM_TIMEOUT", "60"))


def _first_env(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value and not value.endswith("_here"):
            return value
    return ""


SPARK_APP_ID = _first_env("XUNFEI_APP_ID", "SPARK_APP_ID", "SPARKAI_APP_ID")
SPARK_API_KEY = _first_env("XUNFEI_API_KEY", "SPARK_API_KEY", "SPARKAI_API_KEY")
SPARK_API_SECRET = _first_env("XUNFEI_API_SECRET", "SPARK_API_SECRET", "SPARKAI_API_SECRET")
SPARK_URL = (
    _first_env("XUNFEI_SPARK_URL", "SPARK_URL", "SPARKAI_URL")
    or "wss://spark-api.xf-yun.com/v3.5/chat"
)
SPARK_DOMAIN = _first_env("SPARK_DOMAIN", "SPARKAI_DOMAIN") or "generalv3.5"

# 检查 sparkai 包是否真实可用（凭据配置了不代表包已安装）
try:
    import sparkai as _sparkai_test  # noqa: F401
    _SPARKAI_AVAILABLE = True
except ImportError:
    _SPARKAI_AVAILABLE = False
    logger.warning(
        "[LLM] sparkai 包未安装，将强制使用 Mock 模式（即使有 API 凭据），\n"
        "      安装方法：pip install sparkai  或 pip install -r requirements.txt"
    )

_MOCK_MODE = not (SPARK_APP_ID and SPARK_API_KEY and SPARK_API_SECRET) or not _SPARKAI_AVAILABLE

if _MOCK_MODE:
    logger.warning(
        "[LLM] 星火 API 凭据未配置，已启用 Mock 模式。"
        " 请在 .env 中设置 XUNFEI_APP_ID / XUNFEI_API_KEY / XUNFEI_API_SECRET。"
    )
else:
    logger.info("[LLM] 星火 API 已配置（APP_ID=%s），使用真实模型。", SPARK_APP_ID)
    # sparkai 的 on_message 对无 'content' 字段的帧（Spark X 会发送 role-only 帧）
    # 会报 KeyError，在此层面打补丁修复。
    def _patch_sparkai():
        import json as _json
        from sparkai.llm.llm import _SparkLLMClient
        _orig = _SparkLLMClient.on_message
        def _patched(self, ws, message):
            try:
                data = _json.loads(message)
                for item in data.get("payload", {}).get("choices", {}).get("text", []):
                    item.setdefault("content", "")
                message = _json.dumps(data)
            except Exception:
                pass
            return _orig(self, ws, message)
        _SparkLLMClient.on_message = _patched
        logger.debug("[LLM] sparkai on_message patched for Spark X compatibility")
    try:
        _patch_sparkai()
    except Exception as _e:
        logger.warning("[LLM] sparkai patch skipped: %s", _e)


class SparkLLMClient:
    """讯飞星火大模型客户端，支持同步聊天和异步流式输出"""

    def chat(
        self,
        user_message: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """同步聊天接口。

        异常处理：超时 / 网络异常 / API 错误均返回友好提示，不抛异常。
        """
        if _MOCK_MODE:
            return self._mock_response(user_message)

        try:
            from sparkai.core.messages import ChatMessage as SparkMessage
            from sparkai.llm.llm import ChatSparkLLM

            spark = self._build_client(streaming=False, temperature=temperature, max_tokens=max_tokens)
            messages = self._build_messages(user_message, system_prompt, SparkMessage)

            result_holder: dict = {"text": None, "error": None}

            def _do_generate():
                try:
                    resp = spark.generate([messages])
                    result_holder["text"] = resp.generations[0][0].text
                except Exception as exc:
                    result_holder["error"] = exc

            thread = threading.Thread(target=_do_generate, daemon=True)
            thread.start()
            thread.join(timeout=_LLM_TIMEOUT)

            if thread.is_alive():
                logger.warning("[LLM] chat 超时 (%ds)，返回降级提示", _LLM_TIMEOUT)
                return "抱歉，模型响应超时，请稍后重试。"

            if result_holder["error"]:
                raise result_holder["error"]

            return result_holder["text"] or ""
        except Exception as e:
            logger.error("[LLM] chat 调用失败: %s", e)
            return f"抱歉，AI 服务暂时不可用，请稍后重试。"

    async def async_stream_chat(
        self,
        user_message: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """异步流式聊天接口。

        异常处理：超时 / 网络异常时 yield 友好提示 token 而非崩溃。
        """
        if _MOCK_MODE:
            async for token in self._mock_stream(user_message):
                yield token
            return

        token_queue: queue.Queue = queue.Queue()

        # 继承 sparkai 官方基类，避免回调框架因缺少 ignore_llm 等属性
        # 而抛 AttributeError 导致流式生成中断
        try:
            from sparkai.core.callbacks.base import BaseCallbackHandler as _SparkBase
        except ImportError:
            # sparkai 不可用，必须降级到 Mock（不能此处 yield 错误字符串）
            logger.warning("[LLM] sparkai 不可用，降级到 Mock stream")
            async for tok in self._mock_stream(user_message):
                yield tok
            return

        class _TokenCollector(_SparkBase):
            raise_error = True

            def on_llm_new_token(self, token: str, **kwargs):
                if token:
                    token_queue.put(token)

            def on_llm_end(self, *args, **kwargs):
                token_queue.put(_SENTINEL)

            def on_llm_error(self, error, **kwargs):
                token_queue.put(Exception(str(error)))

            def on_chat_model_start(self, *args, **kwargs):
                pass

        def _run_spark():
            try:
                from sparkai.core.messages import ChatMessage as SparkMessage
                from sparkai.llm.llm import ChatSparkLLM

                spark = self._build_client(streaming=True, temperature=temperature, max_tokens=max_tokens)
                messages = self._build_messages(user_message, system_prompt, SparkMessage)
                spark.generate([messages], callbacks=[_TokenCollector()])
            except Exception as exc:
                token_queue.put(exc)

        thread = threading.Thread(target=_run_spark, daemon=True)
        thread.start()

        loop = asyncio.get_event_loop()
        first_token_received = False
        while True:
            try:
                # 首个 token 等待更长超时，后续 token 短超时
                timeout = _LLM_STREAM_TIMEOUT if not first_token_received else 30
                item = await asyncio.wait_for(
                    loop.run_in_executor(None, token_queue.get),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                if not first_token_received:
                    logger.warning("[LLM] stream 首个 token 超时 (%ds)，降级返回", timeout)
                    yield "抱歉，模型响应超时，请稍后重试。"
                else:
                    logger.warning("[LLM] stream 后续 token 超时，提前结束")
                break

            if item is _SENTINEL:
                break
            if isinstance(item, Exception):
                logger.error("[LLM] stream 调用失败: %s", item)
                yield "抱歉，流式生成中断，请稍后重试。"
                break
            first_token_received = True
            yield str(item)

    def _build_client(self, streaming: bool, temperature: float, max_tokens: int):
        from sparkai.llm.llm import ChatSparkLLM

        spark = ChatSparkLLM(
            spark_api_url=SPARK_URL,
            spark_app_id=SPARK_APP_ID,
            spark_api_key=SPARK_API_KEY,
            spark_api_secret=SPARK_API_SECRET,
            spark_llm_domain=SPARK_DOMAIN,
            streaming=streaming,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        # sparkai 的 _adjust_api_by_domain 对未知 domain（如 spark-x）会
        # 回退到默认 v3.5 URL，覆盖我们配置的端点。在此强制纠正。
        if hasattr(spark, "client") and SPARK_URL:
            spark.client.api_url = SPARK_URL
        return spark

    @staticmethod
    def _build_messages(user_message: str, system_prompt: str, spark_message_cls):
        messages = []
        if system_prompt:
            messages.append(spark_message_cls(role="system", content=system_prompt))
        messages.append(spark_message_cls(role="user", content=user_message))
        return messages

    @staticmethod
    def _mock_response(user_message: str) -> str:
        msg = user_message.lower()
    
        # TCP 三次握手 / 演示
        if "三次握手" in user_message or "three-way handshake" in msg or "演示" in user_message and "握手" in user_message:
            return (
                "## TCP 三次握手（RFC 9293）\n\n"
                "建立 TCP 连接需要三次握手，确保双方相互确认发送/接收能力：\n\n"
                "```\n"
                "客户端                         服务端\n"
                "  |--[SYN, seq=x]----------->|   第一次：请求建立\n"
                "  |<--[SYN+ACK, seq=y,ack=x+1]|   第二次：确认并同步\n"
                "  |--[ACK, ack=y+1]---------->|   第三次：建立完成\n"
                "  |====== ESTABLISHED ========|\n"
                "```\n\n"
                "**各阶段状态转换：**\n"
                "1. **第一次**：客户端发 SYN，进入 **SYN-SENT** 状态\n"
                "2. **第二次**：服务端回 SYN-ACK，进入 **SYN-RCVD** 状态\n"
                "3. **第三次**：客户端回 ACK，双方进入 **ESTABLISHED** 状态\n\n"
                "> 关键点：为什么不是两次？两次握手无法防止厂商头 SYN 报文迟到到达导致的进in连接问题。"
            )
    
        # TCP 四次挥手
        if "四次挥手" in user_message or "four-way" in msg:
            return (
                "## TCP 四次挥手（RFC 9293）\n\n"
                "TCP 是全双工协议，双方需要独立关闭发送方向：\n\n"
                "```\n"
                "主动方                         被动方\n"
                "  |--[FIN, seq=u]------------>|   第一次：请求关闭\n"
                "  |<--[ACK, ack=u+1]---------:|   第二次：确认\n"
                "  |<--[FIN, seq=v]-----------:|   第三次：被动方关闭\n"
                "  |--[ACK, ack=v+1]---------->|   第四次：确认\n"
                "  （等待 2MSL 后关闭）\n"
                "```\n\n"
                "**TIME-WAIT** 状态等待 2MSL 的原因：确保最后一个 ACK 能到达被动方。"
            )
    
        # DNS 解析
        if "dns" in msg or "解析" in user_message and "域名" in user_message:
            return (
                "## DNS 域名解析流程（RFC 1034/1035）\n\n"
                "**递归查询全流程**（以 www.example.com 为例）\n\n"
                "```\n"
                "客户端\n"
                "  1. 查本地 hosts 文件 → 未命中\n"
                "  2. 查本地 DNS 缓存  → 未命中\n"
                "  3. 询问本地 DNS 服务器\n"
                "     本地 DNS 不知道 → 询问根 DNS\n"
                "     根 DNS 不知道 → 询问 .com 顶级域 DNS\n"
                "     .com 返回 example.com 权威 DNS 地址\n"
                "     example.com 权威 DNS 返回 www 的 IP\n"
                "  4. 本地 DNS 缓存结果并返回客户端\n"
                "```\n\n"
                "**两种查询模式**：递归查询（客户端视角）vs 迭代查询（DNS 服务器视角）"
            )
    
        # HTTP vs HTTPS
        if ("http" in msg and "https" in msg) or ("http" in msg and ("区别" in user_message or "对比" in user_message)):
            return (
                "## HTTP vs HTTPS（RFC 9110 / RFC 8446）\n\n"
                "| 特性 | HTTP | HTTPS |\n"
                "|------|------|-------|\n"
                "| 加密 | 明文传输 | TLS 加密 |\n"
                "| 端口 | 80 | 443 |\n"
                "| 证书 | 不需要 | 需要 CA 签发 |\n"
                "| 身份认证 | 无 | 有（服务器证书） |\n"
                "| 性能 | 较快 | 稍慢（TLS 握手开销）|\n\n"
                "**HTTPS 工作流程**： TCP 三次握手 → TLS 握手 → HTTP 请求\n"
                "TLS 1.3 将握手往返由 2-RTT 常减为 1-RTT。"
            )
    
        # IP 地址 / 子网
        if "子网" in user_message or "ip" in msg and ("分片" in user_message or "推算" in user_message or "划分" in user_message):
            return (
                "## IPv4 子网划分（RFC 791）\n\n"
                "**CIDR 表示法**：192.168.1.0/24\n"
                "- `/24` 表示网络前缀 24 位，主机部分 8 位\n"
                "- 可用地址 = 2^8 - 2 = 254 个（减去网络地址和广播地址）\n\n"
                "**IPv4 分片**：小于 MTU 时将 IP 包分成多片，字段 DF=1 禁止分片。\n"
                "IPv6 消除了中间路由器分片，只允许源端分片。"
            )
    
        # TCP 拥塞控制
        if "拥塞" in user_message or "拥塞控制" in user_message:
            return (
                "## TCP 拥塞控制（RFC 9293）\n\n"
                "TCP 拥塞控制由四种算法组成：\n\n"
                "1. **慢启动**：cwnd 从 1 MSS 开始，每 RTT 翻倍，指数增长至 ssthresh\n"
                "2. **拥塞避免**：达到 ssthresh 后每 RTT 加 1 MSS，线性增长\n"
                "3. **快速重传**：收到 3 个重复 ACK 时，将 ssthresh 分分halved，cwnd = ssthresh + 3 MSS\n"
                "4. **快速恢复**：不必回到慢启动，减少拥塞窗口后继续拥塞避免\n\n"
                ">超时事件：wnd 回到 1 MSS，ssthrold = cwnd/2，重新慢启动。"
            )
    
        # ARP
        if "arp" in msg:
            return (
                "## ARP 地址解析协议\n\n"
                "**作用**：将 IP 地址映射到 MAC 地址（工作在数据链路层）\n\n"
                "**工作流程**：\n"
                "1. 发送方在 ARP 缓存中查找目标 IP\n"
                "2. 未命中：广播 ARP Request（包含目标 IP）\n"
                "3. 目标主机回复 ARP Reply（包含自己 MAC）\n"
                "4. 发送方缓存该映射并发送数据帧\n\n"
                "**ARP 欺骗**：伏击者发送伪造 ARP Reply，将流量封屏到自身 MAC。"
            )
    
        # UDP
        if "udp" in msg and ("tcp" not in msg or "对比" in user_message or "区别" in user_message):
            return (
                "## UDP vs TCP（RFC 768 / RFC 9293）\n\n"
                "| 特性 | UDP | TCP |\n"
                "|------|-----|-----|\n"
                "| 连接 | 无连接 | 面向连接 |\n"
                "| 可靠性 | 不保证 | 有序可靠 |\n"
                "| 流量控制 | 无 | 有 |\n"
                "| 拥塞控制 | 无 | 有 |\n"
                "| 延迟 | 低 | 较高 |\n"
                "| 适用场景 | DNS/直播/游戏 | 文件传输/HTTP |\n\n"
                ">误区：「UDP 比 TCP 好」 — 两者适用场景不同，不存在绝对优劣。"
            )
    
        # TLS / HTTPS 加密
        if "tls" in msg or "ssl" in msg:
            return (
                "## TLS 1.3 握手流程（RFC 8446）\n\n"
                "TLS 1.3 将握手由原来的 2-RTT 减少到 1-RTT：\n\n"
                "```\n"
                "客户端                     服务端\n"
                "  |--ClientHello----------->|\n"
                "  |<--ServerHello,Cert,Done-|   1-RTT\n"
                "  |--Finished, [AppData]--->|\n"
                "  |<--[AppData]-------------|\n"
                "```\n\n"
                "**TLS 1.3 主要改进**：\n"
                "- 移除了 RSA 密钥交换，强制使用 ECDHE（前向保密）\n"
                "- 加密参数列表精简化，移除弱加密算法（RC4/MD5/SHA-1）"
            )
    
        # QUIC
        if "quic" in msg:
            return (
                "## QUIC 协议（RFC 9000）\n\n"
                "QUIC 基于 UDP 实现，由 Google 设计，是 HTTP/3 的传输层：\n\n"
                "**主要创新**：\n"
                "1. **0-RTT / 1-RTT 连接**：重连时可达到 0-RTT（第一次连接 1-RTT）\n"
                "2. **消除队头阻塞**：多路复用（Multiplexing），单个流丢包不影响其他流\n"
                "3. **连接迁移**：用 Connection ID 代替四元组，IP 变化不断连接\n"
                "4. **内置加密**：全程必须 TLS 1.3，不可读拦"
            )
    
        # BGP / OSPF / RIP 路由
        if "bgp" in msg or "ospf" in msg or "rip" in msg or "路由协议" in user_message:
            return (
                "## 动态路由协议比较\n\n"
                "| 协议 | 类型 | 算法 | 适用场景 |\n"
                "|------|------|------|------|\n"
                "| RIP | IGP | Bellman-Ford | 小型欁局网 |\n"
                "| OSPF | IGP | Dijkstra (SPF) | 大型企业内网 |\n"
                "| BGP | EGP | 路径矢量 | 互联网域间路由 |\n\n"
                "OSPF 将网络划分为 **Area**（骨干区域 Area 0），除少 广播量。"
            )
    
        # 广义网络问题兑底
        return (
            f"关于「{user_message[:40]}」，这是一个好问题！\n\n"
            "在计算机网络中，理解协议的设计意图和工程实践同样重要。\n\n"
            "我可以帮你讲解：\n"
            "- TCP/UDP 协议特性与应用\n"
            "- DNS 解析、HTTP/HTTPS 流程\n"
            "- IP 地址、子网划分\n"
            "- TLS 加密、QUIC 协议\n"
            "- 路由协议（BGP/OSPF/RIP）\n\n"
            "> ℹ️ **当前为离线模式**，后端 API 未连接。\n"
            "> 启动后端：`python -m uvicorn src.loopse.main:app --reload --port 8000`\n"
            "> 或运行 `start.bat` / `start.sh`。"
        )

    @staticmethod
    async def _mock_stream(user_message: str) -> AsyncIterator[str]:
        text = SparkLLMClient._mock_response(user_message)
        chunk_size = 6
        for i in range(0, len(text), chunk_size):
            yield text[i : i + chunk_size]
            await asyncio.sleep(0.05)


llm_client = SparkLLMClient()


# ═══════════════════════════════════════════════════════════════════════════
# 多模型路由客户端（基于 OpenAI 兼容接口，支持 SkyClaw/Qwen/DeepSeek/GLM 等）
# 配置方式：在 .env 中设置：
#   OPENAI_COMPAT_BASE_URL=https://open.bigmodel.cn/api/paas/v4/  (GLM-4)
#   OPENAI_COMPAT_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1  (Qwen)
#   OPENAI_COMPAT_BASE_URL=https://api.deepseek.com/v1  (DeepSeek)
#   OPENAI_COMPAT_API_KEY=your_key
#   OPENAI_COMPAT_MODEL=glm-4-flash  / qwen-plus / deepseek-chat
# 清华GLM说明：GLM-4系列由智谱AI基于清华大学KEG实验室ChatGLM开源研究发展而来
# ⚠️  openai 包可选，未安装时自动降级为 Spark
# ═══════════════════════════════════════════════════════════════════════════

_OPENAI_BASE_URL = os.getenv("OPENAI_COMPAT_BASE_URL", "").strip()
_OPENAI_API_KEY = os.getenv("OPENAI_COMPAT_API_KEY", "").strip()
_OPENAI_MODEL = os.getenv("OPENAI_COMPAT_MODEL", "skywork-ai/skyclaw-v1-lite").strip()

# 人格对应的提示词风格
# GLM-4说明：GLM系列由清华大学KEG实验室研发，开源仓库 https://github.com/THUDM/ChatGLM3
# 商业版GLM-4由智谱AI提供，通过 OpenAI 兼容接口接入，配置见 .env.example
PERSONA_SYSTEM_PROMPTS = {
    "professor": (
        "你是一位严谨专业的计算机网络教授，语气正式、结构化，回答时优先给出理论框架和定义，再配上案例和公式流程。"
        "使用正式学术语言，每次回答期望学生深化理解。"
    ),
    "peer": (
        "你是一位和学生同龄的学长/学姐，语气轻松口语化，喜欢用类比和生活小例子解释复杂概念。"
        "遇到题目会说\"咕我也曾经弄不清楚这个，后来发现...\"来拉近距离。"
    ),
    "expert": (
        "你是一位拥有5年以上工业界网络工程师经验，回答处处联系实际生产场景和排障工作。"
        "快速直接给出可操作的结论，少用理论冗述，强调\"实务上我们会这样处理\"。"
    ),
    "engineer": (
        "你是一位精通TCP/IP协议栈和网络设备配置的网络工程师，聚焦实际工程落地。"
        "回答时善用命令行示例（show ip route、debug bgp、tcpdump等），"
        "并结合RFC规范解释背后原理。遇到排障问题，优先从OSI七层逐层排查。"
    ),
    "interviewer": (
        "你是一家大型互联网公司的技术面试官，正在对候选人进行计算机网络方向的技术面试。"
        "风格：专业严谨，追问深度，不轻易给出答案，会说\"请展开说说...\"或\"能举个实际例子吗？\"。"
        "对模糊回答不满意时会追问，对优秀回答给予简短肯定后继续深挖。"
        "面试结束后给出简短的能力评价和建议。"
    ),
}

class OpenAICompatClient:
    """基于 OpenAI 冖容接口的通用 LLM 客户端（支持 SkyClaw / Qwen / DeepSeek 等），
    不可用时自动降级为 SparkLLMClient。"""

    def __init__(self, base_url: str = "", api_key: str = "", model: str = ""):
        self._base_url = base_url or _OPENAI_BASE_URL
        self._api_key = api_key or _OPENAI_API_KEY
        self._model = model or _OPENAI_MODEL
        self._available = bool(self._base_url and self._api_key)
        if not self._available:
            logger.info("[OpenAI-Compat] API 未配置，将降级至 Spark")

    def _get_client(self):
        """Lazy import openai 包。"""
        import openai
        client = openai.OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
        )
        return client

    def chat(self, user_message: str, system_prompt: str = "", **kwargs) -> str:
        if not self._available:
            return llm_client.chat(user_message, system_prompt, **kwargs)
        try:
            client = self._get_client()
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_message})
            resp = client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", 2048),
                temperature=kwargs.get("temperature", 0.7),
                timeout=_LLM_TIMEOUT,
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:
            logger.error("[OpenAI-Compat] chat 失败: %s，降级至 Spark", exc)
            return llm_client.chat(user_message, system_prompt, **kwargs)

    async def async_stream_chat(self, user_message: str, system_prompt: str = "", **kwargs):
        if not self._available:
            async for tok in llm_client.async_stream_chat(user_message, system_prompt, **kwargs):
                yield tok
            return
        try:
            import openai
            client = openai.OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
            )
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_message})
            stream = client.chat.completions.create(
                model=self._model,
                messages=messages,
                stream=True,
                max_tokens=kwargs.get("max_tokens", 2048),
                temperature=kwargs.get("temperature", 0.7),
                timeout=_LLM_STREAM_TIMEOUT,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
                    await asyncio.sleep(0)
        except Exception as exc:
            logger.error("[OpenAI-Compat] stream 失败: %s，降级至 Spark", exc)
            async for tok in llm_client.async_stream_chat(user_message, system_prompt, **kwargs):
                yield tok


# 人格路由器实例
openai_compat_client = OpenAICompatClient()


def get_client_for_persona(persona: str = "professor"):
    """根据人格返回对应的 LLM 客户端实例。

    路由策略：
    - 如果 Spark 处于 Mock 模式（凭据未配置 / sparkai 包未安装），则所有人格全部用 OpenAI-compat
    - 如果 Spark 凭据已配置，所有人格优先用 Spark（这是项目主力 LLM）
    - 如果 Spark 运行时报错，上层 orchestrator.py 的 try/except 会自动降级到 OpenAI-compat
    """
    if _MOCK_MODE:
        # Spark 凭据缺失，尝试用 OpenAI-compat（豆包等）
        if openai_compat_client._available:
            logger.info("[LLM] Spark Mock模式，改用 OpenAI-compat (model=%s)", openai_compat_client._model)
            return openai_compat_client
    return llm_client  # Spark 凯底（如果凭据已配置就用真实 Spark）


def get_persona_system_prompt(persona: str) -> str:
    """获取人格对应的系统 prompt。"""
    return PERSONA_SYSTEM_PROMPTS.get(persona, PERSONA_SYSTEM_PROMPTS["professor"])
