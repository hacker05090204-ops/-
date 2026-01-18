# PHASE-13 GOVERNANCE COMPLIANCE
# Tests for TASK-4.1, 4.2, 4.3: Human Decision Framework
# Requirement: 3.1, 3.2, 3.3 (Human Decision)
#
# MANDATORY DECLARATION:
# Phase-13 must not alter execution authority, human control,
# governance friction, audit invariants, or legal accountability.
#
# CRITICAL GOVERNANCE CLARIFICATION:
# Decision Point tracking is COUNTING ONLY, LOGGING ONLY, VALIDATION ONLY.
# Decision tracking MUST NOT: interpret, score, recommend, infer, store patterns,
# create memory, create heuristics, or adapt behavior.
# A "Decision Point" is a STRUCTURAL EVENT, not a semantic judgment.

"""Tests for human decision framework - governance-enforcing tests."""

import pytest
import tempfile
import time


# =============================================================================
# TASK-4.1: Decision Point Tracking Tests
# =============================================================================

class TestDecisionPointsTracked:
    """Verify decision points counted correctly."""

    def test_decision_point_counter_increments(self):
        """Decision point counter must increment on each decision."""
        from browser_shell.decision import DecisionTracker
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            tracker = DecisionTracker(storage=storage, hash_chain=chain)
            
            # Record decision points
            tracker.record_decision_point(
                session_id="session-001",
                options_presented=["option_a", "option_b"],
                option_selected="option_a",
            )
            
            assert tracker.get_decision_count("session-001") == 1
            
            tracker.record_decision_point(
                session_id="session-001",
                options_presented=["option_c", "option_d"],
                option_selected="option_c",
            )
            
            assert tracker.get_decision_count("session-001") == 2

    def test_decision_count_per_session(self):
        """Decision counts must be tracked per session."""
        from browser_shell.decision import DecisionTracker
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            tracker = DecisionTracker(storage=storage, hash_chain=chain)
            
            tracker.record_decision_point(
                session_id="session-001",
                options_presented=["a", "b"],
                option_selected="a",
            )
            
            tracker.record_decision_point(
                session_id="session-002",
                options_presented=["c", "d"],
                option_selected="c",
            )
            
            assert tracker.get_decision_count("session-001") == 1
            assert tracker.get_decision_count("session-002") == 1


class TestDecisionPointDefinition:
    """Verify only valid decisions counted."""

    def test_decision_requires_multiple_options(self):
        """Decision point requires at least 2 options."""
        from browser_shell.decision import DecisionTracker
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            tracker = DecisionTracker(storage=storage, hash_chain=chain)
            
            # Single option is not a decision
            result = tracker.record_decision_point(
                session_id="session-001",
                options_presented=["only_option"],
                option_selected="only_option",
            )
            
            assert result.valid is False
            assert tracker.get_decision_count("session-001") == 0

    def test_decision_requires_selection(self):
        """Decision point requires a selection from options."""
        from browser_shell.decision import DecisionTracker
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            tracker = DecisionTracker(storage=storage, hash_chain=chain)
            
            # Selection must be from presented options
            result = tracker.record_decision_point(
                session_id="session-001",
                options_presented=["a", "b"],
                option_selected="c",  # Not in options!
            )
            
            assert result.valid is False


class TestDecisionPointLoggedWithOptions:
    """Verify options recorded."""

    def test_decision_logged_to_audit(self):
        """Decision point must be logged to audit trail."""
        from browser_shell.decision import DecisionTracker
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            tracker = DecisionTracker(storage=storage, hash_chain=chain)
            
            tracker.record_decision_point(
                session_id="session-001",
                options_presented=["approve", "reject"],
                option_selected="approve",
            )
            
            entries = storage.read_all()
            action_types = [e.action_type for e in entries]
            
            assert "DECISION_POINT" in action_types


