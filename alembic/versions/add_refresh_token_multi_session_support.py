"""add_refresh_token_multi_session_support

Revision ID: rt_multi_session_20260421
Revises: add_ai_jobs_table
Create Date: 2026-04-21 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "rt_multi_session_20260421"
down_revision: Union[str, None] = "add_ai_jobs_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE refresh_tokens
        DROP CONSTRAINT IF EXISTS refresh_tokens_user_id_key
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE refresh_tokens
        ADD CONSTRAINT refresh_tokens_user_id_key UNIQUE (user_id)
        """
    )
