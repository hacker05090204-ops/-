"""
Program Manager - Manages multi-program configurations.

This module handles program isolation and cross-program handling.

CRITICAL CONSTRAINTS:
- Findings are isolated by program
- Program-specific policies are applied
- Cross-program findings require human decision
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from bounty_pipeline.types import (
    AuthorizationDocument,
    ValidatedFinding,
)
from bounty_pipeline.errors import (
    HumanApprovalRequired,
    ScopeViolationError,
)


@dataclass
class ProgramPolicy:
    """Policy configuration for a bug bounty program."""

    program_name: str
    min_severity: str  # Minimum severity to submit
    auto_duplicate_check: bool  # Whether to auto-check duplicates
    require_poc: bool  # Whether proof-of-concept is required
    max_submissions_per_day: int  # Rate limit
    custom_fields: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def default(program_name: str) -> "ProgramPolicy":
        """Create default policy for a program."""
        return ProgramPolicy(
            program_name=program_name,
            min_severity="low",
            auto_duplicate_check=True,
            require_poc=True,
            max_submissions_per_day=10,
        )


@dataclass
class ProgramContext:
    """Context for a specific program."""

    program_name: str
    authorization: AuthorizationDocument
    policy: ProgramPolicy
    findings: list[ValidatedFinding] = field(default_factory=list)
    submissions_today: int = 0
    last_submission_date: Optional[datetime] = None

    @property
    def can_submit_today(self) -> bool:
        """Check if more submissions are allowed today."""
        if self.last_submission_date is None:
            return True

        today = datetime.now(timezone.utc).date()
        if self.last_submission_date.date() != today:
            return True

        return self.submissions_today < self.policy.max_submissions_per_day


@dataclass
class CrossProgramFinding:
    """A finding that spans multiple programs."""

    finding: ValidatedFinding
    matching_programs: list[str]
    requires_human_decision: bool = True
    selected_program: Optional[str] = None
    decision_reason: Optional[str] = None


class ProgramManager:
    """
    Manages multi-program configurations.

    Features:
    - Program isolation (findings separated by program)
    - Program-specific policy application
    - Cross-program handling with human decision
    - Rate limiting per program
    """

    def __init__(self) -> None:
        """Initialize program manager."""
        self._programs: dict[str, ProgramContext] = {}
        self._cross_program_findings: list[CrossProgramFinding] = {}

    def register_program(
        self,
        authorization: AuthorizationDocument,
        policy: Optional[ProgramPolicy] = None,
    ) -> ProgramContext:
        """
        Register a bug bounty program.

        Args:
            authorization: Legal authorization document
            policy: Program policy (uses default if not provided)

        Returns:
            ProgramContext for the program
        """
        program_name = authorization.program_name

        if policy is None:
            policy = ProgramPolicy.default(program_name)

        context = ProgramContext(
            program_name=program_name,
            authorization=authorization,
            policy=policy,
        )

        self._programs[program_name] = context
        return context

    def get_program(self, program_name: str) -> Optional[ProgramContext]:
        """Get program context by name."""
        return self._programs.get(program_name)

    def get_all_programs(self) -> list[ProgramContext]:
        """Get all registered programs."""
        return list(self._programs.values())

    def add_finding_to_program(
        self,
        finding: ValidatedFinding,
        program_name: str,
    ) -> None:
        """
        Add a finding to a specific program.

        Args:
            finding: The validated finding
            program_name: Target program name

        Raises:
            ValueError: If program not found
            ScopeViolationError: If finding is out of scope
        """
        if program_name not in self._programs:
            raise ValueError(f"Program not found: {program_name}")

        context = self._programs[program_name]

        # Verify authorization is still valid
        if context.authorization.is_expired:
            raise ScopeViolationError(
                f"Authorization for program '{program_name}' has expired"
            )

        context.findings.append(finding)

    def get_findings_for_program(
        self,
        program_name: str,
    ) -> list[ValidatedFinding]:
        """
        Get all findings for a program.

        Args:
            program_name: Program name

        Returns:
            List of findings for the program

        Raises:
            ValueError: If program not found
        """
        if program_name not in self._programs:
            raise ValueError(f"Program not found: {program_name}")

        return list(self._programs[program_name].findings)

    def check_cross_program(
        self,
        finding: ValidatedFinding,
    ) -> Optional[CrossProgramFinding]:
        """
        Check if a finding matches multiple programs.

        Args:
            finding: The finding to check

        Returns:
            CrossProgramFinding if matches multiple programs, None otherwise
        """
        matching = []

        for program_name, context in self._programs.items():
            if self._finding_matches_program(finding, context):
                matching.append(program_name)

        if len(matching) > 1:
            cross = CrossProgramFinding(
                finding=finding,
                matching_programs=matching,
                requires_human_decision=True,
            )
            return cross

        return None

    def _finding_matches_program(
        self,
        finding: ValidatedFinding,
        context: ProgramContext,
    ) -> bool:
        """Check if a finding matches a program's scope."""
        # In a real implementation, this would check the finding's
        # target against the program's authorized domains/IPs
        # For now, return True if authorization is active
        return context.authorization.is_active

    def assign_cross_program_finding(
        self,
        finding: ValidatedFinding,
        selected_program: str,
        decision_reason: str,
        decider_id: str,
    ) -> None:
        """
        Assign a cross-program finding to a specific program.

        This requires human decision.

        Args:
            finding: The finding to assign
            selected_program: Program to assign to
            decision_reason: Reason for the decision
            decider_id: ID of the human making the decision

        Raises:
            ValueError: If program not found
            HumanApprovalRequired: If no human decision provided
        """
        if selected_program not in self._programs:
            raise ValueError(f"Program not found: {selected_program}")

        if not decision_reason:
            raise HumanApprovalRequired(
                "Cross-program findings require human decision with reason"
            )

        self.add_finding_to_program(finding, selected_program)

    def apply_policy(
        self,
        finding: ValidatedFinding,
        program_name: str,
    ) -> dict[str, Any]:
        """
        Apply program-specific policy to a finding.

        Args:
            finding: The finding to check
            program_name: Program name

        Returns:
            Dict with policy check results

        Raises:
            ValueError: If program not found
        """
        if program_name not in self._programs:
            raise ValueError(f"Program not found: {program_name}")

        context = self._programs[program_name]
        policy = context.policy

        results = {
            "program": program_name,
            "passes_policy": True,
            "issues": [],
        }

        # Check minimum severity
        severity_order = ["informational", "low", "medium", "high", "critical"]
        finding_severity = finding.mcp_finding.severity.lower()
        min_severity = policy.min_severity.lower()

        if finding_severity in severity_order and min_severity in severity_order:
            if severity_order.index(finding_severity) < severity_order.index(min_severity):
                results["passes_policy"] = False
                results["issues"].append(
                    f"Severity '{finding_severity}' below minimum '{min_severity}'"
                )

        # Check rate limit
        if not context.can_submit_today:
            results["passes_policy"] = False
            results["issues"].append(
                f"Daily submission limit ({policy.max_submissions_per_day}) reached"
            )

        return results

    def record_submission(self, program_name: str) -> None:
        """
        Record a submission for rate limiting.

        Args:
            program_name: Program name

        Raises:
            ValueError: If program not found
        """
        if program_name not in self._programs:
            raise ValueError(f"Program not found: {program_name}")

        context = self._programs[program_name]
        now = datetime.now(timezone.utc)

        # Reset counter if new day
        if context.last_submission_date is None or \
           context.last_submission_date.date() != now.date():
            context.submissions_today = 0

        context.submissions_today += 1
        context.last_submission_date = now

    def get_program_stats(self, program_name: str) -> dict[str, Any]:
        """
        Get statistics for a program.

        Args:
            program_name: Program name

        Returns:
            Dict with program statistics

        Raises:
            ValueError: If program not found
        """
        if program_name not in self._programs:
            raise ValueError(f"Program not found: {program_name}")

        context = self._programs[program_name]

        return {
            "program_name": program_name,
            "total_findings": len(context.findings),
            "submissions_today": context.submissions_today,
            "can_submit_today": context.can_submit_today,
            "authorization_active": context.authorization.is_active,
            "authorization_expires": context.authorization.valid_until.isoformat(),
        }

    @property
    def program_count(self) -> int:
        """Get number of registered programs."""
        return len(self._programs)
