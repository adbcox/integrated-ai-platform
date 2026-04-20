"""RGC feature block package and member tables.

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-20

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feature_block_package",
        sa.Column("package_id", sa.String(64), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("scope", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("artifact_path", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("package_id", name="pk_feature_block_package"),
    )
    op.create_table(
        "feature_block_member",
        sa.Column("package_id", sa.String(64), nullable=False),
        sa.Column("roadmap_id", sa.String(64), nullable=False),
        sa.Column("member_role", sa.String(32), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("package_id", "roadmap_id", name="pk_feature_block_member"),
        sa.ForeignKeyConstraint(
            ["package_id"],
            ["feature_block_package.package_id"],
            name="fk_fbm_package_id",
        ),
        sa.ForeignKeyConstraint(
            ["roadmap_id"],
            ["roadmap_item.id"],
            name="fk_fbm_roadmap_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("feature_block_member")
    op.drop_table("feature_block_package")
