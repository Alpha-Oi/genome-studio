# Genome Studio — команды (just).
# Установка just: https://github.com/casey/just

set shell := ["bash", "-cu"]

default:
    @just --list

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
    uv run pytest backend/tests

lint:
    uv run ruff check .
    cd ui && pnpm lint

format:
    uv run ruff format .
    cd core-rs && cargo fmt

typecheck:
    uv run mypy backend
    cd ui && pnpm typecheck

clean:
    rm -rf backend/build backend/dist .pytest_cache .mypy_cache .ruff_cache
    rm -rf core-rs/target
    rm -rf ui/dist ui/node_modules

docker-dev:
    docker compose up --build

docker-prod:
    docker build -f Dockerfile.prod -t gs:prod .
