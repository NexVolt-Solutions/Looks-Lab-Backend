"""
Database configuration with async support.
Provides both sync and async session factories for SQLAlchemy.
"""
from collections.abc import AsyncGenerator, Generator

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from app.core.config import settings
from app.core.logging import logger


Base = declarative_base()


# ── Normalize DATABASE_URI ────────────────────────────────────────

database_uri = settings.DATABASE_URI

if database_uri.startswith("postgresql+asyncpg://"):
    sync_database_uri = database_uri.replace(
        "postgresql+asyncpg://",
        "postgresql://"
    )
    async_database_uri = database_uri
else:
    sync_database_uri = database_uri
    async_database_uri = database_uri.replace(
        "postgresql://",
        "postgresql+asyncpg://"
    )


# ── Sync Engine ───────────────────────────────────────────────────

sync_engine = create_engine(
    sync_database_uri,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=1800,
    pool_timeout=30,
)

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)


def get_db() -> Generator[Session, None, None]:
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Async Engine ──────────────────────────────────────────────────

async_engine = create_async_engine(
    async_database_uri,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=1800,
    pool_timeout=30,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# ── Init & Close Helpers ──────────────────────────────────────────

async def init_async_db() -> None:
    """
    Verify async database connection on startup.
    Imports all models to ensure they are registered with Base.
    """
    try:
        import app.models  # noqa: F401 — registers all models with Base

        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

        logger.info("Async database connection established")
    except Exception as e:
        logger.error(f"Async database connection failed: {e}")
        raise


def init_db() -> None:
    """
    Verify sync database connection on startup.
    Used by Alembic and sync scripts.
    """
    try:
        import app.models  # noqa: F401 — registers all models with Base

        with sync_engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        logger.info("Sync database connection established")
    except Exception as e:
        logger.error(f"Sync database connection failed: {e}")
        raise


async def close_async_db() -> None:
    """Dispose async engine on shutdown."""
    try:
        await async_engine.dispose()
        logger.info("Async database engine disposed")
    except Exception as e:
        logger.error(f"Async database engine dispose failed: {e}")


def close_db() -> None:
    """Dispose sync engine on shutdown."""
    try:
        sync_engine.dispose()
        logger.info("Sync database engine disposed")
    except Exception as e:
        logger.error(f"Sync database engine dispose failed: {e}")

