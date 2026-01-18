"""
MCP Client - Read-Only Interface to MCP (Phase-1 Truth Engine)

ARCHITECTURAL CONSTRAINTS:
    1. This client is READ-ONLY for MCP state
    2. It can only SUBMIT observations and RECEIVE classifications
    3. It CANNOT classify findings, generate proofs, or compute confidence
    4. Any attempt to perform MCP responsibilities raises ArchitecturalViolationError
    5. If MCP is unavailable, raise MCPUnavailableError (HARD STOP)
"""

from typing import Optional, Set
import logging

from .types import (
    Observation,
    MCPClassification,
    ScopeValidation,
    RateLimitStatus,
)
from .errors import (
    MCPUnavailableError,
    MCPCommunicationError,
    ArchitecturalViolationError,
)

logger = logging.getLogger(__name__)


class ObservationSubmissionGuard:
    """Ensures observations are submitted to MCP before any reaction.
    
    ARCHITECTURAL CONSTRAINT:
        Cyfer Brain MUST NOT react to observations until MCP has classified them.
        This guard tracks pending observations and blocks reactions until
        MCP classification is received.
    """
    
    def __init__(self, mcp_client: 'MCPClient'):
        self._client = mcp_client
        self._pending: Set[str] = set()
    
    def register_observation(self, observation: Observation) -> None:
        """Register observation as pending MCP submission."""
        self._pending.add(observation.id)
        logger.debug(f"Registered pending observation: {observation.id}")
    
    def submit_and_clear(self, observation: Observation) -> MCPClassification:
        """Submit to MCP and clear from pending.
        
        CRITICAL: This blocks reaction until MCP responds.
        
        Raises:
            MCPUnavailableError: If MCP is unreachable (HARD STOP)
            MCPCommunicationError: If communication fails
        """
        if observation.id not in self._pending:
            logger.warning(f"Observation {observation.id} was not registered as pending")
        
        classification = self._client.submit_observation(observation)
        self._pending.discard(observation.id)
        logger.debug(f"Cleared pending observation: {observation.id}")
        return classification
    
    def has_pending(self) -> bool:
        """Check if there are unsubmitted observations."""
        return len(self._pending) > 0
    
    def pending_count(self) -> int:
        """Get count of pending observations."""
        return len(self._pending)
    
    def clear_all(self) -> None:
        """Clear all pending observations (use with caution)."""
        self._pending.clear()


