"""
Phase-10: Governance & Friction Layer - Boundary Guard

Enforces architectural boundaries at module load time and runtime.
Prevents forbidden imports, actions, and write operations.
"""

import sys
from typing import ClassVar, Set

from governance_friction.errors import (
    Phase10BoundaryViolation,
    NetworkExecutionAttempt,
    AutomationAttempt,
    FrictionBypassAttempt,
    ReadOnlyViolation,
)


class Phase10BoundaryGuard:
    """
    Validates imports and enforces phase boundaries for Phase-10.
    
    SECURITY: This guard prevents:
    - Forbidden imports (network libs, automation libs)
    - Forbidden actions (auto-approve, auto-submit, bypass)
    - Write operations to Phase-6 through Phase-9 data
    """
    
    # Network modules - PERMANENTLY DISABLED
    FORBIDDEN_NETWORK_IMPORTS: ClassVar[Set[str]] = frozenset({
        "httpx", "requests", "aiohttp", "socket", 
        "urllib.request", "urllib3", "http.client",
    })
    
    # Browser automation - PERMANENTLY DISABLED
    FORBIDDEN_BROWSER_IMPORTS: ClassVar[Set[str]] = frozenset({
        "selenium", "playwright", "puppeteer", 
        "pyppeteer", "splinter", "mechanize",
    })
    
    # UI automation - PERMANENTLY DISABLED
    FORBIDDEN_UI_IMPORTS: ClassVar[Set[str]] = frozenset({
        "pyautogui", "pynput", "keyboard", "mouse",
    })
    
    # All forbidden imports combined
    FORBIDDEN_IMPORTS: ClassVar[Set[str]] = (
        FORBIDDEN_NETWORK_IMPORTS | 
        FORBIDDEN_BROWSER_IMPORTS | 
        FORBIDDEN_UI_IMPORTS
    )
    
    # Forbidden actions - PERMANENTLY DISABLED
    FORBIDDEN_ACTIONS: ClassVar[Set[str]] = frozenset({
        # Automation
        "auto_approve", "auto_submit", "auto_confirm",
        "infer_decision", "suggest_decision", "recommend_action",
        "classify_bug", "assign_severity", "execute_action",
        # Bypass
        "bypass_deliberation", "bypass_edit", "bypass_challenge",
        "bypass_cooldown", "bypass_audit", "bypass_friction",
        "disable_friction", "reduce_friction", "skip_friction",
    })
    
    # Read-only phases
    READ_ONLY_PHASES: ClassVar[Set[str]] = frozenset({
        "phase6", "phase-6", "decision_workflow",
        "phase7", "phase-7", "submission_workflow",
        "phase8", "phase-8", "intelligence_layer",
        "phase9", "phase-9", "browser_assistant",
    })
    
    @classmethod
    def validate_imports(cls) -> None:
        """
        Validate that no forbidden modules are imported.
        
        Raises:
            NetworkExecutionAttempt: If a network module is imported
            Phase10BoundaryViolation: If any forbidden module is imported
        """
        for module_name in cls.FORBIDDEN_IMPORTS:
            if module_name in sys.modules:
                if module_name in cls.FORBIDDEN_NETWORK_IMPORTS:
                    raise NetworkExecutionAttempt(module_name)
                raise Phase10BoundaryViolation(
                    violation_type="forbidden_import",
                    details=f"Module '{module_name}' is forbidden in Phase-10"
                )
    
    @classmethod
    def check_import(cls, module_name: str) -> None:
        """
        Check if a specific import is allowed.
        
        Args:
            module_name: Name of the module to check
            
        Raises:
            NetworkExecutionAttempt: If a network module
            Phase10BoundaryViolation: If forbidden
        """
        # Check exact match
        if module_name in cls.FORBIDDEN_IMPORTS:
            if module_name in cls.FORBIDDEN_NETWORK_IMPORTS:
                raise NetworkExecutionAttempt(module_name)
            raise Phase10BoundaryViolation(
                violation_type="forbidden_import",
                details=f"Module '{module_name}' is forbidden in Phase-10"
            )
        
        # Check if it's a submodule of a forbidden module
        for forbidden in cls.FORBIDDEN_IMPORTS:
            if module_name.startswith(f"{forbidden}."):
                if forbidden in cls.FORBIDDEN_NETWORK_IMPORTS:
                    raise NetworkExecutionAttempt(module_name)
                raise Phase10BoundaryViolation(
                    violation_type="forbidden_import",
                    details=f"Module '{module_name}' is forbidden in Phase-10"
                )
    
    @classmethod
    def check_forbidden_action(cls, action: str) -> None:
        """
        Check if an action is forbidden.
        
        Args:
            action: Name of the action to check
            
        Raises:
            AutomationAttempt: If action is automation-related
            FrictionBypassAttempt: If action is bypass-related
        """
        action_lower = action.lower()
        
        if action_lower in cls.FORBIDDEN_ACTIONS:
            if action_lower.startswith("bypass") or action_lower in {
                "disable_friction", "reduce_friction", "skip_friction"
            }:
                raise FrictionBypassAttempt(action)
            raise AutomationAttempt(action)
        
        # Check for partial matches (e.g., "auto_approve_report")
        for forbidden in cls.FORBIDDEN_ACTIONS:
            if forbidden in action_lower:
                if "bypass" in forbidden or forbidden in {
                    "disable_friction", "reduce_friction", "skip_friction"
                }:
                    raise FrictionBypassAttempt(action)
                raise AutomationAttempt(action)
    
    @classmethod
    def check_write_attempt(cls, phase: str, operation: str) -> None:
        """
        Check if a write operation is attempted on a read-only phase.
        
        Args:
            phase: Name of the phase being accessed
            operation: Name of the operation being attempted
            
        Raises:
            ReadOnlyViolation: If write is attempted on read-only phase
        """
        # Normalize phase name for comparison
        phase_normalized = phase.lower().replace("_", "-").replace(" ", "-")
        
        # Also check with underscores
        phase_underscore = phase.lower().replace("-", "_").replace(" ", "_")
        
        # Check if this is a read-only phase
        is_read_only = False
        for read_only in cls.READ_ONLY_PHASES:
            read_only_normalized = read_only.replace("_", "-")
            read_only_underscore = read_only.replace("-", "_")
            
            if (phase_normalized == read_only_normalized or 
                phase_underscore == read_only_underscore or
                read_only_normalized in phase_normalized or
                read_only_underscore in phase_underscore):
                is_read_only = True
                break
        
        if not is_read_only:
            return
        
        # Check if operation is a write operation
        write_operations = {
            "write", "update", "delete", "insert", "modify",
            "create", "set", "put", "post", "patch", "remove",
            "add", "append", "clear", "reset", "save",
        }
        op_lower = operation.lower()
        for write_op in write_operations:
            if write_op in op_lower:
                raise ReadOnlyViolation(phase, operation)
    
    @classmethod
    def validate_all(cls) -> None:
        """
        Run all validation checks.
        
        Raises:
            Phase10BoundaryViolation: If any violation is detected
        """
        cls.validate_imports()
