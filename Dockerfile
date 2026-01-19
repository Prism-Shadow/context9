# Multi-stage build Dockerfile for Context9 MCP Server

# Stage 1: Build stage
FROM python:3.14-slim as builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy project files
COPY pyproject.toml ./
COPY context9/ ./context9/

# Install project dependencies
RUN pip install --no-cache-dir -e .

# Stage 2: Runtime stage
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies (curl for health checks, git for repository sync)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from build stage
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY context9/ ./context9/
COPY pyproject.toml ./
COPY config.yaml ./

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8011

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Default startup command (polling mode, sync every 600 seconds)
# Users can override this command when running the container to switch modes
CMD ["python", "-m", "context9.server", "--github_sync_interval", "600", "--config_file", "config.yaml"]