class MCPClient:
    """Read-only interface to MCP (Phase-1 Truth Engine).
    
    ARCHITECTURAL CONSTRAINTS:
        1. Can only submit observations and receive classifications
        2. Cannot classify findings — that's MCP's responsibility
        3. Cannot generate proofs — that's MCP's responsibility
        4. Cannot compute confidence — that's MCP's responsibility
        5. Cannot override classifications — architectural violation
        
    If MCP is unavailable, this client raises MCPUnavailableError,
    which causes a HARD STOP. Cyfer Brain cannot operate without MCP.
    """
    
    def __init__(self, mcp_server=None):
        """Initialize MCP client.
        
        Args:
            mcp_server: Reference to MCP server (from kali_mcp.server)
        """
        self._mcp_server = mcp_server
        self._is_available = mcp_server is not None
    
    def submit_observation(self, observation: Observation) -> MCPClassification:
        """Submit observation to MCP for classification.
        
        CRITICAL: This is the ONLY way findings are classified.
        Cyfer Brain submits; MCP judges.
        
        Args:
            observation: The observation to classify
            
        Returns:
            MCPClassification with:
                - classification: BUG | SIGNAL | NO_ISSUE | COVERAGE_GAP
                - invariant_violated: str (if BUG)
                - proof: Proof (if BUG)
                - confidence: float (computed by MCP, not Cyfer Brain)
                
        Raises:
            MCPUnavailableError: If MCP is unreachable (HARD STOP)
            MCPCommunicationError: If communication fails
        """
        if not self._is_available:
            raise MCPUnavailableError(
                "MCP is not available. Cyfer Brain cannot operate without MCP. "
                "HARD STOP: Do not continue exploration."
            )
        
        try:
            logger.info(f"Submitting observation {observation.id} to MCP")
            
            # REAL MCP INTEGRATION: Call MCP's validation pipeline
            # The MCP server MUST implement validate_observation()
            if not hasattr(self._mcp_server, 'validate_observation'):
                raise MCPUnavailableError(
                    "MCP server does not implement validate_observation(). "
                    "HARD STOP: Cannot classify without MCP."
                )
            
            result = self._mcp_server.validate_observation(observation)
            
            # Validate MCP response structure
            if result is None:
                raise MCPCommunicationError(
                    "MCP returned None for observation classification. "
                    "HARD STOP: Invalid MCP response."
                )
            
            # If MCP returns a dict, convert to MCPClassification
            if isinstance(result, dict):
                return MCPClassification(
                    observation_id=observation.id,
                    classification=result.get("classification"),
                    invariant_violated=result.get("invariant_violated"),
                    proof=result.get("proof"),
                    confidence=result.get("confidence", 0.0),
                    coverage_gaps=result.get("coverage_gaps", []),
                )
            
            # If MCP returns MCPClassification directly, use it
            if isinstance(result, MCPClassification):
                return result
            
            raise MCPCommunicationError(
                f"MCP returned unexpected type: {type(result).__name__}. "
                "Expected MCPClassification or dict."
            )
            
        except MCPUnavailableError:
            raise
        except MCPCommunicationError:
            raise
        except Exception as e:
            logger.error(f"MCP communication error: {e}")
            raise MCPCommunicationError(f"Failed to communicate with MCP: {e}")
    
    def get_coverage_report(self) -> dict:
        """Get MCP's authoritative coverage report to guide exploration.
        
        Returns:
            MCP's coverage report showing which invariants have been tested
            
        Raises:
            MCPUnavailableError: If MCP is unreachable
            MCPCommunicationError: If MCP does not implement coverage reporting
        """
        if not self._is_available:
            raise MCPUnavailableError("MCP is not available")
        
        # REAL MCP INTEGRATION: Query MCP's coverage tracker
        if not hasattr(self._mcp_server, 'get_coverage_report'):
            raise MCPCommunicationError(
                "MCP server does not implement get_coverage_report(). "
                "Cannot retrieve coverage data."
            )
        
        result = self._mcp_server.get_coverage_report()
        
        if result is None:
            raise MCPCommunicationError(
                "MCP returned None for coverage report. Invalid response."
            )
        
        return result
    
    def validate_scope(self, target: str) -> ScopeValidation:
        """Check if target is in scope.
        
        DELEGATES to MCP Rule Engine — Cyfer Brain does not make scope decisions.
        
        Args:
            target: The target to validate
            
        Returns:
            ScopeValidation with is_in_scope and reason
            
        Raises:
            MCPUnavailableError: If MCP is unreachable
            MCPCommunicationError: If MCP does not implement scope validation
        """
        if not self._is_available:
            raise MCPUnavailableError("MCP is not available")
        
        # REAL MCP INTEGRATION: Delegate to MCP's Rule Engine
        if not hasattr(self._mcp_server, 'validate_scope'):
            raise MCPCommunicationError(
                "MCP server does not implement validate_scope(). "
                "Cannot validate target scope."
            )
        
        result = self._mcp_server.validate_scope(target)
        
        if result is None:
            raise MCPCommunicationError(
                "MCP returned None for scope validation. Invalid response."
            )
        
        # If MCP returns a dict, convert to ScopeValidation
        if isinstance(result, dict):
            return ScopeValidation(
                target=target,
                is_in_scope=result.get("is_in_scope", False),
                reason=result.get("reason", "Unknown"),
            )
        
        # If MCP returns ScopeValidation directly, use it
        if isinstance(result, ScopeValidation):
            return result
        
        raise MCPCommunicationError(
            f"MCP returned unexpected type for scope validation: {type(result).__name__}"
        )
    
    def check_rate_limit(self) -> RateLimitStatus:
        """Check rate limit status.
        
        DELEGATES to MCP Rule Engine — Cyfer Brain does not track rate limits.
        
        Returns:
            RateLimitStatus indicating current rate limit state
            
        Raises:
            MCPUnavailableError: If MCP is unreachable
            MCPCommunicationError: If MCP does not implement rate limit checking
        """
        if not self._is_available:
            raise MCPUnavailableError("MCP is not available")
        
        # REAL MCP INTEGRATION: Delegate to MCP's Rule Engine
        if not hasattr(self._mcp_server, 'check_rate_limit'):
            raise MCPCommunicationError(
                "MCP server does not implement check_rate_limit(). "
                "Cannot check rate limit status."
            )
        
        result = self._mcp_server.check_rate_limit()
        
        if result is None:
            raise MCPCommunicationError(
                "MCP returned None for rate limit check. Invalid response."
            )
        
        # If MCP returns a string, convert to RateLimitStatus
        if isinstance(result, str):
            try:
                return RateLimitStatus(result)
            except ValueError:
                return RateLimitStatus.UNKNOWN
        
        # If MCP returns RateLimitStatus directly, use it
        if isinstance(result, RateLimitStatus):
            return result
        
        raise MCPCommunicationError(
            f"MCP returned unexpected type for rate limit: {type(result).__name__}"
        )
    
    # =========================================================================
    # EXPLICITLY REJECTED METHODS
    # These methods raise ArchitecturalViolationError because they attempt
    # to perform MCP responsibilities from Cyfer Brain.
    # =========================================================================
    
    def classify_finding(self, *args, **kwargs):
        """REJECTED: Classification is MCP's responsibility.
        
        Raises:
            ArchitecturalViolationError: Always
        """
        raise ArchitecturalViolationError(
            "classify a finding",
            "Submit observations to MCP via submit_observation() instead."
        )
    
    def generate_proof(self, *args, **kwargs):
        """REJECTED: Proof generation is MCP's responsibility.
        
        Raises:
            ArchitecturalViolationError: Always
        """
        raise ArchitecturalViolationError(
            "generate a proof",
            "MCP generates proofs when it classifies observations as BUG."
        )
    
    def compute_confidence(self, *args, **kwargs):
        """REJECTED: Confidence computation is MCP's responsibility.
        
        Raises:
            ArchitecturalViolationError: Always
        """
        raise ArchitecturalViolationError(
            "compute confidence",
            "Confidence is computed by MCP, not Cyfer Brain."
        )
    
    def override_classification(self, *args, **kwargs):
        """REJECTED: Overriding MCP classifications is an architectural violation.
        
        Raises:
            ArchitecturalViolationError: Always
        """
        raise ArchitecturalViolationError(
            "override MCP classification",
            "MCP classifications are authoritative and cannot be overridden."
        )
    
    def auto_submit_report(self, *args, **kwargs):
        """REJECTED: Auto-submitting reports is not allowed.
        
        Only MCP-proven bugs can be reported, and report submission
        requires human review.
        
        Raises:
            ArchitecturalViolationError: Always
        """
        raise ArchitecturalViolationError(
            "auto-submit a report",
            "Only MCP-proven bugs can be reported, and submission requires human review."
        )
