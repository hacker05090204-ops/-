"""
Phase-4.2 Track C: Domain Allow-List - Boundary Enforcement

Enforces domain boundaries for outbound requests:
- Exact match rules
- Suffix match rules (*.example.com)
- Reject IP literals
- Reject redirect escapes

Constraints:
- No domain mutation
- No retry logic
- Fail-closed on violation
- All decisions are auditable
- Integrates ONLY with PayloadGuard
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, FrozenSet, Set
from urllib.parse import urlparse


# Patterns for detecting IP literals
IPV4_PATTERN = re.compile(
    r'^(\d{1,3}\.){3}\d{1,3}$'
)

# Patterns for detecting escape attempts
ESCAPE_PATTERNS = [
    re.compile(r'@'),           # @ sign escape
    re.compile(r'\\'),          # backslash escape
    re.compile(r'%[0-9a-fA-F]{2}'),  # URL encoding
    re.compile(r'\x00'),        # null byte
]

# Reserved/blocked domains
BLOCKED_DOMAINS: FrozenSet[str] = frozenset({
    'localhost',
    'localhost.localdomain',
    '127.0.0.1',
    '0.0.0.0',
    '::1',
    '[::1]',
})


@dataclass
class DomainCheckResult:
    """
    Result of a domain allow-list check.
    
    Attributes:
        allowed: Whether the domain is allowed
        reason: Human-readable reason for the decision
        domain: The domain that was checked
        timestamp: When the check was performed
    """
    allowed: bool
    reason: str
    domain: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for audit logging."""
        return {
            'allowed': self.allowed,
            'reason': self.reason,
            'domain': self.domain,
            'timestamp': self.timestamp.isoformat(),
        }


class DomainAllowList:
    """
    Domain boundary enforcement.
    
    Enforces:
    - Exact match rules
    - Suffix match rules (*.example.com)
    - IP literal rejection
    - Redirect escape rejection
    
    Does NOT:
    - Mutate domains
    - Retry checks
    - Mask errors
    """
    
    __slots__ = ('_exact_domains', '_wildcard_suffixes')
    
    def __init__(self, allowed_domains: List[str]) -> None:
        """
        Initialize Domain Allow-List.
        
        Args:
            allowed_domains: List of allowed domains.
                             Use *.example.com for wildcard subdomains.
        """
        self._exact_domains: Set[str] = set()
        self._wildcard_suffixes: Set[str] = set()
        
        for domain in allowed_domains:
            domain_lower = domain.lower().strip()
            if domain_lower.startswith('*.'):
                # Wildcard rule: *.example.com -> .example.com
                suffix = domain_lower[1:]  # Remove the *
                self._wildcard_suffixes.add(suffix)
            else:
                self._exact_domains.add(domain_lower)
    
    def check(self, domain: Optional[str]) -> DomainCheckResult:
        """
        Check if a domain is allowed.
        
        This method is:
        - Deterministic
        - Non-mutating
        - Fail-closed (any violation blocks)
        
        Args:
            domain: The domain to check
            
        Returns:
            DomainCheckResult with allowed status and audit information
        """
        # Fail-closed: None or empty domain
        if domain is None:
            return DomainCheckResult(
                allowed=False,
                reason="Domain is None - blocked",
                domain="<none>",
            )
        
        if not domain:
            return DomainCheckResult(
                allowed=False,
                reason="Empty domain - blocked",
                domain="<empty>",
            )
        
        domain_lower = domain.lower().strip()
        
        # Check for escape attempts
        escape_result = self._check_escape_attempts(domain_lower)
        if escape_result:
            return DomainCheckResult(
                allowed=False,
                reason=escape_result,
                domain=domain,
            )
        
        # Check for IP literals
        ip_result = self._check_ip_literal(domain_lower)
        if ip_result:
            return DomainCheckResult(
                allowed=False,
                reason=ip_result,
                domain=domain,
            )
        
        # Check for blocked domains
        if domain_lower in BLOCKED_DOMAINS:
            return DomainCheckResult(
                allowed=False,
                reason=f"Domain '{domain}' is blocked (reserved)",
                domain=domain,
            )
        
        # Check exact match
        if domain_lower in self._exact_domains:
            return DomainCheckResult(
                allowed=True,
                reason=f"Domain '{domain}' allowed (exact match)",
                domain=domain,
            )
        
        # Check wildcard suffix match
        for suffix in self._wildcard_suffixes:
            if domain_lower.endswith(suffix) and domain_lower != suffix[1:]:
                # Must be a subdomain, not the base domain itself
                return DomainCheckResult(
                    allowed=True,
                    reason=f"Domain '{domain}' allowed (wildcard match: *{suffix})",
                    domain=domain,
                )
        
        # No match found - fail closed
        return DomainCheckResult(
            allowed=False,
            reason=f"Domain '{domain}' not in allow-list",
            domain=domain,
        )
    
    def check_url(self, url: str) -> DomainCheckResult:
        """
        Extract domain from URL and check if allowed.
        
        Args:
            url: The full URL to check
            
        Returns:
            DomainCheckResult with allowed status and audit information
        """
        if not url:
            return DomainCheckResult(
                allowed=False,
                reason="Empty URL - blocked",
                domain="<empty>",
            )
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Remove port if present
            if ':' in domain:
                domain = domain.split(':')[0]
            
            # Remove userinfo if present (user:pass@host)
            if '@' in domain:
                domain = domain.split('@')[-1]
            
            return self.check(domain)
        except Exception:
            return DomainCheckResult(
                allowed=False,
                reason="Malformed URL - blocked",
                domain=url,
            )
    
    def _check_escape_attempts(self, domain: str) -> Optional[str]:
        """Check for escape attempt patterns."""
        for pattern in ESCAPE_PATTERNS:
            if pattern.search(domain):
                return f"Escape attempt detected in domain - blocked"
        return None
    
    def _check_ip_literal(self, domain: str) -> Optional[str]:
        """Check if domain is an IP literal."""
        # Check IPv4
        if IPV4_PATTERN.match(domain):
            return f"IP literal '{domain}' not allowed - use domain names"
        
        # Check IPv6 (bracketed)
        if domain.startswith('[') and domain.endswith(']'):
            return f"IPv6 literal '{domain}' not allowed - use domain names"
        
        # Check for internal IP ranges
        if self._is_internal_ip(domain):
            return f"Internal IP '{domain}' not allowed"
        
        return None
    
    def _is_internal_ip(self, domain: str) -> bool:
        """Check if domain looks like an internal IP."""
        if not IPV4_PATTERN.match(domain):
            return False
        
        try:
            parts = [int(p) for p in domain.split('.')]
            if len(parts) != 4:
                return False
            
            # 10.0.0.0/8
            if parts[0] == 10:
                return True
            
            # 172.16.0.0/12
            if parts[0] == 172 and 16 <= parts[1] <= 31:
                return True
            
            # 192.168.0.0/16
            if parts[0] == 192 and parts[1] == 168:
                return True
            
            # 127.0.0.0/8 (loopback)
            if parts[0] == 127:
                return True
            
            return False
        except (ValueError, IndexError):
            return False

