"""
Database transaction management utilities.
"""
from contextlib import contextmanager, asynccontextmanager
from typing import Generator, AsyncGenerator
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger


@contextmanager
def db_transaction(db: Session) -> Generator[Session, None, None]:
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database transaction rolled back: {e}", exc_info=True)
        raise


@asynccontextmanager
async def async_db_transaction(db: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    try:
        yield db
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Async database transaction rolled back: {e}", exc_info=True)
        raise

