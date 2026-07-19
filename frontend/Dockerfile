# ─────────────────────────────────────────────────────────────
# Socrates-Cube 前端 Dockerfile（multi-stage build）
# 阶段1 builder：Node 环境构建 dist
# 阶段2 runtime：Nginx 托管静态文件
# ─────────────────────────────────────────────────────────────

# ── 阶段1：前端构建 ───────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# 先复制 package.json（利用缓存加速 npm install）
COPY package.json package-lock.json ./

# 安装依赖（--legacy-peer-deps 兼容部分包版本冲突）
RUN npm ci --silent

# 复制源码并构建
COPY . .
RUN npm run build


# ── 阶段2：Nginx 托管 ─────────────────────────────────────────
FROM nginx:1.25-alpine AS runtime

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置（包含 SPA 回退、SSE 代理等）
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
