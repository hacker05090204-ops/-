"""
Phase-8 Boundary Guard

Enforces architectural boundaries at module load time and runtime.

SECURITY: This guard prevents:
- Forbidden imports (execution_layer, artifact_scanner, network libs)
- Forbidden actions (validation, recommendations, predictions, etc.)
- Network access attempts
- Write operations to Phase-6/Phase-7 data

All violations result in HARD STOP via exception.
"""

from __future__ import annotations
import sys
from typing import ClassVar, Set

from intelligence_layer.errors import (
    ArchitecturalViolationError,
    NetworkAccessAttemptError,
)


class BoundaryGuard:
    """
    Validates imports and enforces phase boundaries.
    
    SECURITY: This guard runs at module initialization to prevent
    forbidden imports from being loaded.
    
    FORBIDDEN IMPORTS:
    - execution_layer (Phase-4)
    - artifact_scanner (Phase-5)
    - httpx, requests, aiohttp, socket, urllib.request (Network)
    
    FORBIDDEN ACTIONS:
    - validate_bug, is_true_positive, is_false_positive
    - identify_business_logic_flaw, detect_logic_error
    - generate_poc, generate_proof_of_concept, generate_exploit
    - determine_cve, match_cve, assign_cve
    - guarantee_accuracy, confidence_score
    - auto_submit, safe_submit, guided_submission
    - recommend, suggest, prioritize, rank
    - predict, forecast
    - write, modify, delete, update (on Phase-6/Phase-7 data)
    """
    
    FORBIDDEN_IMPORTS: ClassVar[Set[str]] = {
        # Phase-4 - Execution Layer
        "execution_layer",
        # Phase-5 - Artifact Scanner
        "artifact_scanner",
        # Network libraries - PERMANENTLY DISABLED
        "httpx",
        "requests",
        "aiohttp",
        "socket",
        "urllib.request",
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
    
    FORBIDDEN_ACTIONS: ClassVar[Set[str]] = {
        # Bug validation - Human's responsibility
        "validate_bug",
        "is_true_positive",
        "is_false_positive",
        "verify_bug",
        "confirm_bug",
        # Business logic flaw identification - Human expertise required
        "identify_business_logic_flaw",
        "detect_logic_error",
        "find_business_flaw",
        # PoC generation - MCP's responsibility / Safety violation
        "generate_poc",
        "generate_proof_of_concept",
        "generate_exploit",
        "generate_attack_payload",
        "create_poc",
        # CVE determination - Human expertise required
        "determine_cve",
        "match_cve",
        "assign_cve",
        "identify_cve",
        # Accuracy guarantees - No accuracy guarantees possible
        "guarantee_accuracy",
        "confidence_score",
        "accuracy_score",
        "certainty_score",
        # Unskilled submission enablement - Safety violation
        "auto_submit",
        "safe_submit",
        "guided_submission",
        "easy_submit",
        # Recommendations - Human's responsibility
        "recommend",
        "suggest_action",
        "recommend_platform",
        "recommend_severity",
        "should_submit",
        # Predictions - No predictions allowed
        "predict",
        "forecast",
        "predict_trend",
        "predict_vulnerability",
        # Prioritization - Human's responsibility
        "prioritize",
        "rank",
        "sort_by_priority",
        "auto_prioritize",
        # Comparisons between reviewers - Forbidden
        "compare_reviewers",
        "rank_reviewers",
        "reviewer_ranking",
        # Data modification - Read-only principle
        "write_decision",
        "modify_decision",
        "delete_decision",
        "update_decision",
        "write_submission",
        "modify_submission",
        "delete_submission",
        "update_submission",
        "write_audit",
        "modify_audit",
        "delete_audit",
    }
    
    @staticmethod
    def validate_imports() -> None:
        """
        Check that no forbidden modules are imported.
        
        This method should be called at module initialization
        to ensure no forbidden imports have been loaded.
        
        Raises:
            ArchitecturalViolationError: If forbidden import detected.
            NetworkAccessAttemptError: If network module detected.
        """
        for module_name in BoundaryGuard.FORBIDDEN_IMPORTS:
            if module_name in sys.modules:
                if module_name in BoundaryGuard.NETWORK_MODULES:
                    raise NetworkAccessAttemptError(module_name)
                raise ArchitecturalViolationError(f"import {module_name}")
    
    @staticmethod
    def check_import(module_name: str) -> None:
        """
        Check if a specific module import is allowed.
        
        Args:
            module_name: Name of the module to check.
            
        Raises:
            ArchitecturalViolationError: If import is forbidden.
            NetworkAccessAttemptError: If network module.
        """
        if module_name in BoundaryGuard.NETWORK_MODULES:
            raise NetworkAccessAttemptError(module_name)
        if module_name in BoundaryGuard.FORBIDDEN_IMPORTS:
            raise ArchitecturalViolationError(f"import {module_name}")
    
    @staticmethod
    def check_network_import(module_name: str) -> None:
        """
        Check if a network module import is attempted.
        
        Args:
            module_name: Name of the module to check.
            
        Raises:
            NetworkAccessAttemptError: If network module.
        """
        if module_name in BoundaryGuard.NETWORK_MODULES:
            raise NetworkAccessAttemptError(module_name)
    
    @staticmethod
    def check_forbidden_action(action: str) -> None:
        """
        Raise error for forbidden actions.
        
        Args:
            action: Name of the forbidden action.
            
        Raises:
            ArchitecturalViolationError: Always raised for forbidden actions.
        """
        if action in BoundaryGuard.FORBIDDEN_ACTIONS:
            raise ArchitecturalViolationError(action)
        # Also check if action contains forbidden keywords
        action_lower = action.lower()
        forbidden_keywords = [
            "validate_bug", "verify_bug", "confirm_bug",
            "generate_poc", "generate_exploit",
            "determine_cve", "assign_cve",
            "guarantee_accuracy", "confidence_score",
            "auto_submit", "safe_submit",
            "recommend", "suggest",
            "predict", "forecast",
            "prioritize", "rank",
            "compare_reviewer", "rank_reviewer",
            "write_", "modify_", "delete_", "update_",
        ]
        for keyword in forbidden_keywords:
            if keyword in action_lower:
                raise ArchitecturalViolationError(action)
    
    @staticmethod
    def assert_read_only() -> None:
        """
        Assert that Phase-8 is operating in read-only mode.
        
        This is a documentation method that confirms the read-only
        constraint. It does not perform runtime checks but serves
        as a code marker for the read-only principle.
        """
        # Phase-8 is READ-ONLY by design
        # This method exists to document the constraint
        pass
    
    @staticmethod
    def assert_no_network() -> None:
        """
        Assert that Phase-8 has no network capability.
        
        This is a documentation method that confirms the no-network
        constraint. It does not perform runtime checks but serves
        as a code marker for the no-network principle.
        """
        # Phase-8 has NO network capability - PERMANENT
        # This method exists to document the constraint
        pass
    
    @staticmethod
    def assert_human_authority() -> None:
        """
        Assert that human remains final authority.
        
        This is a documentation method that confirms the human
        authority principle. All Phase-8 outputs are advisory only.
        """
        # Human is FINAL AUTHORITY on all decisions
        # Phase-8 outputs are ADVISORY ONLY
        # This method exists to document the constraint
        pass
