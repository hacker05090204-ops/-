"""
Rule Engine - Enforces bug bounty program policies and scope restrictions.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set
from collections import deque

from .types import BugBountyProgram, Target, Severity

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels for actions."""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


@dataclass
class ValidationResult:
    """Result of scope validation."""
    is_valid: bool
    reason: str
    warnings: List[str] = field(default_factory=list)


@dataclass
class RiskScore:
    """Risk assessment score."""
    level: RiskLevel
    score: float  # 0.0 to 1.0
    factors: List[str] = field(default_factory=list)
    should_throttle: bool = False
    should_stop: bool = False


@dataclass
class RiskEvent:
    """Record of a risk event."""
    timestamp: datetime
    action: str
    risk_level: RiskLevel
    details: str


class PolicyParser:
    """Parses and normalizes bug bounty program policies."""

    def parse(self, program: BugBountyProgram) -> Dict[str, Any]:
        """Parse program policies into machine-readable format."""
        return {
            "scope": self._parse_scope(program),
            "rate_limits": self._parse_rate_limits(program),
            "restrictions": self._parse_restrictions(program),
            "safe_harbor": program.safe_harbor,
        }

    def _parse_scope(self, program: BugBountyProgram) -> Dict[str, Any]:
        """Parse scope definitions."""
        return {
            "in_scope_patterns": [
                self._compile_pattern(d) for d in program.scope.in_scope_domains
            ],
            "out_of_scope_patterns": [
                self._compile_pattern(d) for d in program.scope.out_of_scope_domains
            ],
            "allowed_vuln_types": set(program.scope.in_scope_vulnerability_types),
            "disallowed_vuln_types": set(program.scope.out_of_scope_vulnerability_types),
        }

    def _parse_rate_limits(self, program: BugBountyProgram) -> Dict[str, Any]:
        """Parse rate limiting configuration."""
        return {
            "requests_per_second": program.rate_limits.requests_per_second,
            "requests_per_minute": program.rate_limits.requests_per_minute,
            "concurrent_connections": program.rate_limits.concurrent_connections,
            "delay_ms": program.rate_limits.delay_between_requests_ms,
        }

    def _parse_restrictions(self, program: BugBountyProgram) -> List[str]:
        """Parse policy restrictions."""
        return program.policies

    def _compile_pattern(self, domain_pattern: str) -> re.Pattern:
        """Compile a domain pattern to regex."""
        if domain_pattern.startswith("*."):
            # Wildcard subdomain
            base = re.escape(domain_pattern[2:])
            return re.compile(f"^([a-zA-Z0-9-]+\\.)*{base}$")
        else:
            return re.compile(f"^{re.escape(domain_pattern)}$")


class ScopeValidator:
    """Validates targets against program scope."""

    def __init__(self, program: BugBountyProgram):
        self.program = program
        self.parser = PolicyParser()
        self.parsed = self.parser.parse(program)

    def validate_target(self, target: str) -> ValidationResult:
        """Validate a target against program scope."""
        # Check out of scope first
        for pattern in self.parsed["scope"]["out_of_scope_patterns"]:
            if pattern.match(target):
                return ValidationResult(
                    is_valid=False,
                    reason=f"Target {target} is explicitly out of scope",
                )

        # Check in scope
        for pattern in self.parsed["scope"]["in_scope_patterns"]:
            if pattern.match(target):
                return ValidationResult(
                    is_valid=True,
                    reason=f"Target {target} matches in-scope pattern",
                )

        return ValidationResult(
            is_valid=False,
            reason=f"Target {target} does not match any in-scope pattern",
        )

    def validate_vulnerability_type(self, vuln_type: str) -> ValidationResult:
        """Validate a vulnerability type against program scope."""
        disallowed = self.parsed["scope"]["disallowed_vuln_types"]
        if vuln_type in disallowed:
            return ValidationResult(
                is_valid=False,
                reason=f"Vulnerability type {vuln_type} is out of scope",
            )

        allowed = self.parsed["scope"]["allowed_vuln_types"]
        if allowed and vuln_type not in allowed:
            return ValidationResult(
                is_valid=False,
                reason=f"Vulnerability type {vuln_type} is not in allowed list",
                warnings=["Consider checking program scope for allowed types"],
            )

        return ValidationResult(
            is_valid=True,
            reason=f"Vulnerability type {vuln_type} is allowed",
        )

    def is_in_scope(self, target: str) -> bool:
        """Quick check if target is in scope."""
        return self.validate_target(target).is_valid