class TestRatioBelow1FlagsReview:
    """Verify low ratio triggers flag."""

    def test_ratio_check_returns_status(self):
        """Ratio check must return status."""
        from browser_shell.decision import DecisionTracker
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            tracker = DecisionTracker(storage=storage, hash_chain=chain)
            
            # Record state changes without decisions
            tracker.record_state_change("session-001")
            tracker.record_state_change("session-001")
            tracker.record_state_change("session-001")
            
            # Only 1 decision for 3 state changes
            tracker.record_decision_point(
                session_id="session-001",
                options_presented=["a", "b"],
                option_selected="a",
            )
            
            ratio_status = tracker.check_decision_ratio("session-001")
            
            # Ratio is 1:3, below 1:1 threshold
            assert ratio_status.ratio < 1.0
            assert ratio_status.flagged is True


class TestRepetitiveChoicesFlagged:
    """Verify >95% same selection triggers review (TH-22)."""

    def test_95_percent_same_option_flagged(self):
        """Same option >95% must be flagged."""
        from browser_shell.decision import DecisionTracker
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            tracker = DecisionTracker(storage=storage, hash_chain=chain)
            
            # Record 20 decisions, 19 same option (95%)
            for i in range(19):
                tracker.record_decision_point(
                    session_id="session-001",
                    options_presented=["approve", "reject"],
                    option_selected="approve",
                )
            
            tracker.record_decision_point(
                session_id="session-001",
                options_presented=["approve", "reject"],
                option_selected="reject",
            )
            
            repetition_status = tracker.check_repetition("session-001")
            
            assert repetition_status.flagged is True


# =============================================================================
# TASK-4.2: Confirmation System Tests
# =============================================================================

class TestConfirmationRequiredForSignificantActions:
    """Verify required actions need confirmation."""

    def test_confirmation_required_for_scope_boundary(self):
        """Scope boundary actions require confirmation."""
        from browser_shell.decision import ConfirmationSystem
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            system = ConfirmationSystem(storage=storage, hash_chain=chain)
            
            assert system.requires_confirmation("SCOPE_BOUNDARY") is True

    def test_confirmation_required_for_evidence_capture(self):
        """Evidence capture requires confirmation."""
        from browser_shell.decision import ConfirmationSystem
        
        with tempfile.TemporaryDirectory() as tmpdir:
            from browser_shell.audit_storage import AuditStorage
            from browser_shell.hash_chain import HashChain
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            system = ConfirmationSystem(storage=storage, hash_chain=chain)
            
            assert system.requires_confirmation("EVIDENCE_CAPTURE") is True

    def test_confirmation_required_for_report_ops(self):
        """Report operations require confirmation."""
        from browser_shell.decision import ConfirmationSystem
        
        with tempfile.TemporaryDirectory() as tmpdir:
            from browser_shell.audit_storage import AuditStorage
            from browser_shell.hash_chain import HashChain
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            system = ConfirmationSystem(storage=storage, hash_chain=chain)
            
            assert system.requires_confirmation("REPORT_OPERATION") is True


class TestConfirmationNotRequiredForRoutine:
    """Verify routine navigation exempt."""

    def test_routine_navigation_no_confirmation(self):
        """Routine in-scope navigation does not require confirmation."""
        from browser_shell.decision import ConfirmationSystem
        
        with tempfile.TemporaryDirectory() as tmpdir:
            from browser_shell.audit_storage import AuditStorage
            from browser_shell.hash_chain import HashChain
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            system = ConfirmationSystem(storage=storage, hash_chain=chain)
            
            assert system.requires_confirmation("ROUTINE_NAVIGATION") is False


class TestConfirmationFrequencyLimit:
    """Verify max 1 per 30 sec average (TH-04)."""

    def test_frequency_limit_constant(self):
        """Confirmation frequency limit must be defined."""
        from browser_shell.decision import ConfirmationSystem
        
        assert hasattr(ConfirmationSystem, 'MAX_CONFIRMATIONS_PER_WINDOW')
        assert hasattr(ConfirmationSystem, 'WINDOW_SECONDS')
        
        # TH-04: 1 per 30 seconds average over 5-minute window
        # 5 minutes = 300 seconds, 1 per 30 sec = 10 confirmations max
        assert ConfirmationSystem.WINDOW_SECONDS == 300
        assert ConfirmationSystem.MAX_CONFIRMATIONS_PER_WINDOW == 10


