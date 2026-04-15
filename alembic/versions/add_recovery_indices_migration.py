"""add recovery_completed_indices to workout_completions

Revision ID: f6a2b94c1e08
Revises: e5f1a32b9c07
Create Date: 2026-03-31
"""
from alembic import op
import sqlalchemy as sa

revision = 'f6a2b94c1e08'
down_revision = 'e5f1a32b9c07'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('workout_completions',
        sa.Column('recovery_completed_indices', sa.JSON(), nullable=False, server_default='[]')
    )


def downgrade() -> None:
    op.drop_column('workout_completions', 'recovery_completed_indices')
    
    