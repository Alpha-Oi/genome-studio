# Backend

Python backend Genome Studio.

## Структура

- src/genome_studio/ — основной пакет
  - __main__.py — точка входа
  - config.py — конфигурация
  - build_resolver.py — определение сборки (prod/internal/dev)
  - intent/ — Intent Layer
  - reasoning/ — Reasoning Layer
  - execution/ — Execution Layer
  - policy/ — Policy Layer (T0/T1/T2)
  - api/ — FastAPI
  - data/ — работа с БД

## Запуск

uv run python -m genome_studio

## Тесты

uv run pytest
