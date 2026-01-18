"""
Cyfer Brain Core Types

ARCHITECTURAL CONSTRAINTS:
    1. Hypothesis has testability_score, NOT confidence — confidence is MCP's domain
    2. Observation has NO classification field — classification is MCP's job
    3. MCPClassification is READ-ONLY from Cyfer Brain's perspective
    4. No type should allow Cyfer Brain to declare bugs or compute confidence
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Optional, List, Dict, Any
import uuid


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class HypothesisStatus(Enum):
    """Status of a hypothesis in the exploration lifecycle."""
    UNTESTED = auto()      # Hypothesis generated but not yet tested
    TESTING = auto()       # Currently being tested
    SUBMITTED = auto()     # Observation submitted to MCP, awaiting classification
    RESOLVED = auto()      # MCP has classified the observation


class ActionType(Enum):
    """Types of exploration actions."""
    HTTP_REQUEST = auto()
    STATE_MUTATION = auto()
    TOOL_EXECUTION = auto()
    AUTHENTICATION = auto()
    WORKFLOW_STEP = auto()


class ActionResult(Enum):
    """Result of an exploration action."""
    SUCCESS = auto()
    FAILURE = auto()
    TIMEOUT = auto()
    BLOCKED = auto()
    RATE_LIMITED = auto()


class BoundaryStatus(Enum):
    """Status of exploration boundaries."""
    WITHIN_BOUNDS = auto()
    APPROACHING_LIMIT = auto()
    LIMIT_REACHED = auto()
    EXCEEDED = auto()


class RateLimitStatus(Enum):
    """Rate limit status from MCP."""
    OK = auto()
    APPROACHING = auto()
    EXCEEDED = auto()
    UNKNOWN = auto()  # When MCP cannot determine status


@dataclass
class ExplorationAction:
    """Action executed by Cyfer Brain.
    
    NOTE: This captures WHAT was done, not the judgement of the result.
    Judgement is MCP's responsibility.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action_type: ActionType = ActionType.HTTP_REQUEST
    target: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    executed_at: datetime = field(default_factory=_utc_now)
    result: ActionResult = ActionResult.SUCCESS
    error_message: Optional[str] = None
    duration_ms: int = 0


@dataclass
class ToolOutput:
    """Output from a security tool.
    
    CRITICAL: Tool outputs are UNTRUSTED signals.
    Even if a tool claims to find a "vulnerability", it is only a hypothesis
    until MCP validates it through invariant checking and proof generation.
    """
    tool_name: str
    raw_output: str
    parsed_findings: List[Dict[str, Any]] = field(default_factory=list)
    exit_code: int = 0
    execution_time_ms: int = 0
    # NOTE: No "is_vulnerability" field — that's MCP's determination


