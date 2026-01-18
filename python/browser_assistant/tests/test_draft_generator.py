"""
Phase-9 Draft Generator Tests

Tests for draft report generation.
"""

import pytest
from datetime import datetime

from browser_assistant.draft_generator import DraftReportGenerator
from browser_assistant.types import BrowserObservation, ObservationType


class TestDraftReportGenerator:
    """Test draft generator functionality."""
    
    def test_generate_draft(self, draft_generator, sample_observations):
        """Verify draft can be generated."""
        draft = draft_generator.generate_draft(sample_observations)
        
        assert draft.draft_id is not None
        assert draft.title_suggestion is not None
        assert draft.description_template is not None
        assert draft.observed_behavior is not None
    
    def test_generate_draft_with_title_hint(self, draft_generator, sample_observations):
        """Verify title hint is used."""
        draft = draft_generator.generate_draft(
            sample_observations,
            title_hint="Custom Title Hint",
        )
        
        assert "Custom Title Hint" in draft.title_suggestion
    
    def test_generate_empty_draft(self, draft_generator):
        """Verify empty draft can be generated."""
        draft = draft_generator.generate_draft([])
        
        assert draft.draft_id is not None
        assert "[TITLE" in draft.title_suggestion
        assert "Human must provide" in draft.description_template
    
    def test_draft_safety_markers(self, draft_generator, sample_observations):
        """Verify draft has safety markers."""
        draft = draft_generator.generate_draft(sample_observations)
        
        assert draft.human_must_review is True
        assert draft.human_must_edit is True
        assert draft.human_must_confirm is True
        assert draft.is_template_only is True
        assert draft.no_auto_submission is True
    
    def test_draft_no_severity(self, draft_generator, sample_observations):
        """Verify draft does not assign severity."""
        draft = draft_generator.generate_draft(sample_observations)
        
        assert "human" in draft.no_severity_assigned.lower()
    
    def test_draft_no_classification(self, draft_generator, sample_observations):
        """Verify draft does not classify."""
        draft = draft_generator.generate_draft(sample_observations)
        
        assert "human" in draft.no_classification_assigned.lower()
    
    def test_draft_has_content_hash(self, draft_generator, sample_observations):
        """Verify draft has content hash."""
        draft = draft_generator.generate_draft(sample_observations)
        
        assert draft.content_hash is not None
        assert len(draft.content_hash) == 64  # SHA-256 hex
    
    def test_draft_references_observations(self, draft_generator, sample_observations):
        """Verify draft references observations."""
        draft = draft_generator.generate_draft(sample_observations)
        
        assert len(draft.related_observations) == len(sample_observations)
        for obs in sample_observations:
            assert obs.observation_id in draft.related_observations
    
    def test_draft_description_template_structure(self, draft_generator, sample_observations):
        """Verify description template has expected sections."""
        draft = draft_generator.generate_draft(sample_observations)
        
        assert "Steps to Reproduce" in draft.description_template
        assert "Expected Behavior" in draft.description_template
        assert "Actual Behavior" in draft.description_template
        assert "Impact" in draft.description_template
        assert "Severity" in draft.description_template
        assert "Classification" in draft.description_template
    
    def test_draft_description_requires_human(self, draft_generator, sample_observations):
        """Verify description requires human input."""
        draft = draft_generator.generate_draft(sample_observations)
        
        # Should have placeholders for human input
        assert "Human must" in draft.description_template
    
    def test_get_draft_by_id(self, draft_generator, sample_observations):
        """Verify draft can be retrieved by ID."""
        draft = draft_generator.generate_draft(sample_observations)
        drafts = [draft]
        
        retrieved = draft_generator.get_draft_by_id(draft.draft_id, drafts)
        assert retrieved is not None
        assert retrieved.draft_id == draft.draft_id
    
    def test_get_draft_by_id_not_found(self, draft_generator):
        """Verify None returned for unknown ID."""
        retrieved = draft_generator.get_draft_by_id("nonexistent", [])
        assert retrieved is None


class TestDraftGeneratorNoForbiddenMethods:
    """Verify generator has no forbidden methods."""
    
    def test_no_submit_report(self, draft_generator):
        """Verify submit_report method does not exist."""
        assert not hasattr(draft_generator, "submit_report")
    
    def test_no_auto_submit(self, draft_generator):
        """Verify auto_submit method does not exist."""
        assert not hasattr(draft_generator, "auto_submit")
    
    def test_no_assign_severity(self, draft_generator):
        """Verify assign_severity method does not exist."""
        assert not hasattr(draft_generator, "assign_severity")
    
    def test_no_classify_vulnerability(self, draft_generator):
        """Verify classify_vulnerability method does not exist."""
        assert not hasattr(draft_generator, "classify_vulnerability")
    
    def test_no_calculate_cvss(self, draft_generator):
        """Verify calculate_cvss method does not exist."""
        assert not hasattr(draft_generator, "calculate_cvss")
    
    def test_no_finalize_report(self, draft_generator):
        """Verify finalize_report method does not exist."""
        assert not hasattr(draft_generator, "finalize_report")
    
    def test_no_send_to_platform(self, draft_generator):
        """Verify send_to_platform method does not exist."""
        assert not hasattr(draft_generator, "send_to_platform")
    
    def test_no_generate_poc(self, draft_generator):
        """Verify generate_poc method does not exist."""
        assert not hasattr(draft_generator, "generate_poc")
    
    def test_no_attach_evidence(self, draft_generator):
        """Verify attach_evidence method does not exist."""
        assert not hasattr(draft_generator, "attach_evidence")
    
    def test_no_auto_fill(self, draft_generator):
        """Verify auto_fill method does not exist."""
        assert not hasattr(draft_generator, "auto_fill")
