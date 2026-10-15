# Genome Studio — единые команды.
# На Windows используйте `make` из Git Bash, MSYS2, WSL или chocolatey.

.PHONY: help install install-dev build build-prod build-dev test lint format typecheck clean docker-dev docker-prod

PYTHON := uv run python
PYTEST := uv run pytest
RUFF := uv run ruff
MYPY := uv run mypy

help:
@echo "Genome Studio — доступные команды:"
@echo ""
@echo "  make install          — установить prod-зависимости"
@echo "  make install-dev      — установить dev-зависимости"
@echo "  make build            — собрать всё (Rust + Python + UI)"
@echo "  make build-prod       — собрать prod"
@echo "  make build-dev        — собрать dev (локально)"
@echo "  make test             — прогнать тесты"
@echo "  make lint             — ruff + eslint"
@echo "  make format           — автоформат"
@echo "  make typecheck        — mypy + tsc"
@echo "  make clean            — очистить артефакты"
@echo "  make docker-dev       — docker compose up"
@echo "  make docker-prod      — собрать prod-образ"

install:
uv sync --no-dev

install-dev:
uv sync --all-extras
cd core-rs && maturin develop --features python
cd ui && pnpm install

build:
cd core-rs && cargo build --release
cd ui && pnpm build

build-prod:
cd core-rs && cargo build --release --no-default-features
cd ui && pnpm build:prod
./scripts/check-prod-build.sh

build-dev:
cd core-rs && maturin develop --features "python,dev_override"
cd ui && pnpm build:dev

test:
$(PYTEST) backend/tests

test-all:
$(PYTEST) backend/tests
cd core-rs && cargo test
cd ui && pnpm typecheck

lint:
$(RUFF) check .
cd ui && pnpm lint

format:
$(RUFF) format .
cd core-rs && cargo fmt
cd ui && pnpm exec prettier --write "src/**/*.{ts,tsx,css}"

typecheck:
$(MYPY) backend
cd ui && pnpm typecheck

clean:
rm -rf backend/build backend/dist .pytest_cache .mypy_cache .ruff_cache
rm -rf core-rs/target
rm -rf ui/dist ui/node_modules
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

docker-dev:
docker compose up --build

docker-prod:
docker build -f Dockerfile.prod -t gs:prod .
