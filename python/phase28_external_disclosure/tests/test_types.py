"""
Phase-28 Type Tests

NO AUTHORITY / PRESENTATION ONLY

Tests for Phase-28 immutable data structures.
All types MUST be frozen (immutable).
All types MUST require human_initiated.
All types MUST include disclaimers.
"""

import pytest
from datetime import datetime, timezone
from dataclasses import FrozenInstanceError


class TestDisclosureContext:
    """Tests for DisclosureContext type."""

    def test_disclosure_context_immutable(self):
        """DisclosureContext MUST be immutable (frozen)."""
        from phase28_external_disclosure import DisclosureContext, DISCLAIMER
        
        context = DisclosureContext(
            context_id="test-001",
            provided_by="HUMAN",
            provided_at=datetime.now(timezone.utc).isoformat(),
            context_text="Test context",
            human_initiated=True,
            disclaimer=DISCLAIMER,
        )
        
        with pytest.raises(FrozenInstanceError):
            context.context_text = "Modified"

    def test_disclosure_context_requires_human_initiated(self):
        """DisclosureContext MUST have human_initiated field."""
        from phase28_external_disclosure import DisclosureContext, DISCLAIMER
        
        context = DisclosureContext(
            context_id="test-001",
            provided_by="HUMAN",
            provided_at=datetime.now(timezone.utc).isoformat(),
            context_text="Test context",
            human_initiated=True,
            disclaimer=DISCLAIMER,
        )
        
        assert hasattr(context, 'human_initiated')
        assert context.human_initiated is True

    def test_disclosure_context_has_disclaimer(self):
        """DisclosureContext MUST have disclaimer field."""
        from phase28_external_disclosure import DisclosureContext, DISCLAIMER
        
        context = DisclosureContext(
            context_id="test-001",
            provided_by="HUMAN",
            provided_at=datetime.now(timezone.utc).isoformat(),
            context_text="Test context",
            human_initiated=True,
            disclaimer=DISCLAIMER,
        )
        
        assert hasattr(context, 'disclaimer')
        assert "NO AUTHORITY" in context.disclaimer


class TestProofSelection:
    """Tests for ProofSelection type."""

    def test_proof_selection_immutable(self):
        """ProofSelection MUST be immutable (frozen)."""
        from phase28_external_disclosure import ProofSelection, DISCLAIMER
        
        selection = ProofSelection(
            selection_id="test-001",
            selected_by="HUMAN",
            selected_at=datetime.now(timezone.utc).isoformat(),
            attestation_ids=("att-001",),
            bundle_ids=("bundle-001",),
            human_initiated=True,
            disclaimer=DISCLAIMER,
        )
        
        with pytest.raises(FrozenInstanceError):
            selection.selection_id = "modified"

    def test_proof_selection_requires_human_initiated(self):
        """ProofSelection MUST have human_initiated field."""
        from phase28_external_disclosure import ProofSelection, DISCLAIMER
        
        selection = ProofSelection(
            selection_id="test-001",
            selected_by="HUMAN",
            selected_at=datetime.now(timezone.utc).isoformat(),
            attestation_ids=("att-001",),
            bundle_ids=("bundle-001",),
            human_initiated=True,
            disclaimer=DISCLAIMER,
        )
        
        assert hasattr(selection, 'human_initiated')
        assert selection.human_initiated is True


