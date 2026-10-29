"""Intent Parser - rule-based разбор фразы пользователя в Goal Object.

На старте - без LLM. Простые правила и regex.
Позже можно заменить на LLM + RAG, но интерфейс останется тот же.
"""

from __future__ import annotations

import re

from genome_studio.intent.goal import (
    Constraint,
    Direction,
    Goal,
    GoalIntent,
    Organism,
    PhenotypeTarget,
    Target,
)


class ParseError(ValueError):
    """Не удалось разобрать фразу."""


# --- Словари для распознавания ---------------------------------------------

_INTENT_PATTERNS: list[tuple[GoalIntent, list[str]]] = [
    (GoalIntent.KNOCKOUT, [r"\bknockout\b", r"\bko\b", r"нокаут", r"выключ"]),
    (
        GoalIntent.INCREASE_EXPRESSION,
        [r"\bincrease\b", r"\bupregulate\b", r"\boverexpress\b", r"повыс", r"увелич", r"усил"],
    ),
    (
        GoalIntent.DECREASE_EXPRESSION,
        [r"\bdecrease\b", r"\bdownregulate\b", r"\bsilence\b", r"пониз", r"уменьш", r"подав"],
    ),
    (GoalIntent.KNOCKIN, [r"\bknock[- ]?in\b", r"\binsert\b", r"встав", r"встро"]),
    (GoalIntent.MODIFY_FUNCTION, [r"\bmodify\b", r"\bmutate\b", r"измен", r"мутир"]),
    (GoalIntent.PRODUCE_METABOLITE, [r"\bproduce\b", r"производ", r"синтез"]),
    (GoalIntent.RESISTANCE, [r"\bresistance\b", r"устойчив", r"резист"]),
]

_ORGANISM_PATTERNS: list[tuple[Organism, list[str]]] = [
    (Organism.E_COLI, [r"\be\.?\s*coli\b", r"кишечн"]),
    (Organism.YEAST, [r"\byeast\b", r"\bs\.?\s*cerevisiae\b", r"дрожж"]),
    (Organism.CHO, [r"\bcho\b", r"яичник"]),
    (Organism.HUMAN, [r"\bhuman\b", r"\bhek\b", r"человек"]),
    (Organism.MOUSE, [r"\bmouse\b", r"\bmus\b", r"мышь"]),
]

_DIRECTION_PATTERNS: list[tuple[Direction, list[str]]] = [
    (Direction.UP, [r"\bup\b", r"\bincrease\b", r"повыс", r"больше", r"↑"]),
    (Direction.DOWN, [r"\bdown\b", r"\bdecrease\b", r"пониз", r"меньше", r"↓"]),
    (Direction.ABOLISH, [r"\babolish\b", r"\bremove\b", r"устран", r"убрать"]),
]

# Имя гена: латиница, цифры, дефисы; не слишком длинное
_GENE_RE = re.compile(r"\b([A-Z][A-Z0-9]{1,9}[A-Za-z0-9]?)\b")


def _match_intent(text: str) -> tuple[GoalIntent, float]:
    """Определяет намерение. Возвращает (intent, confidence)."""
    for intent, patterns in _INTENT_PATTERNS:
        for p in patterns:
            if re.search(p, text, re.IGNORECASE):
                return intent, 0.9
    return GoalIntent.UNKNOWN, 0.3


def _match_organism(text: str) -> Organism | None:
    for org, patterns in _ORGANISM_PATTERNS:
        for p in patterns:
            if re.search(p, text, re.IGNORECASE):
                return org
    return None


def _match_direction(text: str) -> Direction | None:
    for direction, patterns in _DIRECTION_PATTERNS:
        for p in patterns:
            if re.search(p, text, re.IGNORECASE):
                return direction
    return None


def _extract_gene(text: str) -> str | None:
    """Ищет имя гена. Пытается найти самое "геноподобное" слово."""
    # Явная форма "gene X" или "ген X"
    m = re.search(r"(?:gene|ген)\s+([A-Za-z][A-Za-z0-9]{1,9})", text, re.IGNORECASE)
    if m:
        return str(m.group(1))

    # Иначе - ищем uppercase-подобное слово
    candidates = _GENE_RE.findall(text)
    # Отфильтровываем стоп-слова
    stops = {"DNA", "RNA", "PCR", "CRISPR", "CHO", "KO", "KI"}
    candidates = [c for c in candidates if c.upper() not in stops]
    if candidates:
        return str(candidates[0])
    return None


def _extract_constraints(text: str) -> tuple[Constraint, ...]:
    result: list[Constraint] = []
    if re.search(r"(do not|don'?t|не)\s+(modify|меняй|трогай)\s+(cds|кодир)", text, re.IGNORECASE):
        result.append(Constraint.DO_NOT_MODIFY_CDS)
    if re.search(r"\bstable\b|\bстабильн", text, re.IGNORECASE):
        result.append(Constraint.STABLE_INTEGRATION)
    if re.search(r"\btransient\b|\bтранзиент", text, re.IGNORECASE):
        result.append(Constraint.TRANSIENT_ONLY)
    return tuple(result)


def parse_goal(text: str) -> Goal:
    """Разбирает фразу пользователя в Goal Object.

    Raises:
        ParseError: если не удалось определить цель или ген.
    """
    if not text or not text.strip():
        raise ParseError("empty input")

    original = text
    text = text.strip()

    intent, confidence = _match_intent(text)
    if intent == GoalIntent.UNKNOWN:
        raise ParseError(f"could not determine intent from: {text!r}")

    organism = _match_organism(text)
    if organism is None:
        raise ParseError(f"could not determine organism from: {text!r}")

    gene = _extract_gene(text)
    if gene is None:
        raise ParseError(f"could not determine target gene from: {text!r}")

    direction = _match_direction(text)
    phenotype: PhenotypeTarget | None = None
    if direction is not None:
        metric = (
            "protein_yield"
            if intent
            in (
                GoalIntent.INCREASE_EXPRESSION,
                GoalIntent.DECREASE_EXPRESSION,
            )
            else "phenotype"
        )
        phenotype = PhenotypeTarget(metric=metric, direction=direction)

    constraints = _extract_constraints(text)

    return Goal(
        raw_text=original,
        intent=intent,
        target=Target(gene=gene, organism=organism),
        phenotype_target=phenotype,
        constraints=constraints,
        confidence=confidence,
    )
