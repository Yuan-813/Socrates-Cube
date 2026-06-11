"""Download public networking references and prepare local KB markdown files."""
from __future__ import annotations

import argparse
import json
import re
import textwrap
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "external"
CLEANED_DIR = ROOT / "data" / "cleaned"
MANIFEST = ROOT / "data" / "raw" / "external_sources.json"


@dataclass(frozen=True)
class Source:
    id: str
    title: str
    url: str
    collection: str
    chapter: str
    focus: str


SOURCES = [
    Source("rfc9293_tcp", "RFC 9293 Transmission Control Protocol", "https://www.rfc-editor.org/rfc/rfc9293.txt", "protocol_specs", "transport", "TCP connection management, reliability, sequence numbers"),
    Source("rfc9110_http_semantics", "RFC 9110 HTTP Semantics", "https://www.rfc-editor.org/rfc/rfc9110.txt", "protocol_specs", "application", "HTTP methods, status codes, semantics"),
    Source("rfc9112_http11", "RFC 9112 HTTP/1.1", "https://www.rfc-editor.org/rfc/rfc9112.txt", "protocol_specs", "application", "HTTP/1.1 message syntax and connection management"),
    Source("rfc8446_tls13", "RFC 8446 TLS 1.3", "https://www.rfc-editor.org/rfc/rfc8446.txt", "protocol_specs", "security", "TLS handshake and secure transport"),
    Source("rfc9000_quic", "RFC 9000 QUIC", "https://www.rfc-editor.org/rfc/rfc9000.txt", "protocol_specs", "transport", "QUIC transport, streams, congestion"),
    Source("rfc8200_ipv6", "RFC 8200 IPv6 Specification", "https://www.rfc-editor.org/rfc/rfc8200.txt", "protocol_specs", "network", "IPv6 packet format and forwarding"),
    Source("rfc791_ipv4", "RFC 791 Internet Protocol", "https://www.rfc-editor.org/rfc/rfc791.txt", "protocol_specs", "network", "IPv4 datagram and fragmentation"),
    Source("rfc768_udp", "RFC 768 User Datagram Protocol", "https://www.rfc-editor.org/rfc/rfc768.txt", "protocol_specs", "transport", "UDP datagram format"),
    Source("rfc1034_dns_concepts", "RFC 1034 Domain Names Concepts", "https://www.rfc-editor.org/rfc/rfc1034.txt", "protocol_specs", "application", "DNS concepts and resolver behavior"),
    Source("rfc1035_dns_implementation", "RFC 1035 Domain Names Implementation", "https://www.rfc-editor.org/rfc/rfc1035.txt", "protocol_specs", "application", "DNS messages and resource records"),
    Source("iana_protocol_numbers", "IANA Protocol Numbers", "https://www.iana.org/assignments/protocol-numbers/protocol-numbers-1.csv", "course_docs", "reference", "IP protocol number registry"),
]


