"""
Tests for Phase-10 type definitions.

Validates:
- All dataclasses are frozen (immutable)
- Constants have correct values
- Enums are properly defined
"""

import pytest
from dataclasses import FrozenInstanceError

from governance_friction.types import (
    DeliberationRecord,
    ChallengeQuestion,
    RubberStampWarning,
    CooldownState,
    AuditCompleteness,
    FrictionState,
    AuditEntry,
    FrictionAction,
    WarningLevel,
    MIN_DELIBERATION_SECONDS,
    MIN_COOLDOWN_SECONDS,
    MIN_DECISIONS_FOR_ANALYSIS,
)


class TestConstants:
    """Test constant values."""
    
    def test_min_deliberation_seconds(self):
        """MIN_DELIBERATION_SECONDS must be at least 5."""
        assert MIN_DELIBERATION_SECONDS >= 5.0
    
    def test_min_cooldown_seconds(self):
        """MIN_COOLDOWN_SECONDS must be at least 3."""
        assert MIN_COOLDOWN_SECONDS >= 3.0
    
    def test_min_decisions_for_analysis(self):
        """MIN_DECISIONS_FOR_ANALYSIS must be positive."""
        assert MIN_DECISIONS_FOR_ANALYSIS > 0


class TestFrozenDataclasses:
    """Test that all dataclasses are frozen (immutable)."""
    
    def test_deliberation_record_frozen(self):
        """DeliberationRecord must be frozen."""
        record = DeliberationRecord(
            decision_id="test",
            start_monotonic=100.0,
        )
        with pytest.raises(FrozenInstanceError):
            record.decision_id = "modified"
    
    def test_challenge_question_frozen(self):
        """ChallengeQuestion must be frozen."""
        question = ChallengeQuestion(
            question_id="q1",
            decision_id="test",
            question_text="What is the vulnerability?",
            context_summary="Test context",
            expected_answer_type="explanation",
        )
        with pytest.raises(FrozenInstanceError):
            question.question_text = "modified"
    
    def test_rubber_stamp_warning_frozen(self):
        """RubberStampWarning must be frozen."""
        warning = RubberStampWarning(
            reviewer_id="reviewer1",
            warning_level=WarningLevel.NONE,
            reason="No issues",
            decision_count=10,
            approval_rate=0.8,
            average_deliberation_seconds=10.0,
            is_cold_start=False,
        )
        with pytest.raises(FrozenInstanceError):
            warning.warning_level = WarningLevel.HIGH
    
    def test_cooldown_state_frozen(self):
        """CooldownState must be frozen."""
        state = CooldownState(
            decision_id="test",
            start_monotonic=100.0,
            duration_seconds=3.0,
        )
        with pytest.raises(FrozenInstanceError):
            state.duration_seconds = 0.0
    
    def test_audit_completeness_frozen(self):
        """AuditCompleteness must be frozen."""
        completeness = AuditCompleteness(
            decision_id="test",
            has_deliberation=True,
        )
        with pytest.raises(FrozenInstanceError):
            completeness.has_deliberation = False
    
    def test_friction_state_frozen(self):
        """FrictionState must be frozen."""
        state = FrictionState(decision_id="test")
        with pytest.raises(FrozenInstanceError):
            state.is_friction_complete = True
    
    def test_audit_entry_frozen(self):
        """AuditEntry must be frozen."""
        entry = AuditEntry(
            entry_id="e1",
            decision_id="test",
            action=FrictionAction.DELIBERATION_START,
            timestamp_monotonic=100.0,
        )
        with pytest.raises(FrozenInstanceError):
            entry.action = FrictionAction.DELIBERATION_END


class TestDeliberationRecord:
    """Test DeliberationRecord functionality."""
    
    def test_with_end_creates_new_record(self):
        """with_end should create a new record, not modify existing."""
        record = DeliberationRecord(
            decision_id="test",
            start_monotonic=100.0,
        )
        completed = record.with_end(106.0)
        
        # Original unchanged
        assert record.end_monotonic is None
        assert record.elapsed_seconds == 0.0
        assert record.is_complete is False
        
        # New record has end time
        assert completed.end_monotonic == 106.0
        assert completed.elapsed_seconds == 6.0
        assert completed.is_complete is True
    
    def test_is_complete_requires_min_time(self):
        """is_complete should be False if elapsed < MIN_DELIBERATION_SECONDS."""
        record = DeliberationRecord(
            decision_id="test",
            start_monotonic=100.0,
        )
        # 4 seconds - not enough
        incomplete = record.with_end(104.0)
        assert incomplete.is_complete is False
        
        # 5 seconds - exactly enough
        complete = record.with_end(105.0)
        assert complete.is_complete is True


