"""
Phase-20 Core Reflection Tests

These tests verify:
- Reflection required before export
- Reflection can be declined
- No analysis of reflection text
- All actions attributed to HUMAN
"""

import pytest


class TestReflectionRequired:
    """Tests for mandatory reflection before export."""

    def test_reflection_required_before_export(self, session_id: str) -> None:
        """Export must be blocked until reflection exists."""
        from phase20_reflection.export_gate import require_reflection_before_export
        
        # No reflection yet - should return False
        assert require_reflection_before_export(session_id) is False

    def test_reflection_allows_export(
        self, session_id: str, sample_reflection_text: str
    ) -> None:
        """After reflection, export should be allowed."""
        from phase20_reflection.export_gate import require_reflection_before_export
        from phase20_reflection.reflection_record import create_reflection_record
        from phase20_reflection.reflection_logger import log_reflection
        
        record = create_reflection_record(
            session_id=session_id,
            reflection_text=sample_reflection_text,
            phase15_digest="a" * 64,
            phase19_digest="b" * 64,
        )
        log_reflection(record)
        
        assert require_reflection_before_export(session_id) is True

    def test_decline_allows_export(self, session_id: str, decline_reason: str) -> None:
        """Decline with reason should also allow export."""
        from phase20_reflection.export_gate import require_reflection_before_export
        from phase20_reflection.decline import create_decline_record
        from phase20_reflection.reflection_logger import log_reflection
        
        record = create_decline_record(session_id=session_id, reason=decline_reason)
        log_reflection(record)
        
        assert require_reflection_before_export(session_id) is True


class TestReflectionDecline:
    """Tests for decline functionality."""

    def test_reflection_can_be_declined(
        self, session_id: str, decline_reason: str
    ) -> None:
        """Human must be able to decline reflection."""
        from phase20_reflection.decline import create_decline_record
        
        record = create_decline_record(session_id=session_id, reason=decline_reason)
        
        assert record.declined is True
        assert record.decline_reason == decline_reason
        assert record.reflection_text == ""

    def test_decline_reason_not_validated(self, session_id: str) -> None:
        """Decline reason must not be validated for content."""
        from phase20_reflection.decline import create_decline_record
        
        # Any reason should be accepted
        reasons = [
            "",  # Empty
            "x",  # Single char
            "I don't want to",
            "asdfghjkl",  # Gibberish
            "🎉🎊🎈",  # Emoji only
            " " * 100,  # Whitespace only
        ]
        
        for reason in reasons:
            record = create_decline_record(session_id=session_id, reason=reason)
            assert record.declined is True
            assert record.decline_reason == reason


class TestNoContentAnalysis:
    """Tests verifying no content analysis occurs."""

    def test_any_text_accepted(self, session_id: str) -> None:
        """Any text must be accepted without validation."""
        from phase20_reflection.reflection_record import create_reflection_record
        
        texts = [
            "",  # Empty
            "x",  # Single char
            "This is a normal reflection.",
            "asdfghjkl qwertyuiop",  # Gibberish
            "🎉🎊🎈🎁🎀",  # Emoji only
            " " * 1000,  # Whitespace only
            "a" * 10000,  # Very long
            "<script>alert('xss')</script>",  # HTML
            "'; DROP TABLE reflections; --",  # SQL injection attempt
        ]
        
        for text in texts:
            record = create_reflection_record(
                session_id=session_id,
                reflection_text=text,
                phase15_digest="a" * 64,
                phase19_digest="b" * 64,
            )
            assert record.reflection_text == text

    def test_empty_text_accepted(self, session_id: str) -> None:
        """Empty reflection text must be accepted."""
        from phase20_reflection.reflection_record import create_reflection_record
        
        record = create_reflection_record(
            session_id=session_id,
            reflection_text="",
            phase15_digest="a" * 64,
            phase19_digest="b" * 64,
        )
        
        assert record.reflection_text == ""


class TestHumanAttribution:
    """Tests for human attribution requirements."""

    def test_human_initiated_always_true(
        self, session_id: str, sample_reflection_text: str
    ) -> None:
        """human_initiated must always be True."""
        from phase20_reflection.reflection_record import create_reflection_record
        
        record = create_reflection_record(
            session_id=session_id,
            reflection_text=sample_reflection_text,
            phase15_digest="a" * 64,
            phase19_digest="b" * 64,
        )
        
        assert record.human_initiated is True

    def test_actor_always_human(
        self, session_id: str, sample_reflection_text: str
    ) -> None:
        """actor must always be 'HUMAN'."""
        from phase20_reflection.reflection_record import create_reflection_record
        
        record = create_reflection_record(
            session_id=session_id,
            reflection_text=sample_reflection_text,
            phase15_digest="a" * 64,
            phase19_digest="b" * 64,
        )
        
        assert record.actor == "HUMAN"

    def test_decline_also_human_attributed(
        self, session_id: str, decline_reason: str
    ) -> None:
        """Decline records must also be human-attributed."""
        from phase20_reflection.decline import create_decline_record
        
        record = create_decline_record(session_id=session_id, reason=decline_reason)
        
        assert record.human_initiated is True
        assert record.actor == "HUMAN"


class TestDisclaimerDisplay:
    """Tests for disclaimer requirements."""

    def test_disclaimer_displayed(self) -> None:
        """Disclaimer must be displayed on prompt."""
        from phase20_reflection.reflection_prompt import get_reflection_prompt
        
        prompt = get_reflection_prompt()
        
        assert "NOT ANALYZED" in prompt
        assert "NOT VERIFIED" in prompt
        assert "NOT SCORED" in prompt

    def test_disclaimer_is_static(self) -> None:
        """Disclaimer must be static, not generated."""
        from phase20_reflection.reflection_prompt import get_reflection_prompt
        
        # Call multiple times - must be identical
        prompt1 = get_reflection_prompt()
        prompt2 = get_reflection_prompt()
        
        assert prompt1 == prompt2
