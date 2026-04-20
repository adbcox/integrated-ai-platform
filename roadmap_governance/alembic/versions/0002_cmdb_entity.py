"""RGC CMDB layer: cmdb_entity table.

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-20

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cmdb_entity",
        sa.Column("entity_id", sa.String(36), primary_key=True),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("canonical_name", sa.Text, nullable=False),
        sa.Column("display_name", sa.Text, nullable=False),
        sa.Column("platform", sa.Text, nullable=True),
        sa.Column("environment", sa.Text, nullable=True),
        sa.Column("criticality", sa.Text, nullable=True),
        sa.Column("owner", sa.Text, nullable=True),
        sa.Column("lifecycle_state", sa.Text, nullable=True),
        sa.Column("source_system", sa.Text, nullable=True),
        sa.Column("external_ref", sa.Text, nullable=True),
        # ORM always supplies entity_metadata=dict(); no server_default needed.
        sa.Column("metadata", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("canonical_name", name="uq_cmdb_entity_canonical_name"),
    )


def downgrade() -> None:
    op.drop_table("cmdb_entity")
