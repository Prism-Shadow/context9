# Context9 启动脚本

## 开发环境启动

### 方式 1: 使用 Python 脚本（推荐）

```bash
# 启动前后端
python scripts/start_dev.py --github_sync_interval 600 --config_file config.yaml

# 只启动后端
python scripts/start_dev.py --backend-only --github_sync_interval 600 --config_file config.yaml

# 只启动前端
python scripts/start_dev.py --frontend-only --github_sync_interval 600 --config_file config.yaml
```

### 方式 2: 使用 Shell 脚本

```bash
# 启动前后端
./scripts/start.sh --github_sync_interval 600 --config_file config.yaml

# 只启动后端
./scripts/start.sh --backend-only --github_sync_interval 600 --config_file config.yaml

# 只启动前端
./scripts/start.sh --frontend-only --github_sync_interval 600 --config_file config.yaml
```

### 方式 3: 使用 Makefile

```bash
# 启动前后端
make dev

# 只启动后端
make dev-backend

# 只启动前端
make dev-frontend
```

## 生产环境启动

### 1. 构建前端

```bash
# 使用 Makefile
make build-frontend

# 或手动构建
cd gui && npm run build
```

### 2. 启动后端（自动服务前端静态文件）

```bash
uv run python -m context9.server \
  --github_sync_interval 600 \
  --config_file config.yaml
```

后端会自动检测 `gui/dist` 目录，如果存在则提供静态文件服务。

访问 `http://localhost:8011` 即可访问完整应用（前端 + 后端 API）。

## 参数说明

- `--github_sync_interval`: GitHub 同步间隔（秒）
- `--config_file`: 配置文件路径
- `--port`: 后端服务器端口（默认：8011）
- `--enable_github_webhook`: 启用 GitHub Webhook（与 `--github_sync_interval` 互斥）
- `--frontend-only`: 只启动前端
- `--backend-only`: 只启动后端
