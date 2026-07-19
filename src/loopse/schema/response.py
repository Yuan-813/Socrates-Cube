"""统一 API 响应格式。

所有路由应使用此模块中的包装器返回一致的响应结构：

    {
        "success": true,
        "code": 200,
        "message": "ok",
        "data": { ... }
    }

用法示例：
    from ..schema.response import ok, err, ApiResponse

    @router.get("/users/{id}")
    def get_user(id: str) -> ApiResponse[dict]:
        user = db.get(id)
        return ok(data=user, message="获取成功")

迁移策略：
    - 新路由直接使用此格式
    - 已有路由在下一次修改时迁移（向后兼容，不强制立即重写）
"""
from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ────────────────────────────────────────────────────────
# 核心响应模型
# ────────────────────────────────────────────────────────

class ApiResponse(BaseModel, Generic[T]):
    """泛型统一响应包装器。

    字段说明：
        success   - 业务是否成功（True/False）
        code      - HTTP 状态码或业务码
        message   - 人类可读的结果描述（成功时简短，失败时说明原因）
        data      - 业务数据负载（失败时可为 None）
        request_id - 请求追踪 ID（由 RequestIDMiddleware 注入）
    """
    success: bool = True
    code: int = 200
    message: str = "ok"
    data: Optional[T] = None
    request_id: Optional[str] = Field(default=None, description="请求追踪 ID")

    model_config = {"arbitrary_types_allowed": True}


class PagedApiResponse(ApiResponse[T], Generic[T]):
    """带分页信息的列表响应。"""
    total: int = 0
    page: int = 1
    size: int = 20


# ────────────────────────────────────────────────────────
# 快捷构造函数
# ────────────────────────────────────────────────────────

def ok(
    data: Any = None,
    message: str = "ok",
    code: int = 200,
    request_id: Optional[str] = None,
) -> dict:
    """构造成功响应（返回 dict，FastAPI 序列化为 JSON）。"""
    resp: dict[str, Any] = {
        "success": True,
        "code": code,
        "message": message,
        "data": data,
    }
    if request_id:
        resp["request_id"] = request_id
    return resp


def err(
    message: str,
    code: int = 400,
    data: Any = None,
    request_id: Optional[str] = None,
) -> dict:
    """构造失败响应（应配合 HTTPException 使用，或直接返回 JSONResponse）。"""
    resp: dict[str, Any] = {
        "success": False,
        "code": code,
        "message": message,
        "data": data,
    }
    if request_id:
        resp["request_id"] = request_id
    return resp


def paged(
    data: list,
    total: int,
    page: int = 1,
    size: int = 20,
    message: str = "ok",
) -> dict:
    """构造分页列表响应。"""
    return {
        "success": True,
        "code": 200,
        "message": message,
        "data": data,
        "total": total,
        "page": page,
        "size": size,
    }
