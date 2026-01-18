"""
Phase-4.2 Track A: ScanMode - Execution Mode Enforcement

Provides execution modes for preventive hardening:
- PASSIVE: Observe only, no blocking
- SAFE_ACTIVE: Enforce PayloadGuard & Domain Allow-List

Constraints:
- ScanMode does NOT retry
- ScanMode does NOT modify browser flow
- ScanMode does NOT mask errors
- ScanContext is immutable (frozen dataclass)
- ScanModeEvaluator is read-only
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any


class ScanMode(Enum):
    """
    Execution mode enumeration.
    
    PASSIVE: Observe only, no blocking. All requests are allowed.
    SAFE_ACTIVE: Enforce PayloadGuard and Domain Allow-List.
    """
    PASSIVE = 'passive'
    SAFE_ACTIVE = 'safe_active'


@dataclass(frozen=True)
class ScanContext:
    """
    Immutable execution context for a single execution.
    
    Created once per execution and cannot be modified.
    Contains the scan mode and execution identifier for audit trail.
    
    Attributes:
        mode: The ScanMode for this execution
        execution_id: Unique identifier for this execution (for audit)
    """
    mode: ScanMode
    execution_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize context to dictionary for audit logging.
        
        Returns:
            Dictionary representation of the context
        """
        return {
            'mode': self.mode.value,
            'execution_id': self.execution_id,
        }
    
    def __repr__(self) -> str:
        """Readable representation for logging."""
        return f"ScanContext(mode={self.mode.name}, execution_id='{self.execution_id}')"


class ScanModeEvaluator:
    """
    Read-only evaluator for ScanMode decisions.
    
    This class evaluates whether guards should be enforced based on
    the ScanContext. It is intentionally minimal and read-only:
    - No retry logic
    - No error masking
    - No state mutation
    - No network calls
    - No file I/O
    - Deterministic evaluation
    """
    
    __slots__ = ('_context',)
    
    def __init__(self, context: ScanContext) -> None:
        """
        Initialize evaluator with immutable context.
        
        Args:
            context: The ScanContext for this execution
        """
        self._context = context
    
    @property
    def context(self) -> ScanContext:
        """
        Access the underlying context for audit purposes.
        
        Returns:
            The immutable ScanContext
        """
        return self._context
    
    def should_enforce_guards(self) -> bool:
        """
        Determine if PayloadGuard and Domain Allow-List should be enforced.
        
        Returns:
            True if guards should be enforced (SAFE_ACTIVE mode)
            False if guards should not be enforced (PASSIVE mode)
        """
        return self._context.mode == ScanMode.SAFE_ACTIVE
