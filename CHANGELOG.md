# Changelog

Все значимые изменения проекта.

Формат: [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/).
Версии: [Semantic Versioning](https://semver.org/lang/ru/).

## [Unreleased]

### Планируется

- Alignment: выравнивание нескольких последовательностей
- Экран выбора режима (local / multi) при первом запуске
- Авторизация (bcrypt + JWT) для multi-mode
- Организации и шаринг проектов
- LLM-парсер целей (опционально)

## [0.1.0] - 2026-10-15

Первый функциональный релиз. Полный цикл: цель, план, дизайн, симуляция, отчёт.

### Добавлено

- Intent Layer: правило-ориентированный парсер цели (EN и RU)
- BioKG: граф знаний (гены, пути, отношения)
- Reasoning Layer: Intervention Mapper и Planner
- CRISPR: поиск gRNA (NGG PAM), scoring, off-target Hamming-поиск
- Batch gRNA design: дизайн для нескольких последовательностей
- FASTA upload: загрузка .fasta/.fa/.fas через UI
- Simulation: SNP и индели, ORF, эффекты (silent, missense, nonsense, frameshift)
- Consequence tree: правка, транскрипт, белок, путь, фенотип
- Sequencing: Sanger-хроматограмма и NGS-распределение reads
- Warnings Registry: уровни T0/T1/T2, acknowledge lifecycle, дедупликация
- Export: FASTA, VCF, GenBank
- PDF-отчёт: reportlab и DejaVu (поддержка кириллицы)
- Projects и Experiments: SQLite persistence, CRUD, duplicate, JSON-export
- Related history: SQL-поиск похожих прошлых экспериментов
- Multi-user архитектура заложена: заглушки auth/, endpoint /mode, ADR 0007, 0008, 0009
- UX: табы в центре, бейджи LOCAL/SERVER, toast-уведомления, шаблоны целей
- Инфра: Docker (prod и dev), GitHub Actions, три сборки (prod, internal, dev)

### Тесты

- 157 тестов backend (pytest), strict TypeScript, prod-сборка без dev-кода