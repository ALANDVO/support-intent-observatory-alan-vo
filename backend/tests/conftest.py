"""Pytest test configuration and database lifecycle fixtures."""

import pytest
from app.core.database import Base, engine


@pytest.fixture(autouse=True)
def setup_test_database():
    """Ensures database tables are created before each test."""
    Base.metadata.create_all(bind=engine)
    yield