MISCONCEPTIONS = [
    ("mc_001", "TCP 三次握手", "认为两次握手足以建立可靠连接", "flow_omission", "第三次 ACK 用来确认客户端收到服务端 SYN-ACK，避免失效请求导致半开连接。"),
    ("mc_002", "TCP 四次挥手", "认为断开连接也一定是三次报文", "flow_omission", "TCP 是全双工，两个方向的数据流需要分别关闭，所以通常需要 FIN/ACK 两个方向的确认。"),
    ("mc_003", "HTTP 与 TCP", "认为 HTTP 可以直接运行在 IP 上", "layer_misplacement", "HTTP 是应用层协议，通常依赖 TCP 或 QUIC 提供传输能力。"),
    ("mc_004", "UDP", "认为 UDP 完全没有用途，因为不可靠", "over_simplification", "UDP 适合实时、多播、应用自定义可靠性等场景，如 DNS、QUIC 底层、音视频。"),
    ("mc_005", "DNS", "混淆递归查询和迭代查询", "concept_confusion", "递归查询由被询问服务器负责继续查询；迭代查询返回下一步可询问的服务器。"),
    ("mc_006", "滑动窗口", "把接收窗口 rwnd 和拥塞窗口 cwnd 混为一谈", "term_confusion", "rwnd 反映接收方缓存能力，cwnd 反映网络拥塞控制约束，发送窗口受二者共同限制。"),
    ("mc_007", "慢启动", "认为慢启动是线性增长", "calculation_error", "慢启动阶段 cwnd 通常按 RTT 近似指数增长，直到阈值或丢包事件。"),
    ("mc_008", "IP 分片", "认为 TCP 负责 IP 分片重组", "layer_misplacement", "IP 分片属于网络层；TCP 处理的是字节流分段和重传。"),
    ("mc_009", "子网掩码", "把 /24 误认为 24 个主机地址", "calculation_error", "/24 表示 24 位网络前缀，IPv4 下剩余 8 位主机位。"),
    ("mc_010", "ARP", "认为 ARP 解析域名", "concept_confusion", "ARP 解析同一链路内 IP 到 MAC；DNS 解析域名到 IP。"),
    ("mc_011", "NAT", "认为 NAT 增强端到端透明性", "reasoning_breakdown", "NAT 会改写地址/端口，通常削弱端到端连接透明性。"),
    ("mc_012", "TLS", "认为 TLS 只负责加密不认证", "over_simplification", "TLS 同时提供机密性、完整性和身份认证机制。"),
    ("mc_013", "QUIC", "认为 QUIC 是应用层 HTTP 的另一个名字", "layer_misplacement", "QUIC 是基于 UDP 的传输协议，HTTP/3 运行在 QUIC 之上。"),
    ("mc_014", "HTTP 状态码", "认为 404 表示服务器宕机", "concept_confusion", "404 表示目标资源未找到；服务器错误一般是 5xx。"),
    ("mc_015", "拥塞控制", "把流量控制等同于拥塞控制", "concept_confusion", "流量控制保护接收端；拥塞控制保护网络路径。"),
    ("mc_016", "可靠传输", "认为有 ACK 就不会丢包", "over_simplification", "ACK 是可靠传输机制的一部分，还需要序号、重传、校验、超时估计等机制。"),
    ("mc_017", "交换与路由", "认为交换机按 IP 转发", "layer_misplacement", "二层交换主要依据 MAC 地址；路由器依据 IP 前缀转发。"),
    ("mc_018", "MTU", "认为 MTU 越大永远越好", "reasoning_breakdown", "过大的包可能导致分片或丢弃；路径 MTU 需要与链路能力匹配。"),
    ("mc_019", "端口号", "认为端口号标识主机", "concept_confusion", "IP 标识主机/接口，端口标识传输层上的应用进程。"),
    ("mc_020", "TCP 序号", "认为序号按报文个数递增", "calculation_error", "TCP 序号按字节流编号递增，而不是按段数量递增。"),
    ("mc_021", "RTT", "认为 RTT 等于单向传播时延", "calculation_error", "RTT 是往返时间，包含两个方向传播、排队和处理等延迟。"),
    ("mc_022", "缓存", "认为 Web 缓存只在浏览器里", "over_simplification", "缓存可存在于浏览器、代理、CDN、服务端等多个位置。"),
    ("mc_023", "DHCP", "认为 DHCP 只分配 IP 地址", "over_simplification", "DHCP 还可分配网关、DNS、租期等网络配置。"),
    ("mc_024", "ICMP", "认为 ICMP 是传输层协议", "layer_misplacement", "ICMP 是网络层控制/差错报告协议。"),
]


def _fetch(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Socrates-Cube-KB/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def _clean_text(raw: str) -> str:
    raw = raw.replace("\r\n", "\n")
    raw = re.sub(r"\n\s*\[Page \d+\]\s*\n", "\n", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip()


def _to_markdown(source: Source, text: str) -> str:
    excerpt = _clean_text(text)
    if len(excerpt) > 24_000:
        excerpt = excerpt[:24_000] + "\n\n[truncated for local retrieval]\n"
    return textwrap.dedent(
        f"""\
        # {source.title}

        Source URL: {source.url}
        Collection: {source.collection}
        Chapter: {source.chapter}
        Focus: {source.focus}

        ## Retrieved Text

        {excerpt}
        """
    )


def write_misconceptions() -> None:
    path = ROOT / "data" / "raw" / "misconceptions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "id": item[0],
            "knowledge_point": item[1],
            "misconception": item[2],
            "error_type": item[3],
            "correct_answer": item[4],
            "chapter": "computer_networking",
        }
        for item in MISCONCEPTIONS
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    for source in SOURCES:
        raw_path = RAW_DIR / f"{source.id}.txt"
        cleaned_path = CLEANED_DIR / f"{source.id}.md"
        if args.skip_existing and raw_path.exists() and cleaned_path.exists():
            status = "cached"
        else:
            print(f"Downloading {source.url}")
            try:
                text = _fetch(source.url)
                raw_path.write_text(text, encoding="utf-8")
                cleaned_path.write_text(_to_markdown(source, text), encoding="utf-8")
                status = "downloaded"
            except Exception as exc:
                print(f"Failed: {source.url} ({exc})")
                status = f"failed: {exc}"
        manifest.append(
            {
                **source.__dict__,
                "raw_path": str(raw_path.relative_to(ROOT)),
                "cleaned_path": str(cleaned_path.relative_to(ROOT)),
                "status": status,
            }
        )

    write_misconceptions()
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(manifest)} sources and {len(MISCONCEPTIONS)} misconceptions.")


if __name__ == "__main__":
    main()
