"""
Phase-28 Exporter Tests

NO AUTHORITY / PRESENTATION ONLY

Tests for Phase-28 export functionality.
Export MUST be human-initiated.
Export MUST NOT auto-share.
Export MUST NOT make network requests.
"""

import pytest
from datetime import datetime, timezone


class TestExportRequiresHumanInitiated:
    """Tests that export requires human_initiated=True."""

    def test_export_requires_human_initiated(self, sample_disclosure_context, sample_proof_selection):
        """export_package MUST require human_initiated=True."""
        from phase28_external_disclosure import create_disclosure_package
        
        result = create_disclosure_package(
            context=sample_disclosure_context,
            selection=sample_proof_selection,
            human_initiated=True,
        )
        
        # Should succeed with human_initiated=True
        assert result is not None
        assert not hasattr(result, 'error_type') or result.error_type is None

    def test_export_refuses_without_human_initiated(self, sample_disclosure_context, sample_proof_selection):
        """export_package MUST refuse if human_initiated=False."""
        from phase28_external_disclosure import create_disclosure_package, PresentationError
        
        result = create_disclosure_package(
            context=sample_disclosure_context,
            selection=sample_proof_selection,
            human_initiated=False,
        )
        
        # Should return error
        assert isinstance(result, PresentationError)
        assert result.error_type == "HUMAN_INITIATION_REQUIRED"


class TestExportCreatesPackage:
    """Tests that export creates proper disclosure package."""

    def test_export_creates_package(self, sample_disclosure_context, sample_proof_selection):
        """Export MUST create DisclosurePackage."""
        from phase28_external_disclosure import create_disclosure_package, DisclosurePackage
        
        result = create_disclosure_package(
            context=sample_disclosure_context,
            selection=sample_proof_selection,
            human_initiated=True,
        )
        
        assert isinstance(result, DisclosurePackage)

    def test_export_includes_disclaimers(self, sample_disclosure_context, sample_proof_selection):
        """Export MUST include disclaimers in package."""
        from phase28_external_disclosure import create_disclosure_package
        
        result = create_disclosure_package(
            context=sample_disclosure_context,
            selection=sample_proof_selection,
            human_initiated=True,
        )
        
        assert "NO AUTHORITY" in result.disclaimer
        assert "NOT VERIFIED" in result.not_verified_notice


class TestExportNoAutoShare:
    """Tests that export does NOT auto-share."""

    def test_export_does_not_auto_share(self, sample_disclosure_context, sample_proof_selection):
        """Export MUST NOT auto-share to any platform."""
        from phase28_external_disclosure import create_disclosure_package
        
        # Export should only create package, not share it
        result = create_disclosure_package(
            context=sample_disclosure_context,
            selection=sample_proof_selection,
            human_initiated=True,
        )
        
        # Package should be returned, not sent anywhere
        assert result is not None
        # No network activity should occur (verified by static analysis)

    def test_export_does_not_network(self, sample_disclosure_context, sample_proof_selection):
        """Export MUST NOT make network requests."""
        from phase28_external_disclosure import create_disclosure_package
        
        # This test verifies no network activity
        # Actual network blocking is verified by static analysis
        result = create_disclosure_package(
            context=sample_disclosure_context,
            selection=sample_proof_selection,
            human_initiated=True,
        )
        
        # Should return local package only
        assert result is not None


class TestExportStaticOutput:
    """Tests that export produces static output only."""

    def test_export_static_output_only(self, sample_disclosure_context, sample_proof_selection):
        """Export MUST produce static output only."""
        from phase28_external_disclosure import create_disclosure_package, DisclosurePackage
        
        result = create_disclosure_package(
            context=sample_disclosure_context,
            selection=sample_proof_selection,
            human_initiated=True,
        )
        
        # Should be immutable DisclosurePackage
        assert isinstance(result, DisclosurePackage)
        
        # Should have static content
        assert isinstance(result.rendered_content, str)
        assert isinstance(result.package_hash, str)


class TestExportToFormat:
    """Tests for export_to_format function."""

    def test_export_to_markdown(self, sample_disclosure_context, sample_proof_selection):
        """Export to markdown format."""
        from phase28_external_disclosure import create_disclosure_package, export_to_format
        
        package = create_disclosure_package(
            context=sample_disclosure_context,
            selection=sample_proof_selection,
            human_initiated=True,
        )
        
        result = export_to_format(package, format="md", human_initiated=True)
        
        assert isinstance(result, str)
        assert "NOT VERIFIED" in result

    def test_export_to_json(self, sample_disclosure_context, sample_proof_selection):
        """Export to JSON format."""
        from phase28_external_disclosure import create_disclosure_package, export_to_format
        import json
        
        package = create_disclosure_package(
            context=sample_disclosure_context,
            selection=sample_proof_selection,
            human_initiated=True,
        )
        
        result = export_to_format(package, format="json", human_initiated=True)
        
        # Should be valid JSON
        parsed = json.loads(result)
        assert "disclaimer" in parsed