class RiskAssessor:
    """Assesses risk of actions and computes ban-risk scores."""

    def __init__(self):
        self._risk_history: deque = deque(maxlen=1000)
        self._action_weights: Dict[str, float] = {
            "aggressive_scan": 0.8,
            "exploitation_attempt": 0.9,
            "rate_limit_hit": 0.6,
            "error_response": 0.3,
            "blocked_request": 0.7,
            "normal_request": 0.1,
        }
        self._threshold_throttle = 0.5
        self._threshold_stop = 0.8

    def assess_action(self, action: str, context: Optional[Dict[str, Any]] = None) -> RiskScore:
        """Assess risk of an action."""
        weight = self._action_weights.get(action, 0.5)
        
        # Calculate cumulative risk from recent history
        recent_risk = self._calculate_recent_risk()
        combined_risk = (weight + recent_risk) / 2
        
        # Determine risk level
        if combined_risk >= 0.8:
            level = RiskLevel.CRITICAL
        elif combined_risk >= 0.6:
            level = RiskLevel.HIGH
        elif combined_risk >= 0.4:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        factors = [f"Action weight: {weight:.2f}", f"Recent risk: {recent_risk:.2f}"]
        
        # Record event
        self._risk_history.append(RiskEvent(
            timestamp=datetime.utcnow(),
            action=action,
            risk_level=level,
            details=str(context) if context else "",
        ))

        return RiskScore(
            level=level,
            score=combined_risk,
            factors=factors,
            should_throttle=combined_risk >= self._threshold_throttle,
            should_stop=combined_risk >= self._threshold_stop,
        )

    def _calculate_recent_risk(self) -> float:
        """Calculate risk from recent events."""
        if not self._risk_history:
            return 0.0

        # Weight recent events more heavily
        now = datetime.utcnow()
        total_weight = 0.0
        weighted_risk = 0.0

        for event in self._risk_history:
            age = (now - event.timestamp).total_seconds()
            # Decay factor: events older than 5 minutes have less weight
            decay = max(0.1, 1.0 - (age / 300))
            
            risk_value = {
                RiskLevel.LOW: 0.2,
                RiskLevel.MEDIUM: 0.4,
                RiskLevel.HIGH: 0.7,
                RiskLevel.CRITICAL: 1.0,
            }.get(event.risk_level, 0.5)
            
            weighted_risk += risk_value * decay
            total_weight += decay

        return weighted_risk / total_weight if total_weight > 0 else 0.0

    def get_ban_risk_score(self) -> float:
        """Get current ban risk score (0.0 to 1.0)."""
        return self._calculate_recent_risk()

    def should_throttle(self) -> bool:
        """Check if actions should be throttled."""
        return self.get_ban_risk_score() >= self._threshold_throttle

    def should_stop(self) -> bool:
        """Check if actions should stop."""
        return self.get_ban_risk_score() >= self._threshold_stop

    def clear_history(self) -> None:
        """Clear risk history."""
        self._risk_history.clear()


