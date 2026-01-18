"""
Phase-8 Error Hierarchy

All errors for the Read-Only Intelligence Layer.

ERROR POLICY:
- ArchitecturalViolationError: HARD STOP - code fix required
- NetworkAccessAttemptError: HARD STOP - code fix required
- DataNotFoundError: Recoverable - return empty result
- InsufficientDataError: Recoverable - return partial result
- InvalidQueryError: Recoverable - return error message

Phase-8 MUST NOT block any workflow:
- Missing data → Return empty/partial result
- Analysis failure → Return error message, don't block
- Pattern not found → Return "no pattern detected"
"""

from __future__ import annotations


class IntelligenceLayerError(Exception):
    """Base error for Phase-8 Intelligence Layer."""
    pass


class ArchitecturalViolationError(IntelligenceLayerError):
    """
    Forbidden action attempted — HARD STOP.
    
    Raised when code attempts to:
    - Import forbidden modules (execution_layer, artifact_scanner, network libs)
    - Write to Phase-6 or Phase-7 data
    - Make network requests
    - Perform automated actions
    - Validate bugs
    - Generate PoCs
    - Make recommendations
    - Make predictions
    
    This error requires a code fix to resolve.
    """
    
    def __init__(self, action: str):
        self.action = action
        super().__init__(
            f"Architectural violation: '{action}' is forbidden in Phase-8. "
            f"Phase-8 is READ-ONLY with NO automation, NO validation, NO recommendations."
        )


class NetworkAccessAttemptError(IntelligenceLayerError):
    """
    Network access attempted — HARD STOP.
    
    Raised when code attempts to:
    - Import network modules (httpx, requests, aiohttp, socket, urllib.request)
    - Make any network connection
    - Open any socket
    
    Network access is PERMANENTLY DISABLED in Phase-8.
    This error requires a code fix to resolve.
    """
    
    def __init__(self, module: str):
        self.module = module
        super().__init__(
            f"Network access forbidden: attempted to use '{module}'. "
            f"Phase-8 has NO network capability - this is PERMANENT."
        )


class DataNotFoundError(IntelligenceLayerError):
    """
    Referenced data not found.
    
    This is a recoverable error. The caller should handle this
    by returning an empty result or displaying "no data found".
    
    Phase-8 MUST NOT block workflows due to missing data.
    """
    
    def __init__(self, data_type: str, identifier: str):
        self.data_type = data_type
        self.identifier = identifier
        super().__init__(f"{data_type} not found: {identifier}")


class InsufficientDataError(IntelligenceLayerError):
    """
    Not enough data for meaningful analysis.
    
    This is a recoverable error. The caller should handle this
    by returning a partial result with a note about limited data.
    
    Phase-8 MUST NOT block workflows due to insufficient data.
    """
    
    def __init__(self, required: int, available: int):
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient data: need {required}, have {available}. "
            f"Results may be limited."
        )


class InvalidQueryError(IntelligenceLayerError):
    """
    Malformed query parameters.
    
    This is a recoverable error. The caller should handle this
    by returning an error message to the user.
    
    Phase-8 MUST NOT block workflows due to invalid queries.
    """
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(f"Invalid query: {message}")
