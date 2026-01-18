"""
Integration tests for Phase-10: Governance & Friction Layer.

Tests the full friction flow through the FrictionCoordinator,
ensuring all friction mechanisms are enforced and no bypass is possible.

Task 13.2: Write integration tests
- Test full friction flow
- Test all friction mechanisms enforced
- Test no bypass possible
- Requirements: All

Task 16.2: Write comprehensive integration tests
- Test full workflow with all friction
- Test boundary enforcement across components
- Test all safety markers
- Test forbidden method absence
- Requirements: All
"""

import pytest
import time
import inspect
from dataclasses import FrozenInstanceError
from unittest.mock import patch

from governance_friction.coordinator import FrictionCoordinator
from governance_friction.types import (
    FrictionState,
    DeliberationRecord,
    ChallengeQuestion,
    RubberStampWarning,
    CooldownState,
    AuditCompleteness,
    AuditEntry,
    FrictionAction,
    WarningLevel,
    MIN_DELIBERATION_SECONDS,
    MIN_COOLDOWN_SECONDS,
    MIN_DECISIONS_FOR_ANALYSIS,
)
from governance_friction.errors import (
    DeliberationTimeViolation,
    ForcedEditViolation,
    ChallengeNotAnswered,
    CooldownViolation,
    AuditIncomplete,
    Phase10BoundaryViolation,
    NetworkExecutionAttempt,
    AutomationAttempt,
    FrictionBypassAttempt,
    ReadOnlyViolation,
)
from governance_friction.boundaries import Phase10BoundaryGuard
from governance_friction.deliberation import DeliberationTimer
from governance_friction.edit_checker import ForcedEditChecker
from governance_friction.challenge import ChallengeQuestionGenerator, ChallengeAnswerValidator
from governance_friction.rubber_stamp import RubberStampDetector
from governance_friction.cooldown import CooldownEnforcer
from governance_friction.audit_completeness import AuditCompletenessChecker
from governance_friction.audit import FrictionAuditLogger


@pytest.fixture
def coordinator():
    """
    Create a FrictionCoordinator with boundary validation mocked.
    
    Note: We mock validate_all() because pytest/hypothesis import http.client
    which is in the forbidden imports list. The boundary guard is tested
    separately in test_boundaries.py.
    """
    with patch('governance_friction.coordinator.Phase10BoundaryGuard.validate_all'):
        yield FrictionCoordinator()


class TestFullFrictionFlow:
    """Test the complete friction flow from start to finish."""
    
    def test_complete_friction_flow_success(self, coordinator):
        """Test successful completion of full friction flow."""
        decision_id = "test-decision-001"
        reviewer_id = "test-reviewer-001"
        original_content = "Original vulnerability report content."
        edited_content = "MODIFIED vulnerability report with meaningful changes."
        context = {
            "type": "vulnerability",
            "title": "SQL Injection",
            "summary": "Critical SQL injection in login form",
        }
        
        # Step 1: Start friction flow
        state = coordinator.start_friction(decision_id, original_content, context)
        assert state.decision_id == decision_id
        assert state.deliberation is not None
        assert state.challenge is not None
        assert not state.is_friction_complete
        
        # Step 2: Submit meaningful edit
        state = coordinator.submit_edit(decision_id, edited_content)
        assert state.edit_verified is True
        
        # Step 3: Submit challenge answer (must be meaningful)
        answer = "The primary vulnerability is SQL injection in the login endpoint."
        state = coordinator.submit_challenge_answer(decision_id, answer)
        assert state.challenge is not None
        assert state.challenge.is_answered is True
        
        # Step 4: Wait for deliberation time
        time.sleep(MIN_DELIBERATION_SECONDS + 0.1)
        
        # Step 5: Complete deliberation
        state = coordinator.complete_deliberation(decision_id, reviewer_id)
        assert state.deliberation is not None
        assert state.deliberation.is_complete is True
        assert state.cooldown is not None
        
        # Step 6: Wait for cooldown
        time.sleep(MIN_COOLDOWN_SECONDS + 0.1)
        
        # Step 7: Complete friction
        state = coordinator.complete_friction(decision_id)
        assert state.is_friction_complete is True
        assert state.can_proceed is True
        assert state.audit_completeness is not None
        assert state.audit_completeness.is_complete is True
    
    def test_friction_flow_preserves_state(self, coordinator):
        """Test that friction state is preserved throughout the flow."""
        decision_id = "test-decision-002"
        original_content = "Original content for state test."
        context = {"type": "test", "summary": "State preservation test"}
        
        # Start friction
        initial_state = coordinator.start_friction(decision_id, original_content, context)
        
        # Verify state can be retrieved
        retrieved_state = coordinator.get_state(decision_id)
        assert retrieved_state is not None
        assert retrieved_state.decision_id == decision_id
        assert retrieved_state.deliberation.decision_id == decision_id


