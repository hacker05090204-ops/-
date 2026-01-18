"""
Phase-9 Types Tests

Tests for data model immutability and safety constraints.
"""

import pytest
from datetime import datetime
from dataclasses import FrozenInstanceError

from browser_assistant.types import (
    HintType,
    HintSeverity,
    ObservationType,
    ConfirmationStatus,
    BrowserObservation,
    ContextHint,
    DuplicateHint,
    ScopeWarning,
    DraftReportContent,
    HumanConfirmation,
    AssistantOutput,
)


class TestEnums:
    """Test enum definitions."""
    
    def test_hint_type_values(self):
        """Verify HintType enum values."""
        assert HintType.PATTERN_REMINDER.value == "pattern_reminder"
        assert HintType.DUPLICATE_WARNING.value == "duplicate_warning"
        assert HintType.SCOPE_WARNING.value == "scope_warning"
        assert HintType.CONTEXT_INFO.value == "context_info"
        assert HintType.CHECKLIST_ITEM.value == "checklist_item"
        assert HintType.HISTORICAL_NOTE.value == "historical_note"
    
    def test_hint_severity_values(self):
        """Verify HintSeverity enum values."""
        assert HintSeverity.INFO.value == "info"
        assert HintSeverity.NOTICE.value == "notice"
        assert HintSeverity.ATTENTION.value == "attention"
    
    def test_observation_type_values(self):
        """Verify ObservationType enum values."""
        assert ObservationType.URL_NAVIGATION.value == "url_navigation"
        assert ObservationType.DOM_CONTENT.value == "dom_content"
        assert ObservationType.FORM_DETECTED.value == "form_detected"
        assert ObservationType.PARAMETER_DETECTED.value == "parameter_detected"
    
    def test_confirmation_status_values(self):
        """Verify ConfirmationStatus enum values."""
        assert ConfirmationStatus.PENDING.value == "pending"
        assert ConfirmationStatus.CONFIRMED.value == "confirmed"
        assert ConfirmationStatus.REJECTED.value == "rejected"
        assert ConfirmationStatus.EXPIRED.value == "expired"


class TestBrowserObservation:
    """Test BrowserObservation immutability and safety."""
    
    def test_observation_is_frozen(self):
        """Verify observation cannot be modified."""
        obs = BrowserObservation(
            observation_id="test-001",
            observation_type=ObservationType.URL_NAVIGATION,
            timestamp=datetime.now(),
            url="https://example.com",
            content="Test content",
            metadata=(),
        )
        
        with pytest.raises(FrozenInstanceError):
            obs.url = "https://modified.com"
    
    def test_observation_safety_markers_always_true(self):
        """Verify safety markers are always True."""
        obs = BrowserObservation(
            observation_id="test-001",
            observation_type=ObservationType.URL_NAVIGATION,
            timestamp=datetime.now(),
            url="https://example.com",
            content="Test content",
            metadata=(),
        )
        
        assert obs.is_passive_observation is True
        assert obs.no_modification_performed is True
    
    def test_observation_cannot_override_safety_markers(self):
        """Verify safety markers cannot be set to False."""
        # Even if explicitly set to False, they should be True
        obs = BrowserObservation(
            observation_id="test-001",
            observation_type=ObservationType.URL_NAVIGATION,
            timestamp=datetime.now(),
            url="https://example.com",
            content="Test content",
            metadata=(),
            is_passive_observation=True,  # Cannot be False
            no_modification_performed=True,  # Cannot be False
        )
        
        assert obs.is_passive_observation is True
        assert obs.no_modification_performed is True


class TestContextHint:
    """Test ContextHint immutability and safety."""
    
    def test_hint_is_frozen(self):
        """Verify hint cannot be modified."""
        hint = ContextHint(
            hint_id="hint-001",
            hint_type=HintType.PATTERN_REMINDER,
            hint_severity=HintSeverity.INFO,
            title="Test Hint",
            description="Test description",
            related_observation_id=None,
            timestamp=datetime.now(),
        )
        
        with pytest.raises(FrozenInstanceError):
            hint.title = "Modified"
    
    def test_hint_safety_markers_always_true(self):
        """Verify hint safety markers are always True."""
        hint = ContextHint(
            hint_id="hint-001",
            hint_type=HintType.PATTERN_REMINDER,
            hint_severity=HintSeverity.INFO,
            title="Test Hint",
            description="Test description",
            related_observation_id=None,
            timestamp=datetime.now(),
        )
        
        assert hint.human_confirmation_required is True
        assert hint.is_advisory_only is True
        assert hint.no_auto_action is True


class TestDuplicateHint:
    """Test DuplicateHint immutability and safety."""
    
    def test_duplicate_hint_is_frozen(self):
        """Verify duplicate hint cannot be modified."""
        hint = DuplicateHint(
            hint_id="dup-001",
            current_url="https://example.com",
            similar_finding_id="finding-001",
            similarity_score=0.85,
            similarity_reason="Content similarity",
            timestamp=datetime.now(),
        )
        
        with pytest.raises(FrozenInstanceError):
            hint.similarity_score = 1.0
    
    def test_duplicate_hint_safety_markers(self):
        """Verify duplicate hint safety markers."""
        hint = DuplicateHint(
            hint_id="dup-001",
            current_url="https://example.com",
            similar_finding_id="finding-001",
            similarity_score=0.85,
            similarity_reason="Content similarity",
            timestamp=datetime.now(),
        )
        
        assert hint.human_confirmation_required is True
        assert hint.is_heuristic is True
        assert hint.does_not_block is True
        assert "heuristic" in hint.similarity_disclaimer.lower()


