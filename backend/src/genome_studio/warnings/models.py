"""Warning as a persistent object, not a toast."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from genome_studio.data.db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class WarningLevel(str, Enum):
    """Three tiers, per docs/07-policy-security.md."""

    T0_SCIENCE = "T0_science"  # essentiality, off-target, toxicity
    T1_BIOSEC = "T1_biosec"  # DURC, pathogen
    T2_LEGAL = "T2_legal"  # always-on, never disable


class WarningSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WarningStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"


class Warning(Base):
    """A warning tied to a project/experiment/edit.

    Cannot be deleted - only acknowledged with a note.
    """

    __tablename__ = "warnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    experiment_id: Mapped[int | None] = mapped_column(
        ForeignKey("experiments.id", ondelete="SET NULL"), nullable=True, index=True
    )

    level: Mapped[str] = mapped_column(String(16), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)  # essential_gene_knockout, ...
    message: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)

    status: Mapped[str] = mapped_column(
        String(16), default=WarningStatus.OPEN.value, nullable=False
    )
    acknowledged_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledgment_note: Mapped[str] = mapped_column(Text, default="", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    def to_dict(self) -> dict:
        import json

        try:
            evidence = json.loads(self.evidence_json)
        except Exception:
            evidence = []
        return {
            "id": self.id,
            "project_id": self.project_id,
            "experiment_id": self.experiment_id,
            "level": self.level,
            "severity": self.severity,
            "type": self.type,
            "message": self.message,
            "evidence": evidence,
            "status": self.status,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": (self.acknowledged_at.isoformat() if self.acknowledged_at else None),
            "acknowledgment_note": self.acknowledgment_note,
            "created_at": self.created_at.isoformat(),
        }