class TestAllFrictionMechanismsEnforced:
    """Test that all friction mechanisms are properly enforced."""
    
    def test_deliberation_time_enforced(self, coordinator):
        """Test that deliberation time cannot be bypassed."""
        decision_id = "test-delib-001"
        reviewer_id = "test-reviewer"
        original_content = "Content for deliberation test."
        context = {"type": "test"}
        
        # Start friction
        coordinator.start_friction(decision_id, original_content, context)
        
        # Try to complete deliberation immediately - should fail
        with pytest.raises(DeliberationTimeViolation) as exc_info:
            coordinator.complete_deliberation(decision_id, reviewer_id)
        
        assert exc_info.value.decision_id == decision_id
        assert exc_info.value.elapsed_seconds < MIN_DELIBERATION_SECONDS
    
    def test_forced_edit_enforced_identical_content(self, coordinator):
        """Test that identical content is rejected."""
        decision_id = "test-edit-001"
        original_content = "Content that must be edited."
        context = {"type": "test"}
        
        # Start friction
        coordinator.start_friction(decision_id, original_content, context)
        
        # Try to submit identical content - should fail
        with pytest.raises(ForcedEditViolation) as exc_info:
            coordinator.submit_edit(decision_id, original_content)
        
        assert exc_info.value.decision_id == decision_id
        assert "identical" in exc_info.value.reason.lower()
    
    def test_forced_edit_enforced_whitespace_only(self, coordinator):
        """Test that whitespace-only changes are rejected."""
        decision_id = "test-edit-002"
        original_content = "Content that must be edited."
        context = {"type": "test"}
        
        # Start friction
        coordinator.start_friction(decision_id, original_content, context)
        
        # Try to submit whitespace-only change - should fail
        whitespace_edit = original_content + "   \n\t  "
        with pytest.raises(ForcedEditViolation) as exc_info:
            coordinator.submit_edit(decision_id, whitespace_edit)
        
        assert exc_info.value.decision_id == decision_id
        assert "whitespace" in exc_info.value.reason.lower()
    
    def test_challenge_answer_enforced_empty(self, coordinator):
        """Test that empty challenge answers are rejected."""
        decision_id = "test-challenge-001"
        original_content = "Content for challenge test."
        context = {"type": "vulnerability"}
        
        # Start friction
        coordinator.start_friction(decision_id, original_content, context)
        
        # Try to submit empty answer - should fail
        with pytest.raises(ChallengeNotAnswered) as exc_info:
            coordinator.submit_challenge_answer(decision_id, "")
        
        assert exc_info.value.decision_id == decision_id
    
    def test_challenge_answer_enforced_whitespace(self, coordinator):
        """Test that whitespace-only challenge answers are rejected."""
        decision_id = "test-challenge-002"
        original_content = "Content for challenge test."
        context = {"type": "vulnerability"}
        
        # Start friction
        coordinator.start_friction(decision_id, original_content, context)
        
        # Try to submit whitespace-only answer - should fail
        with pytest.raises(ChallengeNotAnswered):
            coordinator.submit_challenge_answer(decision_id, "   \n\t  ")
    
    def test_challenge_answer_enforced_too_short(self, coordinator):
        """Test that short challenge answers are rejected."""
        decision_id = "test-challenge-003"
        original_content = "Content for challenge test."
        context = {"type": "vulnerability"}
        
        # Start friction
        coordinator.start_friction(decision_id, original_content, context)
        
        # Try to submit too-short answer - should fail
        with pytest.raises(ChallengeNotAnswered):
            coordinator.submit_challenge_answer(decision_id, "short")
    
    def test_cooldown_enforced(self, coordinator):
        """Test that cooldown period cannot be bypassed."""
        decision_id = "test-cooldown-001"
        reviewer_id = "test-reviewer"
        original_content = "Content for cooldown test."
        edited_content = "MODIFIED content for cooldown test."
        context = {"type": "test"}
        
        # Start friction and complete prerequisites
        coordinator.start_friction(decision_id, original_content, context)
        coordinator.submit_edit(decision_id, edited_content)
        coordinator.submit_challenge_answer(
            decision_id, 
            "This is a meaningful answer to the challenge question."
        )
        
        # Wait for deliberation
        time.sleep(MIN_DELIBERATION_SECONDS + 0.1)
        coordinator.complete_deliberation(decision_id, reviewer_id)
        
        # Try to complete friction immediately - should fail due to cooldown
        with pytest.raises(CooldownViolation) as exc_info:
            coordinator.complete_friction(decision_id)
        
        assert exc_info.value.decision_id == decision_id
        assert exc_info.value.remaining_seconds > 0
    
    def test_audit_completeness_enforced(self, coordinator):
        """Test that audit completeness is enforced."""
        decision_id = "test-audit-001"
        reviewer_id = "test-reviewer"
        original_content = "Content for audit test."
        context = {"type": "test"}
        
        # Start friction but don't complete all steps
        coordinator.start_friction(decision_id, original_content, context)
        
        # Wait for deliberation
        time.sleep(MIN_DELIBERATION_SECONDS + 0.1)
        
        # Complete deliberation without edit or challenge
        # This should work but audit will be incomplete
        coordinator.complete_deliberation(decision_id, reviewer_id)
        
        # Wait for cooldown
        time.sleep(MIN_COOLDOWN_SECONDS + 0.1)
        
        # Try to complete friction - should fail due to incomplete audit
        with pytest.raises(AuditIncomplete) as exc_info:
            coordinator.complete_friction(decision_id)
        
        assert exc_info.value.decision_id == decision_id
        assert len(exc_info.value.missing_items) > 0


