"""add_ai_jobs_table

Revision ID: add_ai_jobs_table
Revises: a1b2c3d4e5f6
Create Date: 2026-04-21 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_ai_jobs_table"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("domain", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("submission_hash", sa.String(length=64), nullable=True),
        sa.Column("result_payload", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "domain", name="uq_ai_job_user_domain"),
    )
    op.create_index(op.f("ix_ai_jobs_domain"), "ai_jobs", ["domain"], unique=False)
    op.create_index(op.f("ix_ai_jobs_id"), "ai_jobs", ["id"], unique=False)
    op.create_index(op.f("ix_ai_jobs_status"), "ai_jobs", ["status"], unique=False)
    op.create_index(op.f("ix_ai_jobs_user_id"), "ai_jobs", ["user_id"], unique=False)
    op.create_index("ix_ai_job_status", "ai_jobs", ["status"], unique=False)
    op.create_index("ix_ai_job_user_domain_status", "ai_jobs", ["user_id", "domain", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ai_job_user_domain_status", table_name="ai_jobs")
    op.drop_index("ix_ai_job_status", table_name="ai_jobs")
    op.drop_index(op.f("ix_ai_jobs_user_id"), table_name="ai_jobs")
    op.drop_index(op.f("ix_ai_jobs_status"), table_name="ai_jobs")
    op.drop_index(op.f("ix_ai_jobs_id"), table_name="ai_jobs")
    op.drop_index(op.f("ix_ai_jobs_domain"), table_name="ai_jobs")
    op.drop_table("ai_jobs")
