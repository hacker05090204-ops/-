"""
Tests for Phase-10 boundary guard.

Validates:
- Forbidden imports are detected
- Forbidden actions are detected
- Write attempts to read-only phases are detected
"""

import pytest

from governance_friction.boundaries import Phase10BoundaryGuard
from governance_friction.errors import (
    Phase10BoundaryViolation,
    NetworkExecutionAttempt,
    AutomationAttempt,
    FrictionBypassAttempt,
    ReadOnlyViolation,
)


class TestForbiddenImports:
    """Test forbidden import detection."""
    
    def test_network_imports_forbidden(self):
        """Network modules should raise NetworkExecutionAttempt."""
        network_modules = [
            "httpx", "requests", "aiohttp", "socket",
            "urllib.request", "urllib3", "http.client",
        ]
        for module in network_modules:
            with pytest.raises(NetworkExecutionAttempt):
                Phase10BoundaryGuard.check_import(module)
    
    def test_browser_automation_forbidden(self):
        """Browser automation modules should raise Phase10BoundaryViolation."""
        browser_modules = [
            "selenium", "playwright", "puppeteer",
            "pyppeteer", "splinter", "mechanize",
        ]
        for module in browser_modules:
            with pytest.raises(Phase10BoundaryViolation):
                Phase10BoundaryGuard.check_import(module)
    
    def test_ui_automation_forbidden(self):
        """UI automation modules should raise Phase10BoundaryViolation."""
        ui_modules = ["pyautogui", "pynput", "keyboard", "mouse"]
        for module in ui_modules:
            with pytest.raises(Phase10BoundaryViolation):
                Phase10BoundaryGuard.check_import(module)
    
    def test_submodule_imports_forbidden(self):
        """Submodules of forbidden modules should also be forbidden."""
        with pytest.raises(NetworkExecutionAttempt):
            Phase10BoundaryGuard.check_import("requests.sessions")
        
        with pytest.raises(Phase10BoundaryViolation):
            Phase10BoundaryGuard.check_import("selenium.webdriver")
    
    def test_allowed_imports_pass(self):
        """Allowed modules should not raise."""
        allowed_modules = [
            "os", "sys", "json", "hashlib", "uuid",
            "dataclasses", "typing", "time", "enum",
        ]
        for module in allowed_modules:
            # Should not raise
            Phase10BoundaryGuard.check_import(module)


class TestForbiddenActions:
    """Test forbidden action detection."""
    
    def test_automation_actions_forbidden(self):
        """Automation actions should raise AutomationAttempt."""
        automation_actions = [
            "auto_approve", "auto_submit", "auto_confirm",
            "infer_decision", "suggest_decision", "recommend_action",
            "classify_bug", "assign_severity", "execute_action",
        ]
        for action in automation_actions:
            with pytest.raises(AutomationAttempt):
                Phase10BoundaryGuard.check_forbidden_action(action)
    
    def test_bypass_actions_forbidden(self):
        """Bypass actions should raise FrictionBypassAttempt."""
        bypass_actions = [
            "bypass_deliberation", "bypass_edit", "bypass_challenge",
            "bypass_cooldown", "bypass_audit", "bypass_friction",
            "disable_friction", "reduce_friction", "skip_friction",
        ]
        for action in bypass_actions:
            with pytest.raises(FrictionBypassAttempt):
                Phase10BoundaryGuard.check_forbidden_action(action)
    
    def test_partial_match_detected(self):
        """Actions containing forbidden terms should be detected."""
        with pytest.raises(AutomationAttempt):
            Phase10BoundaryGuard.check_forbidden_action("auto_approve_report")
        
        with pytest.raises(FrictionBypassAttempt):
            Phase10BoundaryGuard.check_forbidden_action("bypass_deliberation_check")
    
    def test_case_insensitive(self):
        """Action detection should be case-insensitive."""
        with pytest.raises(AutomationAttempt):
            Phase10BoundaryGuard.check_forbidden_action("AUTO_APPROVE")
        
        with pytest.raises(FrictionBypassAttempt):
            Phase10BoundaryGuard.check_forbidden_action("BYPASS_FRICTION")
    
    def test_allowed_actions_pass(self):
        """Allowed actions should not raise."""
        allowed_actions = [
            "start_deliberation", "check_edit", "present_challenge",
            "record_confirmation", "validate_audit",
        ]
        for action in allowed_actions:
            # Should not raise
            Phase10BoundaryGuard.check_forbidden_action(action)


class TestWriteAttempts:
    """Test write attempt detection on read-only phases."""
    
    def test_write_to_phase6_forbidden(self):
        """Write to Phase-6 should raise ReadOnlyViolation."""
        with pytest.raises(ReadOnlyViolation):
            Phase10BoundaryGuard.check_write_attempt("phase-6", "write_decision")
        
        with pytest.raises(ReadOnlyViolation):
            Phase10BoundaryGuard.check_write_attempt("decision_workflow", "update_status")
    
    def test_write_to_phase7_forbidden(self):
        """Write to Phase-7 should raise ReadOnlyViolation."""
        with pytest.raises(ReadOnlyViolation):
            Phase10BoundaryGuard.check_write_attempt("phase-7", "create_submission")
        
        with pytest.raises(ReadOnlyViolation):
            Phase10BoundaryGuard.check_write_attempt("submission_workflow", "modify_report")
    
    def test_write_to_phase8_forbidden(self):
        """Write to Phase-8 should raise ReadOnlyViolation."""
        with pytest.raises(ReadOnlyViolation):
            Phase10BoundaryGuard.check_write_attempt("phase-8", "insert_analysis")
        
        with pytest.raises(ReadOnlyViolation):
            Phase10BoundaryGuard.check_write_attempt("intelligence_layer", "delete_pattern")
    
    def test_write_to_phase9_forbidden(self):
        """Write to Phase-9 should raise ReadOnlyViolation."""
        with pytest.raises(ReadOnlyViolation):
            Phase10BoundaryGuard.check_write_attempt("phase-9", "save_observation")
        
        with pytest.raises(ReadOnlyViolation):
            Phase10BoundaryGuard.check_write_attempt("browser_assistant", "update_context")
    
    def test_read_operations_allowed(self):
        """Read operations should be allowed."""
        read_operations = [
            "read", "get", "fetch", "query", "list", "find",
        ]
        for op in read_operations:
            # Should not raise
            Phase10BoundaryGuard.check_write_attempt("phase-6", op)
            Phase10BoundaryGuard.check_write_attempt("decision_workflow", op)
    
    def test_write_to_phase10_allowed(self):
        """Write to Phase-10 itself should be allowed."""
        # Should not raise - Phase-10 is not read-only
        Phase10BoundaryGuard.check_write_attempt("phase-10", "write_audit")
        Phase10BoundaryGuard.check_write_attempt("governance_friction", "create_record")
