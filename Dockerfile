# 多阶段构建 Dockerfile for Context9 MCP Server

# 阶段 1: 构建阶段
FROM python:3.14-slim as builder

# 设置工作目录
WORKDIR /build

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 升级 pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 复制项目文件
COPY pyproject.toml ./
COPY context9/ ./context9/

# 安装项目依赖
RUN pip install --no-cache-dir -e .

# 阶段 2: 运行阶段
FROM python:3.14-slim

# 设置工作目录
WORKDIR /app

# 安装运行时依赖（curl 用于健康检查，git 用于仓库同步）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制已安装的包
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY context9/ ./context9/
COPY pyproject.toml ./
COPY config.yaml ./

# 创建非 root 用户
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# 切换到非 root 用户
USER appuser

# 暴露端口
EXPOSE 8011

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8011/api/mcp/ || exit 1

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 默认启动命令（轮询模式，每 600 秒同步一次）
# 用户可以在运行容器时覆盖此命令来切换模式
CMD ["python", "-m", "context9.server", "--github_sync_interval", "600", "--config_file", "config.yaml"]

