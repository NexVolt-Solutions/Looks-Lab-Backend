"""add daily recovery table

Revision ID: d4e7f83a2c19
Revises: c9f3a21e7d84
Create Date: 2026-03-19
"""
from alembic import op
import sqlalchemy as sa

revision = 'd4e7f83a2c19'
down_revision = 'c9f3a21e7d84'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'daily_recovery',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('sleep', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('water', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('stretched', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('rested', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'date', name='uq_daily_recovery_user_date'),
    )
    op.create_index('ix_daily_recovery_user_id', 'daily_recovery', ['user_id'])
    op.create_index('ix_daily_recovery_date', 'daily_recovery', ['date'])


def downgrade() -> None:
    op.drop_index('ix_daily_recovery_date', table_name='daily_recovery')
    op.drop_index('ix_daily_recovery_user_id', table_name='daily_recovery')
    op.drop_table('daily_recovery')
    
    