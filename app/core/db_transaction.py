"""
Database transaction management utilities.
"""
from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from app.core.logging import logger


@contextmanager
def db_transaction(db: Session) -> Generator[Session, None, None]:
    """
    Context manager for database transactions with automatic rollback on error.
    
    Usage:
        with db_transaction(db) as session:
            # Your database operations
            session.add(object)
            # If any exception occurs, rollback is automatic
    """
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database transaction rolled back: {e}", exc_info=True)
        raise
