"""RGC roadmap-to-CMDB link table.

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-20

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roadmap_link",
        sa.Column("roadmap_id", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("link_type", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("evidence_ref", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint(
            "roadmap_id", "entity_id", "link_type", name="pk_roadmap_link"
        ),
        sa.ForeignKeyConstraint(
            ["roadmap_id"], ["roadmap_item.id"], name="fk_roadmap_link_roadmap_id"
        ),
        sa.ForeignKeyConstraint(
            ["entity_id"],
            ["cmdb_entity.entity_id"],
            name="fk_roadmap_link_entity_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("roadmap_link")
