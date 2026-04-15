"""add processing status to image status enum

Revision ID: a1b2c3d4e5f6
Revises: f6a2b94c1e08
Create Date: 2026-04-14
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'f6a2b94c1e08'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL requires explicit ALTER TYPE to add enum value
    op.execute("ALTER TABLE images ALTER COLUMN status TYPE VARCHAR(20)")
    # Update any stale pending images for image-based domains to processing
    op.execute("""
        UPDATE images 
        SET status = 'processing' 
        WHERE status = 'pending' 
        AND domain IN ('skincare', 'haircare', 'facial', 'fashion')
    """)


def downgrade() -> None:
    op.execute("""
        UPDATE images 
        SET status = 'pending' 
        WHERE status = 'processing'
    """)
    
    