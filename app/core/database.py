from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings
from app.core.logging import logger

Base = declarative_base()

_uri = settings.DATABASE_URI
async_database_uri = (
    _uri if _uri.startswith("postgresql+asyncpg://")
    else _uri.replace("postgresql://", "postgresql+asyncpg://")
)

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


async def init_async_db() -> None:
    try:
        import app.models  # noqa: F401
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise


async def close_async_db() -> None:
    await async_engine.dispose()

