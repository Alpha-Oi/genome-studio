# Модули продукта

## 1. Intent Layer

Назначение: превратить фразу пользователя в Goal Object.

Компоненты:
- Parser (LLM + bio-онтологии)
- Clarifier (уточняющие вопросы)
- Dialog Manager (диалог)
- Goal Validator (pydantic)

Вход: текст.
Выход: Goal Object.

## 2. Reasoning Layer

Назначение: из Goal Object построить план.

Компоненты:
- BioKG (граф знаний)
- Intervention Mapper (цель -> вмешательства)
- Planner (HTN / A* / beam)
- Explainer (почему, ссылки, уверенность)

Вход: Goal Object.
Выход: Plan (дерево стратегий).

## 3. Execution Layer

Назначение: симулировать и предсказать.

Компоненты:
- Simulator (мутации, CRISPR)
- Predictors (VEP, SpliceAI, CADD, AlphaFold)
- Consequence Engine (каскад)
- Tools (BWA, samtools, MAFFT)

Вход: Plan.
Выход: Consequences + результаты.

## 4. Policy Layer

Назначение: безопасность и этика.

Компоненты:
- T0 Science (essentiality, off-target, toxicity)
- T1 Biosec (DURC, pathogen)
- T2 Legal (Australia Group, Select Agents)
- Warning Registry (объекты проекта)
- Audit Log (append-only)
- Dev Override (только dev-сборка)

## 5. UI Layer

Панели:
- Projects - список проектов
- Chat - диалог с агентом
- Goal Tree - дерево цели
- Browser - IGV.js
- Editor - последовательности, плазмиды
- Notebook - Jupyter
- Warnings - предупреждения
- Dev Panel - только dev

Режимы: Explore, Plan, Execute, Report.

## 6. Data Layer

- PostgreSQL - метаданные, warnings, аудит
- Neo4j / pgvector - граф, эмбеддинги
- S3/MinIO - файлы
- DuckDB + Parquet - аналитика
- Redis - кэш, очереди

## 7. Infra Layer

- Docker + K8s
- Keycloak/Ory - auth
- Vault - секреты
- Prometheus + Grafana - мониторинг
- CI/CD: prod / internal / dev
