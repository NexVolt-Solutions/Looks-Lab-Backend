"""add domain column to workout_completions

Revision ID: e5f1a32b9c07
Revises: d4e7f83a2c19
Create Date: 2026-03-27
"""
from alembic import op
import sqlalchemy as sa

revision = 'e5f1a32b9c07'
down_revision = 'd4e7f83a2c19'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add domain column with default 'workout'
    op.add_column('workout_completions', sa.Column('domain', sa.String(50), nullable=False, server_default='workout'))
    op.create_index('ix_workout_completions_domain', 'workout_completions', ['domain'])

    # Drop old unique constraint and create new one with domain
    op.drop_constraint('uq_workout_completion_user_date', 'workout_completions', type_='unique')
    op.create_unique_constraint('uq_workout_completion_user_date_domain', 'workout_completions', ['user_id', 'date', 'domain'])


def downgrade() -> None:
    op.drop_constraint('uq_workout_completion_user_date_domain', 'workout_completions', type_='unique')
    op.create_unique_constraint('uq_workout_completion_user_date', 'workout_completions', ['user_id', 'date'])
    op.drop_index('ix_workout_completions_domain', table_name='workout_completions')
    op.drop_column('workout_completions', 'domain')
    
    