import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    with patch("app.database.engine"), patch("app.database.SessionLocal"):
        from app.main import app
        return TestClient(app)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_datasets_empty(client):
    with patch("app.api.ingestion.get_db") as mock_db:
        mock_session = MagicMock()
        mock_session.query.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.return_value = iter([mock_session])
        response = client.get("/api/v1/datasets")
        assert response.status_code == 200


def test_list_alerts_empty(client):
    with patch("app.api.alerts.get_db") as mock_db:
        mock_session = MagicMock()
        mock_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_db.return_value = iter([mock_session])
        response = client.get("/api/v1/alerts")
        assert response.status_code == 200


def test_list_recommendations_empty(client):
    with patch("app.api.recommendations.get_db") as mock_db:
        mock_session = MagicMock()
        mock_session.query.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.return_value = iter([mock_session])
        response = client.get("/api/v1/recommendations")
        assert response.status_code == 200


def test_list_reports_empty(client):
    with patch("app.api.reports.get_db") as mock_db:
        mock_session = MagicMock()
        mock_session.query.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.return_value = iter([mock_session])
        response = client.get("/api/v1/reports")
        assert response.status_code == 200
