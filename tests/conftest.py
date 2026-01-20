import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db

# Dedicated test DB (make sure user has privileges on schema public)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://looks_lab_test:testpassword@localhost:5432/looks_lab_test",
)

# Create engine and session factory
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override FastAPI dependency to use test DB session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Apply override globally
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Drop and recreate tables once per test session."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    """Fixture for FastAPI test client."""
    return TestClient(app)


@pytest.fixture(scope="function")
def db():
    """Fixture for direct DB access in tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def reset_db():
    """Ensure a clean DB state before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

