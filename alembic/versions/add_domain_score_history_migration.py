"""add domain_score_history table

Revision ID: a3f9c21d8e45
Revises: 1e7870d52356
Create Date: 2026-03-09
"""
from alembic import op
import sqlalchemy as sa

revision = 'a3f9c21d8e45'
down_revision = '1e7870d52356'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'domain_score_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('domain', sa.String(50), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('is_first_score', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_domain_score_history_user_id', 'domain_score_history', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_domain_score_history_user_id', table_name='domain_score_history')
    op.drop_table('domain_score_history')
    
    