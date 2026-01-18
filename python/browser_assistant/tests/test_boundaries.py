"""
Phase-9 Boundary Guard Tests

Tests for architectural boundary enforcement.
"""

import pytest
import sys

from browser_assistant.boundaries import Phase9BoundaryGuard
from browser_assistant.errors import (
    ArchitecturalViolationError,
    AutomationAttemptError,
    NetworkExecutionAttemptError,
    ReadOnlyViolationError,
)


class TestForbiddenImports:
    """Test forbidden import detection."""
    
    def test_network_module_detection(self):
        """Verify network modules are detected."""
        with pytest.raises(NetworkExecutionAttemptError):
            Phase9BoundaryGuard.check_import("httpx")
        
        with pytest.raises(NetworkExecutionAttemptError):
            Phase9BoundaryGuard.check_import("requests")
        
        with pytest.raises(NetworkExecutionAttemptError):
            Phase9BoundaryGuard.check_import("aiohttp")
        
        with pytest.raises(NetworkExecutionAttemptError):
            Phase9BoundaryGuard.check_import("socket")
    
    def test_browser_automation_detection(self):
        """Verify browser automation modules are detected."""
        with pytest.raises(AutomationAttemptError):
            Phase9BoundaryGuard.check_import("selenium")
        
        with pytest.raises(AutomationAttemptError):
            Phase9BoundaryGuard.check_import("playwright")
        
        with pytest.raises(AutomationAttemptError):
            Phase9BoundaryGuard.check_import("puppeteer")
    
    def test_ui_automation_detection(self):
        """Verify UI automation modules are detected."""
        with pytest.raises(AutomationAttemptError):
            Phase9BoundaryGuard.check_import("pyautogui")
        
        with pytest.raises(AutomationAttemptError):
            Phase9BoundaryGuard.check_import("pynput")
    
    def test_execution_layer_detection(self):
        """Verify execution layer imports are detected."""
        with pytest.raises(ArchitecturalViolationError):
            Phase9BoundaryGuard.check_import("execution_layer.controller")
        
        with pytest.raises(ArchitecturalViolationError):
            Phase9BoundaryGuard.check_import("execution_layer.actions")
    
    def test_allowed_imports(self):
        """Verify allowed imports don't raise."""
        # Standard library should be allowed
        Phase9BoundaryGuard.check_import("datetime")
        Phase9BoundaryGuard.check_import("uuid")
        Phase9BoundaryGuard.check_import("hashlib")
        Phase9BoundaryGuard.check_import("re")


class TestForbiddenActions:
    """Test forbidden action detection."""
    
    def test_payload_execution_forbidden(self):
        """Verify payload execution actions are forbidden."""
        with pytest.raises(NetworkExecutionAttemptError):
            Phase9BoundaryGuard.check_forbidden_action("execute_payload")
        
        with pytest.raises(NetworkExecutionAttemptError):
            Phase9BoundaryGuard.check_forbidden_action("inject_payload")
    
    def test_traffic_injection_forbidden(self):
        """Verify traffic injection actions are forbidden."""
        with pytest.raises(NetworkExecutionAttemptError):
            Phase9BoundaryGuard.check_forbidden_action("inject_traffic")
        
        with pytest.raises(NetworkExecutionAttemptError):
            Phase9BoundaryGuard.check_forbidden_action("inject_request")
    
    def test_request_modification_forbidden(self):
        """Verify request modification actions are forbidden."""
        with pytest.raises(NetworkExecutionAttemptError):
            Phase9BoundaryGuard.check_forbidden_action("modify_request")
    
    def test_bug_classification_forbidden(self):
        """Verify bug classification actions are forbidden."""
        with pytest.raises(ArchitecturalViolationError):
            Phase9BoundaryGuard.check_forbidden_action("classify_bug")
        
        with pytest.raises(ArchitecturalViolationError):
            Phase9BoundaryGuard.check_forbidden_action("is_vulnerability")
    
    def test_severity_assignment_forbidden(self):
        """Verify severity assignment actions are forbidden."""
        with pytest.raises(ArchitecturalViolationError):
            Phase9BoundaryGuard.check_forbidden_action("determine_severity")
        
        with pytest.raises(ArchitecturalViolationError):
            Phase9BoundaryGuard.check_forbidden_action("assign_severity")
        
        with pytest.raises(ArchitecturalViolationError):
            Phase9BoundaryGuard.check_forbidden_action("assign_cvss")
    
    def test_report_submission_forbidden(self):
        """Verify report submission actions are forbidden."""
        with pytest.raises(ArchitecturalViolationError):
            Phase9BoundaryGuard.check_forbidden_action("submit_report")
        
        # auto_submit raises AutomationAttemptError due to "auto_" prefix
        with pytest.raises(AutomationAttemptError):
            Phase9BoundaryGuard.check_forbidden_action("auto_submit")
    
    def test_poc_generation_forbidden(self):
        """Verify PoC generation actions are forbidden."""
        with pytest.raises(ArchitecturalViolationError):
            Phase9BoundaryGuard.check_forbidden_action("generate_poc")
        
        with pytest.raises(ArchitecturalViolationError):
            Phase9BoundaryGuard.check_forbidden_action("create_exploit")
    
    def test_evidence_automation_forbidden(self):
        """Verify evidence automation actions are forbidden."""
        with pytest.raises(AutomationAttemptError):
            Phase9BoundaryGuard.check_forbidden_action("record_video")
        
        with pytest.raises(AutomationAttemptError):
            Phase9BoundaryGuard.check_forbidden_action("auto_capture")
    
    def test_auto_confirmation_forbidden(self):
        """Verify auto-confirmation actions are forbidden."""
        with pytest.raises(AutomationAttemptError):
            Phase9BoundaryGuard.check_forbidden_action("auto_confirm")
        
        with pytest.raises(AutomationAttemptError):
            Phase9BoundaryGuard.check_forbidden_action("auto_approve")
    
    def test_data_modification_forbidden(self):
        """Verify data modification actions are forbidden."""
        with pytest.raises(ArchitecturalViolationError):
            Phase9BoundaryGuard.check_forbidden_action("write_decision")
        
        with pytest.raises(ArchitecturalViolationError):
            Phase9BoundaryGuard.check_forbidden_action("modify_submission")
        
        with pytest.raises(ArchitecturalViolationError):
            Phase9BoundaryGuard.check_forbidden_action("delete_finding")


