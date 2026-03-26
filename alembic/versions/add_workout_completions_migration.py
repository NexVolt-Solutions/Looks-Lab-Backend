"""add workout_completions table

Revision ID: c9f3a21e7d84
Revises: b7e4d12f9a31
Create Date: 2026-03-12
"""
from alembic import op
import sqlalchemy as sa

revision = 'c9f3a21e7d84'
down_revision = 'b7e4d12f9a31'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'workout_completions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('completed_indices', sa.JSON(), nullable=False),
        sa.Column('total_exercises', sa.Integer(), nullable=False, server_default='6'),
        sa.Column('score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'date', name='uq_workout_completion_user_date'),
    )
    op.create_index('ix_workout_completions_user_id', 'workout_completions', ['user_id'])
    op.create_index('ix_workout_completions_date', 'workout_completions', ['date'])


def downgrade() -> None:
    op.drop_index('ix_workout_completions_date', 'workout_completions')
    op.drop_index('ix_workout_completions_user_id', 'workout_completions')
    op.drop_table('workout_completions')
    
    