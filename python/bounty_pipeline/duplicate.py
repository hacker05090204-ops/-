"""
Duplicate Detector - Checks submissions against previous findings.

This module performs similarity checks to detect potential duplicates.
It is ADVISORY ONLY — final decision is always made by a human.

CRITICAL: This detector does NOT auto-reject or auto-submit.
It only provides similarity information for human decision.
"""

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from bounty_pipeline.types import ValidatedFinding, DuplicateCandidate


@dataclass
class HumanDecisionRequest:
    """Request for human decision on potential duplicate."""

    request_id: str
    finding: ValidatedFinding
    candidate: DuplicateCandidate
    requested_at: datetime
    decision: Optional[str] = None  # "unique", "duplicate", or None
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None


@dataclass
class ArchivedDuplicate:
    """Finding archived as duplicate."""

    finding: ValidatedFinding
    original_finding_id: str
    original_submission_id: str
    archived_by: str
    archived_at: datetime
    archive_id: str


class DuplicateDetector:
    """
    Checks submissions against previous findings.

    This detector:
    - Performs similarity checks (NOT confidence computation)
    - Alerts human with comparison details
    - Requires human decision for all cases
    - Archives confirmed duplicates

    ARCHITECTURAL CONSTRAINT:
    This detector is ADVISORY ONLY.
    It NEVER auto-rejects or auto-submits.
    Human decision is ALWAYS required.
    """

    def __init__(self, similarity_threshold: float = 0.7) -> None:
        """
        Initialize the duplicate detector.

        Args:
            similarity_threshold: Threshold for flagging potential duplicates
        """
        self._similarity_threshold = similarity_threshold
        self._submitted_findings: dict[str, ValidatedFinding] = {}
        self._submission_ids: dict[str, str] = {}  # finding_id -> submission_id
        self._pending_decisions: dict[str, HumanDecisionRequest] = {}
        self._archived_duplicates: dict[str, ArchivedDuplicate] = {}

    def register_submission(
        self, finding: ValidatedFinding, submission_id: str
    ) -> None:
        """
        Register a submitted finding for future duplicate checks.

        Args:
            finding: The submitted finding
            submission_id: The platform submission ID
        """
        self._submitted_findings[finding.finding_id] = finding
        self._submission_ids[finding.finding_id] = submission_id

    def check(self, finding: ValidatedFinding) -> Optional[DuplicateCandidate]:
        """
        Check if finding may be duplicate of previous submission.

        Args:
            finding: The finding to check

        Returns:
            DuplicateCandidate if potential duplicate found, None otherwise
        """
        best_match: Optional[DuplicateCandidate] = None
        best_score = 0.0

        for existing_id, existing in self._submitted_findings.items():
            if existing_id == finding.finding_id:
                continue  # Don't compare to self

            score = self._compute_similarity(finding, existing)

            if score >= self._similarity_threshold and score > best_score:
                best_score = score
                best_match = DuplicateCandidate(
                    original_finding_id=existing_id,
                    original_submission_id=self._submission_ids.get(existing_id, "unknown"),
                    similarity_score=score,
                    comparison_details=self._generate_comparison(finding, existing),
                )

        return best_match

    def _compute_similarity(
        self, finding1: ValidatedFinding, finding2: ValidatedFinding
    ) -> float:
        """
        Compute similarity between two findings.

        This is a SIMILARITY METRIC, not a confidence score.
        It measures how similar two findings are based on:
        - Invariant violated
        - Target similarity
        - Action sequence similarity

        Args:
            finding1: First finding
            finding2: Second finding

        Returns:
            Similarity score between 0.0 and 1.0
        """
        scores = []

        # Compare invariants (exact match = 1.0, different = 0.0)
        if finding1.proof_chain.invariant_violated == finding2.proof_chain.invariant_violated:
            scores.append(1.0)
        else:
            scores.append(0.0)

        # Compare action sequences (Jaccard similarity)
        actions1 = set(str(a) for a in finding1.proof_chain.action_sequence)
        actions2 = set(str(a) for a in finding2.proof_chain.action_sequence)

        if actions1 or actions2:
            intersection = len(actions1 & actions2)
            union = len(actions1 | actions2)
            scores.append(intersection / union if union > 0 else 0.0)
        else:
            scores.append(0.0)

        # Compare proof hashes (exact match = 1.0, different = 0.0)
        if finding1.proof_chain.proof_hash == finding2.proof_chain.proof_hash:
            scores.append(1.0)
        else:
            scores.append(0.0)

        # Average similarity
        return sum(scores) / len(scores) if scores else 0.0

    def _generate_comparison(
        self, finding: ValidatedFinding, existing: ValidatedFinding
    ) -> dict:
        """Generate comparison details for human review."""
        return {
            "new_finding": {
                "id": finding.finding_id,
                "invariant": finding.proof_chain.invariant_violated,
                "severity": finding.mcp_finding.severity,
            },
            "existing_finding": {
                "id": existing.finding_id,
                "invariant": existing.proof_chain.invariant_violated,
                "severity": existing.mcp_finding.severity,
            },
            "same_invariant": (
                finding.proof_chain.invariant_violated
                == existing.proof_chain.invariant_violated
            ),
            "same_proof_hash": (
                finding.proof_chain.proof_hash == existing.proof_chain.proof_hash
            ),
        }

    def request_human_decision(
        self, finding: ValidatedFinding, candidate: DuplicateCandidate
    ) -> HumanDecisionRequest:
        """
        Request human decision on potential duplicate.

        Args:
            finding: The finding being checked
            candidate: The potential duplicate

        Returns:
            HumanDecisionRequest for tracking
        """
        request_id = secrets.token_urlsafe(16)
        request = HumanDecisionRequest(
            request_id=request_id,
            finding=finding,
            candidate=candidate,
            requested_at=datetime.now(timezone.utc),
        )
        self._pending_decisions[request_id] = request
        return request

    def decide_unique(self, request_id: str, decided_by: str) -> HumanDecisionRequest:
        """
        Human decides finding is unique (not a duplicate).

        Args:
            request_id: The decision request ID
            decided_by: Who made the decision

        Returns:
            Updated HumanDecisionRequest
        """
        if request_id not in self._pending_decisions:
            raise ValueError(f"Decision request {request_id} not found")

        request = self._pending_decisions[request_id]
        request.decision = "unique"
        request.decided_by = decided_by
        request.decided_at = datetime.now(timezone.utc)

        return request

    def decide_duplicate(
        self, request_id: str, decided_by: str
    ) -> ArchivedDuplicate:
        """
        Human decides finding is a duplicate.

        Args:
            request_id: The decision request ID
            decided_by: Who made the decision

        Returns:
            ArchivedDuplicate
        """
        if request_id not in self._pending_decisions:
            raise ValueError(f"Decision request {request_id} not found")

        request = self._pending_decisions[request_id]
        request.decision = "duplicate"
        request.decided_by = decided_by
        request.decided_at = datetime.now(timezone.utc)

        # Archive as duplicate
        archived = self.archive_as_duplicate(
            finding=request.finding,
            original_id=request.candidate.original_finding_id,
            original_submission_id=request.candidate.original_submission_id,
            archived_by=decided_by,
        )

        # Remove from pending
        del self._pending_decisions[request_id]

        return archived

    def archive_as_duplicate(
        self,
        finding: ValidatedFinding,
        original_id: str,
        original_submission_id: str,
        archived_by: str,
    ) -> ArchivedDuplicate:
        """
        Archive finding as duplicate without submission.

        Args:
            finding: The duplicate finding
            original_id: ID of the original finding
            original_submission_id: Submission ID of the original
            archived_by: Who archived it

        Returns:
            ArchivedDuplicate
        """
        archive_id = secrets.token_urlsafe(16)
        archived = ArchivedDuplicate(
            finding=finding,
            original_finding_id=original_id,
            original_submission_id=original_submission_id,
            archived_by=archived_by,
            archived_at=datetime.now(timezone.utc),
            archive_id=archive_id,
        )
        self._archived_duplicates[archive_id] = archived
        return archived

    def get_pending_decisions(self) -> list[HumanDecisionRequest]:
        """Get all pending duplicate decisions."""
        return list(self._pending_decisions.values())

    def get_archived_duplicates(self) -> list[ArchivedDuplicate]:
        """Get all archived duplicates."""
        return list(self._archived_duplicates.values())
