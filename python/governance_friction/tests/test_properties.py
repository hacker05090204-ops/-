"""
Property-based tests for Phase-10: Governance & Friction Layer.

These tests use Hypothesis to verify universal properties across all inputs.
MANDATORY: Minimum 100 iterations per property test.
"""

import pytest
import time
from hypothesis import given, strategies as st, settings, assume

from governance_friction.types import (
    DeliberationRecord,
    ChallengeQuestion,
    RubberStampWarning,
    CooldownState,
    AuditCompleteness,
    FrictionState,
    FrictionAction,
    WarningLevel,
    MIN_DELIBERATION_SECONDS,
    MIN_COOLDOWN_SECONDS,
    MIN_DECISIONS_FOR_ANALYSIS,
)
from governance_friction.deliberation import DeliberationTimer
from governance_friction.edit_checker import ForcedEditChecker
from governance_friction.challenge import ChallengeQuestionGenerator, ChallengeAnswerValidator
from governance_friction.rubber_stamp import RubberStampDetector
from governance_friction.cooldown import CooldownEnforcer
from governance_friction.audit_completeness import AuditCompletenessChecker
from governance_friction.boundaries import Phase10BoundaryGuard
from governance_friction.errors import (
    DeliberationTimeViolation,
    ForcedEditViolation,
    ChallengeNotAnswered,
    CooldownViolation,
    Phase10BoundaryViolation,
)


# =============================================================================
# Property 1: Deliberation Time Enforced
# =============================================================================

