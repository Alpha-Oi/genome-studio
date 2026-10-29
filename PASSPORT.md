# PASSPORT — Genome Studio

**Скопируй целиком в начало новой сессии.** Это даст полный контекст.

**Дата:** 2026-10-29 · **Версия:** v0.1.0 · **Репозиторий:** https://github.com/Alpha-Oi/genome-studio (public, main, Apache 2.0)

---

## 1. Что это и зачем

**Genome Studio** — workbench для исследователей генной инженерии. Принимает цель на естественном языке, предлагает стратегию, разворачивает дерево последствий (ген → белок → путь → фенотип), симулирует правки, экспортирует результат.

**Ключевое отличие от Benchling/SnapGene:** интент-слой + симуляция последствий в одном месте.

**Цель через 5 лет:** стандартная среда для CRISPR-дизайна, метаболической инженерии и синтетической биологии.

---

## 2. Окружение

| Поле | Значение |
|---|---|
| ОС | Windows 10 |
| Shell | PowerShell 7.6.6 |
| Рабочая папка | `D:\Development\genome-studio` |
| Python | 3.12.15 (через `uv`, `.python-version` в корне) |
| Rust | 1.99.0 + MSVC BuildTools 17.14.41 |
| Node.js | 24.21.0 (системный) |
| pnpm | 9.15.0 (corepack) |
| БД | SQLite через `aiosqlite`, файл в `~/.gs/data/gs.db` |
| Backend | FastAPI + uvicorn на `127.0.0.1:8000` |
| Frontend | Vite на `localhost:5173`, proxy `/api` → `8000` |

**Быстрые команды:**

    cd D:\Development\genome-studio
    gs-sync                                              # в $PROFILE: uv sync --extra dev
    uv run --package genome-studio-backend uvicorn genome_studio.api.app:create_app --factory --host 127.0.0.1 --port 8000 --reload
    pnpm --dir ui dev

---

## 3. Технологический стек

| Слой | Технология |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 + aiosqlite, pydantic v2 |
| Frontend | React 18, TypeScript 5.9 (strict), Vite 6 |
| Core | Rust 1.99, PyO3, ed25519-dalek |
| PDF | reportlab 4.2 + DejaVu Sans (кириллица) |
| Инфра | Docker, GitHub Actions, Dependabot (patch/minor only) |
| Тесты | pytest (157), ruff, mypy (essential checks), tsc |
| Package managers | uv (Python), pnpm (JS), cargo (Rust) |

---

## 4. Текущее состояние (v0.1.0)

### Метрики

| Метрика | Значение | Статус |
|---|---|---|
| Тестов | 157 passed | OK |
| Coverage | 80% | OK |
| mypy | 0 ошибок (52 файла) | OK |
| Ruff | All checks passed | OK |
| pip-audit | 0 CVE | OK |
| Prod-сборка | DEV PANEL не утекает | OK |
| CI | оба workflow зелёные | OK |
| Локальный = GitHub | синхронно | OK |

### Структура

    genome-studio/
    ├── backend/src/genome_studio/
    │   ├── api/           app.py, mode.py, parse.py, batch.py, related.py
    │   ├── auth/          заглушки: modes.py, dependencies.py
    │   ├── crispr/        pam.py, scoring.py, designer.py, offtarget.py
    │   ├── data/          db.py, models.py, repository.py
    │   ├── export/        fasta.py, vcf.py, genbank.py, report.py
    │   ├── intent/        goal.py, parser.py
    │   ├── io/            fasta.py
    │   ├── knowledge/     graph.py, seed.py
    │   ├── reasoning/     mapper.py, planner.py
    │   ├── report/        pdf.py + fonts/DejaVu*.ttf
    │   ├── simulation/    edit.py, orf.py, effects.py, consequence.py,
    │   │                  mixture.py, sanger.py, ngs.py
    │   └── warnings/      models.py, registry.py, generator.py
    ├── backend/tests/     157 тестов в 14 файлах
    ├── core-rs/src/       lib.rs, build.rs, crypto.rs, dev_override.rs, python.rs
    ├── ui/src/            App.tsx, panels/, components/, lib/, types/
    ├── docs/              15 docs + 4 policy
    ├── adr/               0001–0009
    └── .github/workflows/ ci.yml, build-prod.yml, check-secrets.yml

