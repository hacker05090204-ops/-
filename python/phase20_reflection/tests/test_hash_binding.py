"""
Phase-20 Hash Binding Tests

These tests verify cryptographic binding between reflection and phase artifacts.
"""

import pytest
import hashlib


class TestReflectionHashing:
    """Tests for reflection text hashing."""

    def test_hash_is_sha256(self, sample_reflection_text: str) -> None:
        """Reflection hash must be SHA-256."""
        from phase20_reflection.reflection_hash import hash_reflection
        
        result = hash_reflection(sample_reflection_text)
        
        # SHA-256 produces 64 hex characters
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_hash_changes_with_text(self) -> None:
        """Hash must change when text changes."""
        from phase20_reflection.reflection_hash import hash_reflection
        
        hash1 = hash_reflection("text one")
        hash2 = hash_reflection("text two")
        
        assert hash1 != hash2

    def test_hash_deterministic(self, sample_reflection_text: str) -> None:
        """Same text must produce same hash."""
        from phase20_reflection.reflection_hash import hash_reflection
        
        hash1 = hash_reflection(sample_reflection_text)
        hash2 = hash_reflection(sample_reflection_text)
        
        assert hash1 == hash2

    def test_hash_empty_text(self) -> None:
        """Empty text must produce valid hash."""
        from phase20_reflection.reflection_hash import hash_reflection
        
        result = hash_reflection("")
        
        # SHA-256 of empty string
        expected = hashlib.sha256(b"").hexdigest()
        assert result == expected

    def test_hash_unicode_text(self) -> None:
        """Unicode text must be hashed correctly."""
        from phase20_reflection.reflection_hash import hash_reflection
        
        unicode_text = "日本語テスト 🎉"
        result = hash_reflection(unicode_text)
        
        # Verify it's a valid SHA-256
        assert len(result) == 64


class TestBindingCreation:
    """Tests for binding creation."""

    def test_binding_includes_all_digests(
        self,
        sample_reflection_text: str,
        mock_phase15_digest: str,
        mock_phase19_digest: str,
    ) -> None:
        """Binding must include all three digests."""
        from phase20_reflection.reflection_hash import hash_reflection, create_binding
        
        reflection_hash = hash_reflection(sample_reflection_text)
        binding = create_binding(
            reflection_hash=reflection_hash,
            phase15_digest=mock_phase15_digest,
            phase19_digest=mock_phase19_digest,
        )
        
        assert binding.reflection_hash == reflection_hash
        assert binding.phase15_digest == mock_phase15_digest
        assert binding.phase19_digest == mock_phase19_digest

    def test_binding_hash_is_sha256(
        self,
        sample_reflection_text: str,
        mock_phase15_digest: str,
        mock_phase19_digest: str,
    ) -> None:
        """Binding hash must be SHA-256."""
        from phase20_reflection.reflection_hash import hash_reflection, create_binding
        
        reflection_hash = hash_reflection(sample_reflection_text)
        binding = create_binding(
            reflection_hash=reflection_hash,
            phase15_digest=mock_phase15_digest,
            phase19_digest=mock_phase19_digest,
        )
        
        assert len(binding.binding_hash) == 64
        assert all(c in "0123456789abcdef" for c in binding.binding_hash)

    def test_binding_changes_with_reflection(
        self,
        mock_phase15_digest: str,
        mock_phase19_digest: str,
    ) -> None:
        """Binding must change when reflection changes."""
        from phase20_reflection.reflection_hash import hash_reflection, create_binding
        
        hash1 = hash_reflection("reflection one")
        hash2 = hash_reflection("reflection two")
        
        binding1 = create_binding(hash1, mock_phase15_digest, mock_phase19_digest)
        binding2 = create_binding(hash2, mock_phase15_digest, mock_phase19_digest)
        
        assert binding1.binding_hash != binding2.binding_hash

    def test_binding_changes_with_phase15(
        self,
        sample_reflection_text: str,
        mock_phase19_digest: str,
    ) -> None:
        """Binding must change when Phase-15 digest changes."""
        from phase20_reflection.reflection_hash import hash_reflection, create_binding
        
        reflection_hash = hash_reflection(sample_reflection_text)
        
        binding1 = create_binding(reflection_hash, "a" * 64, mock_phase19_digest)
        binding2 = create_binding(reflection_hash, "c" * 64, mock_phase19_digest)
        
        assert binding1.binding_hash != binding2.binding_hash

    def test_binding_changes_with_phase19(
        self,
        sample_reflection_text: str,
        mock_phase15_digest: str,
    ) -> None:
        """Binding must change when Phase-19 digest changes."""
        from phase20_reflection.reflection_hash import hash_reflection, create_binding
        
        reflection_hash = hash_reflection(sample_reflection_text)
        
        binding1 = create_binding(reflection_hash, mock_phase15_digest, "b" * 64)
        binding2 = create_binding(reflection_hash, mock_phase15_digest, "d" * 64)
        
        assert binding1.binding_hash != binding2.binding_hash

    def test_binding_is_verifiable(
        self,
        sample_reflection_text: str,
        mock_phase15_digest: str,
        mock_phase19_digest: str,
    ) -> None:
        """Binding must be marked as verifiable."""
        from phase20_reflection.reflection_hash import hash_reflection, create_binding
        
        reflection_hash = hash_reflection(sample_reflection_text)
        binding = create_binding(
            reflection_hash=reflection_hash,
            phase15_digest=mock_phase15_digest,
            phase19_digest=mock_phase19_digest,
        )
        
        assert binding.verifiable is True


class TestBindingImmutability:
    """Tests for binding immutability."""

    def test_binding_is_frozen(
        self,
        sample_reflection_text: str,
        mock_phase15_digest: str,
        mock_phase19_digest: str,
    ) -> None:
        """Binding must be immutable (frozen dataclass)."""
        from phase20_reflection.reflection_hash import hash_reflection, create_binding
        
        reflection_hash = hash_reflection(sample_reflection_text)
        binding = create_binding(
            reflection_hash=reflection_hash,
            phase15_digest=mock_phase15_digest,
            phase19_digest=mock_phase19_digest,
        )
        
        with pytest.raises(Exception):  # FrozenInstanceError
            binding.binding_hash = "tampered"  # type: ignore

    def test_binding_timestamp_recorded(
        self,
        sample_reflection_text: str,
        mock_phase15_digest: str,
        mock_phase19_digest: str,
    ) -> None:
        """Binding must include timestamp."""
        from phase20_reflection.reflection_hash import hash_reflection, create_binding
        
        reflection_hash = hash_reflection(sample_reflection_text)
        binding = create_binding(
            reflection_hash=reflection_hash,
            phase15_digest=mock_phase15_digest,
            phase19_digest=mock_phase19_digest,
        )
        
        assert binding.timestamp is not None
        assert len(binding.timestamp) > 0
        # Should be ISO-8601 format
        assert "T" in binding.timestamp or "-" in binding.timestamp