class TestDeliberationTimeProperty:
    """Property 1: Deliberation time is always >= MIN_DELIBERATION_SECONDS."""
    
    @given(
        decision_id=st.text(min_size=1, max_size=50),
        min_seconds=st.floats(min_value=0.0, max_value=10.0),
    )
    @settings(max_examples=100)
    def test_deliberation_minimum_enforced(self, decision_id, min_seconds):
        """Deliberation time cannot be set below MIN_DELIBERATION_SECONDS."""
        timer = DeliberationTimer(min_seconds=min_seconds)
        
        # Property: minimum is always >= MIN_DELIBERATION_SECONDS
        assert timer.min_deliberation_seconds >= MIN_DELIBERATION_SECONDS
    
    @given(decision_id=st.text(min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_early_end_always_raises(self, decision_id):
        """Ending deliberation early always raises DeliberationTimeViolation."""
        timer = DeliberationTimer()
        timer.start_deliberation(decision_id)
        
        # Property: ending immediately always raises
        with pytest.raises(DeliberationTimeViolation):
            timer.end_deliberation(decision_id)


# =============================================================================
# Property 2: Forced Edit Required
# =============================================================================

class TestForcedEditProperty:
    """Property 2: Forced edit is always required."""
    
    @given(
        decision_id=st.text(min_size=1, max_size=50),
        content=st.text(min_size=1, max_size=1000),
    )
    @settings(max_examples=100)
    def test_identical_content_always_rejected(self, decision_id, content):
        """Identical content is always rejected."""
        checker = ForcedEditChecker()
        checker.register_content(decision_id, content)
        
        # Property: identical content always raises
        with pytest.raises(ForcedEditViolation):
            checker.require_edit(decision_id, content)
    
    @given(
        decision_id=st.text(min_size=1, max_size=50),
        content=st.text(min_size=1, max_size=100),
        whitespace=st.text(alphabet=" \t\n\r", min_size=1, max_size=10),
    )
    @settings(max_examples=100)
    def test_whitespace_only_always_rejected(self, decision_id, content, whitespace):
        """Whitespace-only changes are always rejected."""
        assume(content.strip())  # Ensure content has non-whitespace
        
        checker = ForcedEditChecker()
        checker.register_content(decision_id, content)
        
        # Property: adding whitespace always raises
        with pytest.raises(ForcedEditViolation):
            checker.require_edit(decision_id, content + whitespace)


# =============================================================================
# Property 3: Challenge Must Be Answered
# =============================================================================

class TestChallengeProperty:
    """Property 3: Challenge must be answered with meaningful content."""
    
    @given(
        decision_id=st.text(min_size=1, max_size=50),
        empty_answer=st.text(alphabet=" \t\n\r", max_size=20),
    )
    @settings(max_examples=100)
    def test_empty_answer_always_rejected(self, decision_id, empty_answer):
        """Empty or whitespace answers are always rejected."""
        generator = ChallengeQuestionGenerator()
        validator = ChallengeAnswerValidator()
        
        challenge = generator.generate_challenge(decision_id, {"type": "test"})
        
        # Property: empty/whitespace answers always raise
        with pytest.raises(ChallengeNotAnswered):
            validator.validate_answer(challenge, empty_answer)
    
    @given(
        decision_id=st.text(min_size=1, max_size=50),
        short_answer=st.text(min_size=1, max_size=9),  # Less than MIN_ANSWER_LENGTH
    )
    @settings(max_examples=100)
    def test_short_answer_always_rejected(self, decision_id, short_answer):
        """Short answers are always rejected."""
        assume(short_answer.strip())  # Ensure not just whitespace
        
        generator = ChallengeQuestionGenerator()
        validator = ChallengeAnswerValidator()
        
        challenge = generator.generate_challenge(decision_id, {"type": "test"})
        
        # Property: short answers always raise
        with pytest.raises(ChallengeNotAnswered):
            validator.validate_answer(challenge, short_answer)


# =============================================================================
# Property 4: Rubber-Stamp Detection Advisory Only
# =============================================================================

class TestRubberStampProperty:
    """Property 4: Rubber-stamp warnings are always advisory only."""
    
    @given(
        reviewer_id=st.text(min_size=1, max_size=50),
        decision_count=st.integers(min_value=0, max_value=100),
    )
    @settings(max_examples=100)
    def test_warnings_never_block(self, reviewer_id, decision_count):
        """Warnings never have blocking capability."""
        detector = RubberStampDetector()
        
        # Record some decisions
        for i in range(decision_count):
            detector.record_confirmation(reviewer_id, f"decision-{i}", 5.0)
        
        warning = detector.analyze_pattern(reviewer_id)
        
        # Property: warning never has blocking methods
        assert not hasattr(warning, "block")
        assert not hasattr(warning, "reject")
        assert not hasattr(warning, "prevent")
    
    @given(
        reviewer_id=st.text(min_size=1, max_size=50),
        decision_count=st.integers(min_value=0, max_value=MIN_DECISIONS_FOR_ANALYSIS - 1),
    )
    @settings(max_examples=100)
    def test_cold_start_always_silent(self, reviewer_id, decision_count):
        """Cold-start reviewers always get silent warnings."""
        detector = RubberStampDetector()
        
        for i in range(decision_count):
            detector.record_confirmation(reviewer_id, f"decision-{i}", 5.0)
        
        warning = detector.analyze_pattern(reviewer_id)
        
        # Property: cold-start is always advisory silent
        assert warning.is_cold_start is True
        assert warning.is_advisory_silent is True


# =============================================================================
# Property 5: Cooldown Enforced
# =============================================================================

class TestCooldownProperty:
    """Property 5: Cooldown time is always >= MIN_COOLDOWN_SECONDS."""
    
    @given(
        decision_id=st.text(min_size=1, max_size=50),
        min_seconds=st.floats(min_value=0.0, max_value=10.0),
    )
    @settings(max_examples=100)
    def test_cooldown_minimum_enforced(self, decision_id, min_seconds):
        """Cooldown time cannot be set below MIN_COOLDOWN_SECONDS."""
        enforcer = CooldownEnforcer(min_seconds=min_seconds)
        
        # Property: minimum is always >= MIN_COOLDOWN_SECONDS
        assert enforcer.min_cooldown_seconds >= MIN_COOLDOWN_SECONDS
    
    @given(decision_id=st.text(min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_early_end_always_raises(self, decision_id):
        """Ending cooldown early always raises CooldownViolation."""
        enforcer = CooldownEnforcer()
        enforcer.start_cooldown(decision_id)
        
        # Property: ending immediately always raises
        with pytest.raises(CooldownViolation):
            enforcer.end_cooldown(decision_id)


# =============================================================================
# Property 6: Audit Trail Complete
# =============================================================================

class TestAuditCompletenessProperty:
    """Property 6: Audit trail must be complete."""
    
    @given(
        decision_id=st.text(min_size=1, max_size=50),
        items=st.lists(
            st.sampled_from(["deliberation", "edit", "challenge", "cooldown"]),
            max_size=3,
            unique=True,
        ),
    )
    @settings(max_examples=100)
    def test_incomplete_audit_always_raises(self, decision_id, items):
        """Incomplete audit always raises AuditIncomplete."""
        assume(len(items) < 4)  # Ensure not all items
        
        checker = AuditCompletenessChecker()
        checker.initialize_audit(decision_id)
        
        for item in items:
            checker.record_item(decision_id, item)
        
        # Property: incomplete audit always raises
        from governance_friction.errors import AuditIncomplete
        with pytest.raises(AuditIncomplete):
            checker.require_completeness(decision_id)


# =============================================================================
# Property 7: Read-Only Phase Access
# =============================================================================

class TestReadOnlyProperty:
    """Property 7: Phase-6 through Phase-9 are read-only."""
    
    @given(
        phase=st.sampled_from([
            "phase-6", "phase-7", "phase-8", "phase-9",
            "decision_workflow", "submission_workflow",
            "intelligence_layer", "browser_assistant",
        ]),
        write_op=st.sampled_from([
            "write", "update", "delete", "insert", "modify",
            "create", "set", "put", "post", "patch", "remove",
        ]),
    )
    @settings(max_examples=100)
    def test_write_to_readonly_always_raises(self, phase, write_op):
        """Write to read-only phase always raises."""
        from governance_friction.errors import ReadOnlyViolation
        
        with pytest.raises(ReadOnlyViolation):
            Phase10BoundaryGuard.check_write_attempt(phase, write_op)


# =============================================================================
# Property 8: Network Execution Prohibition
# =============================================================================

class TestNetworkProhibitionProperty:
    """Property 8: Network execution is always prohibited."""
    
    @given(
        module=st.sampled_from([
            "httpx", "requests", "aiohttp", "socket",
            "urllib.request", "urllib3", "http.client",
        ]),
    )
    @settings(max_examples=100)
    def test_network_import_always_raises(self, module):
        """Network module import always raises."""
        from governance_friction.errors import NetworkExecutionAttempt
        
        with pytest.raises(NetworkExecutionAttempt):
            Phase10BoundaryGuard.check_import(module)


# =============================================================================
# Property 9: Automation Prohibition
# =============================================================================

class TestAutomationProhibitionProperty:
    """Property 9: Automation is always prohibited."""
    
    @given(
        action=st.sampled_from([
            "auto_approve", "auto_submit", "auto_confirm",
            "infer_decision", "suggest_decision", "recommend_action",
            "classify_bug", "assign_severity", "execute_action",
        ]),
    )
    @settings(max_examples=100)
    def test_automation_action_always_raises(self, action):
        """Automation action always raises."""
        from governance_friction.errors import AutomationAttempt
        
        with pytest.raises(AutomationAttempt):
            Phase10BoundaryGuard.check_forbidden_action(action)
    
    @given(
        action=st.sampled_from([
            "bypass_deliberation", "bypass_edit", "bypass_challenge",
            "bypass_cooldown", "bypass_audit", "bypass_friction",
            "disable_friction", "reduce_friction", "skip_friction",
        ]),
    )
    @settings(max_examples=100)
    def test_bypass_action_always_raises(self, action):
        """Bypass action always raises."""
        from governance_friction.errors import FrictionBypassAttempt
        
        with pytest.raises(FrictionBypassAttempt):
            Phase10BoundaryGuard.check_forbidden_action(action)


# =============================================================================
# Property 10: Immutable Output Models
# =============================================================================

class TestImmutableModelsProperty:
    """Property 10: All output models are immutable."""
    
    @given(decision_id=st.text(min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_deliberation_record_immutable(self, decision_id):
        """DeliberationRecord is always immutable."""
        record = DeliberationRecord(
            decision_id=decision_id,
            start_monotonic=100.0,
        )
        
        with pytest.raises(Exception):  # FrozenInstanceError
            record.decision_id = "modified"
    
    @given(decision_id=st.text(min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_friction_state_immutable(self, decision_id):
        """FrictionState is always immutable."""
        state = FrictionState(decision_id=decision_id)
        
        with pytest.raises(Exception):  # FrozenInstanceError
            state.is_friction_complete = True


# =============================================================================
# Property 11: Friction Always Present
# =============================================================================

class TestFrictionAlwaysPresentProperty:
    """Property 11: Friction mechanisms cannot be bypassed."""
    
    def test_deliberation_timer_no_bypass(self):
        """DeliberationTimer has no bypass methods."""
        timer = DeliberationTimer()
        
        bypass_methods = [
            "bypass", "skip", "disable", "auto_approve",
            "instant", "fast_track", "override",
        ]
        
        for method in bypass_methods:
            assert not hasattr(timer, method)
            assert not hasattr(timer, f"{method}_deliberation")
    
    def test_edit_checker_no_bypass(self):
        """ForcedEditChecker has no bypass methods."""
        checker = ForcedEditChecker()
        
        bypass_methods = [
            "bypass", "skip", "disable", "auto_edit",
            "instant", "fast_track", "override",
        ]
        
        for method in bypass_methods:
            assert not hasattr(checker, method)
            assert not hasattr(checker, f"{method}_edit")
    
    def test_cooldown_enforcer_no_bypass(self):
        """CooldownEnforcer has no bypass methods."""
        enforcer = CooldownEnforcer()
        
        bypass_methods = [
            "bypass", "skip", "disable", "auto_approve",
            "instant", "fast_track", "override",
        ]
        
        for method in bypass_methods:
            assert not hasattr(enforcer, method)
            assert not hasattr(enforcer, f"{method}_cooldown")
