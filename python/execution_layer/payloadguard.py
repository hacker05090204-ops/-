"""
Phase-4.2 Track B: PayloadGuard - Egress Request Firewall

Prevents unsafe outbound requests with:
- HTTPS-only enforcement
- Method allow-list
- Header allow-list (blocks spoofing headers)

Constraints:
- No payload mutation
- No header spoofing
- No retry logic
- Fail-closed on violation
- All decisions are auditable
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, FrozenSet
from urllib.parse import urlparse


# Default allowed HTTP methods (safe methods only)
DEFAULT_ALLOWED_METHODS: FrozenSet[str] = frozenset({
    'GET', 'POST', 'HEAD', 'OPTIONS'
})

# Headers that are forbidden (spoofing/security risk)
FORBIDDEN_HEADERS: FrozenSet[str] = frozenset({
    'host',
    'x-forwarded-for',
    'x-real-ip',
    'x-forwarded-host',
    'x-forwarded-proto',
    'x-original-url',
    'x-rewrite-url',
    'forwarded',
    'via',
    'x-client-ip',
    'client-ip',
    'true-client-ip',
    'cf-connecting-ip',
    'x-cluster-client-ip',
})


@dataclass(frozen=True)
class RequestSpec:
    """
    Immutable specification of an outbound request.
    
    Attributes:
        url: The target URL
        method: HTTP method (GET, POST, etc.)
        headers: Request headers
    """
    url: str
    method: str
    headers: Dict[str, str]


@dataclass
class CheckResult:
    """
    Result of a PayloadGuard check.
    
    Attributes:
        allowed: Whether the request is allowed
        reason: Human-readable reason for the decision
        violations: List of specific violations found
        timestamp: When the check was performed
    """
    allowed: bool
    reason: str
    violations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for audit logging."""
        return {
            'allowed': self.allowed,
            'reason': self.reason,
            'violations': self.violations,
            'timestamp': self.timestamp.isoformat(),
        }


class PayloadGuard:
    """
    Egress request firewall.
    
    Enforces:
    - HTTPS-only URLs
    - Method allow-list
    - Header allow-list (blocks spoofing headers)
    
    Does NOT:
    - Mutate payloads
    - Retry requests
    - Mask errors
    """
    
    __slots__ = ('_allowed_methods',)
    
    def __init__(
        self,
        allowed_methods: Optional[FrozenSet[str]] = None
    ) -> None:
        """
        Initialize PayloadGuard.
        
        Args:
            allowed_methods: Set of allowed HTTP methods (defaults to safe methods)
        """
        self._allowed_methods = allowed_methods or DEFAULT_ALLOWED_METHODS
    
    def check(self, spec: RequestSpec) -> CheckResult:
        """
        Check if a request is allowed.
        
        This method is:
        - Deterministic
        - Non-mutating
        - Fail-closed (any violation blocks)
        
        Args:
            spec: The request specification to check
            
        Returns:
            CheckResult with allowed status and audit information
        """
        violations: List[str] = []
        
        # Check URL validity and protocol
        url_violations = self._check_url(spec.url)
        violations.extend(url_violations)
        
        # Check HTTP method
        method_violations = self._check_method(spec.method)
        violations.extend(method_violations)
        
        # Check headers for spoofing attempts
        header_violations = self._check_headers(spec.headers)
        violations.extend(header_violations)
        
        # Fail-closed: any violation blocks the request
        if violations:
            return CheckResult(
                allowed=False,
                reason=f"Request blocked: {'; '.join(violations)}",
                violations=violations,
            )
        
        return CheckResult(
            allowed=True,
            reason="Request allowed",
            violations=[],
        )
    
    def _check_url(self, url: str) -> List[str]:
        """Check URL for violations."""
        violations: List[str] = []
        
        # Empty URL
        if not url:
            violations.append("Empty URL not allowed")
            return violations
        
        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception:
            violations.append("Malformed URL")
            return violations
        
        # Must have scheme
        if not parsed.scheme:
            violations.append("URL must have scheme (https required)")
            return violations
        
        # HTTPS only
        if parsed.scheme.lower() != 'https':
            violations.append(f"Only HTTPS allowed, got: {parsed.scheme}")
        
        # Must have netloc (host)
        if not parsed.netloc:
            violations.append("URL must have host")
        
        return violations
    
    def _check_method(self, method: str) -> List[str]:
        """Check HTTP method for violations."""
        violations: List[str] = []
        
        if not method:
            violations.append("Empty HTTP method not allowed")
            return violations
        
        method_upper = method.upper()
        if method_upper not in self._allowed_methods:
            violations.append(
                f"HTTP method '{method}' not allowed. "
                f"Allowed: {', '.join(sorted(self._allowed_methods))}"
            )
        
        return violations
    
    def _check_headers(self, headers: Dict[str, str]) -> List[str]:
        """Check headers for spoofing attempts."""
        violations: List[str] = []
        
        for header_name in headers:
            if header_name.lower() in FORBIDDEN_HEADERS:
                violations.append(
                    f"Forbidden header '{header_name}' - potential spoofing"
                )
        
        return violations
