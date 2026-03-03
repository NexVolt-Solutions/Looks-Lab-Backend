"""onboarding_schema_production_fix"""

from alembic import op
import sqlalchemy as sa


revision = '73501bcf02fb'
down_revision = '996cc11efbe5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure onboarding_sessions table has correct state column
    with op.batch_alter_table("onboarding_sessions") as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_completed",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false")
            )
        )

    # Recreate performance indexes safely
    op.create_index(
        "ix_onboarding_answers_session_question",
        "onboarding_answers",
        ["session_id", "question_id"],
        unique=False
    )

    op.create_index(
        "ix_onboarding_questions_step_seq",
        "onboarding_questions",
        ["step", "seq"],
        unique=False
    )


def downgrade() -> None:
    with op.batch_alter_table("onboarding_sessions") as batch_op:
        batch_op.drop_column("is_completed")

    op.drop_index(
        "ix_onboarding_answers_session_question",
        table_name="onboarding_answers"
    )

    op.drop_index(
        "ix_onboarding_questions_step_seq",
        table_name="onboarding_questions"
    )
