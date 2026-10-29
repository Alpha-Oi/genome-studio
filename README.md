# Genome Studio

[![CI](https://github.com/Alpha-Oi/genome-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/Alpha-Oi/genome-studio/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Rust](https://img.shields.io/badge/rust-1.82%2B-orange.svg)](https://www.rust-lang.org/)
[![Node](https://img.shields.io/badge/node-24%2B-green.svg)](https://nodejs.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

> Workbench для исследователей генной инженерии: цель на естественном языке превращается в стратегию, план, дизайн gRNA, симуляцию и PDF-отчёт.

## Что это

Genome Studio — единая среда для молекулярных биологов, генетиков и метаболических инженеров. Вместо десятка разных инструментов (SnapGene, Benchling, IGV, VEP, SpliceAI, Excel) — одна программа, где учёный формулирует **что** он хочет, а система предлагает **как** и показывает **последствия**.

**Ключевая идея:** цель, дерево последствий, план, симуляция, отчёт — в одном месте.

## Возможности

- **Интент-слой** — фраза "knockout gene lacZ in E. coli" превращается в формализованную цель, план и warnings.
- **BioKG** — граф знаний (гены, пути, репрессоры) влияет на рекомендации: для усиления lacZ система предложит нокаут репрессора lacI.
- **CRISPR-дизайн** — поиск gRNA (NGG PAM), scoring (GC, поли-T, Doench-эвристики), off-target Hamming-поиск.
- **Batch gRNA design** — дизайн для нескольких последовательностей сразу (FASTA multi-record).
- **Симуляция правок** — SNP и индели, определение ORF, трансляция, эффект (silent / missense / nonsense / frameshift).
- **Consequence tree** — правка, транскрипт, белок, путь, фенотип с confidence на каждом шаге.
- **Sequencing симуляция** — Sanger-хроматограмма и NGS-распределение reads по аллелям.
- **Warnings Registry** — объекты проекта (уровни T0/T1/T2), нельзя удалить, только acknowledge с причиной.
- **Экспорт** — FASTA, VCF, GenBank, PDF-отчёт (с поддержкой кириллицы).
- **Проекты и эксперименты** — SQLite, всё сохраняется, можно duplicate и скачать JSON.
- **Related history** — под целью показываются похожие прошлые эксперименты.
- **Local / multi-user режимы** — заложены архитектурно (см. docs/15-multiuser-architecture.md).

## Быстрый старт

**Требуется:** Python 3.12, Node.js 24+, pnpm 9+, Rust 1.82+ (опционально, для core-rs).

Backend (терминал 1):

    git clone https://github.com/Alpha-Oi/genome-studio.git
    cd genome-studio
    uv sync --extra dev --package genome-studio-backend
    uv run --package genome-studio-backend uvicorn genome_studio.api.app:create_app --factory --host 127.0.0.1 --port 8000 --reload

Frontend (терминал 2):

    cd ui
    pnpm install
    pnpm dev

Открой http://localhost:5173 — увидишь рабочее пространство.

## Тесты

    uv run --package genome-studio-backend pytest backend/tests -q   # ~157 тестов
    pnpm --dir ui typecheck                                            # TypeScript strict
    pnpm --dir ui build:prod                                           # prod-сборка

## Архитектура

**Backend** (Python 3.12 + FastAPI):

- intent/ — парсер цели (rule-based, позже LLM)
- knowledge/ — BioKG (граф генов и путей)
- reasoning/ — Intervention Mapper и Planner
- crispr/ — gRNA дизайн, PAM, off-target
- simulation/ — правки, ORF, эффекты, Sanger/NGS
- warnings/ — реестр warnings
- export/ — FASTA, VCF, GenBank
- report/ — PDF (reportlab + DejaVu)
- data/ — SQLAlchemy и SQLite (aiosqlite)
- auth/ — заглушки для multi-user

**Frontend** (React 18 + TypeScript + Vite):

- panels/ — Projects, Experiments, Chat, CRISPR, Simulation, Sequencing, Warnings
- components/ — PlanCard, GuideList, ConsequenceTree, Chromatogram, RelatedHistory

**Core** (Rust, опционально): Build Resolver, crypto (ed25519), feature-флаги prod/dev.

## Технологический стек

| Слой | Технология |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, aiosqlite, pydantic v2 |
| Frontend | React 18, TypeScript 5.9, Vite 6 |
| Core | Rust 1.99, PyO3, ed25519-dalek |
| PDF | reportlab 4.2, DejaVu Sans |
| Инфра | Docker, GitHub Actions |
| Тесты | pytest (157), ruff, mypy (essential checks), tsc |

## Документация

- Обзор: docs/00-overview.md
- Видение: docs/01-vision.md
- Архитектура: docs/02-architecture.md
- Модули: docs/03-modules.md
- Multi-user: docs/15-multiuser-architecture.md
- Роадмап: docs/11-roadmap.md
- Безопасность: docs/07-policy-security.md
- ADR: adr/

## Roadmap

**Готово:** интент-слой, CRISPR, симуляция, sequencing, warnings, экспорт, PDF, batch-дизайн, related history.

**В планах:** выравнивание последовательностей, экран выбора режима, авторизация, организации, LLM-парсер.

## Вклад

См. CONTRIBUTING.md.

## Лицензия

См. LICENSE.