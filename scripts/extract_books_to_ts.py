"""
从 data/books/ PDF 提取章节内容 → 生成 extra-books.ts  v2
- 有TOC的文字版PDF：按TOC L1章节切割  
- 无TOC的文字版PDF：先找目录页获取章节页码，再按页提取
- 图片扫描版PDF：使用预置高质量摘要文本（不强行OCR）

用法：
    python scripts/extract_books_to_ts.py
"""
from __future__ import annotations
import re, sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[1]
BOOKS_DIR = ROOT / "data" / "books"
OUT_TS = ROOT / "frontend" / "src" / "data" / "extra-books.ts"

MAX_CHAPTER_CHARS = 6000  # 每章前端展示上限
SKIP_KEYWORDS = {'封面', '书名', '版权', '彩插'}  # 去掉'目录'，保留前言


# ─── 工具函数 ────────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    text = re.sub(r'\x0c', '\n', text)
    text = re.sub(r'\r\n|\r', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if len(line) < 2:
            continue
        if re.match(r'^[—\-–·\s\d]+$', line):
            continue
        lines.append(line)
    return '\n'.join(lines)


def trim_chapter(text: str, fname: str = '', chapter_title: str = '') -> str:
    """截断章节内容并添加提示"""
    text = text.strip()
    if len(text) <= MAX_CHAPTER_CHARS:
        return text
    truncated = text[:MAX_CHAPTER_CHARS]
    # 在句号处截断
    last_period = max(truncated.rfind('。'), truncated.rfind('\n'))
    if last_period > MAX_CHAPTER_CHARS * 0.7:
        truncated = truncated[:last_period + 1]
    total_k = len(text) // 1000
    truncated += f'\n\n...（本章共约 {total_k}K 字，此处展示前 {MAX_CHAPTER_CHARS//1000}K 字，完整内容请参阅原书）'
    return truncated


def escape_ts(s: str) -> str:
    s = s.replace('\\', '\\\\')
    s = s.replace('`', '\\`')
    s = s.replace('${', '\\${')
    return s


def jstr(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


# ─── 提取策略 ────────────────────────────────────────────────────────────────

def extract_toc_book(doc: fitz.Document) -> list[dict]:
    """有TOC的文字版PDF：按L1章节提取"""
    toc = doc.get_toc()
    chapters_raw = []
    for level, title, page in toc:
        if level != 1:
            continue
        t = title.strip()
        # 清理标题中的页码（华为防火墙漫谈格式：第X章 标题／页码）
        t = re.sub(r'／\d+\s*$', '', t)
        t = re.sub(r'/\d+\s*$', '', t)
        t = t.strip()
        if any(kw in t for kw in SKIP_KEYWORDS):
            continue
        if len(t) < 2:
            continue
        chapters_raw.append((t, page))

    chapters = []
    for i, (title, start_pg) in enumerate(chapters_raw):
        end_pg = chapters_raw[i + 1][1] if i + 1 < len(chapters_raw) else doc.page_count
        end_pg = min(start_pg + 80, end_pg, doc.page_count)

        parts = []
        for pg in range(start_pg - 1, end_pg):
            parts.append(doc[pg].get_text())

        raw = clean_text('\n'.join(parts))
        if len(raw) < 30:
            continue

        content = trim_chapter(raw)
        ch_id = f"ch-{i+1}"
        chapters.append({'id': ch_id, 'title': title, 'content': content})
        print(f'    [{i+1}/{len(chapters_raw)}] "{title[:35]}" → {len(raw)}字')

    return chapters


def extract_hcia(doc: fitz.Document) -> list[dict]:
    """HCIA-Datacom：无TOC，从目录页解析章节+页码，再提取文本"""
    # Step1: 找目录页（包含"第X章"密集出现的页面）
    toc_page_idx = -1
    for pg_i in range(min(30, doc.page_count)):
        txt = doc[pg_i].get_text()
        if txt.count('第') >= 5 and ('章' in txt) and ('...' in txt or '……' in txt or '----' in txt or '.' * 4 in txt):
            toc_page_idx = pg_i
            break
        if txt.count('第') >= 5 and txt.count('章') >= 5:
            toc_page_idx = pg_i
            break

    # Step2: 从目录页或全文提取"第X章 标题"唯一列表
    CHAPTER_RE = re.compile(r'第\s*(\d+)\s*章\s*[\u4e00-\u9fff\w ]+')
    chapter_names: dict[int, str] = {}

    if toc_page_idx >= 0:
        toc_text = ''
        for p in range(toc_page_idx, min(toc_page_idx + 5, doc.page_count)):
            toc_text += doc[p].get_text() + '\n'
        for m in CHAPTER_RE.finditer(toc_text):
            num = int(m.group(1))
            title = m.group(0).strip()
            # 清理末尾省略号/页码
            title = re.sub(r'[\s.…\-]+\d+\s*$', '', title).strip()
            if num not in chapter_names:
                chapter_names[num] = title

    if not chapter_names:
        # fallback：扫全文找唯一章节标题
        for pg_i in range(doc.page_count):
            for line in doc[pg_i].get_text().split('\n'):
                m = re.match(r'^第\s*(\d{1,2})\s*章\s+([\u4e00-\u9fff]{2,20})', line.strip())
                if m:
                    num = int(m.group(1))
                    if num not in chapter_names:
                        chapter_names[num] = line.strip()

    print(f'    识别到{len(chapter_names)}个章节：{list(chapter_names.values())[:3]}...')

    if not chapter_names:
        return []

    # Step3: 找每章第一次在正文出现的页码（排除目录页前）
    start_offset = toc_page_idx + 5 if toc_page_idx >= 0 else 10
    chapter_pages: dict[int, int] = {}
    for pg_i in range(start_offset, doc.page_count):
        txt = doc[pg_i].get_text()
        if len(txt) < 30:
            continue
        first_lines = '\n'.join(txt.split('\n')[:8])
        for num, title in chapter_names.items():
            if num not in chapter_pages:
                ch_num_re = re.compile(r'第\s*' + str(num) + r'\s*章')
                if ch_num_re.search(first_lines):
                    chapter_pages[num] = pg_i
                    break

    if not chapter_pages:
        print('    警告：未找到章节起始页，使用全文扫描')
        return []

    # Step4: 按章节提取文本
    sorted_nums = sorted(chapter_pages.keys())
    chapters = []
    for i, num in enumerate(sorted_nums):
        title = chapter_names[num]
        start_pg = chapter_pages[num]
        end_num = sorted_nums[i + 1] if i + 1 < len(sorted_nums) else None
        end_pg = chapter_pages[end_num] if end_num else doc.page_count
        end_pg = min(start_pg + 60, end_pg)

        parts = []
        seen_header = False
        for pg in range(start_pg, end_pg):
            pg_txt = doc[pg].get_text()
            if not seen_header:
                parts.append(pg_txt)
                seen_header = True
            else:
                # 跳过与章节标题相同的页眉（通常在第一行）
                lines = pg_txt.split('\n')
                if lines and re.match(r'^第\s*\d+\s*章', lines[0].strip()):
                    parts.append('\n'.join(lines[1:]))
                else:
                    parts.append(pg_txt)

        raw = clean_text('\n'.join(parts))
        if len(raw) < 50:
            continue
        content = trim_chapter(raw)
        chapters.append({'id': f'ch-{num}', 'title': title, 'content': content})
        print(f'    第{num}章 "{title[:30]}" p{start_pg} → {len(raw)}字')

    return chapters


def extract_small_book(doc: fitz.Document, fname: str) -> list[dict]:
    """小型PDF（如网络安全 29页）：扫描全文，按章节合并"""
    CHAPTER_RE = re.compile(r'^第\s*(\d{1,2})\s*章\s+([\u4e00-\u9fff][\u4e00-\u9fff\w ]{1,20})')

    # 收集每章内容（按章号合并，解决重复页眉问题）
    chapter_texts: dict[int, list[str]] = {}
    chapter_titles: dict[int, str] = {}
    current_chapter = 0

    for pg_i in range(doc.page_count):
        pg_txt = doc[pg_i].get_text()
        lines = pg_txt.split('\n')
        for j, line in enumerate(lines):
            line_s = line.strip()
            m = CHAPTER_RE.match(line_s)
            if m:
                num = int(m.group(1))
                title = line_s
                # 清理标题
                title = re.sub(r'[\s.…]+\d+\s*$', '', title).strip()
                if num not in chapter_titles:
                    chapter_titles[num] = title
                    chapter_texts[num] = []
                current_chapter = num
                # 添加该行之后的内容
                remaining = '\n'.join(lines[j+1:])
                if current_chapter in chapter_texts:
                    chapter_texts[current_chapter].append(remaining)
                break
        else:
            # 本页没有新章节标题，全文追加到当前章
            if current_chapter > 0:
                # 跳过与章标题相同的页眉
                first_line = lines[0].strip() if lines else ''
                if re.match(r'^第\s*\d+\s*章', first_line):
                    content = '\n'.join(lines[1:])
                else:
                    content = pg_txt
                chapter_texts[current_chapter].append(content)

    chapters = []
    for num in sorted(chapter_titles.keys()):
        raw = clean_text('\n'.join(chapter_texts[num]))
        if len(raw) < 30:
            continue
        content = trim_chapter(raw)
        title = chapter_titles[num]
        chapters.append({'id': f'ch-{num}', 'title': title, 'content': content})
        print(f'    第{num}章 "{title[:30]}" → {len(raw)}字')

    return chapters


# ─── 图片PDF的高质量预设内容（从 data/books/image_chapters.json 加载）────────────────

_image_json_path = ROOT / 'data' / 'books' / 'image_chapters.json'
IMAGE_PDF_CHAPTERS: dict = json.loads(_image_json_path.read_text(encoding='utf-8')) if _image_json_path.exists() else {}

# ─── 书目配置 ────────────────────────────────────────────────────────────────

BOOK_CONFIGS: list[dict] = [
    {
        "file": "HCIA-Datacom 网络技术学习指南.pdf",
        "mode": "hcia",
        "meta": {
            "id": "hcia-datacom", "title": "HCIA-Datacom 网络技术学习指南",
            "shortTitle": "HCIA-Datacom", "author": "华为技术有限公司",
            "coverFrom": "#7f1d1d", "coverTo": "#dc2626", "coverText": "#fecaca", "coverTag": "认证",
            "academicPosition": "华为HCIA-Datacom认证官方学习指南，人民邮电出版社 2022 年出版",
            "coreContent": "TCP/IP协议栈、OSPF路由、STP/RSTP、VLAN交换、ACL/NAT、WLAN、IPv6、SDN自动化",
            "tags": ["华为", "HCIA", "OSPF", "VLAN", "STP", "IPv6", "SDN", "ARP"],
            "description": "华为HCIA-Datacom认证官方教材，涵盖数据通信基础、IP路由交换、网络安全、WLAN、广域网（PPP/MPLS）、IPv6及SDN网络自动化10大模块，理论联系华为VRP平台工程实践。",
        }
    },
    {
        "file": "《华为防火墙技术漫谈》.(徐慧洋).pdf",
        "mode": "toc",
        "meta": {
            "id": "hw-firewall", "title": "华为防火墙技术漫谈",
            "shortTitle": "防火墙漫谈", "author": "徐慧洋",
            "coverFrom": "#1c1917", "coverTo": "#57534e", "coverText": "#e7e5e4", "coverTag": "华为",
            "academicPosition": "华为防火墙领域技术专著，来自一线工程师的实战经验结晶",
            "coreContent": "华为USG防火墙有状态检测、安全策略、NAT、IPSec VPN、双机热备、DDoS防御",
            "tags": ["防火墙", "华为", "NAT", "IPSec VPN", "VRRP", "安全策略"],
            "description": "本书由华为资深网络工程师编写，系统讲解华为USG系列防火墙工作原理与工程实践，涵盖有状态检测、安全策略配置、NAT穿越、IPSec VPN隧道搭建、双机热备VRRP/VGMP及DDoS攻击防御等核心技术。",
        }
    },
    {
        "file": "网络安全基础与实践.pdf",
        "mode": "small",
        "meta": {
            "id": "net-security", "title": "网络安全基础与实践",
            "shortTitle": "网络安全", "author": "谭江汇 等",
            "coverFrom": "#312e81", "coverTo": "#4f46e5", "coverText": "#c7d2fe", "coverTag": "安全",
            "academicPosition": "高等院校计算机应用系列教材，清华大学出版社 2025 年出版",
            "coreContent": "防火墙技术、OSPF动态路由、ACL访问控制、渗透测试、IDS/IPS、流量分析",
            "tags": ["网络安全", "防火墙", "OSPF", "ACL", "渗透测试", "IDS/IPS"],
            "description": "本书全面深入介绍网络安全基础知识与核心技术，涵盖计算机网络协议、路由交换基础（eNSP）、防火墙配置、动态路由（OSPF/RIP）、入侵检测、渗透测试及网络流量分析，配套实验指导书。",
        }
    },
    {
        "file": "一本书读懂TCP_IP.pdf",
        "mode": "image",
        "preset_id": "tcpip-guide",
        "meta": {
            "id": "tcpip-guide", "title": "一本书读懂TCP/IP",
            "shortTitle": "TCP/IP入门", "author": "苑津莎 等",
            "coverFrom": "#0c4a6e", "coverTo": "#0284c7", "coverText": "#bae6fd", "coverTag": "TCP/IP",
            "academicPosition": "TCP/IP协议族大众化入门经典读本，图解形式直观易懂",
            "coreContent": "图解TCP三次握手/拥塞控制、IP路由转发、ARP地址解析、DNS解析、HTTP工作全流程",
            "tags": ["TCP/IP", "TCP", "UDP", "IP", "HTTP", "DNS", "路由", "ARP"],
            "description": "本书以大量图解形式直观讲解TCP/IP协议族各层工作原理，包括以太网帧格式、IP数据报路由转发、TCP可靠传输与拥塞控制、DNS域名解析、HTTP/HTTPS通信全过程，适合网络技术入门学习。",
        }
    },
    {
        "file": "《分布式云数据中心的建设与管理》.pdf",
        "mode": "image",
        "preset_id": "cloud-dc",
        "meta": {
            "id": "cloud-dc", "title": "分布式云数据中心的建设与管理",
            "shortTitle": "云数据中心", "author": "业界编著组",
            "coverFrom": "#27272a", "coverTo": "#52525b", "coverText": "#e4e4e7", "coverTag": "云计算",
            "academicPosition": "云数据中心建设规划与运维管理领域专业参考书",
            "coreContent": "Spine-Leaf架构设计、VXLAN/EVPN多租户、服务器虚拟化、SAN存储网络、自动化运维",
            "tags": ["云计算", "数据中心", "虚拟化", "SDN", "VXLAN", "分布式", "Spine-Leaf"],
            "description": "本书系统介绍分布式云数据中心的规划建设与运维管理，涵盖Spine-Leaf网络拓扑设计、VXLAN/EVPN多租户网络隔离、服务器虚拟化技术、SAN/NAS存储网络及数据中心自动化运维最佳实践。",
        }
    },
    {
        "file": "高级网络技术.pdf",
        "mode": "image",
        "preset_id": "adv-network",
        "meta": {
            "id": "adv-network", "title": "高级网络技术",
            "shortTitle": "高级网络", "author": "专业编写组",
            "coverFrom": "#064e3b", "coverTo": "#059669", "coverText": "#a7f3d0", "coverTag": "高级",
            "academicPosition": "面向高级网络工程师的技术参考书，覆盖前沿网络架构与技术",
            "coreContent": "ACL访问控制、网络可靠性、广域网、DHCPv6、IPv6路由、安全技术、WLAN、网络管理",
            "tags": ["企业网", "ACL", "IPv6", "BGP", "QoS", "WLAN", "网络安全"],
            "description": "本书面向有一定基础的网络工程师，系统介绍企业网分层架构、访问控制列表、网络可靠性设计、广域网技术、IPv6路由协议、安全技术及网络管理，配合真实场景工程实践案例。",
        }
    },
]


# ─── TypeScript 生成 ──────────────────────────────────────────────────────────

def book_to_ts(meta: dict, chapters: list[dict]) -> str:
    tags_str = ', '.join(jstr(t) for t in meta.get('tags', []))
    lines = [
        '  {',
        f"    id: {jstr(meta['id'])},",
        f"    title: {jstr(meta['title'])},",
        f"    shortTitle: {jstr(meta['shortTitle'])},",
        f"    author: {jstr(meta['author'])},",
        f"    coverFrom: {jstr(meta['coverFrom'])},",
        f"    coverTo: {jstr(meta['coverTo'])},",
        f"    coverText: {jstr(meta['coverText'])},",
        f"    coverTag: {jstr(meta['coverTag'])},",
        f"    academicPosition: {jstr(meta['academicPosition'])},",
        f"    coreContent: {jstr(meta['coreContent'])},",
        f"    tags: [{tags_str}],",
        f"    description: {jstr(meta['description'])},",
        '    chapters: [',
    ]
    for ch in chapters:
        content = escape_ts(ch['content'])
        lines += [
            '      {',
            f"        id: {jstr(ch['id'])},",
            f"        title: {jstr(ch['title'])},",
            f"        content: `{content}`,",
            '      },',
        ]
    lines += ['    ],', '  },']
    return '\n'.join(lines)


# ─── 主流程 ──────────────────────────────────────────────────────────────────

def main():
    all_books_ts = []
    total_chapters = 0

    for cfg in BOOK_CONFIGS:
        fname = cfg['file']
        meta = cfg['meta']
        mode = cfg['mode']
        pdf_path = BOOKS_DIR / fname

        print(f'\n处理: {fname}  (mode={mode})')

        if mode == 'image':
            preset_id = cfg.get('preset_id', meta['id'])
            chapters = IMAGE_PDF_CHAPTERS.get(preset_id, [])
            print(f'  [图片版PDF] 使用预置高质量内容，{len(chapters)}章')
        elif not pdf_path.exists():
            print(f'  [跳过] 文件不存在')
            continue
        else:
            doc = fitz.open(str(pdf_path))
            toc = doc.get_toc()
            print(f'  页数: {doc.page_count}  TOC条目: {len(toc)}')

            if mode == 'toc':
                chapters = extract_toc_book(doc)
            elif mode == 'hcia':
                chapters = extract_hcia(doc)
            elif mode == 'small':
                chapters = extract_small_book(doc, fname)
            else:
                chapters = []

            doc.close()

        if not chapters:
            print(f'  [警告] 无章节内容，跳过')
            continue

        print(f'  完成：{len(chapters)}章')
        total_chapters += len(chapters)
        all_books_ts.append(book_to_ts(meta, chapters))

    # 写入文件
    header = (
        "import type { Book } from './books'\n\n"
        "// 本文件由 scripts/extract_books_to_ts.py 自动生成\n"
        "// 文字版来源：data/books/ PDF（PyMuPDF提取）；图片版：高质量预置内容\n\n"
        "export const EXTRA_BOOKS: Book[] = [\n"
    )
    OUT_TS.write_text(header + '\n'.join(all_books_ts) + '\n]\n', encoding='utf-8')

    print(f'\n生成完成: {OUT_TS}')
    print(f'共 {len(all_books_ts)} 本书，{total_chapters} 章')


if __name__ == '__main__':
    main()
