# ADR 0003: Rust для hot paths

## Статус
Принято.

## Решение
Rust для:
- парсинга FASTA/FASTQ/BAM/VCF
- PAM/off-target поиска
- Consequence Engine
- крипто (dev-ключ)
- Build Resolver
- WASM

## Обоснование
- Скорость на 3 ГБ.
- Память.
- Крипто.
- WASM для фронта.

## Триггеры для Rust
- Операция > 10 сек на Python.
- Память > 2 ГБ.
- Off-target > минуты.
- Симуляция > 1000 вариантов.