class TestConfirmationRequiresVariableInput:
    """Verify not just 'OK' button."""

    def test_confirmation_requires_input_value(self):
        """Confirmation must include variable input."""
        from browser_shell.decision import ConfirmationSystem
        
        with tempfile.TemporaryDirectory() as tmpdir:
            from browser_shell.audit_storage import AuditStorage
            from browser_shell.hash_chain import HashChain
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            system = ConfirmationSystem(storage=storage, hash_chain=chain)
            
            # Empty input should be rejected
            result = system.record_confirmation(
                session_id="session-001",
                action_type="EVIDENCE_CAPTURE",
                confirmation_input="",
            )
            
            assert result.valid is False


class TestFastResponseFlagged:
    """Verify <1 sec responses flagged (TH-05)."""

    def test_fast_response_flagged(self):
        """Response time <1 second must be flagged."""
        from browser_shell.decision import ConfirmationSystem
        
        with tempfile.TemporaryDirectory() as tmpdir:
            from browser_shell.audit_storage import AuditStorage
            from browser_shell.hash_chain import HashChain
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            system = ConfirmationSystem(storage=storage, hash_chain=chain)
            
            # Record confirmation with fast response time
            result = system.record_confirmation(
                session_id="session-001",
                action_type="EVIDENCE_CAPTURE",
                confirmation_input="confirmed",
                response_time_seconds=0.5,  # Less than 1 second
            )
            
            assert result.flagged_rubber_stamp is True


class TestFrequencyExceededPauses:
    """Verify pause on frequency violation."""

    def test_frequency_exceeded_triggers_pause(self):
        """Exceeding frequency limit must trigger pause."""
        from browser_shell.decision import ConfirmationSystem
        
        with tempfile.TemporaryDirectory() as tmpdir:
            from browser_shell.audit_storage import AuditStorage
            from browser_shell.hash_chain import HashChain
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            system = ConfirmationSystem(storage=storage, hash_chain=chain)
            
            # Record many confirmations quickly
            for i in range(15):  # More than 10 in window
                system.record_confirmation(
                    session_id="session-001",
                    action_type="EVIDENCE_CAPTURE",
                    confirmation_input=f"confirmed-{i}",
                    response_time_seconds=2.0,
                )
            
            status = system.check_frequency_status("session-001")
            
            assert status.paused is True


# =============================================================================
# TASK-4.3: Attribution System Tests
# =============================================================================

class TestAllEntriesHaveInitiator:
    """Verify every audit entry has initiator."""

    def test_decision_entry_has_initiator(self):
        """Decision audit entry must have initiator field."""
        from browser_shell.decision import DecisionTracker
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            tracker = DecisionTracker(storage=storage, hash_chain=chain)
            
            tracker.record_decision_point(
                session_id="session-001",
                options_presented=["a", "b"],
                option_selected="a",
            )
            
            entries = storage.read_all()
            
            for entry in entries:
                assert entry.initiator in ["HUMAN", "SYSTEM"]


class TestHumanActionsAttributedHuman:
    """Verify human actions correctly attributed."""

    def test_decision_attributed_to_human(self):
        """Decision points must be attributed to HUMAN."""
        from browser_shell.decision import DecisionTracker
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            tracker = DecisionTracker(storage=storage, hash_chain=chain)
            
            tracker.record_decision_point(
                session_id="session-001",
                options_presented=["a", "b"],
                option_selected="a",
            )
            
            entries = storage.read_all()
            decision_entries = [e for e in entries if e.action_type == "DECISION_POINT"]
            
            for entry in decision_entries:
                assert entry.initiator == "HUMAN"