class TestChallengeQuestion:
    """Test ChallengeQuestion functionality."""
    
    def test_with_answer_creates_new_question(self):
        """with_answer should create a new question, not modify existing."""
        question = ChallengeQuestion(
            question_id="q1",
            decision_id="test",
            question_text="What is the vulnerability?",
            context_summary="Test context",
            expected_answer_type="explanation",
        )
        answered = question.with_answer("SQL Injection")
        
        # Original unchanged
        assert question.answer is None
        assert question.is_answered is False
        
        # New question has answer
        assert answered.answer == "SQL Injection"
        assert answered.is_answered is True
    
    def test_empty_answer_not_answered(self):
        """Empty or whitespace answers should not be considered answered."""
        question = ChallengeQuestion(
            question_id="q1",
            decision_id="test",
            question_text="What is the vulnerability?",
            context_summary="Test context",
            expected_answer_type="explanation",
        )
        
        empty = question.with_answer("")
        assert empty.is_answered is False
        
        whitespace = question.with_answer("   ")
        assert whitespace.is_answered is False


class TestRubberStampWarning:
    """Test RubberStampWarning functionality."""
    
    def test_advisory_silent_for_cold_start(self):
        """Cold-start warnings should be advisory silent."""
        warning = RubberStampWarning(
            reviewer_id="reviewer1",
            warning_level=WarningLevel.HIGH,  # Even HIGH
            reason="Test",
            decision_count=2,
            approval_rate=1.0,
            average_deliberation_seconds=5.0,
            is_cold_start=True,
        )
        assert warning.is_advisory_silent is True
    
    def test_advisory_silent_for_none_level(self):
        """NONE warning level should be advisory silent."""
        warning = RubberStampWarning(
            reviewer_id="reviewer1",
            warning_level=WarningLevel.NONE,
            reason="No issues",
            decision_count=10,
            approval_rate=0.8,
            average_deliberation_seconds=10.0,
            is_cold_start=False,
        )
        assert warning.is_advisory_silent is True
    
    def test_not_advisory_silent_for_real_warning(self):
        """Real warnings should not be advisory silent."""
        warning = RubberStampWarning(
            reviewer_id="reviewer1",
            warning_level=WarningLevel.MEDIUM,
            reason="Rapid succession detected",
            decision_count=10,
            approval_rate=1.0,
            average_deliberation_seconds=5.0,
            is_cold_start=False,
        )
        assert warning.is_advisory_silent is False


class TestAuditCompleteness:
    """Test AuditCompleteness functionality."""
    
    def test_is_complete_requires_all_items(self):
        """is_complete should require all items."""
        # Missing items
        incomplete = AuditCompleteness(
            decision_id="test",
            has_deliberation=True,
            has_edit=True,
            has_challenge=True,
            has_cooldown=False,
        )
        assert incomplete.is_complete is False
        
        # All items
        complete = AuditCompleteness(
            decision_id="test",
            has_deliberation=True,
            has_edit=True,
            has_challenge=True,
            has_cooldown=True,
        )
        assert complete.is_complete is True


class TestFrictionState:
    """Test FrictionState functionality."""
    
    def test_can_proceed_requires_all_conditions(self):
        """can_proceed should require all friction conditions met."""
        # Incomplete state
        incomplete = FrictionState(decision_id="test")
        assert incomplete.can_proceed is False
        
        # Complete state
        complete = FrictionState(
            decision_id="test",
            deliberation=DeliberationRecord(
                decision_id="test",
                start_monotonic=100.0,
                end_monotonic=106.0,
                elapsed_seconds=6.0,
                is_complete=True,
            ),
            edit_verified=True,
            challenge=ChallengeQuestion(
                question_id="q1",
                decision_id="test",
                question_text="Test?",
                context_summary="Test",
                expected_answer_type="explanation",
                answer="Answer",
                is_answered=True,
            ),
            cooldown=CooldownState(
                decision_id="test",
                start_monotonic=106.0,
                duration_seconds=3.0,
                end_monotonic=109.0,
                is_complete=True,
            ),
            audit_completeness=AuditCompleteness(
                decision_id="test",
                has_deliberation=True,
                has_edit=True,
                has_challenge=True,
                has_cooldown=True,
            ),
            is_friction_complete=True,
        )
        assert complete.can_proceed is True