class TestNoBypassPossible:
    """Test that no bypass mechanisms exist."""
    
    def test_coordinator_has_no_bypass_methods(self, coordinator):
        """Test that FrictionCoordinator has no bypass methods."""
        bypass_methods = [
            "bypass", "skip", "disable", "auto_approve",
            "instant", "fast_track", "override", "bypass_all",
            "skip_deliberation", "skip_edit", "skip_challenge",
            "skip_cooldown", "skip_audit", "reduce_friction",
        ]
        
        for method in bypass_methods:
            assert not hasattr(coordinator, method), f"Coordinator has forbidden method: {method}"
    
    def test_cannot_skip_deliberation_step(self, coordinator):
        """Test that deliberation step cannot be skipped."""
        decision_id = "test-skip-delib"
        reviewer_id = "test-reviewer"
        original_content = "Content for skip test."
        edited_content = "MODIFIED content for skip test."
        context = {"type": "test"}
        
        # Start friction
        coordinator.start_friction(decision_id, original_content, context)
        coordinator.submit_edit(decision_id, edited_content)
        coordinator.submit_challenge_answer(
            decision_id,
            "This is a meaningful answer to the challenge question."
        )
        
        # Try to complete deliberation without waiting - should fail
        with pytest.raises(DeliberationTimeViolation):
            coordinator.complete_deliberation(decision_id, reviewer_id)
    
    def test_cannot_skip_edit_step(self, coordinator):
        """Test that edit step cannot be skipped."""
        decision_id = "test-skip-edit"
        reviewer_id = "test-reviewer"
        original_content = "Content for skip edit test."
        context = {"type": "test"}
        
        # Start friction
        coordinator.start_friction(decision_id, original_content, context)
        
        # Submit challenge answer
        coordinator.submit_challenge_answer(
            decision_id,
            "This is a meaningful answer to the challenge question."
        )
        
        # Wait for deliberation
        time.sleep(MIN_DELIBERATION_SECONDS + 0.1)
        coordinator.complete_deliberation(decision_id, reviewer_id)
        
        # Wait for cooldown
        time.sleep(MIN_COOLDOWN_SECONDS + 0.1)
        
        # Try to complete friction without edit - should fail
        with pytest.raises(AuditIncomplete) as exc_info:
            coordinator.complete_friction(decision_id)
        
        assert "edit" in exc_info.value.missing_items
    
    def test_cannot_skip_challenge_step(self, coordinator):
        """Test that challenge step cannot be skipped."""
        decision_id = "test-skip-challenge"
        reviewer_id = "test-reviewer"
        original_content = "Content for skip challenge test."
        edited_content = "MODIFIED content for skip challenge test."
        context = {"type": "test"}
        
        # Start friction
        coordinator.start_friction(decision_id, original_content, context)
        coordinator.submit_edit(decision_id, edited_content)
        
        # Wait for deliberation
        time.sleep(MIN_DELIBERATION_SECONDS + 0.1)
        coordinator.complete_deliberation(decision_id, reviewer_id)
        
        # Wait for cooldown
        time.sleep(MIN_COOLDOWN_SECONDS + 0.1)
        
        # Try to complete friction without challenge - should fail
        with pytest.raises(AuditIncomplete) as exc_info:
            coordinator.complete_friction(decision_id)
        
        assert "challenge" in exc_info.value.missing_items
    
    def test_cannot_skip_cooldown_step(self, coordinator):
        """Test that cooldown step cannot be skipped."""
        decision_id = "test-skip-cooldown"
        reviewer_id = "test-reviewer"
        original_content = "Content for skip cooldown test."
        edited_content = "MODIFIED content for skip cooldown test."
        context = {"type": "test"}
        
        # Start friction and complete all prerequisites
        coordinator.start_friction(decision_id, original_content, context)
        coordinator.submit_edit(decision_id, edited_content)
        coordinator.submit_challenge_answer(
            decision_id,
            "This is a meaningful answer to the challenge question."
        )
        
        # Wait for deliberation
        time.sleep(MIN_DELIBERATION_SECONDS + 0.1)
        coordinator.complete_deliberation(decision_id, reviewer_id)
        
        # Try to complete friction immediately without cooldown - should fail
        with pytest.raises(CooldownViolation):
            coordinator.complete_friction(decision_id)
    
    def test_friction_state_cannot_be_modified(self, coordinator):
        """Test that FrictionState is immutable."""
        decision_id = "test-immutable"
        original_content = "Content for immutability test."
        context = {"type": "test"}
        
        # Start friction
        state = coordinator.start_friction(decision_id, original_content, context)
        
        # Try to modify state - should fail
        with pytest.raises(Exception):  # FrozenInstanceError
            state.is_friction_complete = True
        
        with pytest.raises(Exception):  # FrozenInstanceError
            state.edit_verified = True


