"""
Phase-29 Human Initiation Enforcement Tests

PYTEST-FIRST: These tests MUST be written BEFORE implementation.
All tests should FAIL until implementation is complete.

GOVERNANCE:
- Every endpoint MUST require human_initiated=True
- Requests without human_initiated MUST be rejected
- Requests with human_initiated=False MUST be rejected
"""

import pytest
from phase29_api.types import GovernanceViolationError
from phase29_api.validation import validate_human_initiated


class TestHumanInitiatedValidation:
    """Test human_initiated validation logic."""

    def test_accepts_human_initiated_true(self, valid_human_initiation: dict) -> None:
        """MUST accept requests with human_initiated=True."""
        # Should not raise
        validate_human_initiated(valid_human_initiation)

    def test_rejects_human_initiated_false(
        self, invalid_human_initiation_false: dict
    ) -> None:
        """MUST reject requests with human_initiated=False."""
        with pytest.raises(GovernanceViolationError) as exc_info:
            validate_human_initiated(invalid_human_initiation_false)
        assert "human_initiated=true required" in str(exc_info.value).lower()

    def test_rejects_human_initiated_missing(
        self, invalid_human_initiation_missing: dict
    ) -> None:
        """MUST reject requests with human_initiated missing."""
        with pytest.raises(GovernanceViolationError) as exc_info:
            validate_human_initiated(invalid_human_initiation_missing)
        assert "human_initiated=true required" in str(exc_info.value).lower()

    def test_rejects_human_initiated_none(self) -> None:
        """MUST reject requests with human_initiated=None."""
        data = {"human_initiated": None}
        with pytest.raises(GovernanceViolationError) as exc_info:
            validate_human_initiated(data)
        assert "human_initiated=true required" in str(exc_info.value).lower()

    def test_rejects_human_initiated_string_true(self) -> None:
        """MUST reject requests with human_initiated='true' (string)."""
        data = {"human_initiated": "true"}
        with pytest.raises(GovernanceViolationError) as exc_info:
            validate_human_initiated(data)
        assert "human_initiated=true required" in str(exc_info.value).lower()

    def test_rejects_human_initiated_integer_one(self) -> None:
        """MUST reject requests with human_initiated=1 (integer)."""
        data = {"human_initiated": 1}
        with pytest.raises(GovernanceViolationError) as exc_info:
            validate_human_initiated(data)
        assert "human_initiated=true required" in str(exc_info.value).lower()

    def test_rejects_empty_dict(self) -> None:
        """MUST reject empty request body."""
        with pytest.raises(GovernanceViolationError) as exc_info:
            validate_human_initiated({})
        assert "human_initiated=true required" in str(exc_info.value).lower()


class TestHumanInitiatedInResponses:
    """Test that responses include human_initiated field."""

    def test_response_includes_human_initiated(self) -> None:
        """All responses MUST include human_initiated field."""
        from phase29_api.types import BrowserStartResponse

        response = BrowserStartResponse(
            success=True,
            session_id="test-session",
            execution_id="test-execution",
            started_at="2026-01-07T12:00:00Z",
            human_initiated=True,
            disclaimer="NOT VERIFIED",
        )
        assert response.human_initiated is True

    def test_response_includes_disclaimer(self) -> None:
        """All responses MUST include disclaimer field."""
        from phase29_api.types import BrowserStartResponse

        response = BrowserStartResponse(
            success=True,
            session_id="test-session",
            execution_id="test-execution",
            started_at="2026-01-07T12:00:00Z",
            human_initiated=True,
            disclaimer="NOT VERIFIED",
        )
        assert "NOT VERIFIED" in response.disclaimer
