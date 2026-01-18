"""
Tests for Phase-10 audit logger and completeness checker.

Validates:
- Audit entries are append-only
- Hash chain provides tamper detection
- Completeness is enforced
"""

import pytest

from governance_friction.audit import FrictionAuditLogger
from governance_friction.audit_completeness import AuditCompletenessChecker
from governance_friction.types import FrictionAction
from governance_friction.errors import AuditIncomplete


class TestFrictionAuditLogger:
    """Test friction audit logger functionality."""
    
    def test_log_action(self, decision_id):
        """log_action should create an audit entry."""
        logger = FrictionAuditLogger()
        
        entry = logger.log_action(
            FrictionAction.DELIBERATION_START,
            decision_id,
            {"test": "value"},
        )
        
        assert entry.decision_id == decision_id
        assert entry.action == FrictionAction.DELIBERATION_START
        assert entry.entry_id is not None
        assert entry.entry_hash is not None
    
    def test_entries_are_append_only(self, decision_id):
        """Entries should be append-only."""
        logger = FrictionAuditLogger()
        
        logger.log_action(FrictionAction.DELIBERATION_START, decision_id)
        logger.log_action(FrictionAction.DELIBERATION_END, decision_id)
        
        entries = logger.get_all_entries()
        
        assert len(entries) == 2
        assert entries[0].action == FrictionAction.DELIBERATION_START
        assert entries[1].action == FrictionAction.DELIBERATION_END
    
    def test_hash_chain_valid(self, decision_id):
        """Hash chain should be valid."""
        logger = FrictionAuditLogger()
        
        logger.log_action(FrictionAction.DELIBERATION_START, decision_id)
        logger.log_action(FrictionAction.EDIT_REQUIRED, decision_id)
        logger.log_action(FrictionAction.CHALLENGE_PRESENTED, decision_id)
        
        assert logger.verify_chain() is True
    
    def test_hash_chain_links_entries(self, decision_id):
        """Each entry should link to previous via hash."""
        logger = FrictionAuditLogger()
        
        entry1 = logger.log_action(FrictionAction.DELIBERATION_START, decision_id)
        entry2 = logger.log_action(FrictionAction.DELIBERATION_END, decision_id)
        
        assert entry2.previous_hash == entry1.entry_hash
    
    def test_get_entries_by_decision(self, decision_id):
        """get_entries should return entries for specific decision."""
        logger = FrictionAuditLogger()
        
        logger.log_action(FrictionAction.DELIBERATION_START, decision_id)
        logger.log_action(FrictionAction.DELIBERATION_START, "other-decision")
        logger.log_action(FrictionAction.DELIBERATION_END, decision_id)
        
        entries = logger.get_entries(decision_id)
        
        assert len(entries) == 2
        assert all(e.decision_id == decision_id for e in entries)
    
    def test_entry_count(self, decision_id):
        """get_entry_count should return total entries."""
        logger = FrictionAuditLogger()
        
        logger.log_action(FrictionAction.DELIBERATION_START, decision_id)
        logger.log_action(FrictionAction.DELIBERATION_END, decision_id)
        
        assert logger.get_entry_count() == 2
    
    def test_decision_count(self, decision_id):
        """get_decision_count should return unique decisions."""
        logger = FrictionAuditLogger()
        
        logger.log_action(FrictionAction.DELIBERATION_START, decision_id)
        logger.log_action(FrictionAction.DELIBERATION_START, "other-decision")
        logger.log_action(FrictionAction.DELIBERATION_END, decision_id)
        
        assert logger.get_decision_count() == 2


class TestAuditCompletenessChecker:
    """Test audit completeness checker functionality."""
    
    def test_initialize_audit(self, decision_id):
        """initialize_audit should create empty audit state."""
        checker = AuditCompletenessChecker()
        checker.initialize_audit(decision_id)
        
        completeness = checker.check_completeness(decision_id)
        
        assert completeness.has_deliberation is False
        assert completeness.has_edit is False
        assert completeness.has_challenge is False
        assert completeness.has_cooldown is False
    
    def test_record_item(self, decision_id):
        """record_item should mark item as complete."""
        checker = AuditCompletenessChecker()
        checker.initialize_audit(decision_id)
        
        checker.record_item(decision_id, "deliberation")
        
        completeness = checker.check_completeness(decision_id)
        assert completeness.has_deliberation is True
    
    def test_incomplete_audit_raises(self, decision_id):
        """require_completeness should raise if incomplete."""
        checker = AuditCompletenessChecker()
        checker.initialize_audit(decision_id)
        
        # Only record some items
        checker.record_item(decision_id, "deliberation")
        checker.record_item(decision_id, "edit")
        
        with pytest.raises(AuditIncomplete) as exc_info:
            checker.require_completeness(decision_id)
        
        assert exc_info.value.decision_id == decision_id
        assert "challenge" in exc_info.value.missing_items
        assert "cooldown" in exc_info.value.missing_items
    
    def test_complete_audit_succeeds(self, decision_id):
        """require_completeness should succeed if complete."""
        checker = AuditCompletenessChecker()
        checker.initialize_audit(decision_id)
        
        checker.record_item(decision_id, "deliberation")
        checker.record_item(decision_id, "edit")
        checker.record_item(decision_id, "challenge")
        checker.record_item(decision_id, "cooldown")
        
        completeness = checker.require_completeness(decision_id)
        
        assert completeness.is_complete is True
    
    def test_get_missing_items(self, decision_id):
        """get_missing_items should return list of missing items."""
        checker = AuditCompletenessChecker()
        checker.initialize_audit(decision_id)
        
        checker.record_item(decision_id, "deliberation")
        
        missing = checker.get_missing_items(decision_id)
        
        assert "edit" in missing
        assert "challenge" in missing
        assert "cooldown" in missing
        assert "deliberation" not in missing
    
    def test_is_complete(self, decision_id):
        """is_complete should return boolean."""
        checker = AuditCompletenessChecker()
        checker.initialize_audit(decision_id)
        
        assert checker.is_complete(decision_id) is False
        
        checker.record_item(decision_id, "deliberation")
        checker.record_item(decision_id, "edit")
        checker.record_item(decision_id, "challenge")
        checker.record_item(decision_id, "cooldown")
        
        assert checker.is_complete(decision_id) is True
    
    def test_clear_audit(self, decision_id):
        """clear_audit should remove audit state."""
        checker = AuditCompletenessChecker()
        checker.initialize_audit(decision_id)
        checker.record_item(decision_id, "deliberation")
        
        checker.clear_audit(decision_id)
        
        # Should be back to default (all False)
        completeness = checker.check_completeness(decision_id)
        assert completeness.has_deliberation is False


class TestAuditNoAutoPopulate:
    """Test that no auto-populate capability exists."""
    
    def test_no_auto_populate_method(self):
        """AuditCompletenessChecker should not have auto_populate method."""
        checker = AuditCompletenessChecker()
        
        assert not hasattr(checker, "auto_populate")
        assert not hasattr(checker, "fill_missing")
        assert not hasattr(checker, "bypass_audit")
        assert not hasattr(checker, "skip_validation")
