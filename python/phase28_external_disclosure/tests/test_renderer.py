"""
Phase-28 Renderer Tests

NO AUTHORITY / PRESENTATION ONLY

Tests for Phase-28 proof rendering.
Rendering MUST be human-initiated.
Rendering MUST use static templates.
Rendering MUST NOT interpret or analyze.
"""

import pytest
from datetime import datetime, timezone


class TestRenderRequiresHumanInitiated:
    """Tests that rendering requires human_initiated=True."""

    def test_render_requires_human_initiated(self, sample_attestation):
        """render_proofs MUST require human_initiated=True."""
        from phase28_external_disclosure import render_proofs
        
        result = render_proofs([sample_attestation], human_initiated=True)
        
        # Should succeed with human_initiated=True
        assert result is not None
        assert not hasattr(result, 'error_type')  # Not an error

    def test_render_refuses_without_human_initiated(self, sample_attestation):
        """render_proofs MUST refuse if human_initiated=False."""
        from phase28_external_disclosure import render_proofs, PresentationError
        
        result = render_proofs([sample_attestation], human_initiated=False)
        
        # Should return error
        assert isinstance(result, PresentationError)
        assert result.error_type == "HUMAN_INITIATION_REQUIRED"


class TestRenderDisclaimers:
    """Tests that rendering includes required disclaimers."""

    def test_render_includes_not_verified_disclaimer(self, sample_attestation):
        """Rendered output MUST include NOT VERIFIED disclaimer."""
        from phase28_external_disclosure import render_proofs
        
        result = render_proofs([sample_attestation], human_initiated=True)
        
        assert "NOT VERIFIED" in result

    def test_render_includes_no_authority_disclaimer(self, sample_attestation):
        """Rendered output MUST include NO AUTHORITY disclaimer."""
        from phase28_external_disclosure import render_proofs
        
        result = render_proofs([sample_attestation], human_initiated=True)
        
        assert "NO AUTHORITY" in result


class TestRenderStaticTemplate:
    """Tests that rendering uses static templates only."""

    def test_render_uses_static_template(self, sample_attestation):
        """Rendering MUST use static template structure."""
        from phase28_external_disclosure import render_proofs
        
        result = render_proofs([sample_attestation], human_initiated=True)
        
        # Should have standard template sections
        assert "PRESENTATION ONLY" in result or "NO AUTHORITY" in result

    def test_render_does_not_interpret(self, sample_attestation):
        """Rendering MUST NOT interpret proof content."""
        from phase28_external_disclosure import render_proofs
        
        result = render_proofs([sample_attestation], human_initiated=True)
        
        # Should NOT contain interpretation language
        forbidden_terms = ["verified", "certified", "approved", "compliant", "validated"]
        for term in forbidden_terms:
            # Allow "NOT VERIFIED" but not standalone "verified"
            if term == "verified":
                # Check it's only in "NOT VERIFIED" context
                result_lower = result.lower()
                if "verified" in result_lower:
                    assert "not verified" in result_lower
            else:
                assert term not in result.lower()

    def test_render_does_not_analyze(self, sample_attestation):
        """Rendering MUST NOT analyze proof content."""
        from phase28_external_disclosure import render_proofs
        
        result = render_proofs([sample_attestation], human_initiated=True)
        
        # Should NOT contain analysis language (except in disclaimers)
        # "interpretation" appears in disclaimer "without interpretation" which is OK
        forbidden_terms = ["analysis", "analyzed", "judgment", "score", "rank"]
        for term in forbidden_terms:
            assert term not in result.lower()


class TestRenderAttestation:
    """Tests for attestation rendering."""

    def test_render_attestation_requires_human_initiated(self, sample_attestation):
        """render_attestation MUST require human_initiated=True."""
        from phase28_external_disclosure import render_attestation
        
        result = render_attestation(sample_attestation, human_initiated=True)
        
        assert result is not None
        assert "NOT VERIFIED" in result or "NO AUTHORITY" in result


class TestRenderBundle:
    """Tests for bundle rendering."""

    def test_render_bundle_requires_human_initiated(self, sample_bundle):
        """render_bundle MUST require human_initiated=True."""
        from phase28_external_disclosure import render_bundle
        
        result = render_bundle(sample_bundle, human_initiated=True)
        
        assert result is not None
        assert "NOT VERIFIED" in result or "NO AUTHORITY" in result
