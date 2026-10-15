#!/usr/bin/env bash
set -euo pipefail

echo "==> Checking prod build"

# Нет dev-флагов
if grep -r "dev_override" dist/prod/ 2>/dev/null; then
    echo "ERROR: dev_override found in prod build"
    exit 1
fi

# T2 всегда включён
if grep -r "t2_override = true" dist/prod/ 2>/dev/null; then
    echo "ERROR: t2_override in prod build"
    exit 1
fi

# Dev panel отсутствует
if [ -d "dist/prod/dev_panel" ]; then
    echo "ERROR: dev_panel in prod build"
    exit 1
fi

echo "==> Prod build OK"
