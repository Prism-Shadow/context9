# Multi-stage build Dockerfile for Context9 (Frontend + Backend)
# This Dockerfile builds both the frontend and backend for production deployment

# Stage 1: Build frontend
FROM node:20-slim AS frontend-builder

WORKDIR /build/web

# Copy frontend package files
COPY web/package*.json ./

# Install frontend dependencies
RUN npm ci

# Copy frontend source code
COPY web/ ./

# Build frontend for production
# Set VITE_API_BASE_URL to empty string for production mode
# This makes the frontend use relative paths (same origin) since backend serves both API and frontend
ENV VITE_API_BASE_URL=""
RUN npm run build

# Stage 2: Build backend Python dependencies
FROM python:3.14-slim AS backend-builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
RUN pip install --no-cache-dir uv

# Copy project files for dependency installation
COPY pyproject.toml ./
COPY context9/ ./context9/

# Install Python dependencies using uv
RUN uv pip install --system --no-cache -e .

# Stage 3: Runtime stage
FROM python:3.14-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from build stage
COPY --from=backend-builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy application code
COPY context9/ ./context9/
COPY pyproject.toml ./

# Copy built frontend from frontend-builder stage
COPY --from=frontend-builder /build/web/dist ./web/dist

# Copy startup script (optional, for convenience)
COPY scripts/start.py ./scripts/start.py

# Note: 
# - config.yaml should be provided via volume mount: -v /path/to/config.yaml:/app/config.yaml
# - Environment variables should be provided via --env-file .env (recommended) or -e flags
#   The .env file only needs to contain the optional CONTEXT9_PORT (defaults to 8011 if not set)

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Port mapping is configured at runtime via -p HOST_PORT:CONTAINER_PORT
# The application listens on the port specified by CONTEXT9_PORT environment variable (default: 8011)
# Example: -p 8080:8080 (if CONTEXT9_PORT=8080) or -p 8080:8011 (if using default)

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CONTEXT9_PORT=8011

# Default startup command
# Frontend is already built in the frontend-builder stage, so we directly start the backend server
# The backend server will serve both API and frontend static files from web/dist
# 
# Usage examples:
# 1. Recommended: Using --env-file to load environment variables:
#    docker run -d \
#               --name context9 \
#               -p 8011:8011 \
#               -v /path/to/config.yaml:/app/config.yaml \
#               --env-file .env \
#               --restart unless-stopped \
#               context9:latest \
#               python -m context9.server --config_file config.yaml --github_sync_interval 600
#
# 2. Using start.py script with --env-file (start.py will also load .env from container):
#    docker run -d \
#               --name context9 \
#               -p 8011:8011 \
#               -v /path/to/config.yaml:/app/config.yaml \
#               --env-file .env \
#               --restart unless-stopped \
#               context9:latest \
#               python scripts/start.py --skip_build --config_file config.yaml --github_sync_interval 600
#
# 3. Using individual environment variables with -e flags (if not using --env-file):
#    docker run -d \
#               --name context9 \
#               -p 8011:8011 \
#               -v /path/to/config.yaml:/app/config.yaml \
#               -e CONTEXT9_PORT=8011 \
#               --restart unless-stopped \
#               context9:latest \
#               python -m context9.server --config_file config.yaml --github_sync_interval 600
#
# 4. Changing the port via CONTEXT9_PORT environment variable:
#    # If .env contains: CONTEXT9_PORT=8080
#    docker run -d \
#               --name context9 \
#               -p 8080:8080 \
#               -v /path/to/config.yaml:/app/config.yaml \
#               --env-file .env \
#               --restart unless-stopped \
#               context9:latest \
#               python -m context9.server --config_file config.yaml --github_sync_interval 600
#    # Note: The -p HOST_PORT:CONTAINER_PORT mapping must match CONTEXT9_PORT
#
# Default: sync repos every 600 seconds (10 minutes)
# Note: --config_file is typically required for production use
# The .env file only needs to contain the optional CONTEXT9_PORT (defaults to 8011 if not set)
# The application reads CONTEXT9_PORT at runtime to determine which port to listen on
CMD ["python", "-m", "context9.server", "--github_sync_interval", "600"]
