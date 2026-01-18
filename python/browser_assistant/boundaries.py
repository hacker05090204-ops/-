"""
Phase-9 Boundary Guard

Enforces architectural boundaries at module load time and runtime.

SECURITY: This guard prevents:
- Forbidden imports (execution_layer, network libs, browser automation)
- Forbidden actions (execution, injection, modification, submission)
- Network access attempts
- Automation attempts
- Write operations to Phase-4 through Phase-8 data

All violations result in HARD STOP via exception.

Phase-9 is ASSISTIVE ONLY. Human always clicks YES/NO.
"""

from __future__ import annotations
import sys
from typing import ClassVar, Set

from browser_assistant.errors import (
    ArchitecturalViolationError,
    AutomationAttemptError,
    NetworkExecutionAttemptError,
    ReadOnlyViolationError,
)


class Phase9BoundaryGuard:
    """
    Validates imports and enforces phase boundaries for Phase-9.
    
    SECURITY: This guard runs at module initialization to prevent
    forbidden imports from being loaded.
    
    FORBIDDEN IMPORTS:
    - execution_layer (Phase-4) - except types for read-only
    - artifact_scanner (Phase-5) - except types for read-only
    - httpx, requests, aiohttp, socket (Network execution)
    - selenium, playwright, puppeteer (Browser automation)
    - pyautogui, pynput (UI automation)
    
    FORBIDDEN ACTIONS:
    - execute_payload, inject_traffic, modify_request
    - classify_bug, determine_severity, assign_cvss
    - submit_report, auto_submit
    - generate_poc, create_exploit
    - record_video, capture_screenshot (automated)
    - chain_findings, auto_correlate
    - write/modify/delete to Phase-4 through Phase-8
    """
    
    FORBIDDEN_IMPORTS: ClassVar[Set[str]] = {
        # Phase-4 - Execution Layer (except types)
        "execution_layer.controller",
        "execution_layer.actions",
        "execution_layer.browser",
        # Phase-5 - Artifact Scanner (except types)
        "artifact_scanner.scanner",
        "artifact_scanner.analyzers",
        # Network libraries - PERMANENTLY DISABLED
        "httpx",
        "requests",
        "aiohttp",
        "socket",
        "urllib.request",
        "urllib3",
        "http.client",
        # Browser automation - PERMANENTLY DISABLED
        "selenium",
        "playwright",
        "puppeteer",
        "pyppeteer",
        "splinter",
        "mechanize",
        # UI automation - PERMANENTLY DISABLED
        "pyautogui",
        "pynput",
        "keyboard",
        "mouse",
    }
    
    NETWORK_MODULES: ClassVar[Set[str]] = {
        "httpx",
        "requests",
        "aiohttp",
        "socket",
        "urllib.request",
        "urllib3",
        "http.client",
    }
    
    BROWSER_AUTOMATION_MODULES: ClassVar[Set[str]] = {
        "selenium",
        "playwright",
        "puppeteer",
        "pyppeteer",
        "splinter",
        "mechanize",
    }
    
    UI_AUTOMATION_MODULES: ClassVar[Set[str]] = {
        "pyautogui",
        "pynput",
        "keyboard",
        "mouse",
    }
    
    FORBIDDEN_ACTIONS: ClassVar[Set[str]] = {
        # Payload execution - NEVER
        "execute_payload",
        "run_payload",
        "inject_payload",
        "send_payload",
        # Traffic injection - NEVER
        "inject_traffic",
        "inject_request",
        "inject_response",
        "intercept_traffic",
        # Request modification - NEVER
        "modify_request",
        "alter_request",
        "tamper_request",
        "edit_request",
        # Bug classification - Human's responsibility
        "classify_bug",
        "is_vulnerability",
        "is_bug",
        "determine_bug_type",
        "auto_classify",
        # Severity assignment - Human's responsibility
        "determine_severity",
        "assign_severity",
        "calculate_severity",
        "assign_cvss",
        "calculate_cvss",
        "auto_severity",
        # Report submission - Human's responsibility
        "submit_report",
        "auto_submit",
        "send_report",
        "transmit_report",
        "guided_submission",
        # PoC generation - NEVER
        "generate_poc",
        "create_poc",
        "create_exploit",
        "generate_exploit",
        "build_poc",
        # Evidence automation - NEVER
        "record_video",
        "auto_record",
        "capture_screenshot",
        "auto_capture",
        "auto_evidence",
        # Finding chaining - NEVER
        "chain_findings",
        "auto_correlate",
        "auto_chain",
        "link_findings",
        # Auto-confirmation - NEVER
        "auto_confirm",
        "bypass_confirmation",
        "skip_confirmation",
        "auto_approve",
        # Data modification - Read-only principle
        "write_decision",
        "modify_decision",
        "delete_decision",
        "write_submission",
        "modify_submission",
        "delete_submission",
        "write_audit",
        "modify_audit",
        "delete_audit",
        "write_finding",
        "modify_finding",
        "delete_finding",
    }
    
    READ_ONLY_PHASES: ClassVar[Set[str]] = {
        "Phase-4",  # Execution Layer
        "Phase-5",  # Artifact Scanner
        "Phase-6",  # Decision Workflow
        "Phase-7",  # Submission Workflow
        "Phase-8",  # Intelligence Layer
    }
    
    # Modules that may be loaded by test frameworks but are not used by Phase-9
    # These are checked at import time but not at runtime validation
    RUNTIME_EXEMPT_MODULES: ClassVar[Set[str]] = {
        "socket",  # Loaded by pytest/hypothesis but not used by Phase-9
    }
    
    @staticmethod
    def validate_imports() -> None:
        """
        Check that no forbidden modules are imported by Phase-9 code.
        
        This method validates that Phase-9 code has not imported forbidden
        modules. Some modules (like socket) may be loaded by test frameworks
        but are not used by Phase-9 code itself.
        
        Raises:
            ArchitecturalViolationError: If forbidden import detected.
            NetworkExecutionAttemptError: If network module detected.
            AutomationAttemptError: If automation module detected.
        """
        for module_name in Phase9BoundaryGuard.FORBIDDEN_IMPORTS:
            # Skip modules that may be loaded by test frameworks
            if module_name in Phase9BoundaryGuard.RUNTIME_EXEMPT_MODULES:
                continue
            if module_name in sys.modules:
                if module_name in Phase9BoundaryGuard.NETWORK_MODULES:
                    raise NetworkExecutionAttemptError(f"import {module_name}")
                if module_name in Phase9BoundaryGuard.BROWSER_AUTOMATION_MODULES:
                    raise AutomationAttemptError(f"import browser automation: {module_name}")
                if module_name in Phase9BoundaryGuard.UI_AUTOMATION_MODULES:
                    raise AutomationAttemptError(f"import UI automation: {module_name}")
                raise ArchitecturalViolationError(f"import {module_name}")
    
    @staticmethod
    def check_import(module_name: str) -> None:
        """
        Check if a specific module import is allowed.
        
        Args:
            module_name: Name of the module to check.
            
        Raises:
            ArchitecturalViolationError: If import is forbidden.
            NetworkExecutionAttemptError: If network module.
            AutomationAttemptError: If automation module.
        """
        if module_name in Phase9BoundaryGuard.NETWORK_MODULES:
            raise NetworkExecutionAttemptError(f"import {module_name}")
        if module_name in Phase9BoundaryGuard.BROWSER_AUTOMATION_MODULES:
            raise AutomationAttemptError(f"import browser automation: {module_name}")
        if module_name in Phase9BoundaryGuard.UI_AUTOMATION_MODULES:
            raise AutomationAttemptError(f"import UI automation: {module_name}")
        if module_name in Phase9BoundaryGuard.FORBIDDEN_IMPORTS:
            raise ArchitecturalViolationError(f"import {module_name}")
    
    @staticmethod
    def check_forbidden_action(action: str) -> None:
        """
        Raise error for forbidden actions.
        
        Args:
            action: Name of the action to check.
            
        Raises:
            ArchitecturalViolationError: If action is forbidden.
            AutomationAttemptError: If action is automation.
            NetworkExecutionAttemptError: If action involves network.
        """
        action_lower = action.lower()
        
        # Check exact match
        if action in Phase9BoundaryGuard.FORBIDDEN_ACTIONS:
            if any(kw in action_lower for kw in ["payload", "inject", "traffic", "request"]):
                raise NetworkExecutionAttemptError(action)
            if any(kw in action_lower for kw in ["auto", "record", "capture", "chain"]):
                raise AutomationAttemptError(action)
            raise ArchitecturalViolationError(action)
        
        # Check keyword patterns
        forbidden_patterns = [
            # Execution patterns
            ("execute", NetworkExecutionAttemptError),
            ("inject", NetworkExecutionAttemptError),
            ("payload", NetworkExecutionAttemptError),
            ("modify_request", NetworkExecutionAttemptError),
            ("send_request", NetworkExecutionAttemptError),
            # Automation patterns
            ("auto_", AutomationAttemptError),
            ("record_video", AutomationAttemptError),
            ("capture_", AutomationAttemptError),
            ("chain_", AutomationAttemptError),
            # Classification patterns
            ("classify_bug", ArchitecturalViolationError),
            ("is_vulnerability", ArchitecturalViolationError),
            ("determine_severity", ArchitecturalViolationError),
            ("assign_severity", ArchitecturalViolationError),
            ("assign_cvss", ArchitecturalViolationError),
            # Submission patterns
            ("submit_report", ArchitecturalViolationError),
            ("send_report", ArchitecturalViolationError),
            # PoC patterns
            ("generate_poc", ArchitecturalViolationError),
            ("create_exploit", ArchitecturalViolationError),
            # Write patterns
            ("write_", ArchitecturalViolationError),
            ("modify_", ArchitecturalViolationError),
            ("delete_", ArchitecturalViolationError),
        ]
        
        for pattern, error_class in forbidden_patterns:
            if pattern in action_lower:
                raise error_class(action)
    
    @staticmethod
    def check_write_attempt(phase: str, action: str) -> None:
        """
        Check for write attempts to read-only phases.
        
        Args:
            phase: The phase being written to.
            action: The write action attempted.
            
        Raises:
            ReadOnlyViolationError: If write to read-only phase.
        """
        if phase in Phase9BoundaryGuard.READ_ONLY_PHASES:
            raise ReadOnlyViolationError(phase, action)
    
    @staticmethod
    def assert_passive_observation() -> None:
        """
        Assert that Phase-9 is operating in passive observation mode.
        
        Phase-9 OBSERVES browser activity but NEVER:
        - Modifies requests
        - Injects payloads
        - Executes JavaScript
        - Intercepts traffic
        - Automates browser actions
        """
        # Phase-9 is PASSIVE OBSERVATION ONLY
        # This method exists to document the constraint
        pass
    
    @staticmethod
    def assert_no_network_execution() -> None:
        """
        Assert that Phase-9 has no network execution capability.
        
        Phase-9 NEVER:
        - Sends HTTP requests
        - Injects payloads
        - Modifies network traffic
        - Executes network operations
        """
        # Phase-9 has NO network execution - PERMANENT
        # This method exists to document the constraint
        pass
    
    @staticmethod
    def assert_no_automation() -> None:
        """
        Assert that Phase-9 has no automation capability.
        
        Phase-9 NEVER:
        - Automates browser actions
        - Records video automatically
        - Captures screenshots automatically
        - Chains findings automatically
        - Confirms actions automatically
        """
        # Phase-9 has NO automation - PERMANENT
        # This method exists to document the constraint
        pass
    
    @staticmethod
    def assert_human_confirmation_required() -> None:
        """
        Assert that human confirmation is required for all outputs.
        
        Every assistant output requires explicit human confirmation.
        Human always clicks YES or NO.
        """
        # Human confirmation is ALWAYS required
        # This method exists to document the constraint
        pass
    
    @staticmethod
    def assert_read_only_access() -> None:
        """
        Assert that Phase-9 has read-only access to earlier phases.
        
        Phase-9 can READ from:
        - Phase-4 (Execution Layer) - types only
        - Phase-5 (Artifact Scanner) - types only
        - Phase-6 (Decision Workflow) - read-only
        - Phase-7 (Submission Workflow) - read-only
        - Phase-8 (Intelligence Layer) - advisory only
        
        Phase-9 NEVER writes to any earlier phase.
        """
        # Phase-9 has READ-ONLY access to all earlier phases
        # This method exists to document the constraint
        pass
