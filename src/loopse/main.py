"""Socrates-Cube 应用入口。

初始化 FastAPI 应用，注册 CORS 中间件和 API 路由。
支持两种运行模式：

- **在线模式**：连接讯飞星火 LLM API，全功能运行。
- **Mock 模式**（`--mock-mode` 或 `MOCK_MODE=true`）：使用 MockProvider
  模拟 LLM 响应，无需 API Key 即可离线演示全链路。

日志级别通过 `LOG_LEVEL` 环境变量配置（默认 INFO）。
"""
import argparse
import logging
import os
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Check for --mock-mode flag
_parser = argparse.ArgumentParser(add_help=False)
_parser.add_argument("--mock-mode", action="store_true", default=False)
_args, _ = _parser.parse_known_args()
MOCK_MODE = _args.mock_mode or os.getenv("MOCK_MODE", "").lower() in ("1", "true", "yes")
if MOCK_MODE:
    os.environ["MOCK_MODE"] = "true"

# 日志级别：演示环境 INFO，调试时设 LOG_LEVEL=DEBUG
_log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s | %(message)s",
)
logger = logging.getLogger("loopse")
logger.info("Socrates-Cube 启动中 | LOG_LEVEL=%s | MOCK_MODE=%s", _log_level, MOCK_MODE)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Socrates-Cube",
    version="1.0.0",
    description="苏格拉底方块——多智能体自适应《计算机网络》学习系统（软件杯A3）",
)


# ═══════════════════════════════════════════════════════════════════════════
# 中间件：请求追踪 ID
# ═══════════════════════════════════════════════════════════════════════════

class RequestIDMiddleware(BaseHTTPMiddleware):
    """\u4e3a\u6bcf\u4e2a\u8bf7\u6c42\u6ce8\u5165\u552f\u4e00 X-Request-ID\uff0c\u5e76\u56de\u5199\u5230\u54cd\u5e94\u5934\u3002"""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


app.add_middleware(RequestIDMiddleware)

# ═══════════════════════════════════════════════════════════════════════════
# CORS：从环境变量读取允许源（开发默认 ["*"]，生产环境配置具体域名）
# ═══════════════════════════════════════════════════════════════════════════

def _parse_cors_origins() -> list[str]:
    """  解析 ALLOWED_ORIGINS 环境变量。
    - 未配置或 * → [“*”]（开发 / Mock 模式）
    - JSON 数组字符串 → 解析为列表
    - 逗号分隔字符串 → 拆分为列表
    """
    import json as _json
    raw = os.getenv("ALLOWED_ORIGINS", "*").strip()
    if raw == "*":
        return ["*"]
    try:
        parsed = _json.loads(raw)
        if isinstance(parsed, list):
            return [str(o).strip() for o in parsed]
    except Exception:
        pass
    return [o.strip() for o in raw.split(",") if o.strip()]


_CORS_ORIGINS = _parse_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# ═══════════════════════════════════════════════════════════════════════════
# 全局异常处理器
# ═══════════════════════════════════════════════════════════════════════════

@app.exception_handler(RequestValidationError)
async def _validation_error_handler(request: Request, exc: RequestValidationError):
    """Pydantic 校验失败 → 422，返回统一格式的中文提示。"""
    request_id = getattr(request.state, "request_id", "-")
    logger.warning(
        "[%s] 请求参数校验失败 %s %s: %s",
        request_id, request.method, request.url.path, exc.errors()
    )
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "code": 422,
            "message": "请求参数格式错误，请检查输入",
            "errors": exc.errors(),
            "request_id": request_id,
        },
    )


@app.exception_handler(HTTPException)
async def _http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 业务异常 → 统一包装格式。"""
    request_id = getattr(request.state, "request_id", "-")
    if exc.status_code >= 500:
        logger.error(
            "[%s] HTTP %d %s %s: %s",
            request_id, exc.status_code, request.method, request.url.path, exc.detail
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "code": exc.status_code,
            "message": exc.detail,
            "request_id": request_id,
        },
    )


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception):
    """未捕获的裄异常 → 500，仅返回通用提示，完整跟踪写日志。"""
    request_id = getattr(request.state, "request_id", "-")
    logger.exception(
        "[%s] 未处理异常 %s %s",
        request_id, request.method, request.url.path
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "code": 500,
            "message": "服务器内部错误，请稍后重试或联系管理员",
            "request_id": request_id,
        },
    )


@app.on_event("startup")
async def _on_startup():
    """应用启动时初始化数据库"""
    try:
        from .db.connection import init_db
        init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error("数据库初始化失败（非致命）: %s", e)


# 注册所有路由
from .api.health import router as health_router
from .api.auth import router as auth_router
from .api.chat import router as chat_router
from .api.profile import router as profile_router
from .api.logs import router as logs_router
from .api.resources import router as resources_router
from .api.path import router as path_router
from .api.simulator import router as simulator_router
from .api.challenger import router as challenger_router
from .api.rl import router as rl_router
from .api.question import router as question_router
from .api.export import router as export_router
from .api.persona import router as persona_router
from .api.onboarding import router as onboarding_router
from .api.career import router as career_router
from .api.video_gen import router as video_gen_router
from .api.books import router as books_router
from .api.infographic import router as infographic_router
from .api.knowledge_base import router as kb_router
from .api.exam import router as exam_router
from .api.federated_privacy import router as federated_privacy_router
from .api.automation import router as automation_router
from .api.generate_media import router as media_router
from .api.search import router as search_router
from .api.scenario import router as scenario_router
from .api.homework import router as homework_router
from .api.lesson import router as lesson_router
from .api.virtual_teacher import router as virtual_teacher_router
from .api.stats import router as stats_router
from .api.admin import router as admin_router

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(profile_router)
app.include_router(logs_router)
app.include_router(resources_router)
app.include_router(path_router)
app.include_router(simulator_router)
app.include_router(challenger_router)
app.include_router(rl_router)
app.include_router(question_router)
app.include_router(export_router)
app.include_router(persona_router)
app.include_router(onboarding_router)
app.include_router(career_router)
app.include_router(video_gen_router)
app.include_router(books_router)
app.include_router(infographic_router)
app.include_router(kb_router)
app.include_router(exam_router)
app.include_router(federated_privacy_router)
app.include_router(automation_router)
app.include_router(media_router)
app.include_router(search_router)
app.include_router(scenario_router)
app.include_router(homework_router)
app.include_router(lesson_router)
app.include_router(virtual_teacher_router)
app.include_router(stats_router)
app.include_router(admin_router)
