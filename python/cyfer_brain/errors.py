"""
Cyfer Brain Error Hierarchy

ARCHITECTURAL CONSTRAINT:
    ArchitecturalViolationError and MCPUnavailableError cause HARD STOP.
    These errors indicate fundamental violations that cannot be recovered from.
"""


class CyferBrainError(Exception):
    """Base error for all Cyfer Brain errors."""
    pass


class ExplorationError(CyferBrainError):
    """Error during exploration action execution.
    
    This error is recoverable — retry with variations or skip and continue.
    """
    pass


class BoundaryExceededError(CyferBrainError):
    """Exploration boundary exceeded.
    
    This error indicates exploration should stop gracefully.
    Generate exploration summary and report what was explored.
    """
    pass


class MCPCommunicationError(CyferBrainError):
    """Error communicating with MCP.
    
    This error may be transient — retry with backoff.
    If persistent, escalate to MCPUnavailableError.
    """
    pass


class MCPUnavailableError(CyferBrainError):
    """MCP is unreachable — HARD STOP.
    
    CRITICAL: Do not continue exploration without MCP.
    Cyfer Brain cannot make judgements; it can only submit observations.
    Without MCP, no classifications can be made.
    
    This error is NOT recoverable. Exploration must stop immediately.
    """
    pass


class ArchitecturalViolationError(CyferBrainError):
    """Attempted to perform MCP responsibility — HARD STOP.
    
    CRITICAL: This error indicates a fundamental architectural violation.
    Cyfer Brain attempted to:
        - Classify a finding (MCP's responsibility)
        - Generate a proof (MCP's responsibility)
        - Compute confidence (MCP's responsibility)
        - Override MCP classification (architectural violation)
        - Auto-submit a report (only MCP-proven bugs can be reported)
    
    This error is NOT recoverable. The system must stop and be audited.
    """
    
    def __init__(self, attempted_action: str, message: str = ""):
        self.attempted_action = attempted_action
        full_message = (
            f"ARCHITECTURAL VIOLATION: Cyfer Brain attempted to {attempted_action}. "
            f"This is MCP's responsibility. {message}"
        )
        super().__init__(full_message)
