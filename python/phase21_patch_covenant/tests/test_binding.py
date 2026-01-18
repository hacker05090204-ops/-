"""
Phase-21 Binding Tests

Tests verifying cryptographic binding creation and immutability.
"""

import pytest
from dataclasses import FrozenInstanceError


class TestBindingCreation:
    """Tests verifying binding creation."""

    def test_create_binding(
        self,
        sample_patch_id: str,
        sample_session_id: str,
        sample_timestamp: str,
    ) -> None:
        """Binding must be created with all required fields."""
        from phase21_patch_covenant.binding import create_patch_binding
        
        binding = create_patch_binding(
            patch_hash="a" * 64,
            decision_hash="b" * 64,
            timestamp=sample_timestamp,
            session_id=sample_session_id,
        )
        
        assert binding.patch_hash == "a" * 64
        assert binding.decision_hash == "b" * 64
        assert binding.timestamp == sample_timestamp
        assert binding.session_id == sample_session_id
        assert len(binding.binding_hash) == 64

    def test_binding_hash_is_sha256(
        self,
        sample_session_id: str,
        sample_timestamp: str,
    ) -> None:
        """Binding hash must be SHA-256 format."""
        from phase21_patch_covenant.binding import create_patch_binding
        
        binding = create_patch_binding(
            patch_hash="a" * 64,
            decision_hash="b" * 64,
            timestamp=sample_timestamp,
            session_id=sample_session_id,
        )
        
        assert len(binding.binding_hash) == 64
        assert all(c in "0123456789abcdef" for c in binding.binding_hash)

    def test_binding_verifiable_always_true(
        self,
        sample_session_id: str,
        sample_timestamp: str,
    ) -> None:
        """Binding.verifiable must always be True."""
        from phase21_patch_covenant.binding import create_patch_binding
        
        binding = create_patch_binding(
            patch_hash="a" * 64,
            decision_hash="b" * 64,
            timestamp=sample_timestamp,
            session_id=sample_session_id,
        )
        
        assert binding.verifiable is True


class TestBindingImmutability:
    """Tests verifying binding is immutable."""

    def test_binding_is_frozen(
        self,
        sample_session_id: str,
        sample_timestamp: str,
    ) -> None:
        """Binding must be frozen (immutable)."""
        from phase21_patch_covenant.binding import create_patch_binding
        
        binding = create_patch_binding(
            patch_hash="a" * 64,
            decision_hash="b" * 64,
            timestamp=sample_timestamp,
            session_id=sample_session_id,
        )
        
        with pytest.raises(FrozenInstanceError):
            binding.binding_hash = "modified"

    def test_binding_cannot_be_deleted(
        self,
        sample_session_id: str,
        sample_timestamp: str,
    ) -> None:
        """Binding fields cannot be deleted."""
        from phase21_patch_covenant.binding import create_patch_binding
        
        binding = create_patch_binding(
            patch_hash="a" * 64,
            decision_hash="b" * 64,
            timestamp=sample_timestamp,
            session_id=sample_session_id,
        )
        
        with pytest.raises((FrozenInstanceError, AttributeError)):
            del binding.binding_hash


class TestBindingVerification:
    """Tests verifying binding can be verified."""

    def test_verify_valid_binding(
        self,
        sample_session_id: str,
        sample_timestamp: str,
    ) -> None:
        """Valid binding must verify successfully."""
        from phase21_patch_covenant.binding import create_patch_binding, verify_binding
        
        binding = create_patch_binding(
            patch_hash="a" * 64,
            decision_hash="b" * 64,
            timestamp=sample_timestamp,
            session_id=sample_session_id,
        )
        
        is_valid = verify_binding(binding)
        
        assert is_valid is True

    def test_binding_changes_with_patch_hash(
        self,
        sample_session_id: str,
        sample_timestamp: str,
    ) -> None:
        """Different patch hash must produce different binding."""
        from phase21_patch_covenant.binding import create_patch_binding
        
        binding1 = create_patch_binding(
            patch_hash="a" * 64,
            decision_hash="b" * 64,
            timestamp=sample_timestamp,
            session_id=sample_session_id,
        )
        
        binding2 = create_patch_binding(
            patch_hash="c" * 64,  # Different
            decision_hash="b" * 64,
            timestamp=sample_timestamp,
            session_id=sample_session_id,
        )
        
        assert binding1.binding_hash != binding2.binding_hash

    def test_binding_changes_with_decision_hash(
        self,
        sample_session_id: str,
        sample_timestamp: str,
    ) -> None:
        """Different decision hash must produce different binding."""
        from phase21_patch_covenant.binding import create_patch_binding
        
        binding1 = create_patch_binding(
            patch_hash="a" * 64,
            decision_hash="b" * 64,
            timestamp=sample_timestamp,
            session_id=sample_session_id,
        )
        
        binding2 = create_patch_binding(
            patch_hash="a" * 64,
            decision_hash="d" * 64,  # Different
            timestamp=sample_timestamp,
            session_id=sample_session_id,
        )
        
        assert binding1.binding_hash != binding2.binding_hash

