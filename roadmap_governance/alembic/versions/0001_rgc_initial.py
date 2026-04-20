"""RGC initial schema: roadmap_item and integrity_finding tables.

Revision ID: 0001
Revises:
Create Date: 2026-04-20

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roadmap_item",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("item_type", sa.String(64), nullable=False),
        sa.Column("priority", sa.String(8), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("source_path", sa.Text, nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column("naming_version", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "integrity_finding",
        sa.Column("finding_id", sa.String(36), primary_key=True),
        sa.Column("finding_type", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("object_type", sa.String(64), nullable=False),
        sa.Column("object_ref", sa.String(256), nullable=False),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("details", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("resolution_note", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("integrity_finding")
    op.drop_table("roadmap_item")
