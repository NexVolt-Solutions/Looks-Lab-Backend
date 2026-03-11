"""add step to domain_questions and reseed

Revision ID: b7e4d12f9a31
Revises: a3f9c21d8e45
Create Date: 2026-03-10
"""
from alembic import op
import sqlalchemy as sa

revision = 'b7e4d12f9a31'
down_revision = 'a3f9c21d8e45'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add step column
    op.add_column('domain_questions', sa.Column('step', sa.String(50), nullable=True))

    # Update existing rows with step values based on seq order per domain
    conn = op.get_bind()

    step_map = {
        "haircare":  ["type", "density", "scalp", "concerns", "wash", "styling", "family", "goals"],
        "skincare":  ["hydration", "breakouts", "redness", "dullness", "elasticity", "routine", "allergies", "allergy_details", "goals"],
        "height":    ["activity", "diet", "stretching", "family_height", "growth", "calcium", "goal"],
        "workout":   ["body_type", "goal", "target", "frequency", "type", "experience", "duration"],
        "diet":      ["meals", "tracking", "type", "sugar", "supplements", "cooking"],
        "fashion":   ["body_type", "style", "fit", "season", "trends", "accessories", "events", "goal"],
        "facial":    ["areas", "natural", "exercise", "sleep", "symmetry", "grinding", "breathing", "jaw_goal"],
        "quit_porn": ["frequency", "triggers", "other_triggers", "urge_time", "exercise", "coping", "hobbies", "goal", "guilt", "commitment"],
    }

    for domain, steps in step_map.items():
        rows = conn.execute(
            sa.text("SELECT id, seq FROM domain_questions WHERE domain = :d ORDER BY seq ASC"),
            {"d": domain}
        ).fetchall()
        for row in rows:
            idx = row.seq - 1  # seq is 1-based
            if 0 <= idx < len(steps):
                conn.execute(
                    sa.text("UPDATE domain_questions SET step = :s WHERE id = :id"),
                    {"s": steps[idx], "id": row.id}
                )


def downgrade() -> None:
    op.drop_column('domain_questions', 'step')
    
    