"""
Database configuration with async support.
Provides both sync and async session factories for SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from app.core.config import settings
from app.core.logging import logger


Base = declarative_base()


sync_engine = create_engine(
    settings.DATABASE_URI,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
)

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)


def get_db() -> Session:
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


async_database_uri = settings.DATABASE_URI.replace("postgresql://", "postgresql+asyncpg://")

async_engine = create_async_engine(
    async_database_uri,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_async_db():
    try:
        import app.models
        async with async_engine.begin() as conn:
            logger.info("Async database connection established")
    except Exception as e:
        logger.error(f"Async database connection failed: {e}")
        raise


def init_db():
    try:
        import app.models
        with sync_engine.connect() as conn:
            logger.info("Sync database connection established")
    except Exception as e:
        logger.error(f"Sync database connection failed: {e}")
        raise


async def close_async_db():
    try:
        await async_engine.dispose()
        logger.info("Async database engine disposed")
    except Exception as e:
        logger.error(f"Async database engine dispose failed: {e}")


def close_db():
    try:
        sync_engine.dispose()
        logger.info("Sync database engine disposed")
    except Exception as e:
        logger.error(f"Sync database engine dispose failed: {e}")

