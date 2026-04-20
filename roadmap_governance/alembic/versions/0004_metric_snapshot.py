"""RGC metric snapshot table.

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-20

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "metric_snapshot",
        sa.Column("snapshot_id", sa.String(36), nullable=False),
        sa.Column("scope_type", sa.String(64), nullable=False),
        sa.Column("scope_ref", sa.String(256), nullable=False),
        sa.Column("metrics", sa.JSON, nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("snapshot_id", name="pk_metric_snapshot"),
    )
    op.create_index("ix_metric_snapshot_scope", "metric_snapshot", ["scope_type", "scope_ref"])


def downgrade() -> None:
    op.drop_index("ix_metric_snapshot_scope", table_name="metric_snapshot")
    op.drop_table("metric_snapshot")
