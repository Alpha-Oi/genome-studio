# Архитектура

## Слои

L1. UI Layer         - Chat | Tree | Browser | Editor | Notebook
L2. Intent Layer     - Parser -> Goal Object -> Clarifier
L3. Reasoning Layer  - BioKG -> Mapper -> Planner -> Explainer
L4. Policy Layer     - T0 Science | T1 Biosec | T2 Legal | Dev Override
L5. Execution Layer  - Simulator | Predictors | Consequence Engine
L6. Data Layer       - BioKG | Vectors | Files | Projects | Audit
L7. Infra Layer      - Auth | Storage | Queue | Monitoring | CI/CD

## Поток данных

Пользователь: "хочу ↑ белок X"
   ↓
Intent Parser (LLM + bio-онтологии) -> Goal Object
   ↓
Intervention Mapper (BioKG + правила)
   ↓
Planner (HTN / A* / beam) -> дерево цели
   ↓
Policy Layer (T0 / T1 / T2) -> warnings
   ↓
Execution (симуляция, предикторы) -> consequences
   ↓
UI: дерево, браузер, отчёт

## Две сборки

PROD BUILD
- T0: отключается пользователем
- T1: отключается с трением
- T2: жёстко
- Warnings: в проекте
- Нет dev-кода

DEV BUILD (только локально)
- T0/T1/T2: всё отключаемо
- Dev Panel
- Подписанный ключ
- Loopback-only
- Export: disabled
- Sandbox DB

## Goal Object

{
  "goal_id": "g_001",
  "intent": "increase_expression",
  "target": {
    "gene": "X",
    "organism": "Cricetulus griseus",
    "cell_line": "CHO-K1"
  },
  "constraints": ["do_not_modify_CDS"],
  "phenotype_target": {
    "metric": "protein_yield",
    "direction": "up",
    "magnitude": ">=2x"
  },
  "context": {
    "existing_edits": [],
    "available_tools": ["CRISPR-Cas9"]
  }
}

## Warning Object

{
  "warning_id": "w_042",
  "level": "T0",
  "type": "essential_gene_knockout",
  "severity": "high",
  "message": "Ген A эссенциален. Нокаут вероятно летален.",
  "evidence": ["DepMap: score -0.85", "PMID:12345678"],
  "status": "acknowledged",
  "acknowledged_by": "user_123",
  "acknowledgment_note": "Изучаю механизм летальности.",
  "persists": true,
  "linked_edits": ["edit_007"]
}

## Consequence Node

{
  "node_id": "c_001",
  "parent": null,
  "type": "transcript",
  "description": "Нет мРНК (NMD)",
  "confidence": 0.90,
  "method": "rule-based",
  "sources": ["PMID:xxx"],
  "children": ["c_002", "c_003"]
}
