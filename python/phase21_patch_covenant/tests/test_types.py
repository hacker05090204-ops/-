"""
Phase-21 Type Tests

Tests verifying immutable data structures with no scoring fields.
"""

import pytest
from dataclasses import FrozenInstanceError


class TestPatchRecordImmutability:
    """Tests verifying PatchRecord is immutable."""

    def test_patch_record_is_frozen(self) -> None:
        """PatchRecord must be a frozen dataclass."""
        from phase21_patch_covenant.types import PatchRecord
        
        record = PatchRecord(
            patch_id="test-id",
            timestamp="2026-01-07T00:00:00Z",
            patch_hash="abc123",
            patch_diff="diff content",
            symbols_modified=("func1",),
            human_confirmed=True,
            human_rejected=False,
            human_reason="test reason",
            human_initiated=True,
            actor="HUMAN",
        )
        
        with pytest.raises(FrozenInstanceError):
            record.patch_id = "modified"

    def test_patch_record_has_human_initiated_field(self) -> None:
        """PatchRecord must have human_initiated field."""
        from phase21_patch_covenant.types import PatchRecord
        
        record = PatchRecord(
            patch_id="test-id",
            timestamp="2026-01-07T00:00:00Z",
            patch_hash="abc123",
            patch_diff="diff content",
            symbols_modified=("func1",),
            human_confirmed=True,
            human_rejected=False,
            human_reason="test reason",
            human_initiated=True,
            actor="HUMAN",
        )
        
        assert hasattr(record, "human_initiated")
        assert record.human_initiated is True

    def test_patch_record_has_actor_field(self) -> None:
        """PatchRecord must have actor field set to HUMAN."""
        from phase21_patch_covenant.types import PatchRecord
        
        record = PatchRecord(
            patch_id="test-id",
            timestamp="2026-01-07T00:00:00Z",
            patch_hash="abc123",
            patch_diff="diff content",
            symbols_modified=("func1",),
            human_confirmed=True,
            human_rejected=False,
            human_reason="test reason",
            human_initiated=True,
            actor="HUMAN",
        )
        
        assert hasattr(record, "actor")
        assert record.actor == "HUMAN"

    def test_patch_record_symbols_is_tuple(self) -> None:
        """symbols_modified must be immutable tuple."""
        from phase21_patch_covenant.types import PatchRecord
        
        record = PatchRecord(
            patch_id="test-id",
            timestamp="2026-01-07T00:00:00Z",
            patch_hash="abc123",
            patch_diff="diff content",
            symbols_modified=("func1", "func2"),
            human_confirmed=True,
            human_rejected=False,
            human_reason="test reason",
            human_initiated=True,
            actor="HUMAN",
        )
        
        assert isinstance(record.symbols_modified, tuple)


class TestPatchBindingImmutability:
    """Tests verifying PatchBinding is immutable."""

    def test_patch_binding_is_frozen(self) -> None:
        """PatchBinding must be a frozen dataclass."""
        from phase21_patch_covenant.types import PatchBinding
        
        binding = PatchBinding(
            binding_hash="hash123",
            patch_hash="patch456",
            decision_hash="decision789",
            timestamp="2026-01-07T00:00:00Z",
            session_id="session-abc",
            verifiable=True,
        )
        
        with pytest.raises(FrozenInstanceError):
            binding.binding_hash = "modified"

    def test_patch_binding_verifiable_always_true(self) -> None:
        """PatchBinding.verifiable must always be True."""
        from phase21_patch_covenant.types import PatchBinding
        
        binding = PatchBinding(
            binding_hash="hash123",
            patch_hash="patch456",
            decision_hash="decision789",
            timestamp="2026-01-07T00:00:00Z",
            session_id="session-abc",
            verifiable=True,
        )
        
        assert binding.verifiable is True


class TestSymbolConstraintsImmutability:
    """Tests verifying SymbolConstraints is immutable."""

    def test_symbol_constraints_is_frozen(self) -> None:
        """SymbolConstraints must be a frozen dataclass."""
        from phase21_patch_covenant.types import SymbolConstraints
        
        constraints = SymbolConstraints(
            allowlist=frozenset({"func1"}),
            denylist=frozenset({"eval"}),
            version="1.0.0",
        )
        
        with pytest.raises(FrozenInstanceError):
            constraints.version = "2.0.0"

    def test_symbol_constraints_uses_frozenset(self) -> None:
        """SymbolConstraints must use frozenset for lists."""
        from phase21_patch_covenant.types import SymbolConstraints
        
        constraints = SymbolConstraints(
            allowlist=frozenset({"func1", "func2"}),
            denylist=frozenset({"eval", "exec"}),
            version="1.0.0",
        )
        
        assert isinstance(constraints.allowlist, frozenset)
        assert isinstance(constraints.denylist, frozenset)


class TestNoScoringFields:
    """Tests verifying no scoring fields exist."""

    def test_patch_record_has_no_score_field(self) -> None:
        """PatchRecord must not have score field."""
        from phase21_patch_covenant.types import PatchRecord
        
        assert not hasattr(PatchRecord, "score")
        assert not hasattr(PatchRecord, "quality")
        assert not hasattr(PatchRecord, "rating")
        assert not hasattr(PatchRecord, "safety_score")

    def test_patch_binding_has_no_score_field(self) -> None:
        """PatchBinding must not have score field."""
        from phase21_patch_covenant.types import PatchBinding
        
        assert not hasattr(PatchBinding, "score")
        assert not hasattr(PatchBinding, "quality")
        assert not hasattr(PatchBinding, "confidence")

