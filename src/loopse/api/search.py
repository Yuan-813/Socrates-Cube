"""行业资料检索与收藏接口。

支持：
1. 聚合搜索（精选资料库优先，可扩展外部搜索）
2. 一键收藏到个人知识库
3. 书签列表查询/删除
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/search", tags=["search"])


# ── 精选资料库（内置，无需外部 API）──────────────────────────────────────────
_CURATED_RESOURCES: list[dict] = [
    {"title": "华为 HCIA-Datacom 官方教材", "url": "https://support.huawei.com/enterprise/zh/", "type": "official_doc", "topics": ["HCIA", "路由交换", "华为"]},
    {"title": "思科 CCNA 学习指南", "url": "https://www.cisco.com/c/en/us/training-events/training-certifications/certifications/associate/ccna.html", "type": "official_doc", "topics": ["CCNA", "思科", "网络工程师"]},
    {"title": "RFC 793 - TCP 协议规范", "url": "https://datatracker.ietf.org/doc/html/rfc793", "type": "rfc", "topics": ["TCP", "传输层", "可靠传输"]},
    {"title": "RFC 791 - IPv4 协议规范", "url": "https://datatracker.ietf.org/doc/html/rfc791", "type": "rfc", "topics": ["IP", "网络层", "IPv4"]},
    {"title": "RFC 9293 - TCP（更新版）", "url": "https://datatracker.ietf.org/doc/html/rfc9293", "type": "rfc", "topics": ["TCP", "传输控制协议"]},
    {"title": "RFC 768 - UDP 协议规范", "url": "https://datatracker.ietf.org/doc/html/rfc768", "type": "rfc", "topics": ["UDP", "无连接", "传输层"]},
    {"title": "RFC 1034/1035 - DNS 协议规范", "url": "https://datatracker.ietf.org/doc/html/rfc1034", "type": "rfc", "topics": ["DNS", "域名解析", "应用层"]},
    {"title": "RFC 9110 - HTTP 语义规范", "url": "https://datatracker.ietf.org/doc/html/rfc9110", "type": "rfc", "topics": ["HTTP", "应用层", "Web"]},
    {"title": "RFC 8446 - TLS 1.3 规范", "url": "https://datatracker.ietf.org/doc/html/rfc8446", "type": "rfc", "topics": ["TLS", "加密", "安全"]},
    {"title": "RFC 8200 - IPv6 规范", "url": "https://datatracker.ietf.org/doc/html/rfc8200", "type": "rfc", "topics": ["IPv6", "网络层", "下一代IP"]},
    {"title": "Wireshark 官方学习资料", "url": "https://www.wireshark.org/docs/", "type": "tool_doc", "topics": ["抓包", "故障排查", "网络分析"]},
    {"title": "B站《计算机网络》谢希仁配套视频", "url": "https://search.bilibili.com/all?keyword=计算机网络谢希仁", "type": "video", "topics": ["计算机网络", "谢希仁", "教材配套"]},
    {"title": "中国大学MOOC 计算机网络课程", "url": "https://www.icourse163.org/search.htm#query=计算机网络", "type": "mooc", "topics": ["MOOC", "在线课程", "计算机网络"]},
    {"title": "Packet Tracer 模拟器官方下载", "url": "https://www.netacad.com/courses/packet-tracer", "type": "tool", "topics": ["思科", "模拟器", "实验"]},
    {"title": "GNS3 网络仿真平台", "url": "https://www.gns3.com/", "type": "tool", "topics": ["仿真", "路由器", "实验环境"]},
    {"title": "华为云学院-网络技术", "url": "https://edu.huaweicloud.com/courses?keywords=网络", "type": "mooc", "topics": ["华为", "网络技术", "在线学习"]},
    {"title": "IANA 协议号注册表", "url": "https://www.iana.org/protocols", "type": "reference", "topics": ["IANA", "协议号", "端口号"]},
    {"title": "TCP/IP 详解（W.Stevens）豆瓣书评", "url": "https://book.douban.com/subject/1088054/", "type": "book", "topics": ["TCP/IP", "经典书籍", "Stevens"]},
    {"title": "Linux 内核网络子系统文档", "url": "https://www.kernel.org/doc/html/latest/networking/", "type": "official_doc", "topics": ["Linux", "内核", "网络实现"]},
    {"title": "阿里云网络学习资料", "url": "https://help.aliyun.com/zh/vpc/", "type": "cloud_doc", "topics": ["云网络", "VPC", "阿里云"]},
]

_KEYWORD_TOPIC_MAP = {
    "tcp": ["TCP", "传输层", "三次握手", "四次挥手"],
    "udp": ["UDP", "无连接", "传输层"],
    "http": ["HTTP", "应用层", "Web"],
    "dns": ["DNS", "域名解析", "应用层"],
    "ip": ["IP", "网络层", "IPv4", "IPv6"],
    "路由": ["路由交换", "路由协议", "网络层"],
    "交换": ["路由交换", "局域网", "以太网"],
    "安全": ["TLS", "加密", "安全", "防火墙"],
    "hcia": ["HCIA", "华为", "路由交换"],
    "ccna": ["CCNA", "思科", "网络工程师"],
    "抓包": ["抓包", "故障排查", "网络分析"],
    "仿真": ["模拟器", "仿真", "实验环境"],
    "视频": ["MOOC", "在线课程", "视频"],
    "教材": ["计算机网络", "谢希仁", "教材配套"],
}


def _search_curated(query: str, limit: int = 10) -> list[dict]:
    """在精选资料库中搜索匹配的资源。"""
    query_lower = query.lower()
    results = []
    seen = set()

    # 精确主题匹配
    for resource in _CURATED_RESOURCES:
        topics = [t.lower() for t in resource["topics"]]
        title_lower = resource["title"].lower()
        match_score = 0
        if query_lower in title_lower:
            match_score += 3
        for topic in topics:
            if query_lower in topic or topic in query_lower:
                match_score += 2
        # 关键词扩展匹配
        for kw, related_topics in _KEYWORD_TOPIC_MAP.items():
            if kw in query_lower:
                for rt in related_topics:
                    if rt.lower() in topics:
                        match_score += 1
        if match_score > 0 and resource["url"] not in seen:
            seen.add(resource["url"])
            results.append({**resource, "match_score": match_score, "source": "curated"})

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:limit]


# ── 请求模型 ───────────────────────────────────────────────────────────────

class ResourceSearchRequest(BaseModel):
    q: str = Field(..., min_length=1, max_length=100, description="搜索关键词")
    limit: int = Field(default=10, ge=1, le=30)


class BookmarkRequest(BaseModel):
    user_id: str = Field(default="student-001")
    resource_url: str = Field(..., description="资料 URL")
    resource_title: str = Field(..., description="资料标题")
    resource_type: str = Field(default="link", description="link/doc/video/paper")
    source: str = Field(default="web", description="来源：web/kb/generated")


# ── 路由 ──────────────────────────────────────────────────────────────────

@router.get("/resources")
def search_resources(q: str, limit: int = 10):
    """搜索行业资料（精选库优先，可扩展外部搜索）。"""
    if not q.strip():
        raise HTTPException(status_code=400, detail="搜索关键词不能为空")
    results = _search_curated(q.strip(), limit=limit)
    # 如未找到精确匹配，补充通用推荐
    if not results:
        results = [
            {
                "title": "RFC 文档搜索",
                "url": f"https://datatracker.ietf.org/doc/search/?name={q}",
                "type": "rfc_search",
                "topics": [q],
                "source": "external",
                "match_score": 1,
            },
            {
                "title": f"B站搜索「{q}」",
                "url": f"https://search.bilibili.com/all?keyword={q}+计算机网络",
                "type": "video",
                "topics": [q],
                "source": "external",
                "match_score": 1,
            },
        ]
    return {
        "query": q,
        "total": len(results),
        "results": [
            {
                "title": r["title"],
                "url": r["url"],
                "type": r.get("type", "link"),
                "topics": r.get("topics", []),
                "source": r.get("source", "curated"),
            }
            for r in results
        ],
    }


@router.post("/bookmark")
def add_bookmark(req: BookmarkRequest):
    """一键收藏资料到个人知识库。"""
    try:
        from ..db.repositories import get_db_session
        from ..db.models import Bookmark
        bookmark_id = str(uuid.uuid4())[:16]
        with get_db_session() as db:
            bm = Bookmark(
                id=bookmark_id,
                user_id=req.user_id,
                resource_url=req.resource_url,
                resource_title=req.resource_title,
                resource_type=req.resource_type,
                source=req.source,
                created_at=datetime.now(),
            )
            db.add(bm)
        return {
            "success": True,
            "bookmark_id": bookmark_id,
            "message": f"已收藏「{req.resource_title}」",
        }
    except Exception as exc:
        logger.error("[Search] 收藏失败 user=%s: %s", req.user_id, exc)
        raise HTTPException(status_code=500, detail="收藏失败") from exc


@router.get("/bookmarks/{user_id}")
def get_bookmarks(user_id: str, resource_type: Optional[str] = None, limit: int = 20):
    """获取用户收藏列表。"""
    try:
        from ..db.repositories import get_db_session
        from ..db.models import Bookmark
        with get_db_session() as db:
            q = db.query(Bookmark).filter(Bookmark.user_id == user_id)
            if resource_type:
                q = q.filter(Bookmark.resource_type == resource_type)
            bookmarks = q.order_by(Bookmark.created_at.desc()).limit(limit).all()
            return {
                "user_id": user_id,
                "total": len(bookmarks),
                "bookmarks": [
                    {
                        "id": bm.id,
                        "title": bm.resource_title,
                        "url": bm.resource_url,
                        "type": bm.resource_type,
                        "source": bm.source,
                        "created_at": bm.created_at.isoformat() if bm.created_at else None,
                    }
                    for bm in bookmarks
                ],
            }
    except Exception as exc:
        logger.warning("[Search] 获取收藏失败 user=%s: %s", user_id, exc)
        return {"user_id": user_id, "total": 0, "bookmarks": []}


@router.delete("/bookmark/{bookmark_id}")
def delete_bookmark(bookmark_id: str, user_id: str):
    """删除收藏。"""
    try:
        from ..db.repositories import get_db_session
        from ..db.models import Bookmark
        with get_db_session() as db:
            bm = db.query(Bookmark).filter(
                Bookmark.id == bookmark_id,
                Bookmark.user_id == user_id,
            ).first()
            if not bm:
                raise HTTPException(status_code=404, detail="收藏不存在")
            db.delete(bm)
        return {"success": True, "message": "已删除收藏"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="删除失败") from exc


@router.get("/curated")
def list_curated_resources(resource_type: Optional[str] = None):
    """返回内置精选资料库（全量或按类型过滤）。"""
    resources = _CURATED_RESOURCES
    if resource_type:
        resources = [r for r in resources if r.get("type") == resource_type]
    return {"total": len(resources), "resources": resources}
