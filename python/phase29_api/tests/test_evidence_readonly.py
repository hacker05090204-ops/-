"""
Phase-29 Evidence Read-Only Tests

PYTEST-FIRST: These tests MUST be written BEFORE implementation.

GOVERNANCE:
- Evidence endpoints are READ-ONLY
- No interpretation of evidence
- No scoring of evidence
- No recommendations based on evidence
- All evidence includes "NOT VERIFIED" disclaimer
"""

import pytest
from phase29_api.types import EvidenceResponse, EvidenceItem


class TestEvidenceReadOnly:
    """Test that evidence is read-only."""

    def test_evidence_response_is_immutable(self) -> None:
        """Evidence response should be immutable (frozen dataclass)."""
        response = EvidenceResponse(
            success=True,
            session_id="test-session",
            evidence={
                "screenshots": [],
                "har_path": None,
                "video_path": None,
                "console_logs": [],
            },
            human_initiated=True,
            disclaimer="NOT VERIFIED — Evidence is read-only",
        )
        # Frozen dataclass should raise on attribute assignment
        with pytest.raises((AttributeError, TypeError)):
            response.success = False  # type: ignore

    def test_evidence_includes_disclaimer(self) -> None:
        """All evidence responses MUST include NOT VERIFIED disclaimer."""
        response = EvidenceResponse(
            success=True,
            session_id="test-session",
            evidence={
                "screenshots": [],
                "har_path": None,
                "video_path": None,
                "console_logs": [],
            },
            human_initiated=True,
            disclaimer="NOT VERIFIED — Evidence is read-only",
        )
        assert "NOT VERIFIED" in response.disclaimer

    def test_evidence_item_has_no_interpretation_field(self) -> None:
        """Evidence items MUST NOT have interpretation fields."""
        item = EvidenceItem(
            path="/evidence/test/screenshot.png",
            captured_at="2026-01-07T12:00:00Z",
            label="test",
        )
        # Should not have these fields
        assert not hasattr(item, "interpretation")
        assert not hasattr(item, "analysis")
        assert not hasattr(item, "score")
        assert not hasattr(item, "recommendation")
        assert not hasattr(item, "severity")
        assert not hasattr(item, "classification")


class TestNoEvidenceInterpretation:
    """Test that no interpretation logic exists."""

    def test_no_scoring_in_evidence_module(self) -> None:
        """Evidence module MUST NOT contain scoring logic."""
        from pathlib import Path
        import ast

        evidence_file = Path(__file__).parent.parent / "evidence.py"
        if not evidence_file.exists():
            pytest.skip("evidence.py not yet created")

        content = evidence_file.read_text()
        forbidden_patterns = [
            "score",
            "rank",
            "classify",
            "severity",
            "priority",
            "recommend",
            "suggest",
            "analyze",
            "interpret",
        ]
        content_lower = content.lower()
        for pattern in forbidden_patterns:
            # Allow in comments and docstrings explaining what we DON'T do
            if pattern in content_lower:
                # Check if it's in a "no" or "not" context
                lines = content.split("\n")
                for line in lines:
                    if pattern in line.lower():
                        if "no " + pattern not in line.lower() and "not " + pattern not in line.lower():
                            if not line.strip().startswith("#"):
                                if '"""' not in line and "'''" not in line:
                                    pytest.fail(
                                        f"GOVERNANCE VIOLATION: '{pattern}' in evidence.py"
                                    )

    def test_no_ai_imports_in_evidence(self) -> None:
        """Evidence module MUST NOT import AI/ML libraries."""
        from pathlib import Path

        evidence_file = Path(__file__).parent.parent / "evidence.py"
        if not evidence_file.exists():
            pytest.skip("evidence.py not yet created")

        content = evidence_file.read_text()
        forbidden_imports = [
            "openai",
            "anthropic",
            "transformers",
            "torch",
            "tensorflow",
            "sklearn",
            "numpy",  # Could be used for scoring
            "pandas",  # Could be used for analysis
        ]
        for imp in forbidden_imports:
            assert imp not in content, (
                f"GOVERNANCE VIOLATION: {imp} import in evidence.py"
            )


class TestEvidenceRequiresHumanInitiated:
    """Test that evidence endpoints require human_initiated."""

    def test_get_evidence_requires_human_initiated(self) -> None:
        """GET /evidence MUST require human_initiated=true."""
        from phase29_api.validation import validate_human_initiated
        from phase29_api.types import GovernanceViolationError

        # Missing human_initiated should fail
        with pytest.raises(GovernanceViolationError):
            validate_human_initiated({"session_id": "test"})

        # human_initiated=False should fail
        with pytest.raises(GovernanceViolationError):
            validate_human_initiated({"session_id": "test", "human_initiated": False})

        # human_initiated=True should pass
        validate_human_initiated({"session_id": "test", "human_initiated": True})