### Что работает

| Модуль | Backend | UI | Тесты |
|---|---|---|---|
| Intent (Goal Object + Parser) | да | — | да |
| BioKG (12 генов) | да | — | да |
| Reasoning (Mapper + Planner) | да | PlanCard | да |
| CRISPR (PAM, scoring) | да | CrisprPanel | да |
| Off-target (Hamming) | да | CrisprPanel | да |
| Batch gRNA design | да | CrisprPanel | да |
| Simulation (edit → effect) | да | SimulationPanel | да |
| Consequence tree | да | ConsequenceTree | да |
| Sequencing (Sanger + NGS) | да | Chromatogram SVG | да |
| Warnings Registry (T0/T1/T2) | да | WarningsPanel | да |
| Export (FASTA/VCF/GenBank) | да | кнопки | да |
| PDF-отчёт (кириллица) | да | кнопка PDF | да |
| Projects + Experiments | да | Projects/Experiments | да |
| FASTA upload | да | Upload button | да |
| Related history | да | RelatedHistory | да |
| Multi-user архитектура | заглушки | бейдж LOCAL/SERVER | — |
| /mode endpoint | да (всегда local) | — | да |

---
## 5. Принятые архитектурные решения

### ADR — сводка

| ADR | Решение |
|---|---|
| 0001 | Монорепо (backend + core-rs + ui + wasm) |
| 0002 | Python-first (80% кода), Rust только для hot paths |
| 0003 | Rust для парсинга/PAM/крипто, после замеров |
| 0004 | PyO3 + maturin для Python↔Rust |
| 0005 | Три сборки (prod/internal/dev) из одной базы |
| 0006 | Три уровня безопасности (T0/T1/T2) |
| 0007 | Два режима: local (без логина) / multi (с auth) |
| 0008 | Auth: User, Organization, Membership, роли |
| 0009 | Переиспользование знаний: C1 (SQL) → C2 (эмбеддинги) |

### Ключевые принципы

1. Наука свободна, ответственность явная, закон непреклонен.
2. LLM не принимает биологических решений — только парсит язык.
3. BioKG — источник истины. "Нокаут репрессора lacI" для ↑lacZ — следствие графа.
4. Warnings — объекты проекта, нельзя удалить, только acknowledge.
5. Dev Override — только compile-time флаг, отсутствует в prod-бинарнике.
6. Local mode без пароля, но слушает только 127.0.0.1.

---

## 6. Что сделано в последней сессии (аудит P0)

| Проблема | Было | Стало |
|---|---|---|
| mypy strict | 12 ошибок, конфиг потерян | 0 ошибок (essential checks) |
| Ruff конфиг | нет | есть (игнор RUF001-003, UP042) |
| Ruff ошибок | 198 | 0 |
| Coverage | не измерялось | 80% |
| pip-audit | не проверялось | 0 CVE |
| uv.lock, Cargo.lock | не в git | в git |
| .coverage в git | был | убран |
| CI: forbidden-files | regex-баг | glob, работает |
| CI: --all-extras | тянул 2 ГБ ML | --extra dev |
| README | "strict mypy" (ложь) | "essential checks" (правда) |

---

## 7. Что осталось — план следующей сессии

### P0 Stability (приоритет — 7 часов)

