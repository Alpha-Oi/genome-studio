"""Goal Object - формализованное представление цели пользователя.

Это центральная структура Intent Layer. Из неё рождается весь
дальнейший конвейер: BioKG -> Intervention Mapper -> Planner.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


class GoalIntent(str, Enum):
    """Что хочет сделать пользователь."""

    INCREASE_EXPRESSION = "increase_expression"
    DECREASE_EXPRESSION = "decrease_expression"
    KNOCKOUT = "knockout"
    KNOCKIN = "knockin"
    MODIFY_FUNCTION = "modify_function"
    PRODUCE_METABOLITE = "produce_metabolite"
    RESISTANCE = "resistance"
    UNKNOWN = "unknown"


class Organism(str, Enum):
    """Организм."""

    E_COLI = "Escherichia coli"
    YEAST = "Saccharomyces cerevisiae"
    CHO = "Cricetulus griseus"
    HUMAN = "Homo sapiens"
    MOUSE = "Mus musculus"


class Direction(str, Enum):
    """Направление изменения фенотипа."""

    UP = "up"
    DOWN = "down"
    ABOLISH = "abolish"


class Constraint(str, Enum):
    """Ограничения на правки."""

    DO_NOT_MODIFY_CDS = "do_not_modify_CDS"
    STABLE_INTEGRATION = "stable_integration"
    TRANSIENT_ONLY = "transient_only"
    NO_OFF_TARGET_ESSENTIAL = "no_off_target_in_essential_genes"


class Target(BaseModel):
    """Целевой объект воздействия."""

    model_config = {"frozen": True}

    gene: str = Field(..., description="Имя гена (символ)")
    organism: Organism = Field(..., description="Организм")
    cell_line: str | None = Field(None, description="Клеточная линия (опционально)")

    @field_validator("gene")
    @classmethod
    def _gene_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("gene must not be empty")
        return v


class PhenotypeTarget(BaseModel):
    """Желаемый фенотипический результат."""

    model_config = {"frozen": True}

    metric: str = Field(..., description="Что измеряем: protein_yield, growth, etc.")
    direction: Direction = Field(..., description="Вверх / вниз / устранить")
    magnitude: str | None = Field(None, description="Например, '>=2x'")


class Goal(BaseModel):
    """Цель пользователя в формализованном виде."""

    model_config = {"frozen": True}

    raw_text: str = Field(..., description="Исходная фраза пользователя")
    intent: GoalIntent = Field(..., description="Что хочет сделать")
    target: Target = Field(..., description="На что воздействовать")
    phenotype_target: PhenotypeTarget | None = Field(
        None, description="Желаемый фенотип (опционально)"
    )
    constraints: tuple[Constraint, ...] = Field(
        default_factory=tuple, description="Ограничения"
    )
    confidence: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        1.0, description="Уверенность парсера"
    )

    def to_dict(self) -> dict[str, object]:
        """Сериализация для API."""
        return self.model_dump(mode="json")