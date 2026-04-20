# No 'from __future__ import annotations' — SQLAlchemy 2 needs real annotations
# resolved at class-definition time on Python 3.9.

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class RoadmapItem(Base):
    __tablename__ = "roadmap_item"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    item_type: Mapped[str] = mapped_column(String(64), nullable=False)
    priority: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_path: Mapped[str] = mapped_column(Text, nullable=False)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    naming_version: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"<RoadmapItem id={self.id!r} status={self.status!r}>"


class IntegrityFinding(Base):
    __tablename__ = "integrity_finding"

    finding_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    finding_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    object_type: Mapped[str] = mapped_column(String(64), nullable=False)
    object_ref: Mapped[str] = mapped_column(String(256), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Any] = mapped_column(JSON, nullable=False, default=dict)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<IntegrityFinding id={self.finding_id!r}"
            f" type={self.finding_type!r}"
            f" ref={self.object_ref!r}>"
        )


class CmdbEntity(Base):
    __tablename__ = "cmdb_entity"
    __table_args__ = (UniqueConstraint("canonical_name", name="uq_cmdb_entity_canonical_name"),)

    entity_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_name: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    environment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    criticality: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lifecycle_state: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_system: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    external_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Python attr is entity_metadata to avoid shadowing DeclarativeBase.metadata.
    entity_metadata: Mapped[Any] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"<CmdbEntity id={self.entity_id!r} name={self.canonical_name!r}>"


class RoadmapLink(Base):
    """Persisted link between a roadmap item and a CMDB entity.

    Composite PK (roadmap_id, entity_id, link_type) makes upserts idempotent.
    confidence is in [0.0, 1.0]; only exact matches (1.0) are auto-linked.
    """

    __tablename__ = "roadmap_link"

    roadmap_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("roadmap_item.id"), primary_key=True
    )
    entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cmdb_entity.entity_id"), primary_key=True
    )
    link_type: Mapped[str] = mapped_column(String(64), primary_key=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<RoadmapLink roadmap={self.roadmap_id!r}"
            f" entity={self.entity_id!r}"
            f" type={self.link_type!r}"
            f" confidence={self.confidence}>"
        )