| # | Задача | Время | Зачем |
|---|---|---|---|
| P0.1 | Alembic миграции вместо create_all | 2 ч | Без миграций любое изменение модели = потеря данных в prod |
| P0.2 | Engine DI через app.state + conftest | 1 ч | Сейчас глобал _engine, тесты хрупкие, xdist не работает |
| P0.4 | Валидация payload эксперимента | 30 мин | payload: dict принимает 50 МБ JSON |
| P0.5 | Rate limiting (slowapi) | 1 ч | 100 req/min per IP |
| P0.6 | Дедуп warnings по target_gene + kind | 1 ч | Сейчас по message — при рефакторинге схлопнется не то |
| P1.2 | Разнести app.py (700 строк) на APIRouter | 1 ч | Читаемость |

### После P0 — можно деплоить

**Дальше (по приоритету):**

- P1.1 — /related через денормализацию (сейчас O(n))
- P1.6 — "злые" тесты (XSS, нагрузка, path traversal)
- P1.7 — Sanger noise
- P1.8 — Индексы в БД (kind, created_at)
- A0 — экран выбора режима (local/multi)
- A1 — реальная авторизация (bcrypt + JWT)
- B — организации и шаринг
- ML-слой — Fine-tune на ClinVar/COSMIC
- Alignment — MAFFT-подобное
- LLM-парсер — Claude/GPT вместо regex

---

## 8. Известные грабли

### Окружение Windows

1. Не ставить fnm — создаёт alias cd → Set-LocationWithFnm, ломает cd. Node через "winget install OpenJS.NodeJS.LTS".
2. MSVC link.exe not found — установить BuildTools + C++ workload.
3. Node.js MSI 1603 — скачать .msi вручную, "msiexec /i ... /qb REMOVE=ETW".
4. Python 3.14/3.16 не тянут ML — фиксировать 3.12 в .python-version.
5. pysam не ставится без MSVC — отложить до BuildTools.

### PowerShell

6. Все команды начинать с "cd D:\Development\genome-studio".
7. Многострочные файлы писать через [System.IO.File]::WriteAllText с here-string (одинарным или двойным) — не через Set-Content -Value.
8. Символ $1 в двойных кавычках интерполируется — в -replace использовать single-quoted или [regex]::Escape.
9. Замена переменной — глобально: -replace с границами слова, не точечный .Replace.
10. Не копировать вывод лога как команду.

### Backend

11. "uv pip install --package" не работает в workspace — "uv sync --extra dev --package genome-studio-backend".
12. SQLAlchemy async требует greenlet — sqlalchemy[asyncio], aiosqlite, greenlet>=3.0.
13. Env-переменные читать внутри функций, не module-level константы.
14. Тесты с БД — сбрасывать _engine = None в фикстуре, GS_DB_PATH в tmp_path.
15. Path.home() в тестах — вводить GS_HOME env var.
16. "uv sync" без --extra dev — теряет mypy/ruff/pytest-cov.

### Ruff

17. В русском проекте игнорировать RUF001-003 — иначе ruff ругается на кириллицу в строках.
18. UP042 (str, Enum → StrEnum) — откладывать.
19. N806 в тестах — lacI, GAL4 валидны, per-file-ignores.

### mypy

20. "strict = true" не для FastAPI — disallow_any_generics требует dict[str, Any] везде. Использовать явный набор: disallow_untyped_defs, warn_return_any, check_untyped_defs, warn_unused_ignores, no_implicit_optional.
21. Тесты исключить из mypy.
22. pydantic.mypy plugin — обязателен.
23. types-reportlab — в dev extras backend.

### CI/Git

24. uv.lock, Cargo.lock — в git для приложений.
25. check-secrets.yml — case с glob, не "grep -E" (regex).
26. "uv sync --all-extras" в CI — 2 ГБ ML. Только --extra dev.
27. .gitignore обязательные: .coverage*, htmlcov/, coverage.xml, "~/.gs/keys/", *.key, .env*
28. Перед коммитом — три проверки: "ruff check ." + "mypy backend" + "pytest -q".

### Frontend

29. "pnpm typecheck" не равно "pnpm build:prod" — прогонять обе.
30. Неиспользуемые переменные TS ломают build (TS6133).
31. Новые props — обновлять все вызовы в App.tsx.
32. Chrome авто-переводит UI — "html translate=no".
33. Vite HMR зависает — Ctrl+C, "pnpm dev" заново.

