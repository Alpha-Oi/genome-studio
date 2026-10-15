"""SQLAlchemy ORM models.

ТЕКУЩИЕ ТАБЛИЦЫ:
- projects (name, description, organism, timestamps)
- experiments (project_id, kind, title, payload_json, created_at)
- warnings (project_id, level, severity, type, message, ...)

ПЛАН БУДУЩИХ ТАБЛИЦ (НЕ реализовано, см. docs/15-multiuser-architecture.md):

AppSettings (Фаза A0):
- id, mode (local|multi), set_at, set_by

User (Фаза A1):
- id, email, password_hash, name, is_admin, created_at

RefreshToken (Фаза A1):
- id, user_id, token_hash, expires_at, created_at

Organization (Фаза B):
- id, name, created_at

Membership (Фаза B):
- id, user_id, org_id, role (owner|admin|member|viewer)

ПЛАН БУДУЩИХ ПОЛЕЙ в существующих таблицах:

Project (Фаза B):
- owner_id (FK users.id) — кто создал
- organization_id (FK organizations.id) — какая организация
- visibility (private|org_read|org_edit) — уровень доступа

Experiment (Фаза C1, опционально):
- gene, organism, intent — денормализованные поля для быстрого
  SQL-поиска «где-то уже делали knockout lacZ в E. coli»

ВАЖНО: эти поля пока НЕ создаются. Существующие проекты
мигрируют при первом переходе в multi mode — привязка к админу.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from genome_studio.data.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Project(Base):
    """A research project.

    TODO (Фаза B): owner_id, organization_id, visibility.
    """

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    organism: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    experiments: Mapped[list["Experiment"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Experiment.created_at",
    )

    def to_dict(self, include_experiments: bool = False) -> dict:
        d = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "organism": self.organism,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_experiments:
            d["experiments"] = [e.to_dict() for e in self.experiments]
        return d


class Experiment(Base):
    """A single experiment (goal plan, crispr design, simulation, etc.).

    TODO (Фаза C1): денормализованные gene / organism / intent
    для быстрого поиска похожих экспериментов.
    """

    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    project: Mapped[Project] = relationship(back_populates="experiments")

    def to_dict(self) -> dict:
        import json
        try:
            payload = json.loads(self.payload_json)
        except Exception:
            payload = {}
        return {
            "id": self.id,
            "project_id": self.project_id,
            "kind": self.kind,
            "title": self.title,
            "payload": payload,
            "created_at": self.created_at.isoformat(),
        }