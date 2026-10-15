#!/usr/bin/env bash
set -euo pipefail

echo "==> Running DEV (local only)"

# Проверка изоляции
if ip route | grep -q "default via"; then
    echo "WARNING: external network detected"
    echo "Dev mode requires isolation. Continue? [y/N]"
    read -r answer
    [ "$answer" = "y" ] || exit 1
fi

# Проверка ключа
if [ ! -f "$HOME/.gs/keys/dev-signing.key" ]; then
    echo "ERROR: dev signing key not found"
    exit 1
fi

# Запуск
export GS_BUILD=dev
export GS_MODE=dev
uv run python -m backend.dev
