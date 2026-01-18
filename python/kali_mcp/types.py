"""
Core type definitions for the Kali MCP Toolkit Python layer.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional, List, Dict, Set, Any
import uuid


class Severity(Enum):
    """Severity levels for findings."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    def cvss_range(self) -> tuple[float, float]:
        """Get CVSS score range for this severity."""
        ranges = {
            Severity.INFO: (0.0, 0.0),
            Severity.LOW: (0.1, 3.9),
            Severity.MEDIUM: (4.0, 6.9),
            Severity.HIGH: (7.0, 8.9),
            Severity.CRITICAL: (9.0, 10.0),
        }
        return ranges[self]


class FindingClassification(Enum):
    """Classification of findings."""
    BUG = "bug"
    SIGNAL = "signal"
    NO_ISSUE = "no_issue"
    COVERAGE_GAP = "coverage_gap"


class HuntPhase(Enum):
    """Phases of a bug bounty hunt."""
    RECONNAISSANCE = auto()
    SCANNING = auto()
    EXPLOITATION = auto()
    VERIFICATION = auto()
    REPORTING = auto()


class Protocol(Enum):
    """Network protocols."""
    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    UDP = "udp"
    SSH = "ssh"
    FTP = "ftp"
    SMTP = "smtp"
    DNS = "dns"
    WEBSOCKET = "websocket"


@dataclass
class Service:
    """Service running on a target."""
    host: str
    port: int
    protocol: Protocol
    service_type: str
    version: Optional[str] = None
    banner: Optional[str] = None


@dataclass
class TechnologyProfile:
    """Technology stack profile for a target."""
    web_server: Optional[str] = None
    application_framework: Optional[str] = None
    programming_language: Optional[str] = None
    database: Optional[str] = None
    cache: Optional[str] = None
    cdn: Optional[str] = None
    waf: Optional[str] = None
    cms: Optional[str] = None
    javascript_frameworks: List[str] = field(default_factory=list)
    css_frameworks: List[str] = field(default_factory=list)
    additional_technologies: Dict[str, str] = field(default_factory=dict)


@dataclass
class AuthenticationProfile:
    """Authentication profile for a target."""
    auth_type: str
    login_url: Optional[str] = None
    logout_url: Optional[str] = None
    session_cookie_name: Optional[str] = None
    csrf_token_name: Optional[str] = None
    roles_discovered: List[str] = field(default_factory=list)


@dataclass
class Target:
    """Target domain representation."""
    domain: str
    subdomains: List[str] = field(default_factory=list)
    services: List[Service] = field(default_factory=list)
    technology_stack: TechnologyProfile = field(default_factory=TechnologyProfile)
    authentication: Optional[AuthenticationProfile] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "domain": self.domain,
            "subdomains": self.subdomains,
            "services": [
                {
                    "host": s.host,
                    "port": s.port,
                    "protocol": s.protocol.value,
                    "service_type": s.service_type,
                    "version": s.version,
                    "banner": s.banner,
                }
                for s in self.services
            ],
            "technology_stack": {
                "web_server": self.technology_stack.web_server,
                "application_framework": self.technology_stack.application_framework,
                "programming_language": self.technology_stack.programming_language,
                "database": self.technology_stack.database,
            },
        }


@dataclass
class ScopeDefinition:
    """Scope definition for a bug bounty program."""
    in_scope_domains: List[str] = field(default_factory=list)
    out_of_scope_domains: List[str] = field(default_factory=list)
    in_scope_vulnerability_types: List[str] = field(default_factory=list)
    out_of_scope_vulnerability_types: List[str] = field(default_factory=list)
    special_instructions: str = ""


@dataclass
class RateLimits:
    """Rate limiting configuration."""
    requests_per_second: int = 10
    requests_per_minute: int = 300
    concurrent_connections: int = 5
    delay_between_requests_ms: int = 100


@dataclass
class PayoutStructure:
    """Payout structure for a bug bounty program."""
    critical_min: int = 0
    critical_max: int = 0
    high_min: int = 0
    high_max: int = 0
    medium_min: int = 0
    medium_max: int = 0
    low_min: int = 0
    low_max: int = 0


@dataclass
class BugBountyProgram:
    """Bug bounty program definition."""
    name: str
    platform: str  # e.g., "hackerone", "bugcrowd", "private"
    scope: ScopeDefinition = field(default_factory=ScopeDefinition)
    rate_limits: RateLimits = field(default_factory=RateLimits)
    payout_structure: PayoutStructure = field(default_factory=PayoutStructure)
    policies: List[str] = field(default_factory=list)
    safe_harbor: bool = True

    def is_in_scope(self, domain: str) -> bool:
        """Check if a domain is in scope."""
        # Check explicit out of scope first
        for pattern in self.scope.out_of_scope_domains:
            if self._matches_pattern(domain, pattern):
                return False
        
        # Check in scope
        for pattern in self.scope.in_scope_domains:
            if self._matches_pattern(domain, pattern):
                return True
        
        return False

    def _matches_pattern(self, domain: str, pattern: str) -> bool:
        """Check if domain matches a scope pattern."""
        if pattern.startswith("*."):
            # Wildcard subdomain match
            base = pattern[2:]
            return domain == base or domain.endswith("." + base)
        return domain == pattern


@dataclass
class Evidence:
    """Evidence for a finding."""
    request: Optional[str] = None
    response: Optional[str] = None
    screenshot: Optional[bytes] = None
    exploit_output: Optional[str] = None
    state_before: Optional[Dict[str, Any]] = None
    state_after: Optional[Dict[str, Any]] = None
    additional: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Finding:
    """Security finding."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    invariant_violated: str = ""
    title: str = ""
    description: str = ""
    severity: Severity = Severity.INFO
    confidence: float = 0.0
    classification: FindingClassification = FindingClassification.SIGNAL
    evidence: Evidence = field(default_factory=Evidence)
    cvss_score: Optional[float] = None
    cwe_id: Optional[str] = None
    target: Optional[str] = None
    endpoint: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def is_bug(self) -> bool:
        """Check if this finding is classified as a bug."""
        return self.classification == FindingClassification.BUG

    def is_reportable(self) -> bool:
        """Check if this finding should be reported."""
        return (
            self.is_bug() and
            self.confidence >= 0.8 and
            self.invariant_violated != ""
        )


@dataclass
class HuntSession:
    """Bug bounty hunting session."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target: Optional[Target] = None
    program: Optional[BugBountyProgram] = None
    current_phase: HuntPhase = HuntPhase.RECONNAISSANCE
    findings: List[Finding] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    is_active: bool = True

    def add_finding(self, finding: Finding) -> None:
        """Add a finding to the session."""
        self.findings.append(finding)

    def get_bugs(self) -> List[Finding]:
        """Get all findings classified as bugs."""
        return [f for f in self.findings if f.is_bug()]

    def get_reportable(self) -> List[Finding]:
        """Get all reportable findings."""
        return [f for f in self.findings if f.is_reportable()]

    def complete(self) -> None:
        """Mark session as complete."""
        self.is_active = False
        self.completed_at = datetime.utcnow()