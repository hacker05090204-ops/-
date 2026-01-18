"""
Phase-6 Boundary Guard

Enforces architectural constraints via forbidden method stubs.
All forbidden methods raise ArchitecturalViolationError.

FORBIDDEN ACTIONS:
- auto_classify() — MCP's responsibility
- auto_severity() — Human's responsibility
- auto_submit() — Human's responsibility
- trigger_execution() — Phase-4's responsibility
- trigger_scan() — Phase-5's responsibility
- make_network_request() — FORBIDDEN (offline principle)
"""

from __future__ import annotations
from typing import NoReturn

from decision_workflow.errors import ArchitecturalViolationError


class BoundaryGuard:
    """
    Enforces Phase-6 architectural boundaries.
    
    All methods in this class are forbidden and will raise
    ArchitecturalViolationError when called. They exist as
    explicit documentation of what Phase-6 cannot do.
    """
    
    def auto_classify(self) -> NoReturn:
        """
        FORBIDDEN: Auto-classification is MCP's responsibility.
        
        Phase-6 displays MCP classifications but never generates them.
        
        Raises:
            ArchitecturalViolationError: Always.
        """
        raise ArchitecturalViolationError("auto_classify")
    
    def auto_severity(self) -> NoReturn:
        """
        FORBIDDEN: Auto-severity assignment is forbidden.
        
        Severity must be assigned by a human Reviewer.
        
        Raises:
            ArchitecturalViolationError: Always.
        """
        raise ArchitecturalViolationError("auto_severity")
    
    def auto_submit(self) -> NoReturn:
        """
        FORBIDDEN: Auto-submission is forbidden.
        
        Report submission must be initiated by a human.
        
        Raises:
            ArchitecturalViolationError: Always.
        """
        raise ArchitecturalViolationError("auto_submit")
    
    def trigger_execution(self) -> NoReturn:
        """
        FORBIDDEN: Triggering execution is Phase-4's responsibility.
        
        Phase-6 cannot trigger browser actions or replay attacks.
        
        Raises:
            ArchitecturalViolationError: Always.
        """
        raise ArchitecturalViolationError("trigger_execution")
    
    def trigger_scan(self) -> NoReturn:
        """
        FORBIDDEN: Triggering scans is Phase-5's responsibility.
        
        Phase-6 cannot trigger artifact scanning.
        
        Raises:
            ArchitecturalViolationError: Always.
        """
        raise ArchitecturalViolationError("trigger_scan")
    
    def make_network_request(self) -> NoReturn:
        """
        FORBIDDEN: Network requests violate the offline principle.
        
        Phase-6 operates offline (except audit log persistence).
        
        Raises:
            ArchitecturalViolationError: Always.
        """
        raise ArchitecturalViolationError("make_network_request")