@dataclass
class Observation:
    """Observation submitted to MCP for classification.
    
    ARCHITECTURAL CONSTRAINT:
        This dataclass has NO classification field.
        Classification is MCP's responsibility, not Cyfer Brain's.
        
    The observation captures:
        - before_state: State before the action
        - action: What was done
        - after_state: State after the action
        - tool_outputs: Any tool outputs (untrusted signals)
        
    MCP will:
        - Validate against invariants
        - Generate proof if violation found
        - Return classification (BUG/SIGNAL/NO_ISSUE/COVERAGE_GAP)
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    hypothesis_id: str = ""
    before_state: Dict[str, Any] = field(default_factory=dict)
    action: ExplorationAction = field(default_factory=ExplorationAction)
    after_state: Dict[str, Any] = field(default_factory=dict)
    tool_outputs: List[ToolOutput] = field(default_factory=list)
    timestamp: datetime = field(default_factory=_utc_now)
    # NOTE: NO classification field — that's MCP's job


@dataclass
class MCPClassification:
    """Classification returned by MCP.
    
    ARCHITECTURAL CONSTRAINT:
        This is READ-ONLY from Cyfer Brain's perspective.
        Cyfer Brain MUST NOT modify, override, or reinterpret these values.
        
    Fields:
        - classification: The authoritative judgement from MCP
        - invariant_violated: Which invariant was violated (if BUG)
        - proof: The formal proof of violation (if BUG)
        - confidence: Computed by MCP, NOT by Cyfer Brain
        - coverage_gaps: Areas where MCP couldn't validate
    """
    observation_id: str
    classification: str  # BUG | SIGNAL | NO_ISSUE | COVERAGE_GAP
    invariant_violated: Optional[str] = None
    proof: Optional[Dict[str, Any]] = None
    confidence: float = 0.0  # Computed by MCP, not Cyfer Brain
    coverage_gaps: List[str] = field(default_factory=list)
    
    def is_bug(self) -> bool:
        """Check if MCP classified this as a proven bug."""
        return self.classification == "BUG"
    
    def is_signal(self) -> bool:
        """Check if MCP classified this as an interesting signal."""
        return self.classification == "SIGNAL"
    
    def is_no_issue(self) -> bool:
        """Check if MCP classified this as not an issue."""
        return self.classification == "NO_ISSUE"
    
    def is_coverage_gap(self) -> bool:
        """Check if MCP reported a coverage gap."""
        return self.classification == "COVERAGE_GAP"


@dataclass
class Hypothesis:
    """A testable security hypothesis.
    
    ARCHITECTURAL CONSTRAINTS:
        1. testability_score is NOT a confidence score — it measures ease of testing
        2. mcp_classification is set by MCP, NEVER by Cyfer Brain
        3. Hypotheses are NEVER marked as confirmed vulnerabilities by Cyfer Brain
        
    Cyfer Brain generates hypotheses; MCP judges them.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    target_invariant_categories: List[str] = field(default_factory=list)
    test_actions: List[ExplorationAction] = field(default_factory=list)
    testability_score: float = 0.5  # NOT confidence — measures ease of testing only
    status: HypothesisStatus = HypothesisStatus.UNTESTED
    mcp_classification: Optional[MCPClassification] = None  # Set by MCP, never by Cyfer Brain
    created_at: datetime = field(default_factory=_utc_now)
    tested_at: Optional[datetime] = None
    # NOTE: No "is_vulnerability" or "confidence" field — those are MCP's domain


@dataclass
class ExplorationBoundary:
    """Boundaries for exploration.
    
    These limits prevent runaway exploration and ensure resource efficiency.
    """
    max_depth: int = 10
    max_breadth: int = 100
    max_time_seconds: int = 3600
    max_actions: int = 1000
    max_mcp_submissions: int = 500


@dataclass
class ExplorationStats:
    """Statistics for an exploration session.
    
    NOTE: bugs_found counts MCP BUG classifications, not Cyfer Brain guesses.
    """
    hypotheses_generated: int = 0
    hypotheses_tested: int = 0
    observations_submitted: int = 0
    bugs_found: int = 0  # Count of MCP BUG classifications
    signals_found: int = 0
    no_issues: int = 0
    coverage_gaps: int = 0
    time_elapsed_seconds: float = 0.0
    actions_executed: int = 0
    retries_attempted: int = 0
    errors_encountered: int = 0


@dataclass
class ExplorationSummary:
    """Summary of what was explored.
    
    ARCHITECTURAL CONSTRAINT:
        This is an EXPLORATION summary, NOT a coverage report.
        MCP's CoverageReport is authoritative for invariant coverage.
        This summary only reports what Cyfer Brain explored.
        
    CRITICAL: This summary does NOT claim completeness.
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target: str = ""
    stats: ExplorationStats = field(default_factory=ExplorationStats)
    hypotheses_tested: List[str] = field(default_factory=list)
    strategies_used: List[str] = field(default_factory=list)
    boundary_status: BoundaryStatus = BoundaryStatus.WITHIN_BOUNDS
    stopped_reason: str = ""
    started_at: datetime = field(default_factory=_utc_now)
    completed_at: Optional[datetime] = None
    # NOTE: No "coverage_percentage" — we don't claim completeness


@dataclass
class ScopeValidation:
    """Result of scope validation from MCP."""
    target: str
    is_in_scope: bool
    reason: str = ""
    warnings: List[str] = field(default_factory=list)
