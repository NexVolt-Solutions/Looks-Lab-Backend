"""
Alembic migration environment configuration.
Detects all SQLAlchemy models for autogeneration.
"""
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── Add project root to path ─────────────────────────────────────
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ── Import settings and Base ──────────────────────────────────────
from app.core.config import settings
from app.core.database import Base

# ── Import ALL models explicitly ──────────────────────────────────
# This ensures Alembic can detect all tables for autogeneration
from app.models.user import User  # noqa: F401
from app.models.onboarding import (  # noqa: F401
    OnboardingSession,
    OnboardingQuestion,
    OnboardingAnswer,
)
from app.models.domain import (  # noqa: F401
    DomainQuestion,
    DomainAnswer,
)
from app.models.image import Image  # noqa: F401
from app.models.insight import Insight  # noqa: F401
from app.models.subscription import Subscription  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401

# ── Alembic Configuration ─────────────────────────────────────────
config = context.config

# Inject DATABASE_URI from settings
database_url = settings.DATABASE_URI

# Convert asyncpg to sync driver for Alembic
if database_url.startswith("postgresql+asyncpg://"):
    database_url = database_url.replace(
        "postgresql+asyncpg://",
        "postgresql://"
    )

config.set_main_option("sqlalchemy.url", database_url)

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


# ── Migration Functions ───────────────────────────────────────────

def run_migrations_offline() -> None:
    """
    Run migrations in offline mode.
    This configures the context with just a URL and not an Engine.
    """
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in online mode.
    Creates an Engine and associates a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# ── Entry Point ───────────────────────────────────────────────────

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