class TestAuditTrailIntegrity:
    """Test audit trail integrity throughout the friction flow."""
    
    def test_audit_entries_created_for_each_step(self, coordinator):
        """Test that audit entries are created for each friction step."""
        decision_id = "test-audit-entries"
        reviewer_id = "test-reviewer"
        original_content = "Content for audit entries test."
        edited_content = "MODIFIED content for audit entries test."
        context = {"type": "vulnerability"}
        
        # Complete full friction flow
        coordinator.start_friction(decision_id, original_content, context)
        coordinator.submit_edit(decision_id, edited_content)
        coordinator.submit_challenge_answer(
            decision_id,
            "This is a meaningful answer to the challenge question."
        )
        
        time.sleep(MIN_DELIBERATION_SECONDS + 0.1)
        coordinator.complete_deliberation(decision_id, reviewer_id)
        
        time.sleep(MIN_COOLDOWN_SECONDS + 0.1)
        coordinator.complete_friction(decision_id)
        
        # Verify audit entries exist
        entries = coordinator.get_audit_entries(decision_id)
        assert len(entries) > 0
        
        # Verify audit chain integrity
        assert coordinator.verify_audit_chain() is True
    
    def test_audit_chain_verification(self, coordinator):
        """Test that audit chain can be verified."""
        decision_id = "test-chain-verify"
        original_content = "Content for chain verification."
        context = {"type": "test"}
        
        # Start friction (creates audit entries)
        coordinator.start_friction(decision_id, original_content, context)
        
        # Verify chain is valid
        assert coordinator.verify_audit_chain() is True


class TestRubberStampDetectionIntegration:
    """Test rubber-stamp detection integration."""
    
    def test_rubber_stamp_warning_is_advisory_only(self, coordinator):
        """Test that rubber-stamp warnings don't block the flow."""
        reviewer_id = "test-reviewer-rapid"
        
        # Complete multiple decisions rapidly to trigger warning
        for i in range(6):  # More than MIN_DECISIONS_FOR_ANALYSIS
            decision_id = f"test-rapid-{i}"
            original_content = f"Content for rapid test {i}."
            edited_content = f"MODIFIED content for rapid test {i}."
            context = {"type": "test"}
            
            coordinator.start_friction(decision_id, original_content, context)
            coordinator.submit_edit(decision_id, edited_content)
            coordinator.submit_challenge_answer(
                decision_id,
                "This is a meaningful answer to the challenge question."
            )
            
            time.sleep(MIN_DELIBERATION_SECONDS + 0.1)
            state = coordinator.complete_deliberation(decision_id, reviewer_id)
            
            # Rubber-stamp warning should be present but not blocking
            if state.rubber_stamp_warning is not None:
                # Warning should be advisory only
                assert not hasattr(state.rubber_stamp_warning, "block")
                assert not hasattr(state.rubber_stamp_warning, "reject")
            
            time.sleep(MIN_COOLDOWN_SECONDS + 0.1)
            final_state = coordinator.complete_friction(decision_id)
            
            # Flow should complete despite any warnings
            assert final_state.is_friction_complete is True


# =============================================================================
# Task 16.2: Comprehensive Integration Tests
# =============================================================================


