# Технологический стек

## Карта по компонентам

Компонент              | Язык
-----------------------|----------------------
UI                     | TypeScript + React
Геномный браузер       | TypeScript + IGV.js
Редактор               | TypeScript + Monaco
Desktop                | Rust (Tauri)
WASM                   | Rust -> WASM
API                    | Python (FastAPI)
Intent Layer           | Python
Reasoning Layer        | Python
Planner                | Python
Policy T0/T1/T2        | Python
Dev Override           | Rust
Build Resolver         | Rust
Крипто                 | Rust (ed25519-dalek)
Парсинг FASTA/FASTQ    | Rust (needletail)
Парсинг BAM/VCF        | Rust (noodles)
PAM / off-target       | Rust
Consequence Engine     | Rust + Python
ML-инференс            | Python (PyTorch, ONNX)
Интеграции             | Python
Оркестрация            | Python (Celery)
БД                     | SQL
Граф                   | Cypher (Neo4j)
Вектора                | pgvector

## Backend

- Python 3.12
- FastAPI + uvicorn
- pydantic v2
- SQLAlchemy 2.0 + Alembic
- Celery + Redis
- Biopython, pysam, pyfaidx
- uv (менеджер пакетов)

## Rust-модули (PyO3 + maturin)

- needletail - FASTA/FASTQ
- noodles - BAM/CRAM/VCF
- rust-bio - алгоритмы
- rayon - параллелизм
- ed25519-dalek - крипто
- pyo3 + maturin - связка

## Данные

- PostgreSQL 16 + pgvector
- Neo4j (или пока PG)
- MinIO (S3)
- Redis
- DuckDB + Parquet

## ML

- PyTorch
- HuggingFace transformers
- ONNX Runtime
- sentence-transformers

## Frontend

- React 18 + TypeScript
- Vite
- Tailwind + shadcn/ui
- IGV.js
- Monaco Editor
- React Flow
- TanStack Query
- Zustand
- pnpm

## Инфра

- Docker + Compose (MVP) / K8s
- GitHub Actions
- Keycloak / Ory
- Vault
- Prometheus + Grafana
- OpenTelemetry

## Правило

- Python - скорость разработки.
- Rust - скорость выполнения (только после замеров).
- TypeScript - интерфейс.
- Начинаете на Python, добавляете Rust по мере необходимости.
