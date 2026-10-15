# Роадмап

## Фаза 0. Фундамент (1-2 мес.)

- Монорепо.
- Build-система: prod / internal / dev.
- Dev-ключ, изоляция, sandbox.
- Документы и политика.
- CI/CD с проверками.

## Фаза 1. MVP (3-4 мес.)

- Goal Object + чат.
- BioKG для одного организма (E. coli или yeast).
- Intervention Mapper на правилах.
- Planner: дерево 3 уровня.
- Consequence Explorer.
- Браузер (IGV.js), редактор, экспорт VCF/GenBank.
- Warnings в проекте.
- T0/T1/T2.

## Фаза 2. CRISPR-модуль (2-3 мес.)

- Guides, PAM, on/off-target.
- Base / prime editing.
- Симуляция NHEJ/HDR.
- Интеграция с Benchling.

## Фаза 3. Анализ (2-3 мес.)

- VEP, SpliceAI, CADD.
- Трансляция ORF.
- Структура белка.
- Notebook-панель.

## Фаза 4. Коллаборация (2-3 мес.)

- Роли, шаринг, комментарии.
- Real-time.
- Review workflow.
- Уведомления.

## Фаза 5. ML-слой (3-4 мес.)

- Fine-tune моделей на ClinVar/COSMIC.
- Прогноз патогенности.
- Генерация последовательностей (осторожно).
- Feedback loop.

## Фаза 6. Интеграции (3-4 мес.)

- Addgene, Twist, IDT.
- LIMS, лабораторные роботы.
- API, SDK.

## Фаза 7. Enterprise (4-6 мес.)

- On-prem.
- GxP.
- SSO, SCIM.
- Аудит для регуляторики.

## Фаза 8. Сообщество (постоянно)

- Маркетплейс.
- Публичные пайплайны.
- Форум.

## Rust-внедрение

Месяц  | Что
-------|----------------------------
1-6    | Python-only MVP
7      | Парсинг FASTA/FASTQ
8      | PAM-поиск
9      | Парсинг BAM/VCF
10     | ORF, Consequence Engine
11     | Dev Override, крипто
12     | WASM для фронта
Год 2  | Tauri, gRPC