class TestReadOnlyViolations:
    """Test read-only violation detection."""
    
    def test_phase4_write_forbidden(self):
        """Verify writes to Phase-4 are forbidden."""
        with pytest.raises(ReadOnlyViolationError) as exc_info:
            Phase9BoundaryGuard.check_write_attempt("Phase-4", "write_action")
        
        assert "Phase-4" in str(exc_info.value)
    
    def test_phase5_write_forbidden(self):
        """Verify writes to Phase-5 are forbidden."""
        with pytest.raises(ReadOnlyViolationError):
            Phase9BoundaryGuard.check_write_attempt("Phase-5", "modify_scan")
    
    def test_phase6_write_forbidden(self):
        """Verify writes to Phase-6 are forbidden."""
        with pytest.raises(ReadOnlyViolationError):
            Phase9BoundaryGuard.check_write_attempt("Phase-6", "write_decision")
    
    def test_phase7_write_forbidden(self):
        """Verify writes to Phase-7 are forbidden."""
        with pytest.raises(ReadOnlyViolationError):
            Phase9BoundaryGuard.check_write_attempt("Phase-7", "modify_submission")
    
    def test_phase8_write_forbidden(self):
        """Verify writes to Phase-8 are forbidden."""
        with pytest.raises(ReadOnlyViolationError):
            Phase9BoundaryGuard.check_write_attempt("Phase-8", "write_insight")


class TestAssertionMethods:
    """Test assertion methods don't raise."""
    
    def test_assert_passive_observation(self):
        """Verify passive observation assertion doesn't raise."""
        Phase9BoundaryGuard.assert_passive_observation()
    
    def test_assert_no_network_execution(self):
        """Verify no network execution assertion doesn't raise."""
        Phase9BoundaryGuard.assert_no_network_execution()
    
    def test_assert_no_automation(self):
        """Verify no automation assertion doesn't raise."""
        Phase9BoundaryGuard.assert_no_automation()
    
    def test_assert_human_confirmation_required(self):
        """Verify human confirmation assertion doesn't raise."""
        Phase9BoundaryGuard.assert_human_confirmation_required()
    
    def test_assert_read_only_access(self):
        """Verify read-only access assertion doesn't raise."""
        Phase9BoundaryGuard.assert_read_only_access()


class TestForbiddenSets:
    """Test forbidden sets are properly defined."""
    
    def test_forbidden_imports_not_empty(self):
        """Verify forbidden imports set is not empty."""
        assert len(Phase9BoundaryGuard.FORBIDDEN_IMPORTS) > 0
    
    def test_network_modules_not_empty(self):
        """Verify network modules set is not empty."""
        assert len(Phase9BoundaryGuard.NETWORK_MODULES) > 0
    
    def test_browser_automation_modules_not_empty(self):
        """Verify browser automation modules set is not empty."""
        assert len(Phase9BoundaryGuard.BROWSER_AUTOMATION_MODULES) > 0
    
    def test_forbidden_actions_not_empty(self):
        """Verify forbidden actions set is not empty."""
        assert len(Phase9BoundaryGuard.FORBIDDEN_ACTIONS) > 0
    
    def test_read_only_phases_complete(self):
        """Verify all earlier phases are in read-only set."""
        assert "Phase-4" in Phase9BoundaryGuard.READ_ONLY_PHASES
        assert "Phase-5" in Phase9BoundaryGuard.READ_ONLY_PHASES
        assert "Phase-6" in Phase9BoundaryGuard.READ_ONLY_PHASES
        assert "Phase-7" in Phase9BoundaryGuard.READ_ONLY_PHASES
        assert "Phase-8" in Phase9BoundaryGuard.READ_ONLY_PHASES