class TestDisclosurePackage:
    """Tests for DisclosurePackage type."""

    def test_disclosure_package_immutable(self):
        """DisclosurePackage MUST be immutable (frozen)."""
        from phase28_external_disclosure import (
            DisclosurePackage, DisclosureContext, ProofSelection,
            DISCLAIMER, NOT_VERIFIED_NOTICE,
        )
        
        context = DisclosureContext(
            context_id="ctx-001",
            provided_by="HUMAN",
            provided_at=datetime.now(timezone.utc).isoformat(),
            context_text="Test",
            human_initiated=True,
            disclaimer=DISCLAIMER,
        )
        
        selection = ProofSelection(
            selection_id="sel-001",
            selected_by="HUMAN",
            selected_at=datetime.now(timezone.utc).isoformat(),
            attestation_ids=(),
            bundle_ids=(),
            human_initiated=True,
            disclaimer=DISCLAIMER,
        )
        
        package = DisclosurePackage(
            package_id="pkg-001",
            created_at=datetime.now(timezone.utc).isoformat(),
            created_by="HUMAN",
            context=context,
            selection=selection,
            rendered_content="Test content",
            package_hash="hash123",
            human_initiated=True,
            disclaimer=DISCLAIMER,
            not_verified_notice=NOT_VERIFIED_NOTICE,
        )
        
        with pytest.raises(FrozenInstanceError):
            package.package_id = "modified"

    def test_disclosure_package_requires_human_initiated(self):
        """DisclosurePackage MUST have human_initiated field."""
        from phase28_external_disclosure import (
            DisclosurePackage, DisclosureContext, ProofSelection,
            DISCLAIMER, NOT_VERIFIED_NOTICE,
        )
        
        context = DisclosureContext(
            context_id="ctx-001",
            provided_by="HUMAN",
            provided_at=datetime.now(timezone.utc).isoformat(),
            context_text="Test",
            human_initiated=True,
            disclaimer=DISCLAIMER,
        )
        
        selection = ProofSelection(
            selection_id="sel-001",
            selected_by="HUMAN",
            selected_at=datetime.now(timezone.utc).isoformat(),
            attestation_ids=(),
            bundle_ids=(),
            human_initiated=True,
            disclaimer=DISCLAIMER,
        )
        
        package = DisclosurePackage(
            package_id="pkg-001",
            created_at=datetime.now(timezone.utc).isoformat(),
            created_by="HUMAN",
            context=context,
            selection=selection,
            rendered_content="Test content",
            package_hash="hash123",
            human_initiated=True,
            disclaimer=DISCLAIMER,
            not_verified_notice=NOT_VERIFIED_NOTICE,
        )
        
        assert hasattr(package, 'human_initiated')
        assert package.human_initiated is True

    def test_disclosure_package_has_disclaimer(self):
        """DisclosurePackage MUST have disclaimer field."""
        from phase28_external_disclosure import (
            DisclosurePackage, DisclosureContext, ProofSelection,
            DISCLAIMER, NOT_VERIFIED_NOTICE,
        )
        
        context = DisclosureContext(
            context_id="ctx-001",
            provided_by="HUMAN",
            provided_at=datetime.now(timezone.utc).isoformat(),
            context_text="Test",
            human_initiated=True,
            disclaimer=DISCLAIMER,
        )
        
        selection = ProofSelection(
            selection_id="sel-001",
            selected_by="HUMAN",
            selected_at=datetime.now(timezone.utc).isoformat(),
            attestation_ids=(),
            bundle_ids=(),
            human_initiated=True,
            disclaimer=DISCLAIMER,
        )
        
        package = DisclosurePackage(
            package_id="pkg-001",
            created_at=datetime.now(timezone.utc).isoformat(),
            created_by="HUMAN",
            context=context,
            selection=selection,
            rendered_content="Test content",
            package_hash="hash123",
            human_initiated=True,
            disclaimer=DISCLAIMER,
            not_verified_notice=NOT_VERIFIED_NOTICE,
        )
        
        assert hasattr(package, 'disclaimer')
        assert "NO AUTHORITY" in package.disclaimer

    def test_disclosure_package_has_not_verified_notice(self):
        """DisclosurePackage MUST have not_verified_notice field."""
        from phase28_external_disclosure import (
            DisclosurePackage, DisclosureContext, ProofSelection,
            DISCLAIMER, NOT_VERIFIED_NOTICE,
        )
        
        context = DisclosureContext(
            context_id="ctx-001",
            provided_by="HUMAN",
            provided_at=datetime.now(timezone.utc).isoformat(),
            context_text="Test",
            human_initiated=True,
            disclaimer=DISCLAIMER,
        )
        
        selection = ProofSelection(
            selection_id="sel-001",
            selected_by="HUMAN",
            selected_at=datetime.now(timezone.utc).isoformat(),
            attestation_ids=(),
            bundle_ids=(),
            human_initiated=True,
            disclaimer=DISCLAIMER,
        )
        
        package = DisclosurePackage(
            package_id="pkg-001",
            created_at=datetime.now(timezone.utc).isoformat(),
            created_by="HUMAN",
            context=context,
            selection=selection,
            rendered_content="Test content",
            package_hash="hash123",
            human_initiated=True,
            disclaimer=DISCLAIMER,
            not_verified_notice=NOT_VERIFIED_NOTICE,
        )
        
        assert hasattr(package, 'not_verified_notice')
        assert "NOT VERIFIED" in package.not_verified_notice


class TestPresentationError:
    """Tests for PresentationError type."""

    def test_presentation_error_immutable(self):
        """PresentationError MUST be immutable (frozen)."""
        from phase28_external_disclosure import PresentationError, DISCLAIMER
        
        error = PresentationError(
            error_type="TEST_ERROR",
            message="Test error message",
            timestamp=datetime.now(timezone.utc).isoformat(),
            disclaimer=DISCLAIMER,
        )
        
        with pytest.raises(FrozenInstanceError):
            error.message = "Modified"
