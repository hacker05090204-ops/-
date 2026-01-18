"""
Phase-21 Hash Tests

Tests verifying SHA-256 hashing of patch content.
"""

import pytest


class TestPatchHashDeterminism:
    """Tests verifying hash is deterministic."""

    def test_same_content_same_hash(self, sample_patch_content: str) -> None:
        """Same patch content must produce same hash."""
        from phase21_patch_covenant.patch_hash import compute_patch_hash
        
        hash1 = compute_patch_hash(sample_patch_content)
        hash2 = compute_patch_hash(sample_patch_content)
        
        assert hash1 == hash2

    def test_different_content_different_hash(self) -> None:
        """Different patch content must produce different hash."""
        from phase21_patch_covenant.patch_hash import compute_patch_hash
        
        hash1 = compute_patch_hash("patch content A")
        hash2 = compute_patch_hash("patch content B")
        
        assert hash1 != hash2

    def test_hash_is_sha256_format(self, sample_patch_content: str) -> None:
        """Hash must be 64-character hex string (SHA-256)."""
        from phase21_patch_covenant.patch_hash import compute_patch_hash
        
        hash_value = compute_patch_hash(sample_patch_content)
        
        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)


class TestPatchHashChanges:
    """Tests verifying hash changes with content."""

    def test_hash_changes_with_whitespace(self) -> None:
        """Hash must change if whitespace changes."""
        from phase21_patch_covenant.patch_hash import compute_patch_hash
        
        hash1 = compute_patch_hash("content")
        hash2 = compute_patch_hash("content ")
        
        assert hash1 != hash2

    def test_hash_changes_with_newline(self) -> None:
        """Hash must change if newline added."""
        from phase21_patch_covenant.patch_hash import compute_patch_hash
        
        hash1 = compute_patch_hash("content")
        hash2 = compute_patch_hash("content\n")
        
        assert hash1 != hash2

    def test_empty_content_has_hash(self) -> None:
        """Empty content must still produce valid hash."""
        from phase21_patch_covenant.patch_hash import compute_patch_hash
        
        hash_value = compute_patch_hash("")
        
        assert len(hash_value) == 64


class TestBindingHashCreation:
    """Tests for binding hash creation."""

    def test_create_binding_hash(self) -> None:
        """Binding hash must combine all component hashes."""
        from phase21_patch_covenant.patch_hash import create_binding_hash
        
        binding = create_binding_hash(
            patch_hash="a" * 64,
            decision_hash="b" * 64,
            timestamp="2026-01-07T00:00:00Z",
        )
        
        assert len(binding) == 64

    def test_binding_hash_changes_with_components(self) -> None:
        """Binding hash must change if any component changes."""
        from phase21_patch_covenant.patch_hash import create_binding_hash
        
        binding1 = create_binding_hash(
            patch_hash="a" * 64,
            decision_hash="b" * 64,
            timestamp="2026-01-07T00:00:00Z",
        )
        
        binding2 = create_binding_hash(
            patch_hash="c" * 64,  # Changed
            decision_hash="b" * 64,
            timestamp="2026-01-07T00:00:00Z",
        )
        
        assert binding1 != binding2

