"""
Phase-4.2 Track D: Policy Engine - Policy-Driven Execution Constraints

Provides policy-driven execution constraints:
- Immutable Policy model
- Single evaluation per execution
- Max requests enforcement
- Allowed domains enforcement
- Allowed methods enforcement

Constraints:
- No dynamic branching
- No runtime changes
- No retry logic
- All decisions are auditable
- Deterministic evaluation
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple, Set


@dataclass(frozen=True)
class Policy:
    """
    Immutable policy model for execution constraints.
    
    Once created, a Policy cannot be modified. This ensures
    deterministic evaluation and prevents runtime policy changes.
    
    Attributes:
        max_requests: Maximum number of requests allowed per execution
        allowed_domains: List of allowed domains (supports *.example.com wildcards)
        allowed_methods: List of allowed HTTP methods
    """
    max_requests: int
    allowed_domains: Tuple[str, ...]
    allowed_methods: Tuple[str, ...]
    
    def __init__(
        self,
        max_requests: int,
        allowed_domains: List[str],
        allowed_methods: List[str]
    ) -> None:
        """
        Initialize Policy with immutable fields.
        
        Args:
            max_requests: Maximum number of requests allowed
            allowed_domains: List of allowed domains
            allowed_methods: List of allowed HTTP methods
        """
        # Use object.__setattr__ because dataclass is frozen
        object.__setattr__(self, 'max_requests', max_requests)
        object.__setattr__(self, 'allowed_domains', tuple(allowed_domains))
        object.__setattr__(self, 'allowed_methods', tuple(m.upper() for m in allowed_methods))
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for audit logging."""
        return {
            'max_requests': self.max_requests,
            'allowed_domains': list(self.allowed_domains),
            'allowed_methods': list(self.allowed_methods),
        }


@dataclass
class PolicyEvaluationResult:
    """
    Result of a policy evaluation.
    
    Attributes:
        allowed: Whether the request is allowed
        reason: Human-readable reason for the decision
        request_number: The request number in this execution
        timestamp: When the evaluation was performed
    """
    allowed: bool
    reason: str
    request_number: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for audit logging."""
        return {
            'allowed': self.allowed,
            'reason': self.reason,
            'request_number': self.request_number,
            'timestamp': self.timestamp.isoformat(),
        }


class PolicyEvaluator:
    """
    Policy evaluator for execution constraints.
    
    Enforces:
    - Max requests per execution
    - Domain allow-list
    - Method allow-list
    
    Does NOT:
    - Allow policy changes at runtime
    - Retry evaluations
    - Mask errors
    - Branch dynamically
    """
    
    __slots__ = ('_policy', '_request_count', '_exact_domains', '_wildcard_suffixes', '_allowed_methods')
    
    def __init__(self, policy: Policy) -> None:
        """
        Initialize PolicyEvaluator with immutable policy.
        
        Args:
            policy: The Policy to enforce
        """
        self._policy = policy
        self._request_count = 0
        
        # Pre-process domains for efficient matching
        self._exact_domains: Set[str] = set()
        self._wildcard_suffixes: Set[str] = set()
        
        for domain in policy.allowed_domains:
            domain_lower = domain.lower().strip()
            if domain_lower.startswith('*.'):
                # Wildcard rule: *.example.com -> .example.com
                suffix = domain_lower[1:]  # Remove the *
                self._wildcard_suffixes.add(suffix)
            else:
                self._exact_domains.add(domain_lower)
        
        # Pre-process methods for efficient matching
        self._allowed_methods: Set[str] = set(m.upper() for m in policy.allowed_methods)
    
    @property
    def request_count(self) -> int:
        """Get current request count."""
        return self._request_count
    
    @property
    def policy(self) -> Policy:
        """Get the policy (read-only access for audit)."""
        return self._policy
    
    def evaluate_request(
        self,
        domain: str,
        method: str
    ) -> PolicyEvaluationResult:
        """
        Evaluate a request against the policy.
        
        This method is:
        - Deterministic
        - Non-mutating (except request count)
        - Fail-closed
        
        Args:
            domain: The target domain
            method: The HTTP method
            
        Returns:
            PolicyEvaluationResult with allowed status and audit information
        """
        # Increment request count first (fail-closed)
        self._request_count += 1
        current_request = self._request_count
        
        # Check max requests
        if current_request > self._policy.max_requests:
            return PolicyEvaluationResult(
                allowed=False,
                reason=f"Max requests exceeded ({current_request}/{self._policy.max_requests})",
                request_number=current_request,
            )
        
        # Check method
        method_upper = method.upper()
        if method_upper not in self._allowed_methods:
            return PolicyEvaluationResult(
                allowed=False,
                reason=f"Method '{method}' not allowed by policy",
                request_number=current_request,
            )
        
        # Check domain
        domain_lower = domain.lower().strip()
        
        # Check exact match
        if domain_lower in self._exact_domains:
            return PolicyEvaluationResult(
                allowed=True,
                reason=f"Request {current_request} allowed (domain exact match)",
                request_number=current_request,
            )
        
        # Check wildcard suffix match
        for suffix in self._wildcard_suffixes:
            if domain_lower.endswith(suffix) and domain_lower != suffix[1:]:
                return PolicyEvaluationResult(
                    allowed=True,
                    reason=f"Request {current_request} allowed (domain wildcard match)",
                    request_number=current_request,
                )
        
        # Domain not allowed
        return PolicyEvaluationResult(
            allowed=False,
            reason=f"Domain '{domain}' not allowed by policy",
            request_number=current_request,
        )

