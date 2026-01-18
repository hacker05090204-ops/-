"""
Phase-29 API Endpoint Tests

GOVERNANCE:
- All endpoints require human_initiated=True
- All responses include disclaimer
- NO automation patterns
"""

import pytest
from fastapi.testclient import TestClient
from phase29_api.server import app


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


class TestBrowserStartEndpoint:
    """Tests for POST /api/browser/start."""

    def test_start_with_human_initiated_true(self, client: TestClient) -> None:
        """MUST accept requests with human_initiated=True."""
        response = client.post(
            "/api/browser/start",
            json={
                "human_initiated": True,
                "session_config": {"enable_video": False},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "session_id" in data
        assert "execution_id" in data
        assert data["human_initiated"] is True
        assert "NOT VERIFIED" in data["disclaimer"]

    def test_start_rejects_human_initiated_false(self, client: TestClient) -> None:
        """MUST reject requests with human_initiated=False."""
        response = client.post(
            "/api/browser/start",
            json={"human_initiated": False},
        )
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert "GOVERNANCE VIOLATION" in data["error"]

    def test_start_rejects_missing_human_initiated(self, client: TestClient) -> None:
        """MUST reject requests without human_initiated."""
        response = client.post(
            "/api/browser/start",
            json={"session_config": {}},
        )
        # Pydantic validation will fail
        assert response.status_code == 422


class TestBrowserActionEndpoint:
    """Tests for POST /api/browser/action."""

    def test_action_with_human_initiated_true(self, client: TestClient) -> None:
        """MUST accept actions with human_initiated=True."""
        # First start a session
        start_response = client.post(
            "/api/browser/start",
            json={"human_initiated": True},
        )
        session_id = start_response.json()["session_id"]

        # Execute action
        response = client.post(
            "/api/browser/action",
            json={
                "human_initiated": True,
                "session_id": session_id,
                "action": {
                    "action_type": "navigate",
                    "target": "https://example.com",
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["human_initiated"] is True
        assert "NOT VERIFIED" in data["disclaimer"]

    def test_action_rejects_human_initiated_false(self, client: TestClient) -> None:
        """MUST reject actions with human_initiated=False."""
        response = client.post(
            "/api/browser/action",
            json={
                "human_initiated": False,
                "session_id": "test",
                "action": {"action_type": "click", "target": "#btn"},
            },
        )
        assert response.status_code == 403

    def test_action_rejects_invalid_session(self, client: TestClient) -> None:
        """MUST reject actions for non-existent sessions."""
        response = client.post(
            "/api/browser/action",
            json={
                "human_initiated": True,
                "session_id": "non-existent-session",
                "action": {"action_type": "click", "target": "#btn"},
            },
        )
        assert response.status_code == 404


class TestBrowserEvidenceEndpoint:
    """Tests for GET /api/browser/evidence."""

    def test_evidence_with_human_initiated_true(self, client: TestClient) -> None:
        """MUST accept evidence requests with human_initiated=True."""
        # First start a session
        start_response = client.post(
            "/api/browser/start",
            json={"human_initiated": True},
        )
        session_id = start_response.json()["session_id"]

        # Get evidence
        response = client.get(
            f"/api/browser/evidence?session_id={session_id}&human_initiated=true"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["human_initiated"] is True
        assert "NOT VERIFIED" in data["disclaimer"]
        assert "evidence" in data

    def test_evidence_rejects_human_initiated_false(self, client: TestClient) -> None:
        """MUST reject evidence requests with human_initiated=False."""
        response = client.get(
            "/api/browser/evidence?session_id=test&human_initiated=false"
        )
        assert response.status_code == 403


class TestBrowserStopEndpoint:
    """Tests for POST /api/browser/stop."""

    def test_stop_with_human_initiated_true(self, client: TestClient) -> None:
        """MUST accept stop requests with human_initiated=True."""
        # First start a session
        start_response = client.post(
            "/api/browser/start",
            json={"human_initiated": True},
        )
        session_id = start_response.json()["session_id"]

        # Stop session
        response = client.post(
            "/api/browser/stop",
            json={
                "human_initiated": True,
                "session_id": session_id,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["human_initiated"] is True
        assert "NOT VERIFIED" in data["disclaimer"]
        assert "evidence_summary" in data

    def test_stop_rejects_human_initiated_false(self, client: TestClient) -> None:
        """MUST reject stop requests with human_initiated=False."""
        response = client.post(
            "/api/browser/stop",
            json={
                "human_initiated": False,
                "session_id": "test",
            },
        )
        assert response.status_code == 403


class TestBrowserStatusEndpoint:
    """Tests for GET /api/browser/status."""

    def test_status_with_human_initiated_true(self, client: TestClient) -> None:
        """MUST accept status requests with human_initiated=True."""
        # First start a session
        start_response = client.post(
            "/api/browser/start",
            json={"human_initiated": True},
        )
        session_id = start_response.json()["session_id"]

        # Get status
        response = client.get(
            f"/api/browser/status?session_id={session_id}&human_initiated=true"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["human_initiated"] is True
        assert "NOT VERIFIED" in data["disclaimer"]

    def test_status_rejects_human_initiated_false(self, client: TestClient) -> None:
        """MUST reject status requests with human_initiated=False."""
        response = client.get(
            "/api/browser/status?session_id=test&human_initiated=false"
        )
        assert response.status_code == 403


class TestHealthEndpoint:
    """Tests for GET /api/health."""

    def test_health_check(self, client: TestClient) -> None:
        """Health check should return healthy status."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["phase"] == "29"
        assert data["governance"] == "CONNECTIVITY-ONLY"