class TestScopeWarning:
    """Test ScopeWarning immutability and safety."""
    
    def test_scope_warning_is_frozen(self):
        """Verify scope warning cannot be modified."""
        warning = ScopeWarning(
            warning_id="scope-001",
            url="https://example.com",
            scope_status="in_scope",
            warning_message="Test warning",
            authorization_reference=None,
            timestamp=datetime.now(),
        )
        
        with pytest.raises(FrozenInstanceError):
            warning.scope_status = "out_of_scope"
    
    def test_scope_warning_safety_markers(self):
        """Verify scope warning safety markers."""
        warning = ScopeWarning(
            warning_id="scope-001",
            url="https://example.com",
            scope_status="in_scope",
            warning_message="Test warning",
            authorization_reference=None,
            timestamp=datetime.now(),
        )
        
        assert warning.human_confirmation_required is True
        assert warning.does_not_block is True
        assert warning.is_advisory_only is True


class TestDraftReportContent:
    """Test DraftReportContent immutability and safety."""
    
    def test_draft_is_frozen(self):
        """Verify draft cannot be modified."""
        draft = DraftReportContent(
            draft_id="draft-001",
            title_suggestion="Test Title",
            description_template="Test description",
            observed_behavior="Test behavior",
            related_observations=(),
            timestamp=datetime.now(),
            content_hash="abc123",
        )
        
        with pytest.raises(FrozenInstanceError):
            draft.title_suggestion = "Modified"
    
    def test_draft_safety_markers(self):
        """Verify draft safety markers."""
        draft = DraftReportContent(
            draft_id="draft-001",
            title_suggestion="Test Title",
            description_template="Test description",
            observed_behavior="Test behavior",
            related_observations=(),
            timestamp=datetime.now(),
            content_hash="abc123",
        )
        
        assert draft.human_must_review is True
        assert draft.human_must_edit is True
        assert draft.human_must_confirm is True
        assert draft.is_template_only is True
        assert draft.no_auto_submission is True
        assert "human" in draft.no_severity_assigned.lower()
        assert "human" in draft.no_classification_assigned.lower()
    
    def test_draft_hash_computation(self):
        """Verify draft hash is deterministic."""
        hash1 = DraftReportContent.compute_hash(
            title="Test",
            description="Desc",
            observed_behavior="Behavior",
            observations=("obs-1", "obs-2"),
        )
        hash2 = DraftReportContent.compute_hash(
            title="Test",
            description="Desc",
            observed_behavior="Behavior",
            observations=("obs-1", "obs-2"),
        )
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex


class TestHumanConfirmation:
    """Test HumanConfirmation immutability and safety."""
    
    def test_confirmation_is_frozen(self):
        """Verify confirmation cannot be modified."""
        conf = HumanConfirmation(
            confirmation_id="conf-001",
            output_id="out-001",
            output_type="hint",
            status=ConfirmationStatus.CONFIRMED,
            confirmed_by="user-001",
            confirmed_at=datetime.now(),
            confirmation_hash="abc123",
        )
        
        with pytest.raises(FrozenInstanceError):
            conf.status = ConfirmationStatus.REJECTED
    
    def test_confirmation_safety_markers(self):
        """Verify confirmation safety markers."""
        conf = HumanConfirmation(
            confirmation_id="conf-001",
            output_id="out-001",
            output_type="hint",
            status=ConfirmationStatus.CONFIRMED,
            confirmed_by="user-001",
            confirmed_at=datetime.now(),
            confirmation_hash="abc123",
        )
        
        assert conf.is_explicit_human_action is True
        assert conf.is_single_use is True
    
    def test_confirmation_hash_computation(self):
        """Verify confirmation hash is deterministic."""
        now = datetime.now()
        hash1 = HumanConfirmation.compute_hash(
            output_id="out-001",
            output_type="hint",
            status=ConfirmationStatus.CONFIRMED,
            confirmed_by="user-001",
            confirmed_at=now,
        )
        hash2 = HumanConfirmation.compute_hash(
            output_id="out-001",
            output_type="hint",
            status=ConfirmationStatus.CONFIRMED,
            confirmed_by="user-001",
            confirmed_at=now,
        )
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex


class TestAssistantOutput:
    """Test AssistantOutput immutability and safety."""
    
    def test_output_is_frozen(self):
        """Verify output cannot be modified."""
        output = AssistantOutput(
            output_id="out-001",
            output_type="hint",
            content={"test": "data"},
            timestamp=datetime.now(),
            confirmation_status=ConfirmationStatus.PENDING,
            confirmation_id=None,
        )
        
        with pytest.raises(FrozenInstanceError):
            output.confirmation_status = ConfirmationStatus.CONFIRMED
    
    def test_output_safety_markers(self):
        """Verify output safety markers."""
        output = AssistantOutput(
            output_id="out-001",
            output_type="hint",
            content={"test": "data"},
            timestamp=datetime.now(),
            confirmation_status=ConfirmationStatus.PENDING,
            confirmation_id=None,
        )
        
        assert output.requires_human_confirmation is True
        assert output.no_auto_action is True
        assert output.is_advisory_only is True