class TestBoundaryEnforcementAcrossComponents:
    """Test boundary enforcement across all Phase-10 components."""
    
    def test_boundary_guard_validates_on_coordinator_init(self):
        """Test that boundary guard validates on coordinator initialization."""
        # When boundary validation fails, coordinator should not initialize
        with patch('governance_friction.coordinator.Phase10BoundaryGuard.validate_all') as mock_validate:
            mock_validate.side_effect = NetworkExecutionAttempt("httpx")
            
            with pytest.raises(NetworkExecutionAttempt):
                FrictionCoordinator()
    
    def test_all_components_respect_phase_boundaries(self):
        """Test that all components respect read-only phase boundaries."""
        # All write operations to Phase-6 through Phase-9 should fail
        phases = [
            "phase-6", "phase-7", "phase-8", "phase-9",
            "decision_workflow", "submission_workflow",
            "intelligence_layer", "browser_assistant",
        ]
        write_ops = ["write", "update", "delete", "create", "modify", "insert"]
        
        for phase in phases:
            for op in write_ops:
                with pytest.raises(ReadOnlyViolation):
                    Phase10BoundaryGuard.check_write_attempt(phase, op)
    
    def test_forbidden_imports_blocked_globally(self):
        """Test that forbidden imports are blocked across all code paths."""
        forbidden_network = [
            "httpx", "requests", "aiohttp", "socket",
            "urllib.request", "urllib3", "http.client",
        ]
        forbidden_browser = [
            "selenium", "playwright", "puppeteer",
            "pyppeteer", "splinter", "mechanize",
        ]
        forbidden_ui = ["pyautogui", "pynput", "keyboard", "mouse"]
        
        for module in forbidden_network:
            with pytest.raises(NetworkExecutionAttempt):
                Phase10BoundaryGuard.check_import(module)
        
        for module in forbidden_browser + forbidden_ui:
            with pytest.raises(Phase10BoundaryViolation):
                Phase10BoundaryGuard.check_import(module)
    
    def test_forbidden_actions_blocked_globally(self):
        """Test that forbidden actions are blocked across all code paths."""
        automation_actions = [
            "auto_approve", "auto_submit", "auto_confirm",
            "infer_decision", "suggest_decision", "recommend_action",
            "classify_bug", "assign_severity", "execute_action",
        ]
        bypass_actions = [
            "bypass_deliberation", "bypass_edit", "bypass_challenge",
            "bypass_cooldown", "bypass_audit", "bypass_friction",
            "disable_friction", "reduce_friction", "skip_friction",
        ]
        
        for action in automation_actions:
            with pytest.raises(AutomationAttempt):
                Phase10BoundaryGuard.check_forbidden_action(action)
        
        for action in bypass_actions:
            with pytest.raises(FrictionBypassAttempt):
                Phase10BoundaryGuard.check_forbidden_action(action)


class TestAllSafetyMarkers:
    """Test all safety markers across Phase-10 components."""
    
    def test_deliberation_record_is_frozen(self):
        """Test that DeliberationRecord is immutable."""
        record = DeliberationRecord(
            decision_id="test-001",
            start_monotonic=100.0,
        )
        
        with pytest.raises((FrozenInstanceError, AttributeError)):
            record.decision_id = "modified"
        
        with pytest.raises((FrozenInstanceError, AttributeError)):
            record.start_monotonic = 200.0
    
    def test_challenge_question_is_frozen(self):
        """Test that ChallengeQuestion is immutable."""
        question = ChallengeQuestion(
            question_id="q-001",
            decision_id="test-001",
            question_text="What is the vulnerability?",
            context_summary="SQL injection",
            expected_answer_type="explanation",
        )
        
        with pytest.raises((FrozenInstanceError, AttributeError)):
            question.question_id = "modified"
        
        with pytest.raises((FrozenInstanceError, AttributeError)):
            question.is_answered = True
    
    def test_rubber_stamp_warning_is_frozen(self):
        """Test that RubberStampWarning is immutable."""
        warning = RubberStampWarning(
            reviewer_id="reviewer-001",
            warning_level=WarningLevel.NONE,
            reason="No warning",
            decision_count=0,
            approval_rate=0.0,
            average_deliberation_seconds=0.0,
            is_cold_start=True,
        )
        
        with pytest.raises((FrozenInstanceError, AttributeError)):
            warning.warning_level = WarningLevel.HIGH
        
        with pytest.raises((FrozenInstanceError, AttributeError)):
            warning.is_cold_start = False
    
    def test_cooldown_state_is_frozen(self):
        """Test that CooldownState is immutable."""
        state = CooldownState(
            decision_id="test-001",
            start_monotonic=100.0,
            duration_seconds=3.0,
        )
        
        with pytest.raises((FrozenInstanceError, AttributeError)):
            state.decision_id = "modified"
        
        with pytest.raises((FrozenInstanceError, AttributeError)):
            state.is_complete = True
    
    def test_audit_completeness_is_frozen(self):
        """Test that AuditCompleteness is immutable."""
        audit = AuditCompleteness(
            decision_id="test-001",
            has_deliberation=True,
        )
        
        with pytest.raises((FrozenInstanceError, AttributeError)):
            audit.has_deliberation = False
        
        with pytest.raises((FrozenInstanceError, AttributeError)):
            audit.has_edit = True
    
    def test_friction_state_is_frozen(self):
        """Test that FrictionState is immutable."""
        state = FrictionState(decision_id="test-001")
        
        with pytest.raises((FrozenInstanceError, AttributeError)):
            state.decision_id = "modified"
        
        with pytest.raises((FrozenInstanceError, AttributeError)):
            state.is_friction_complete = True
    
    def test_audit_entry_is_frozen(self):
        """Test that AuditEntry is immutable."""
        entry = AuditEntry(
            entry_id="entry-001",
            decision_id="test-001",
            action=FrictionAction.DELIBERATION_START,
            timestamp_monotonic=100.0,
        )
        
        with pytest.raises((FrozenInstanceError, AttributeError)):
            entry.entry_id = "modified"
        
        with pytest.raises((FrozenInstanceError, AttributeError)):
            entry.action = FrictionAction.FRICTION_COMPLETE
    
    def test_minimum_deliberation_seconds_constant(self):
        """Test that MIN_DELIBERATION_SECONDS is at least 5."""
        assert MIN_DELIBERATION_SECONDS >= 5.0
    
    def test_minimum_cooldown_seconds_constant(self):
        """Test that MIN_COOLDOWN_SECONDS is at least 3."""
        assert MIN_COOLDOWN_SECONDS >= 3.0


