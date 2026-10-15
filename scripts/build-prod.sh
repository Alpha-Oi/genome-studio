#!/usr/bin/env bash
set -euo pipefail

echo "==> Building PROD"

# Rust — без dev-флагов
cd core-rs
maturin build --release --no-default-features
cd ..

# Python
uv sync --no-dev

# Frontend
cd ui
pnpm install --frozen-lockfile
pnpm build
cd ..

# Проверки
./scripts/check-prod-build.sh

# Docker
docker build -f Dockerfile.prod -t gs:prod .

echo "==> PROD ready"