class TestSystemActionsAttributedSystem:
    """Verify system actions correctly attributed."""

    def test_validation_attributed_to_system(self):
        """Validation actions must be attributed to SYSTEM."""
        from browser_shell.decision import DecisionTracker
        from browser_shell.audit_storage import AuditStorage
        from browser_shell.hash_chain import HashChain
        
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = AuditStorage(storage_path=tmpdir)
            chain = HashChain()
            tracker = DecisionTracker(storage=storage, hash_chain=chain)
            
            # Record state change (system action)
            tracker.record_state_change("session-001")
            
            entries = storage.read_all()
            
            # State change logging is a system action
            for entry in entries:
                if "state" in entry.action_details.lower():
                    assert entry.initiator == "SYSTEM"


class TestNoActionWithoutAttribution:
    """Verify unattributed actions blocked."""

    def test_attribution_is_required(self):
        """Actions without attribution must be blocked."""
        from browser_shell.decision import AttributionValidator
        
        validator = AttributionValidator()
        
        # Attempt to validate action without initiator
        result = validator.validate_attribution(
            action_type="DECISION_POINT",
            initiator=None,
        )
        
        assert result.valid is False
        assert "attribution" in result.error_message.lower()


class TestAmbiguousAttributionBlocks:
    """Verify ambiguous cases blocked."""

    def test_invalid_initiator_blocked(self):
        """Invalid initiator value must be blocked."""
        from browser_shell.decision import AttributionValidator
        
        validator = AttributionValidator()
        
        result = validator.validate_attribution(
            action_type="DECISION_POINT",
            initiator="UNKNOWN",  # Invalid!
        )
        
        assert result.valid is False


# =============================================================================
# Forbidden Capability Tests
# =============================================================================

class TestNoAutomationInDecision:
    """Verify no automation methods in decision module."""

    def test_no_auto_methods(self):
        """No auto_* methods allowed."""
        from browser_shell.decision import DecisionTracker
        
        methods = [m for m in dir(DecisionTracker) if m.startswith('auto')]
        assert methods == [], f"Forbidden auto methods found: {methods}"

    def test_no_interpret_methods(self):
        """No interpret_* methods allowed."""
        from browser_shell.decision import DecisionTracker
        
        methods = [m for m in dir(DecisionTracker) if m.startswith('interpret')]
        assert methods == [], f"Forbidden interpret methods found: {methods}"

    def test_no_score_methods(self):
        """No score_* methods allowed."""
        from browser_shell.decision import DecisionTracker
        
        methods = [m for m in dir(DecisionTracker) if m.startswith('score')]
        assert methods == [], f"Forbidden score methods found: {methods}"

    def test_no_recommend_methods(self):
        """No recommend_* methods allowed."""
        from browser_shell.decision import DecisionTracker
        
        methods = [m for m in dir(DecisionTracker) if m.startswith('recommend')]
        assert methods == [], f"Forbidden recommend methods found: {methods}"

    def test_no_learn_methods(self):
        """No learn_* methods allowed."""
        from browser_shell.decision import DecisionTracker
        
        methods = [m for m in dir(DecisionTracker) if m.startswith('learn')]
        assert methods == [], f"Forbidden learn methods found: {methods}"

    def test_no_pattern_methods(self):
        """No pattern_* methods allowed."""
        from browser_shell.decision import DecisionTracker
        
        methods = [m for m in dir(DecisionTracker) if m.startswith('pattern')]
        assert methods == [], f"Forbidden pattern methods found: {methods}"

    def test_no_heuristic_methods(self):
        """No heuristic_* methods allowed."""
        from browser_shell.decision import DecisionTracker
        
        methods = [m for m in dir(DecisionTracker) if m.startswith('heuristic')]
        assert methods == [], f"Forbidden heuristic methods found: {methods}"

    def test_no_infer_methods(self):
        """No infer_* methods allowed."""
        from browser_shell.decision import DecisionTracker
        
        methods = [m for m in dir(DecisionTracker) if m.startswith('infer')]
        assert methods == [], f"Forbidden infer methods found: {methods}"