class TestForbiddenMethodAbsence:
    """Test that forbidden methods do not exist on any component."""
    
    FORBIDDEN_METHOD_PATTERNS = [
        "auto_approve", "auto_submit", "auto_confirm", "auto_edit", "auto_answer",
        "bypass", "skip", "disable", "reduce",
        "instant", "fast_track", "override",
        "infer", "suggest", "recommend",
        "classify", "assign_severity", "execute",
    ]
    
    def _check_no_forbidden_methods(self, obj, component_name):
        """Helper to check that an object has no forbidden methods."""
        for attr_name in dir(obj):
            if attr_name.startswith('_'):
                continue
            for pattern in self.FORBIDDEN_METHOD_PATTERNS:
                assert pattern not in attr_name.lower(), \
                    f"{component_name} has forbidden method: {attr_name}"
    
    def test_friction_coordinator_no_forbidden_methods(self):
        """Test FrictionCoordinator has no forbidden methods."""
        with patch('governance_friction.coordinator.Phase10BoundaryGuard.validate_all'):
            coordinator = FrictionCoordinator()
        self._check_no_forbidden_methods(coordinator, "FrictionCoordinator")
    
    def test_deliberation_timer_no_forbidden_methods(self):
        """Test DeliberationTimer has no forbidden methods."""
        timer = DeliberationTimer()
        self._check_no_forbidden_methods(timer, "DeliberationTimer")
    
    def test_forced_edit_checker_no_forbidden_methods(self):
        """Test ForcedEditChecker has no forbidden methods."""
        checker = ForcedEditChecker()
        self._check_no_forbidden_methods(checker, "ForcedEditChecker")
    
    def test_challenge_generator_no_forbidden_methods(self):
        """Test ChallengeQuestionGenerator has no forbidden methods."""
        generator = ChallengeQuestionGenerator()
        self._check_no_forbidden_methods(generator, "ChallengeQuestionGenerator")
    
    def test_challenge_validator_no_forbidden_methods(self):
        """Test ChallengeAnswerValidator has no forbidden methods."""
        validator = ChallengeAnswerValidator()
        self._check_no_forbidden_methods(validator, "ChallengeAnswerValidator")
    
    def test_rubber_stamp_detector_no_forbidden_methods(self):
        """Test RubberStampDetector has no forbidden methods."""
        detector = RubberStampDetector()
        self._check_no_forbidden_methods(detector, "RubberStampDetector")
    
    def test_cooldown_enforcer_no_forbidden_methods(self):
        """Test CooldownEnforcer has no forbidden methods."""
        enforcer = CooldownEnforcer()
        self._check_no_forbidden_methods(enforcer, "CooldownEnforcer")
    
    def test_audit_completeness_checker_no_forbidden_methods(self):
        """Test AuditCompletenessChecker has no forbidden methods."""
        checker = AuditCompletenessChecker()
        self._check_no_forbidden_methods(checker, "AuditCompletenessChecker")
    
    def test_audit_logger_no_forbidden_methods(self):
        """Test FrictionAuditLogger has no forbidden methods."""
        logger = FrictionAuditLogger()
        self._check_no_forbidden_methods(logger, "FrictionAuditLogger")
    
    def test_boundary_guard_no_forbidden_methods(self):
        """Test Phase10BoundaryGuard has no forbidden methods."""
        self._check_no_forbidden_methods(Phase10BoundaryGuard, "Phase10BoundaryGuard")


