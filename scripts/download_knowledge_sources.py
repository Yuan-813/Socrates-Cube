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
SEED_CHAPTERS_DIR = ROOT / "scripts" / "seeds" / "course_chapters"


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
    ("mc_025", "OSI 模型", "认为 OSI 七层与 TCP/IP 四层一一对应", "concept_confusion", "TCP/IP 是四层模型，OSI 是参考模型，二者是抽象层次而非严格一一映射。"),
    ("mc_026", "以太网", "认为以太网帧最大长度就是 MTU", "term_confusion", "以太网 MTU 通常指 IP 层有效载荷上限；帧本身还包含头部和尾部。"),
    ("mc_027", "CSMA/CD", "认为现代交换机网络仍依赖 CSMA/CD 碰撞检测", "over_simplification", "全双工交换式以太网通常不再使用 CSMA/CD。"),
    ("mc_028", "VLAN", "认为 VLAN 标签只在路由器上添加", "layer_misplacement", "802.1Q VLAN 标签通常在交换机上添加和处理。"),
    ("mc_029", "BGP", "认为 BGP 是内部网关协议", "concept_confusion", "BGP 是域间路由协议；OSPF/RIP 等常用于域内。"),
    ("mc_030", "OSPF", "认为 OSPF 按跳数选路", "concept_confusion", "OSPF 基于链路状态与代价（cost），RIP 才主要按跳数。"),
    ("mc_031", "RIP", "认为 RIP 适合大型互联网核心网", "over_simplification", "RIP 跳数限制和收敛特性使其更适合小型网络。"),
    ("mc_032", "IPv6", "认为 IPv6 只是把地址变长了", "over_simplification", "IPv6 还简化了头部、改进邻居发现，并内置扩展头机制。"),
    ("mc_033", "IPv6 地址", "认为 IPv6 不需要子网划分", "concept_confusion", "IPv6 仍使用前缀长度进行子网划分，只是通常默认 /64。"),
    ("mc_034", "CIDR", "认为 CIDR 只用于 IPv6", "concept_confusion", "CIDR 最初用于缓解 IPv4 地址耗尽，也适用于 IPv6。"),
    ("mc_035", "HTTP/2", "认为 HTTP/2 必须基于 TLS", "over_simplification", "HTTP/2 可在明文 TCP 上运行，但浏览器通常要求 HTTPS。"),
    ("mc_036", "HTTP 持久连接", "认为 HTTP/1.1 每个请求都要新建 TCP 连接", "flow_omission", "HTTP/1.1 默认支持持久连接（Keep-Alive）。"),
    ("mc_037", "Cookie", "认为 Cookie 只能由 JavaScript 设置", "concept_confusion", "Set-Cookie 响应头由服务器设置；HttpOnly Cookie 不能由 JS 访问。"),
    ("mc_038", "CDN", "认为 CDN 只是 DNS 解析服务", "over_simplification", "CDN 还包含缓存、负载均衡、边缘计算等能力。"),
    ("mc_039", "负载均衡", "认为负载均衡器只做轮询", "over_simplification", "还可使用最少连接、加权、一致性哈希等策略。"),
    ("mc_040", "防火墙", "认为防火墙只能过滤 IP 和端口", "over_simplification", "现代防火墙可基于应用层协议、状态、用户身份等过滤。"),
    ("mc_041", "代理", "认为正向代理和反向代理是同一种东西", "concept_confusion", "正向代理代表客户端访问外网；反向代理代表服务端接收外部请求。"),
    ("mc_042", "Socket", "认为 Socket 就是端口号", "concept_confusion", "Socket 是 (IP, 端口, 协议) 等标识通信端点的抽象。"),
    ("mc_043", "半开连接", "认为 SYN 洪水只会占用客户端资源", "reasoning_breakdown", "服务端会为半开连接维护状态，SYN 洪水主要攻击服务端。"),
    ("mc_044", "TCP 重传", "认为超时重传和快速重传是同一机制", "concept_confusion", "超时重传基于 RTO；快速重传基于重复 ACK。"),
    ("mc_045", "Nagle 算法", "认为 Nagle 算法提高所有 TCP 应用性能", "over_simplification", "Nagle 适合小数据包场景，实时交互应用可能需关闭。"),
    ("mc_046", "DNS 缓存", "认为 DNS 查询结果永不失效", "flow_omission", "DNS 记录有 TTL，缓存会过期并重新查询。"),
    ("mc_047", "DNS 污染", "认为 DNS 只能返回正确结果", "reasoning_breakdown", "DNS 响应可能被篡改或劫持，需要 DNSSEC 等机制防护。"),
    ("mc_048", "FTP", "认为 FTP 只使用一个端口", "concept_confusion", "FTP 控制连接用 21 端口，数据连接另开端口（主动/被动模式）。"),
    ("mc_049", "SMTP", "认为发邮件时客户端直接投递到收件人邮箱服务器", "flow_omission", "通常经发件人 SMTP 服务器中继，再路由到收件人 MX。"),
    ("mc_050", "WebSocket", "认为 WebSocket 是 HTTP 的一个方法", "layer_misplacement", "WebSocket 通过 HTTP Upgrade 建立，之后是独立的全双工协议。"),
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


def write_course_chapters() -> int:
    """Copy bundled course chapter markdown into data/cleaned for course_docs indexing."""
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    if not SEED_CHAPTERS_DIR.exists():
        print(f"[WARN] seed chapters missing: {SEED_CHAPTERS_DIR}")
        return 0
    count = 0
    for seed in sorted(SEED_CHAPTERS_DIR.glob("chapter*.md")):
        target = CLEANED_DIR / seed.name
        target.write_text(seed.read_text(encoding="utf-8"), encoding="utf-8")
        count += 1
    print(f"Wrote {count} course chapter files to {CLEANED_DIR}")
    return count


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
    chapter_count = write_course_chapters()
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(manifest)} sources, {len(MISCONCEPTIONS)} misconceptions, {chapter_count} course chapters.")


if __name__ == "__main__":
    main()
