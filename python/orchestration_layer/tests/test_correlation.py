# PHASE-12 GOVERNANCE COMPLIANCE
# This module is part of Phase-12 (Runtime Orchestration Implementation)
#
# FORBIDDEN CAPABILITIES:
# - NO execution logic
# - NO decision logic
# - NO submission logic
# - NO network access
# - NO browser automation
# - NO friction wiring or execution
# - NO auto-approval
# - NO frozen phase modification
#
# MANDATORY DECLARATION:
# Phase-12 implements orchestration without altering execution,
# human authority, governance friction, or audit invariants.

"""
Phase-12 Track 4 Cross-Phase Correlation Tests

TEST CATEGORY: Per-Track Tests - Track 4 (Priority: MEDIUM)
EXECUTION ORDER: 4 (After Property Tests)

Test IDs:
- TEST-T4-001: Correlation is READ-ONLY
- TEST-T4-002: No modification of phase audit logs
- TEST-T4-003: Only references audit entry IDs
- TEST-T4-004: Phase-10 friction is READ-ONLY
- TEST-T4-005: No friction wiring
- TEST-T4-006: No friction execution
"""

import pytest

from orchestration_layer.correlation import (
    create_correlation,
    get_correlated_entries,
    consume_friction_result,
)
from orchestration_layer.errors import (
    ReadOnlyViolationError,
)
from orchestration_layer.types import CrossPhaseCorrelation


@pytest.mark.track4
class TestCorrelationReadOnly:
    """Test IDs: TEST-T4-001, TEST-T4-002, TEST-T4-003 - Requirement: REQ-3.2.3"""
    
    def test_correlation_is_read_only(self):
        """TEST-T4-001: Verify correlation operations are read-only."""
        # Create correlation with ID references
        phase_entries = {
            "phase_4": "entry_abc123",
            "phase_5": "entry_def456",
            "phase_10": "entry_ghi789",
        }
        
        correlation = create_correlation(phase_entries)
        
        # Verify correlation is immutable (frozen dataclass)
        assert isinstance(correlation, CrossPhaseCorrelation)
        
        # Verify attempting to modify raises error
        with pytest.raises(AttributeError):
            correlation.correlation_id = "modified_id"
        
        with pytest.raises(AttributeError):
            correlation.phase_entries = {}
        
        # Verify human_confirmation_required is True
        assert correlation.human_confirmation_required is True
        
        # Verify no_auto_action is True
        assert correlation.no_auto_action is True
    
    def test_no_modification_of_phase_audit_logs(self):
        """TEST-T4-002: Verify no modification of phase audit logs."""
        # Create correlation
        phase_entries = {
            "phase_4": "entry_001",
            "phase_10": "entry_002",
        }
        
        correlation = create_correlation(phase_entries)
        
        # Get correlated entries (READ-ONLY)
        entries = get_correlated_entries(correlation)
        
        # Verify we get a copy, not the original
        assert entries == phase_entries
        assert entries is not correlation.phase_entries
        
        # Modifying the returned dict does NOT affect the correlation
        entries["phase_4"] = "modified_entry"
        
        # Original correlation is unchanged
        original_entries = get_correlated_entries(correlation)
        assert original_entries["phase_4"] == "entry_001"
    
    def test_only_references_audit_entry_ids(self):
        """TEST-T4-003: Verify correlation only references audit entry IDs."""
        # Valid: string IDs only
        valid_entries = {
            "phase_4": "entry_id_1",
            "phase_5": "entry_id_2",
        }
        
        correlation = create_correlation(valid_entries)
        assert correlation.phase_entries == valid_entries
        
        # Invalid: non-string values should raise error
        with pytest.raises(ReadOnlyViolationError):
            create_correlation({"phase_4": 12345})  # int instead of str
        
        with pytest.raises(ReadOnlyViolationError):
            create_correlation({123: "entry_id"})  # int key instead of str
        
        with pytest.raises(ReadOnlyViolationError):
            create_correlation("not_a_dict")  # not a dict at all
        
        # Invalid: get_correlated_entries with wrong type
        with pytest.raises(ReadOnlyViolationError):
            get_correlated_entries("not_a_correlation")


@pytest.mark.track4
class TestPhase10FrictionReadOnly:
    """Test IDs: TEST-T4-004, TEST-T4-005, TEST-T4-006 - Requirement: INV-5.4"""
    
    def test_phase10_friction_read_only(self):
        """TEST-T4-004: Verify Phase-10 friction is read-only."""
        friction_record_id = "friction_record_abc123"
        
        result = consume_friction_result(friction_record_id)
        
        # Verify result is a READ-ONLY reference
        assert result["friction_record_id"] == friction_record_id
        assert result["reference_type"] == "read_only"
        assert result["phase"] == "phase_10"
        
        # Verify human confirmation required
        assert result["human_confirmation_required"] is True
        assert result["no_auto_action"] is True
        
        # Verify invalid input raises error
        with pytest.raises(ReadOnlyViolationError):
            consume_friction_result(12345)  # not a string
        
        with pytest.raises(ReadOnlyViolationError):
            consume_friction_result("")  # empty string
        
        with pytest.raises(ReadOnlyViolationError):
            consume_friction_result("   ")  # whitespace only
    
    def test_no_friction_wiring(self):
        """TEST-T4-005: Verify no friction wiring occurs."""
        friction_record_id = "friction_record_xyz789"
        
        result = consume_friction_result(friction_record_id)
        
        # Verify friction is NOT wired
        assert result["friction_wired"] is False
        
        # Verify this is explicitly a read-only reference
        assert result["reference_type"] == "read_only"
        
        # The function does NOT:
        # - Connect friction to any workflow
        # - Enable friction enforcement
        # - Create friction dependencies
    
    def test_no_friction_execution(self):
        """TEST-T4-006: Verify no friction execution occurs."""
        friction_record_id = "friction_record_def456"
        
        result = consume_friction_result(friction_record_id)
        
        # Verify friction is NOT executed
        assert result["friction_executed"] is False
        
        # Verify friction is NOT enforced
        assert result["friction_enforced"] is False
        
        # The function does NOT:
        # - Execute any friction mechanisms
        # - Enforce any friction policy
        # - Trigger any friction checks
        # - Bypass or reduce friction