class TestFullWorkflowWithAllFriction:
    """Test complete workflow with all friction mechanisms active."""
    
    @pytest.fixture
    def coordinator(self):
        """Create a FrictionCoordinator with boundary validation mocked."""
        with patch('governance_friction.coordinator.Phase10BoundaryGuard.validate_all'):
            yield FrictionCoordinator()
    
    def test_complete_workflow_all_friction_enforced(self, coordinator):
        """Test that complete workflow enforces all friction mechanisms."""
        decision_id = "workflow-test-001"
        reviewer_id = "reviewer-001"
        original_content = "Original vulnerability report content."
        edited_content = "MODIFIED vulnerability report with meaningful changes."
        context = {
            "type": "vulnerability",
            "title": "SQL Injection",
            "summary": "Critical SQL injection in login form",
        }
        
        # Step 1: Start friction - creates deliberation, challenge
        state = coordinator.start_friction(decision_id, original_content, context)
        assert state.decision_id == decision_id
        assert state.deliberation is not None
        assert state.challenge is not None
        assert not state.is_friction_complete
        assert not state.can_proceed
        
        # Step 2: Verify deliberation cannot be completed early
        with pytest.raises(DeliberationTimeViolation):
            coordinator.complete_deliberation(decision_id, reviewer_id)
        
        # Step 3: Submit meaningful edit
        state = coordinator.submit_edit(decision_id, edited_content)
        assert state.edit_verified is True
        
        # Step 4: Submit challenge answer
        answer = "The primary vulnerability is SQL injection in the login endpoint."
        state = coordinator.submit_challenge_answer(decision_id, answer)
        assert state.challenge.is_answered is True
        
        # Step 5: Wait for deliberation time
        time.sleep(MIN_DELIBERATION_SECONDS + 0.1)
        
        # Step 6: Complete deliberation - starts cooldown
        state = coordinator.complete_deliberation(decision_id, reviewer_id)
        assert state.deliberation.is_complete is True
        assert state.cooldown is not None
        assert state.rubber_stamp_warning is not None
        
        # Step 7: Verify cooldown cannot be bypassed
        with pytest.raises(CooldownViolation):
            coordinator.complete_friction(decision_id)
        
        # Step 8: Wait for cooldown
        time.sleep(MIN_COOLDOWN_SECONDS + 0.1)
        
        # Step 9: Complete friction
        state = coordinator.complete_friction(decision_id)
        assert state.is_friction_complete is True
        assert state.can_proceed is True
        assert state.audit_completeness.is_complete is True
    
    def test_workflow_fails_without_edit(self, coordinator):
        """Test that workflow fails if edit is skipped."""
        decision_id = "no-edit-test"
        reviewer_id = "reviewer-001"
        original_content = "Content without edit."
        context = {"type": "test"}
        
        coordinator.start_friction(decision_id, original_content, context)
        
        # Submit challenge answer
        coordinator.submit_challenge_answer(
            decision_id,
            "This is a meaningful answer to the challenge question."
        )
        
        # Wait for deliberation
        time.sleep(MIN_DELIBERATION_SECONDS + 0.1)
        coordinator.complete_deliberation(decision_id, reviewer_id)
        
        # Wait for cooldown
        time.sleep(MIN_COOLDOWN_SECONDS + 0.1)
        
        # Should fail due to missing edit
        with pytest.raises(AuditIncomplete) as exc_info:
            coordinator.complete_friction(decision_id)
        assert "edit" in exc_info.value.missing_items
    
    def test_workflow_fails_without_challenge(self, coordinator):
        """Test that workflow fails if challenge is skipped."""
        decision_id = "no-challenge-test"
        reviewer_id = "reviewer-001"
        original_content = "Content without challenge."
        edited_content = "MODIFIED content without challenge."
        context = {"type": "test"}
        
        coordinator.start_friction(decision_id, original_content, context)
        coordinator.submit_edit(decision_id, edited_content)
        
        # Wait for deliberation
        time.sleep(MIN_DELIBERATION_SECONDS + 0.1)
        coordinator.complete_deliberation(decision_id, reviewer_id)
        
        # Wait for cooldown
        time.sleep(MIN_COOLDOWN_SECONDS + 0.1)
        
        # Should fail due to missing challenge
        with pytest.raises(AuditIncomplete) as exc_info:
            coordinator.complete_friction(decision_id)
        assert "challenge" in exc_info.value.missing_items
    
    def test_workflow_audit_trail_integrity(self, coordinator):
        """Test that audit trail maintains integrity throughout workflow."""
        decision_id = "audit-integrity-test"
        reviewer_id = "reviewer-001"
        original_content = "Content for audit integrity test."
        edited_content = "MODIFIED content for audit integrity test."
        context = {"type": "vulnerability"}
        
        # Complete full workflow
        coordinator.start_friction(decision_id, original_content, context)
        coordinator.submit_edit(decision_id, edited_content)
        coordinator.submit_challenge_answer(
            decision_id,
            "This is a meaningful answer to the challenge question."
        )
        
        time.sleep(MIN_DELIBERATION_SECONDS + 0.1)
        coordinator.complete_deliberation(decision_id, reviewer_id)
        
        time.sleep(MIN_COOLDOWN_SECONDS + 0.1)
        coordinator.complete_friction(decision_id)
        
        # Verify audit entries
        entries = coordinator.get_audit_entries(decision_id)
        assert len(entries) > 0
        
        # Verify audit chain integrity
        assert coordinator.verify_audit_chain() is True
        
        # Verify all expected actions are logged
        actions = [e.action for e in entries]
        assert FrictionAction.DELIBERATION_START in actions
        assert FrictionAction.DELIBERATION_END in actions
        assert FrictionAction.EDIT_VERIFIED in actions
        assert FrictionAction.CHALLENGE_ANSWERED in actions
        assert FrictionAction.COOLDOWN_START in actions
        assert FrictionAction.COOLDOWN_END in actions
        assert FrictionAction.FRICTION_COMPLETE in actions


