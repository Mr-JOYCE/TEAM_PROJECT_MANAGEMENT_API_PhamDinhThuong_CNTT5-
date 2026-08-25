"""add project soft delete and audit logs

Revision ID: 9b7e2c4a1d5f
Revises: f4c1bdc1e2c6
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9b7e2c4a1d5f"
down_revision: Union[str, Sequence[str], None] = "f4c1bdc1e2c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("projects", "is_deleted", server_default=None)
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_column("projects", "is_deleted")
    op.drop_column("projects", "deleted_at")
