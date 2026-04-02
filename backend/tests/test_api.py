import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import MagicMock

# Use in-memory SQLite for tests
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.main import app
from app.database import get_db, Base

# Create a fresh in-memory SQLite engine for tests
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_datasets_empty(client):
    response = client.get("/api/v1/datasets")
    assert response.status_code == 200
    assert response.json() == []


def test_list_alerts_empty(client):
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    assert response.json() == []


def test_list_recommendations_empty(client):
    response = client.get("/api/v1/recommendations")
    assert response.status_code == 200
    assert response.json() == []


def test_list_reports_empty(client):
    response = client.get("/api/v1/reports")
    assert response.status_code == 200
    assert response.json() == []
