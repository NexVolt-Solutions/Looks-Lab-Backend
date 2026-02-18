"""
Database transaction management utilities.
Provides sync and async context managers for safe DB transactions.
"""
from contextlib import contextmanager, asynccontextmanager
from typing import Generator, AsyncGenerator

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger


@contextmanager
def db_transaction(db: Session) -> Generator[Session, None, None]:
    """
    Sync transaction context manager.

    Usage:
        with db_transaction(db) as session:
            session.add(obj)

    - Commits on success
    - Rolls back on exception
    - Supports nested transactions via savepoints
    """

    if db.in_transaction():
        with db.begin_nested():
            yield db
        return

    try:
        yield db
        db.flush()
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(
            f"Database transaction rolled back: {type(e).__name__}: {e}",

            exc_info=settings.is_development
        )
        raise


@asynccontextmanager
async def async_db_transaction(
    db: AsyncSession
) -> AsyncGenerator[AsyncSession, None]:
    """
    Async transaction context manager.

    Usage:
        async with async_db_transaction(db) as session:
            session.add(obj)

    - Commits on success
    - Rolls back on exception
    - Supports nested transactions via savepoints
    """

    if db.in_transaction():
        async with db.begin_nested():
            yield db
        return

    try:
        yield db
        await db.flush()
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(
            f"Async database transaction rolled back: {type(e).__name__}: {e}",

            exc_info=settings.is_development
        )
        raise

