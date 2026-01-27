from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
from app.core.logging import logger

# SQLAlchemy Engine
engine = create_engine(
    settings.DATABASE_URI,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
)

# Session Factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base Class for ORM Models
Base = declarative_base()


# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database connection and ensure models are imported."""
    try:
        import app.models
        with engine.connect() as conn:
            logger.info("Database connection established successfully")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")


def close_db() -> None:
    """Dispose the SQLAlchemy engine (best-effort)."""
    try:
        engine.dispose()
        logger.info("Database engine disposed successfully")
    except Exception as e:
        logger.error(f"Database engine dispose failed: {e}")