---

## 9. Как работать со мной

### Мои обязательства

1. Начинаю с результата/решения, без вступлений.
2. Даю блоки powershell — копировать целиком, запускать один Enter.
3. Не даю примеры вывода как команды.
4. Перед фиксом — диагностика, не 3 патча вслепую.
5. После каждого шага — три проверки (ruff, mypy, pytest).
6. Не выдумываю функции, версии, API.
7. Оцениваю по цифрам.
8. Одна задача за раз, большую разбиваю.

### Правила синхронизации

После каждого завершённого шага (все проверки зелёные):

    git add .
    git commit -m "тип: что сделано"
    git push

Проверка синхронности:

    git log --oneline -1
    git log --oneline -1 origin/main

Хеши одинаковые — синхронно. Не копить коммиты локально.

### Правило безопасности

Перед "git add .":

    git log --all --full-history -- "*.key" "*.pem" ".env*" "secrets/*"

Должно быть пусто.

---

## 10. Установка с нуля

    # 1. Python 3.12
    winget install --id Python.Python.3.12 -e

    # 2. uv
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    # Открыть новое окно PowerShell

    # 3. Rust + MSVC
    winget install --id Rustlang.Rustup -e
    winget install --id Microsoft.VisualStudio.2022.BuildTools -e --override "--quiet --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
    # Открыть новое окно PowerShell

    # 4. Node + pnpm
    winget install --id OpenJS.NodeJS.LTS -e
    # Открыть новое окно PowerShell
    corepack enable
    corepack prepare pnpm@9.15.0 --activate

    # 5. Git + GitHub CLI
    winget install --id Git.Git -e
    winget install --id GitHub.cli -e

    # 6. Клонировать
    git clone https://github.com/Alpha-Oi/genome-studio.git
    cd genome-studio

    # 7. Sync
    uv sync --extra dev --package genome-studio-backend
    cd ui && pnpm install && cd ..

    # 8. Проверить
    uv run --package genome-studio-backend pytest backend/tests -q
    uv run --package genome-studio-backend ruff check .
    uv run --package genome-studio-backend mypy backend
    pnpm --dir ui typecheck
    pnpm --dir ui build:prod

---

## 11. Ссылки

| Что | Где |
|---|---|
| Репозиторий | https://github.com/Alpha-Oi/genome-studio |
| Релиз | https://github.com/Alpha-Oi/genome-studio/releases/tag/v0.1.0 |
| Документация | docs/00-overview.md — docs/15-multiuser-architecture.md |
| ADR | adr/0001-monorepo.md — adr/0009-experiment-history.md |
| Безопасность | docs/07-policy-security.md, docs/policy/DEV_POLICY.md, SECURITY.md |
| Roadmap | docs/11-roadmap.md, CHANGELOG.md |

---

## 12. Готовые команды для новой сессии

Проверить что всё зелёное:

    cd D:\Development\genome-studio
    uv run --package genome-studio-backend ruff check .
    uv run --package genome-studio-backend mypy backend
    uv run --package genome-studio-backend pytest backend/tests -q
    pnpm --dir ui typecheck

Запустить локально:

    # Окно 1 — backend
    uv run --package genome-studio-backend uvicorn genome_studio.api.app:create_app --factory --host 127.0.0.1 --port 8000 --reload

    # Окно 2 — frontend
    cd ui
    pnpm dev

Открыть: http://localhost:5173

---

## 13. Статус на 2026-10-29

- Проект: v0.1.0, MVP готов, prod-ready после P0 Stability
- Оценка: 8/10 (было 6.0/10 в начале последней сессии)
- Git: синхронизирован с origin/main
- CI: оба workflow зелёные
- Следующая задача: Alembic + Engine DI (P0.1 + P0.2, ~3 часа)
- Долгосрочная цель: multi-user режим (A0 → A1 → B), ML-слой, Alignment