class TestCrossComponentIntegration:
    """Test integration between different Phase-10 components."""
    
    def test_deliberation_timer_enforces_minimum(self):
        """Test that DeliberationTimer enforces minimum time."""
        timer = DeliberationTimer()
        
        # Even if we try to set a lower minimum, it should be enforced
        timer_low = DeliberationTimer(min_seconds=1.0)
        assert timer_low.min_deliberation_seconds >= MIN_DELIBERATION_SECONDS
    
    def test_cooldown_enforcer_enforces_minimum(self):
        """Test that CooldownEnforcer enforces minimum time."""
        enforcer = CooldownEnforcer()
        
        # Even if we try to set a lower minimum, it should be enforced
        enforcer_low = CooldownEnforcer(min_seconds=1.0)
        assert enforcer_low.min_cooldown_seconds >= MIN_COOLDOWN_SECONDS
    
    def test_edit_checker_rejects_whitespace_only(self):
        """Test that ForcedEditChecker rejects whitespace-only changes."""
        checker = ForcedEditChecker()
        decision_id = "whitespace-test"
        original = "Original content"
        
        checker.register_content(decision_id, original)
        
        # Whitespace-only changes should be rejected
        with pytest.raises(ForcedEditViolation):
            checker.require_edit(decision_id, original + "   ")
        
        with pytest.raises(ForcedEditViolation):
            checker.require_edit(decision_id, original + "\n\t")
    
    def test_challenge_validator_rejects_empty_answers(self):
        """Test that ChallengeAnswerValidator rejects empty answers."""
        generator = ChallengeQuestionGenerator()
        validator = ChallengeAnswerValidator()
        
        challenge = generator.generate_challenge("test-001", {"type": "test"})
        
        # Empty answers should be rejected
        with pytest.raises(ChallengeNotAnswered):
            validator.validate_answer(challenge, "")
        
        with pytest.raises(ChallengeNotAnswered):
            validator.validate_answer(challenge, "   ")
        
        with pytest.raises(ChallengeNotAnswered):
            validator.validate_answer(challenge, "\n\t")
    
    def test_rubber_stamp_detector_cold_start_safety(self):
        """Test that RubberStampDetector has cold-start safety."""
        detector = RubberStampDetector()
        reviewer_id = "new-reviewer"
        
        # New reviewer with no history should get cold-start warning
        warning = detector.analyze_pattern(reviewer_id)
        assert warning.is_cold_start is True
        assert warning.is_advisory_silent is True
        
        # Even with a few decisions, should still be cold-start
        for i in range(MIN_DECISIONS_FOR_ANALYSIS - 1):
            detector.record_confirmation(reviewer_id, f"decision-{i}", 5.0)
        
        warning = detector.analyze_pattern(reviewer_id)
        assert warning.is_cold_start is True
    
    def test_audit_completeness_requires_all_items(self):
        """Test that AuditCompletenessChecker requires all items."""
        checker = AuditCompletenessChecker()
        decision_id = "completeness-test"
        
        checker.initialize_audit(decision_id)
        
        # Missing all items should fail
        with pytest.raises(AuditIncomplete) as exc_info:
            checker.require_completeness(decision_id)
        assert len(exc_info.value.missing_items) == 4
        
        # Add items one by one
        checker.record_item(decision_id, "deliberation")
        with pytest.raises(AuditIncomplete) as exc_info:
            checker.require_completeness(decision_id)
        assert len(exc_info.value.missing_items) == 3
        
        checker.record_item(decision_id, "edit")
        checker.record_item(decision_id, "challenge")
        with pytest.raises(AuditIncomplete) as exc_info:
            checker.require_completeness(decision_id)
        assert len(exc_info.value.missing_items) == 1
        
        # All items present should succeed
        checker.record_item(decision_id, "cooldown")
        result = checker.require_completeness(decision_id)
        assert result.is_complete is True


class TestErrorHierarchy:
    """Test that error hierarchy is correct."""
    
    def test_all_errors_inherit_from_phase10_error(self):
        """Test that all Phase-10 errors inherit from Phase10Error."""
        from governance_friction.errors import Phase10Error
        
        error_classes = [
            DeliberationTimeViolation,
            ForcedEditViolation,
            ChallengeNotAnswered,
            CooldownViolation,
            AuditIncomplete,
            Phase10BoundaryViolation,
            NetworkExecutionAttempt,
            AutomationAttempt,
            FrictionBypassAttempt,
            ReadOnlyViolation,
        ]
        
        for error_class in error_classes:
            assert issubclass(error_class, Phase10Error), \
                f"{error_class.__name__} should inherit from Phase10Error"
    
    def test_boundary_violations_inherit_from_boundary_violation(self):
        """Test that boundary violations inherit from Phase10BoundaryViolation."""
        boundary_errors = [
            NetworkExecutionAttempt,
            AutomationAttempt,
            FrictionBypassAttempt,
            ReadOnlyViolation,
        ]
        
        for error_class in boundary_errors:
            assert issubclass(error_class, Phase10BoundaryViolation), \
                f"{error_class.__name__} should inherit from Phase10BoundaryViolation"
