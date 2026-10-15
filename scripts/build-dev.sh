#!/usr/bin/env bash
set -euo pipefail

echo "==> Building DEV"

# Проверка: dev-сборка только локально
if [ -n "${CI:-}" ]; then
    echo "ERROR: dev build must not run in CI"
    exit 1
fi

# Rust
cd core-rs
maturin develop --features dev_override
cd ..

# Python
uv sync --all-extras

# Frontend
cd ui
pnpm install
pnpm build
cd ..

# Docker
docker build -f Dockerfile.dev -t gs:dev .

echo "==> DEV ready"
