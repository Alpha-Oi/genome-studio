# Execution Layer

## Назначение

Симулировать правки, предсказывать последствия,
интегрировать внешние инструменты.

## Simulator

### Мутации
- SNP: transition / transversion, CpG-контекст
- Индели: вставки, делеции, дупликации
- Структурные: инверсии, транслокации, CNV
- Регуляторные: промоторы, энхансеры, splice-сайты

### CRISPR
- Cas9, Cas12, Cas13
- Base editing, prime editing
- NHEJ / HDR
- On-target / off-target

### Клонирование
- Gibson, Golden Gate
- Рестрикция / лигирование
- Автодизайн праймеров

### Масштаб
- Monte Carlo для распределений
- Батч-симуляция 1000+ вариантов (Rust)

## Predictors

Инструмент              | Что             | Как
------------------------|-----------------|------------------
VEP, SnpEff             | Аннотация       | Python-обёртка
SpliceAI                | Сплайсинг       | ONNX Runtime
CADD, REVEL             | Патогенность    | ONNX / TF
Enformer                | Регуляция       | PyTorch
Nucleotide Transformer  | Эффекты         | HuggingFace
AlphaFold / ESMFold     | Структура       | Внешний сервис
BWA, Minimap2           | Выравнивание    | CLI
samtools, bcftools      | BAM/VCF         | CLI
MAFFT, Clustal          | MSA             | CLI

## Consequence Engine

Каскад:

правка
  -> транскрипт (NMD, усечение)
    -> белок (потеря функции, доминант-негатив)
      -> путь (активация, подавление, компенсация)
        -> фенотип (устойчивость, рост, метаболизм)

Каждый узел:
- уверенность (0-1)
- метод (rule / ML / literature)
- источники
- дети (для дерева)

Реализация:
- обход графа - Rust (быстро)
- правила и объяснения - Python

## Интеграции

- Benchling, SnapGene, Geneious - импорт/экспорт
- Addgene - поиск плазмид
- Twist, IDT, GenScript - заказ
- NCBI, Ensembl, UniProt - референсы
- Лабораторные роботы - только prod

## Технологии

- Python: Biopython, pysam, pyfaidx, scikit-bio
- Rust: noodles, needletail, rust-bio, rayon
- ML: PyTorch, HuggingFace, ONNX Runtime
- CLI-обёртки для внешних инструментов
- Celery для фоновых задач
