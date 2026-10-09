"""Pytest test configuration and database lifecycle fixtures.

Uses a shared in-memory SQLite database with StaticPool so that the lifespan
and all request-handling sessions see the same tables in every test run.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import create_app


TEST_DB_URL = "sqlite:///:memory:"


def _make_test_engine():
    """Create a SQLAlchemy engine backed by a single shared in-memory SQLite connection."""
    return create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="session")
def test_engine():
    """Session-scoped engine so all tests share one in-memory database."""
    engine = _make_test_engine()
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def app_with_test_db(test_engine, test_session_factory):
    """
    Build the FastAPI app and override its get_db dependency to use the
    shared in-memory engine. Startup lifespan runs once for the session.
    """
    application = create_app()

    def override_get_db():
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    application.dependency_overrides[get_db] = override_get_db
    return application


@pytest.fixture(scope="session")
def client(app_with_test_db):
    """Session-scoped TestClient so the lifespan runs exactly once."""
    with TestClient(app_with_test_db) as c:
        yield c


@pytest.fixture(autouse=True)
def setup_test_database(test_engine):
    """Ensures database tables exist before each test (idempotent)."""
    Base.metadata.create_all(bind=test_engine)
