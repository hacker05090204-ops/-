"""
Report Generator - Formats proven findings into platform-specific reports.

This module generates submission-ready reports from validated findings.
It handles platform-specific formatting, severity mapping, and data redaction.

CRITICAL: Severity mapping is DETERMINISTIC, not computed.
We map MCP severity to platform severity using a fixed mapping table.
We do NOT compute or estimate severity — that's MCP's responsibility.
"""

import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from bounty_pipeline.errors import ArchitecturalViolationError
from bounty_pipeline.types import (
    ValidatedFinding,
    SubmissionDraft,
    ProofChain,
    ReproductionStep,
    DraftStatus,
)


# Deterministic severity mapping — NOT confidence computation
# This maps MCP severity to platform-specific severity labels
SEVERITY_MAPPING: dict[str, dict[str, str]] = {
    "critical": {
        "hackerone": "critical",
        "bugcrowd": "P1",
        "generic": "Critical",
    },
    "high": {
        "hackerone": "high",
        "bugcrowd": "P2",
        "generic": "High",
    },
    "medium": {
        "hackerone": "medium",
        "bugcrowd": "P3",
        "generic": "Medium",
    },
    "low": {
        "hackerone": "low",
        "bugcrowd": "P4",
        "generic": "Low",
    },
    "informational": {
        "hackerone": "none",
        "bugcrowd": "P5",
        "generic": "Informational",
    },
}

