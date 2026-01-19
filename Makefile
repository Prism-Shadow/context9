.PHONY: default build commit quality style test dev dev-backend dev-frontend build-frontend

check_dirs := .

default:
	uv pip install -e .

build:
	uv build

commit:
	uv run pre-commit install
	uv run pre-commit run --all-files

quality:
	uv run ruff check $(check_dirs)
	uv run ruff format --check $(check_dirs)

style:
	uv run ruff check $(check_dirs) --fix
	uv run ruff format $(check_dirs)

test:
	uv pip install -e .[tests]
	uv run pytest -vvv tests

# Development commands
dev:
	@echo "Starting both backend and frontend servers..."
	@python scripts/start_dev.py --github_sync_interval 600 --config_file config.yaml

dev-backend:
	@echo "Starting backend server only..."
	@python scripts/start_dev.py --backend-only --github_sync_interval 600 --config_file config.yaml

dev-frontend:
	@echo "Starting frontend server only..."
	@python scripts/start_dev.py --frontend-only --github_sync_interval 600 --config_file config.yaml

# Build frontend for production
build-frontend:
	@echo "Building frontend for production..."
	@cd gui && npm run build
	@echo "Frontend built! Now backend will serve static files automatically."