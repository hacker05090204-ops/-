"""
Test Execution Layer Audit Log

Tests for hash-chained immutable audit trail.
"""

import pytest
from datetime import datetime, timezone

from execution_layer.types import SafeActionType, SafeAction, ExecutionToken
from execution_layer.audit import ExecutionAuditLog
from execution_layer.errors import AuditIntegrityError


class TestExecutionAuditLog:
    """Test ExecutionAuditLog class."""
    
    @pytest.fixture
    def audit_log(self):
        return ExecutionAuditLog()
    
    @pytest.fixture
    def action(self):
        return SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://example.com",
            parameters={},
            description="Test",
        )
    
    @pytest.fixture
    def token(self, action):
        return ExecutionToken.generate(
            approver_id="human-1",
            action=action,
        )
    
    def test_record_action(self, audit_log, action, token):
        """Should record action in audit log."""
        record = audit_log.record(
            action=action,
            actor="human-1",
            outcome="success",
            token=token,
        )
        assert record.record_id
        assert record.action == action
        assert record.actor == "human-1"
        assert record.outcome == "success"
    
    def test_hash_chain(self, audit_log, action, token):
        """Should maintain hash chain."""
        # First record
        record1 = audit_log.record(
            action=action,
            actor="human-1",
            outcome="success",
            token=token,
        )
        assert record1.previous_hash == ExecutionAuditLog.GENESIS_HASH
        
        # Second record
        action2 = SafeAction(
            action_id="test-2",
            action_type=SafeActionType.CLICK,
            target="#button",
            parameters={},
            description="Click",
        )
        token2 = ExecutionToken.generate(approver_id="human-1", action=action2)
        record2 = audit_log.record(
            action=action2,
            actor="human-1",
            outcome="success",
            token=token2,
        )
        assert record2.previous_hash == record1.record_hash
    
    def test_verify_chain_empty(self, audit_log):
        """Should verify empty chain."""
        assert audit_log.verify_chain() is True
    
    def test_verify_chain_valid(self, audit_log, action, token):
        """Should verify valid chain."""
        audit_log.record(action=action, actor="human-1", outcome="success", token=token)
        
        action2 = SafeAction(
            action_id="test-2",
            action_type=SafeActionType.CLICK,
            target="#button",
            parameters={},
            description="Click",
        )
        token2 = ExecutionToken.generate(approver_id="human-1", action=action2)
        audit_log.record(action=action2, actor="human-1", outcome="success", token=token2)
        
        assert audit_log.verify_chain() is True
    
    def test_record_count(self, audit_log, action, token):
        """Should track record count."""
        assert audit_log.record_count == 0
        
        audit_log.record(action=action, actor="human-1", outcome="success", token=token)
        assert audit_log.record_count == 1
    
    def test_get_records_for_execution(self, audit_log, action, token):
        """Should retrieve records by execution_id."""
        audit_log.record(
            action=action,
            actor="human-1",
            outcome="success",
            token=token,
            execution_id="exec-1",
        )
        
        records = audit_log.get_records_for_execution("exec-1")
        assert len(records) == 1
        assert records[0].action == action
    
    def test_get_records_by_actor(self, audit_log, action, token):
        """Should retrieve records by actor."""
        audit_log.record(action=action, actor="human-1", outcome="success", token=token)
        
        records = audit_log.get_records_by_actor("human-1")
        assert len(records) == 1
    
    def test_get_records_by_outcome(self, audit_log, action, token):
        """Should retrieve records by outcome."""
        audit_log.record(action=action, actor="human-1", outcome="success", token=token)
        
        records = audit_log.get_records_by_outcome("success")
        assert len(records) == 1


class TestAuditExport:
    """Test audit export functionality."""
    
    @pytest.fixture
    def audit_log(self):
        return ExecutionAuditLog()
    
    @pytest.fixture
    def action(self):
        return SafeAction(
            action_id="test-1",
            action_type=SafeActionType.NAVIGATE,
            target="https://example.com",
            parameters={},
            description="Test",
        )
    
    @pytest.fixture
    def token(self, action):
        return ExecutionToken.generate(approver_id="human-1", action=action)
    
    def test_export_for_compliance(self, audit_log, action, token):
        """Should export records for compliance."""
        audit_log.record(action=action, actor="human-1", outcome="success", token=token)
        
        export = audit_log.export_for_compliance()
        assert len(export) == 1
        assert "record_id" in export[0]
        assert "timestamp" in export[0]
        assert "action_type" in export[0]
        assert "actor" in export[0]
        assert "outcome" in export[0]
        assert "record_hash" in export[0]