class ComplianceMonitor:
    """Monitors compliance with program policies."""

    def __init__(self, program: BugBountyProgram):
        self.program = program
        self.scope_validator = ScopeValidator(program)
        self.risk_assessor = RiskAssessor()
        self._violations: List[Dict[str, Any]] = []
        self._request_times: deque = deque(maxlen=1000)

    def check_action(
        self,
        action: str,
        target: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Check if an action is compliant with program policies."""
        result = {
            "allowed": True,
            "warnings": [],
            "violations": [],
            "risk_score": 0.0,
        }

        # Check scope
        scope_result = self.scope_validator.validate_target(target)
        if not scope_result.is_valid:
            result["allowed"] = False
            result["violations"].append(scope_result.reason)
            self._record_violation("scope", target, scope_result.reason)

        # Check rate limits
        rate_check = self._check_rate_limits()
        if not rate_check["allowed"]:
            result["allowed"] = False
            result["violations"].append(rate_check["reason"])
            self._record_violation("rate_limit", target, rate_check["reason"])
        elif rate_check.get("warning"):
            result["warnings"].append(rate_check["warning"])

        # Assess risk
        risk = self.risk_assessor.assess_action(action, context)
        result["risk_score"] = risk.score
        
        if risk.should_stop:
            result["allowed"] = False
            result["violations"].append("Risk threshold exceeded - stopping")
        elif risk.should_throttle:
            result["warnings"].append("Risk elevated - throttling recommended")

        return result

    def _check_rate_limits(self) -> Dict[str, Any]:
        """Check rate limit compliance."""
        now = datetime.utcnow()
        self._request_times.append(now)

        # Count requests in last second
        one_second_ago = now - timedelta(seconds=1)
        requests_last_second = sum(
            1 for t in self._request_times if t > one_second_ago
        )

        # Count requests in last minute
        one_minute_ago = now - timedelta(minutes=1)
        requests_last_minute = sum(
            1 for t in self._request_times if t > one_minute_ago
        )

        limits = self.program.rate_limits
        
        if requests_last_second > limits.requests_per_second:
            return {
                "allowed": False,
                "reason": f"Rate limit exceeded: {requests_last_second}/{limits.requests_per_second} req/s",
            }

        if requests_last_minute > limits.requests_per_minute:
            return {
                "allowed": False,
                "reason": f"Rate limit exceeded: {requests_last_minute}/{limits.requests_per_minute} req/min",
            }

        # Warning if approaching limits
        if requests_last_second > limits.requests_per_second * 0.8:
            return {
                "allowed": True,
                "warning": "Approaching rate limit",
            }

        return {"allowed": True}

    def _record_violation(self, violation_type: str, target: str, reason: str) -> None:
        """Record a policy violation."""
        self._violations.append({
            "type": violation_type,
            "target": target,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        })
        logger.warning(f"Policy violation: {violation_type} - {reason}")

    def get_violations(self) -> List[Dict[str, Any]]:
        """Get all recorded violations."""
        return self._violations.copy()

    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate compliance report."""
        return {
            "program": self.program.name,
            "total_violations": len(self._violations),
            "violations_by_type": self._count_violations_by_type(),
            "current_risk_score": self.risk_assessor.get_ban_risk_score(),
            "should_throttle": self.risk_assessor.should_throttle(),
            "should_stop": self.risk_assessor.should_stop(),
        }

    def _count_violations_by_type(self) -> Dict[str, int]:
        """Count violations by type."""
        counts: Dict[str, int] = {}
        for v in self._violations:
            vtype = v["type"]
            counts[vtype] = counts.get(vtype, 0) + 1
        return counts


class RuleEngine:
    """
    Main rule engine for enforcing bug bounty program policies.
    
    Coordinates policy parsing, scope validation, risk assessment,
    and compliance monitoring.
    """

    def __init__(self, program: Optional[BugBountyProgram] = None):
        self._program = program
        self._compliance_monitor: Optional[ComplianceMonitor] = None
        if program:
            self._compliance_monitor = ComplianceMonitor(program)

    def set_program(self, program: BugBountyProgram) -> None:
        """Set the bug bounty program."""
        self._program = program
        self._compliance_monitor = ComplianceMonitor(program)

    def validate_target(self, target: str) -> ValidationResult:
        """Validate a target against program scope."""
        if not self._compliance_monitor:
            return ValidationResult(
                is_valid=False,
                reason="No program configured",
            )
        return self._compliance_monitor.scope_validator.validate_target(target)

    def assess_action_risk(self, action: str, context: Optional[Dict[str, Any]] = None) -> RiskScore:
        """Assess risk of an action."""
        if not self._compliance_monitor:
            return RiskScore(
                level=RiskLevel.HIGH,
                score=1.0,
                factors=["No program configured"],
                should_stop=True,
            )
        return self._compliance_monitor.risk_assessor.assess_action(action, context)

    def check_compliance(
        self,
        action: str,
        target: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Check if an action is compliant."""
        if not self._compliance_monitor:
            return {
                "allowed": False,
                "violations": ["No program configured"],
                "risk_score": 1.0,
            }
        return self._compliance_monitor.check_action(action, target, context)

    def should_throttle(self) -> bool:
        """Check if actions should be throttled."""
        if not self._compliance_monitor:
            return True
        return self._compliance_monitor.risk_assessor.should_throttle()

    def should_stop(self) -> bool:
        """Check if actions should stop."""
        if not self._compliance_monitor:
            return True
        return self._compliance_monitor.risk_assessor.should_stop()

    def get_compliance_report(self) -> Dict[str, Any]:
        """Get compliance report."""
        if not self._compliance_monitor:
            return {"error": "No program configured"}
        return self._compliance_monitor.get_compliance_report()