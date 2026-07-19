# ─────────────────────────────────────────────────────────────
# Socrates-Cube 后端 Dockerfile（multi-stage build）
# 阶段1 builder：安装依赖（利用 Docker layer 缓存）
# 阶段2 runtime：精简镜像，仅复制运行所需文件
# ─────────────────────────────────────────────────────────────

# ── 阶段1：依赖构建 ───────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# 安装编译依赖（bcrypt 等 C 扩展需要 gcc）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件（变化少，利用缓存加速重新构建）
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── 阶段2：运行时镜像 ─────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# 从 builder 阶段复制已安装的包
COPY --from=builder /install /usr/local

# 复制项目源码（排除 .dockerignore 中列出的文件）
COPY src/ ./src/
COPY config/ ./config/
COPY data/ ./data/
COPY scripts/ ./scripts/
COPY .env.example .env.example

# 创建数据目录（数据库 + 向量库挂载点）
RUN mkdir -p /app/data/vector_db /app/outputs

# 运行时不以 root 运行（安全最佳实践）
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# 环境变量默认值（可通过 docker run -e 覆盖）
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    LOG_LEVEL=INFO \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000

EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "src.loopse.main:app", "--host", "0.0.0.0", "--port", "8000"]