# Patterns for sensitive data redaction
REDACTION_PATTERNS = [
    # Email addresses
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[REDACTED_EMAIL]"),
    # Phone numbers (various formats)
    (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[REDACTED_PHONE]"),
    # Credit card numbers
    (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "[REDACTED_CC]"),
    # SSN
    (r"\b\d{3}[-]?\d{2}[-]?\d{4}\b", "[REDACTED_SSN]"),
    # API keys (common patterns)
    (r"\b[A-Za-z0-9]{32,}\b", "[REDACTED_KEY]"),
    # Bearer tokens
    (r"Bearer\s+[A-Za-z0-9._-]+", "Bearer [REDACTED_TOKEN]"),
    # Basic auth
    (r"Basic\s+[A-Za-z0-9+/=]+", "Basic [REDACTED_AUTH]"),
    # Passwords in URLs
    (r"://[^:]+:[^@]+@", "://[REDACTED_CREDS]@"),
]


@dataclass
class PlatformSchema:
    """Schema for a bug bounty platform."""

    platform_name: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    severity_field: str
    max_title_length: int
    max_body_length: int


# Platform schemas
PLATFORM_SCHEMAS: dict[str, PlatformSchema] = {
    "hackerone": PlatformSchema(
        platform_name="HackerOne",
        required_fields=("title", "vulnerability_information", "impact"),
        optional_fields=("weakness_id", "asset_identifier"),
        severity_field="severity_rating",
        max_title_length=150,
        max_body_length=65535,
    ),
    "bugcrowd": PlatformSchema(
        platform_name="Bugcrowd",
        required_fields=("title", "description", "proof_of_concept"),
        optional_fields=("vrt_id", "target"),
        severity_field="priority",
        max_title_length=200,
        max_body_length=50000,
    ),
    "generic": PlatformSchema(
        platform_name="Generic",
        required_fields=("title", "description"),
        optional_fields=(),
        severity_field="severity",
        max_title_length=500,
        max_body_length=100000,
    ),
}


class ReportGenerator:
    """
    Generates platform-specific reports from validated findings.

    This generator:
    - Formats reports according to platform schema
    - Maps MCP severity to platform severity (deterministic)
    - Extracts reproduction steps from MCP replay instructions
    - Redacts sensitive data by default

    ARCHITECTURAL CONSTRAINT:
    This generator does NOT compute severity or confidence.
    It only maps MCP's severity to platform-specific labels.
    """

    def __init__(self, redact_by_default: bool = True) -> None:
        """
        Initialize the report generator.

        Args:
            redact_by_default: Whether to redact sensitive data by default
        """
        self._redact_by_default = redact_by_default

    def generate(
        self,
        finding: ValidatedFinding,
        platform: str,
        custom_title: Optional[str] = None,
    ) -> SubmissionDraft:
        """
        Generate platform-specific report from validated finding.

        Args:
            finding: The validated finding
            platform: Target platform (hackerone, bugcrowd, generic)
            custom_title: Optional custom title

        Returns:
            SubmissionDraft ready for human review
        """
        # Get platform schema
        schema = PLATFORM_SCHEMAS.get(platform, PLATFORM_SCHEMAS["generic"])

        # Map severity
        severity = self.map_severity(finding.mcp_finding.severity, platform)

        # Extract reproduction steps
        reproduction_steps = self.extract_reproduction_steps(finding.proof_chain)

        # Generate report body
        report_body = self._generate_body(finding, platform, reproduction_steps)

        # Redact if enabled
        if self._redact_by_default:
            report_body = self.redact_sensitive_data(report_body)

        # Generate title
        title = custom_title or self._generate_title(finding, schema)

        # Generate proof summary
        proof_summary = self._generate_proof_summary(finding.proof_chain)

        return SubmissionDraft(
            draft_id=secrets.token_urlsafe(16),
            finding=finding,
            platform=platform,
            report_title=title[:schema.max_title_length],
            report_body=report_body[:schema.max_body_length],
            severity=severity,
            reproduction_steps=reproduction_steps,
            proof_summary=proof_summary,
            created_at=datetime.now(timezone.utc),
            status=DraftStatus.PENDING_REVIEW,
        )

    def extract_reproduction_steps(self, proof: ProofChain) -> list[ReproductionStep]:
        """
        Extract reproduction steps from MCP replay instructions.

        Args:
            proof: The proof chain from MCP

        Returns:
            List of reproduction steps
        """
        steps = []
        for i, instruction in enumerate(proof.replay_instructions, 1):
            action = instruction.get("action", instruction.get("step", str(instruction)))
            expected = instruction.get("expected", instruction.get("result", ""))

            steps.append(
                ReproductionStep(
                    step_number=i,
                    action=str(action),
                    expected_result=str(expected) if expected else "Observe the behavior",
                )
            )

        return steps

    def redact_sensitive_data(self, content: str) -> str:
        """
        Redact PII and credentials from report content.

        Args:
            content: The content to redact

        Returns:
            Content with sensitive data redacted
        """
        redacted = content
        for pattern, replacement in REDACTION_PATTERNS:
            redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)
        return redacted

    def map_severity(self, mcp_severity: str, platform: str) -> str:
        """
        Map MCP severity to platform severity (deterministic).

        This is a DETERMINISTIC mapping, not a computation.
        We do NOT estimate or compute severity — MCP has already done that.

        Args:
            mcp_severity: Severity from MCP
            platform: Target platform

        Returns:
            Platform-specific severity label
        """
        mcp_severity_lower = mcp_severity.lower()

        if mcp_severity_lower not in SEVERITY_MAPPING:
            # Default to medium if unknown
            mcp_severity_lower = "medium"

        platform_mapping = SEVERITY_MAPPING[mcp_severity_lower]
        return platform_mapping.get(platform, platform_mapping["generic"])

    def _generate_title(self, finding: ValidatedFinding, schema: PlatformSchema) -> str:
        """Generate report title."""
        invariant = finding.proof_chain.invariant_violated
        severity = finding.mcp_finding.severity.upper()
        return f"[{severity}] Security Issue: {invariant}"

    def _generate_body(
        self,
        finding: ValidatedFinding,
        platform: str,
        steps: list[ReproductionStep],
    ) -> str:
        """Generate report body."""
        if platform == "hackerone":
            return self._generate_hackerone_body(finding, steps)
        elif platform == "bugcrowd":
            return self._generate_bugcrowd_body(finding, steps)
        else:
            return self._generate_generic_body(finding, steps)

    def _generate_hackerone_body(
        self, finding: ValidatedFinding, steps: list[ReproductionStep]
    ) -> str:
        """Generate HackerOne-formatted report body."""
        proof = finding.proof_chain

        body = f"""## Summary

A security vulnerability was identified that violates the following security invariant:
**{proof.invariant_violated}**

## Vulnerability Information

### Before State
```json
{proof.before_state}
```

### Action Sequence
The following actions were performed:
"""
        for i, action in enumerate(proof.action_sequence, 1):
            body += f"\n{i}. {action}"

        body += f"""

### After State
```json
{proof.after_state}
```

## Steps to Reproduce

"""
        for step in steps:
            body += f"{step.step_number}. {step.action}\n"
            body += f"   Expected: {step.expected_result}\n\n"

        body += f"""
## Impact

This vulnerability allows an attacker to violate the security invariant: **{proof.invariant_violated}**

The causality chain demonstrates how the vulnerability can be exploited:
"""
        for cause in proof.causality_chain:
            body += f"- {cause}\n"

        body += """
## Proof

This finding has been validated by MCP (Model Context Protocol) with a complete proof chain.
The proof hash is included for verification.
"""
        return body

    def _generate_bugcrowd_body(
        self, finding: ValidatedFinding, steps: list[ReproductionStep]
    ) -> str:
        """Generate Bugcrowd-formatted report body."""
        proof = finding.proof_chain

        body = f"""# Description

A security vulnerability was identified that violates the security invariant: **{proof.invariant_violated}**

# Proof of Concept

## Steps to Reproduce

"""
        for step in steps:
            body += f"{step.step_number}. {step.action}\n"

        body += f"""
## Technical Details

**Before State:**
```
{proof.before_state}
```

**After State:**
```
{proof.after_state}
```

# Impact

This vulnerability allows violation of: {proof.invariant_violated}
"""
        return body

    def _generate_generic_body(
        self, finding: ValidatedFinding, steps: list[ReproductionStep]
    ) -> str:
        """Generate generic markdown report body."""
        proof = finding.proof_chain

        body = f"""# Security Vulnerability Report

## Summary

A security vulnerability was identified that violates the following invariant:
**{proof.invariant_violated}**

## Reproduction Steps

"""
        for step in steps:
            body += f"{step.step_number}. {step.action}\n"
            body += f"   - Expected: {step.expected_result}\n"

        body += f"""
## Technical Details

### Before State
```
{proof.before_state}
```

### After State
```
{proof.after_state}
```

### Causality Chain
"""
        for cause in proof.causality_chain:
            body += f"- {cause}\n"

        body += f"""
## Proof

This finding has been validated with MCP proof.
Proof hash: `{proof.proof_hash}`
"""
        return body

    def _generate_proof_summary(self, proof: ProofChain) -> str:
        """Generate a summary of the proof."""
        return (
            f"MCP validated proof showing violation of invariant '{proof.invariant_violated}'. "
            f"Proof hash: {proof.proof_hash[:16]}..."
        )

    # =========================================================================
    # ARCHITECTURAL BOUNDARY ENFORCEMENT
    # =========================================================================

    def compute_severity(self, *args, **kwargs) -> None:
        """
        FORBIDDEN: Cannot compute severity.

        Raises:
            ArchitecturalViolationError: Always - severity is MCP's domain
        """
        raise ArchitecturalViolationError(
            "Cannot compute severity. "
            "Severity computation is MCP's responsibility. "
            "Use map_severity() to map MCP's severity to platform labels."
        )

    def estimate_confidence(self, *args, **kwargs) -> None:
        """
        FORBIDDEN: Cannot estimate confidence.

        Raises:
            ArchitecturalViolationError: Always - confidence is MCP's domain
        """
        raise ArchitecturalViolationError(
            "Cannot estimate confidence. "
            "Confidence computation is MCP's responsibility. "
            "Bounty Pipeline only uses MCP's confidence value."
        )

    def classify_vulnerability(self, *args, **kwargs) -> None:
        """
        FORBIDDEN: Cannot classify vulnerabilities.

        Raises:
            ArchitecturalViolationError: Always - classification is MCP's domain
        """
        raise ArchitecturalViolationError(
            "Cannot classify vulnerabilities. "
            "Vulnerability classification is MCP's responsibility. "
            "Bounty Pipeline only processes MCP-classified findings."
        )
