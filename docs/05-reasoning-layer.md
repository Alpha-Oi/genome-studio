# Reasoning Layer

## Назначение

Из Goal Object построить дерево стратегий и план действий.

## BioKG - граф знаний

### Узлы
- Gene, Protein, Pathway, Phenotype
- Variant, Drug, CellLine, Organism
- RegulatoryElement, SpliceSite

### Рёбра
- regulates, activates, inhibits
- interacts_with, binds
- expressed_in, localized_in
- associated_with, causes
- catalyzes, transports

### Источники
- Reactome, KEGG, GO
- STRING, BioGRID
- ClinVar, gnomAD, COSMIC
- UniProt, Ensembl, PDB
- ENCODE, Addgene

### Хранение
- Neo4j (Cypher) - граф
- PostgreSQL + pgvector - векторный поиск
- DuckDB + Parquet - аналитика

## Intervention Mapper

### Прямые цели

Цель                | Вмешательство
--------------------|--------------------------------
↑ экспрессия        | промотор, энхансер, копийность
↓ экспрессия        | KO, RNAi, CRISPRi
Изменить функцию    | точечные мутации в CDS
Устойчивость        | нокаут гена-мишени

### Косвенные цели
1. Найти путь в KEGG/Reactome.
2. Найти лимитирующие узлы.
3. Предложить ↑/↓ узлов.
4. Проверить токсичность, регуляцию.

### Ранжирование

score = w1 * predicted_effect
      - w2 * off_target_risk
      - w3 * essentiality_risk
      - w4 * complexity
      - w5 * cost
      + w6 * confidence

Веса настраиваются: conservative / aggressive.

## Planner

- HTN (Hierarchical Task Network) или A* / beam search
- Дерево: цель -> стратегия -> действие -> шаг
- Backtracking: альтернативы
- Учёт: эффект, риск, стоимость, обратимость

## Explainer

Каждое предложение:
- почему - с ссылкой на источник
- уверенность - с методом
- альтернативы - с trade-off

## Технологии

- Python: networkx, igraph, numpy, scikit-learn
- Neo4j driver, psycopg
- Redis для кэша
- Jinja2 для шаблонов
- LLM для объяснений
