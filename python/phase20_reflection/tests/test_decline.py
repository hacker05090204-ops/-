"""
Phase-20 Decline Tests

These tests verify decline functionality works correctly.
"""

import pytest


class TestDeclineCreation:
    """Tests for decline record creation."""

    def test_decline_creates_valid_record(
        self, session_id: str, decline_reason: str
    ) -> None:
        """Decline must create a valid reflection record."""
        from phase20_reflection.decline import create_decline_record
        
        record = create_decline_record(session_id=session_id, reason=decline_reason)
        
        assert record is not None
        assert record.session_id == session_id
        assert record.declined is True
        assert record.decline_reason == decline_reason

    def test_decline_has_empty_reflection_text(
        self, session_id: str, decline_reason: str
    ) -> None:
        """Decline record must have empty reflection text."""
        from phase20_reflection.decline import create_decline_record
        
        record = create_decline_record(session_id=session_id, reason=decline_reason)
        
        assert record.reflection_text == ""

    def test_decline_is_human_initiated(
        self, session_id: str, decline_reason: str
    ) -> None:
        """Decline must be marked as human-initiated."""
        from phase20_reflection.decline import create_decline_record
        
        record = create_decline_record(session_id=session_id, reason=decline_reason)
        
        assert record.human_initiated is True
        assert record.actor == "HUMAN"


class TestDeclineReasonNotValidated:
    """Tests verifying decline reason is not validated."""

    def test_empty_reason_accepted(self, session_id: str) -> None:
        """Empty decline reason must be accepted."""
        from phase20_reflection.decline import create_decline_record
        
        record = create_decline_record(session_id=session_id, reason="")
        
        assert record.declined is True
        assert record.decline_reason == ""

    def test_single_char_reason_accepted(self, session_id: str) -> None:
        """Single character reason must be accepted."""
        from phase20_reflection.decline import create_decline_record
        
        record = create_decline_record(session_id=session_id, reason="x")
        
        assert record.decline_reason == "x"

    def test_gibberish_reason_accepted(self, session_id: str) -> None:
        """Gibberish reason must be accepted."""
        from phase20_reflection.decline import create_decline_record
        
        gibberish = "asdfghjkl qwertyuiop"
        record = create_decline_record(session_id=session_id, reason=gibberish)
        
        assert record.decline_reason == gibberish

    def test_emoji_reason_accepted(self, session_id: str) -> None:
        """Emoji-only reason must be accepted."""
        from phase20_reflection.decline import create_decline_record
        
        emoji = "🤷‍♂️"
        record = create_decline_record(session_id=session_id, reason=emoji)
        
        assert record.decline_reason == emoji

    def test_very_long_reason_accepted(self, session_id: str) -> None:
        """Very long reason must be accepted."""
        from phase20_reflection.decline import create_decline_record
        
        long_reason = "a" * 10000
        record = create_decline_record(session_id=session_id, reason=long_reason)
        
        assert record.decline_reason == long_reason


class TestDeclineNotBlocked:
    """Tests verifying decline is never blocked."""

    def test_decline_always_succeeds(self, session_id: str) -> None:
        """Decline must always succeed regardless of reason."""
        from phase20_reflection.decline import create_decline_record
        
        # Various reasons that might be "suspicious"
        reasons = [
            "I refuse",
            "No",
            "This is stupid",
            "I don't trust this system",
            "DELETE FROM database",
            "",
            " ",
            "🖕",
        ]
        
        for reason in reasons:
            record = create_decline_record(session_id=session_id, reason=reason)
            assert record.declined is True
            # No exception raised = success

    def test_multiple_declines_allowed(self, session_id: str) -> None:
        """Multiple decline records can be created."""
        from phase20_reflection.decline import create_decline_record
        
        record1 = create_decline_record(session_id=session_id, reason="First decline")
        record2 = create_decline_record(session_id=session_id, reason="Second decline")
        
        assert record1.declined is True
        assert record2.declined is True


class TestDeclineHashing:
    """Tests for decline record hashing."""

    def test_decline_has_reflection_hash(
        self, session_id: str, decline_reason: str
    ) -> None:
        """Decline record must have reflection hash (of empty string)."""
        from phase20_reflection.decline import create_decline_record
        
        record = create_decline_record(session_id=session_id, reason=decline_reason)
        
        assert record.reflection_hash is not None
        assert len(record.reflection_hash) == 64  # SHA-256

    def test_decline_hash_is_empty_string_hash(self, session_id: str) -> None:
        """Decline reflection hash must be hash of empty string."""
        from phase20_reflection.decline import create_decline_record
        from phase20_reflection.reflection_hash import hash_reflection
        
        record = create_decline_record(session_id=session_id, reason="any reason")
        expected_hash = hash_reflection("")
        
        assert record.reflection_hash == expected_hash


class TestDeclineImmutability:
    """Tests for decline record immutability."""

    def test_decline_record_is_frozen(
        self, session_id: str, decline_reason: str
    ) -> None:
        """Decline record must be immutable."""
        from phase20_reflection.decline import create_decline_record
        
        record = create_decline_record(session_id=session_id, reason=decline_reason)
        
        with pytest.raises(Exception):  # FrozenInstanceError
            record.declined = False  # type: ignore

    def test_decline_reason_cannot_be_changed(
        self, session_id: str, decline_reason: str
    ) -> None:
        """Decline reason cannot be modified after creation."""
        from phase20_reflection.decline import create_decline_record
        
        record = create_decline_record(session_id=session_id, reason=decline_reason)
        
        with pytest.raises(Exception):  # FrozenInstanceError
            record.decline_reason = "changed"  # type: ignore
