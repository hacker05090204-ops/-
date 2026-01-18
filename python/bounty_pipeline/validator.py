"""
Finding Validator - Ensures only MCP-proven findings are processed.

This module validates that findings meet the requirements for submission:
1. Must have MCP BUG classification
2. Must have valid proof chain
3. Must link to original MCP proof and Cyfer Brain observation

CRITICAL: This validator does NOT classify findings.
Classification is MCP's responsibility (Phase-1, FROZEN).
This validator only VERIFIES that MCP has already classified the finding.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from bounty_pipeline.errors import FindingValidationError, ArchitecturalViolationError
from bounty_pipeline.types import (
    MCPClassification,
    MCPFinding,
    ProofChain,
    ValidatedFinding,
    SourceLinks,
)


@dataclass(frozen=True)
class ValidationResult:
    """Result of finding validation."""

    is_valid: bool
    reason: str
    validated_finding: Optional[ValidatedFinding] = None


class FindingValidator:
    """
    Validates that findings meet MCP proof requirements.

    This validator ensures:
    - Finding has MCP BUG classification
    - Finding has valid proof chain
    - Proof chain is complete and verifiable

    ARCHITECTURAL CONSTRAINT:
    This validator does NOT classify findings.
    It only verifies that MCP has already classified them.
    """

    # Classifications that are NOT valid for submission
    INVALID_CLASSIFICATIONS = frozenset(
        [
            MCPClassification.SIGNAL,
            MCPClassification.NO_ISSUE,
            MCPClassification.COVERAGE_GAP,
        ]
    )

    def validate(self, finding: MCPFinding) -> ValidatedFinding:
        """
        Validate finding has MCP BUG classification with proof.

        Args:
            finding: The MCP finding to validate

        Returns:
            ValidatedFinding if validation passes

        Raises:
            FindingValidationError: If finding lacks proof or has wrong classification
        """
        # Check classification
        if finding.classification in self.INVALID_CLASSIFICATIONS:
            raise FindingValidationError(
                f"Finding {finding.finding_id} has {finding.classification.value} classification. "
                f"Only BUG classification with proof is valid for submission."
            )

        if finding.classification != MCPClassification.BUG:
            raise FindingValidationError(
                f"Finding {finding.finding_id} has unknown classification: {finding.classification}. "
                f"Only BUG classification is valid for submission."
            )

        # Check proof exists
        if finding.proof is None:
            raise FindingValidationError(
                f"Finding {finding.finding_id} has BUG classification but no proof chain. "
                f"MCP proof is required for submission."
            )

        # Check invariant is specified
        if finding.invariant_violated is None:
            raise FindingValidationError(
                f"Finding {finding.finding_id} has no invariant_violated specified. "
                f"MCP must specify which invariant was violated."
            )

        # Validate proof chain integrity
        self._validate_proof_chain(finding.finding_id, finding.proof)

        # Create source links
        source_links = self.link_to_sources(finding)

        # Create validated finding
        return ValidatedFinding(
            finding_id=finding.finding_id,
            mcp_finding=finding,
            proof_chain=finding.proof,
            source_links=source_links,
            validated_at=datetime.now(timezone.utc),
        )

    def _validate_proof_chain(self, finding_id: str, proof: ProofChain) -> None:
        """
        Validate proof chain integrity.

        Args:
            finding_id: ID of the finding (for error messages)
            proof: The proof chain to validate

        Raises:
            FindingValidationError: If proof chain is invalid
        """
        # Check proof hash exists
        if not proof.proof_hash:
            raise FindingValidationError(
                f"Finding {finding_id} has proof chain with empty proof_hash."
            )

        # Check invariant is specified in proof
        if not proof.invariant_violated:
            raise FindingValidationError(
                f"Finding {finding_id} has proof chain with no invariant_violated."
            )

        # Check action sequence exists
        if not proof.action_sequence:
            raise FindingValidationError(
                f"Finding {finding_id} has proof chain with empty action_sequence."
            )

        # Check causality chain exists
        if not proof.causality_chain:
            raise FindingValidationError(
                f"Finding {finding_id} has proof chain with empty causality_chain."
            )

        # Check replay instructions exist
        if not proof.replay_instructions:
            raise FindingValidationError(
                f"Finding {finding_id} has proof chain with empty replay_instructions."
            )

    def extract_proof_chain(self, finding: MCPFinding) -> ProofChain:
        """
        Extract complete proof chain from MCP finding.

        Args:
            finding: The MCP finding

        Returns:
            The proof chain

        Raises:
            FindingValidationError: If finding has no proof
        """
        if finding.proof is None:
            raise FindingValidationError(
                f"Finding {finding.finding_id} has no proof chain to extract."
            )
        return finding.proof

    def link_to_sources(self, finding: MCPFinding) -> SourceLinks:
        """
        Link to original MCP proof and Cyfer Brain observation.

        Args:
            finding: The MCP finding

        Returns:
            SourceLinks with references to original sources
        """
        proof_hash = finding.proof.proof_hash if finding.proof else "no_proof"

        return SourceLinks(
            mcp_proof_id=finding.finding_id,
            mcp_proof_hash=proof_hash,
            cyfer_brain_observation_id=finding.cyfer_brain_observation_id,
            linked_at=datetime.now(timezone.utc),
        )

    def check_valid(self, finding: MCPFinding) -> ValidationResult:
        """
        Check if finding is valid without raising exceptions.

        Args:
            finding: The MCP finding to check

        Returns:
            ValidationResult with is_valid, reason, and optional validated_finding
        """
        try:
            validated = self.validate(finding)
            return ValidationResult(
                is_valid=True,
                reason="Finding has valid MCP BUG classification with proof",
                validated_finding=validated,
            )
        except FindingValidationError as e:
            return ValidationResult(
                is_valid=False,
                reason=str(e),
                validated_finding=None,
            )

    # =========================================================================
    # ARCHITECTURAL BOUNDARY ENFORCEMENT
    # =========================================================================

    def classify_finding(self, *args, **kwargs) -> None:
        """
        FORBIDDEN: Bounty Pipeline cannot classify findings.

        Raises:
            ArchitecturalViolationError: Always - this is MCP's responsibility
        """
        raise ArchitecturalViolationError(
            "Bounty Pipeline cannot classify findings. "
            "Classification is MCP's responsibility (Phase-1, FROZEN). "
            "Use validate() to verify MCP has already classified the finding."
        )

    def generate_proof(self, *args, **kwargs) -> None:
        """
        FORBIDDEN: Bounty Pipeline cannot generate proofs.

        Raises:
            ArchitecturalViolationError: Always - this is MCP's responsibility
        """
        raise ArchitecturalViolationError(
            "Bounty Pipeline cannot generate proofs. "
            "Proof generation is MCP's responsibility (Phase-1, FROZEN). "
            "Use extract_proof_chain() to get the proof MCP has already generated."
        )

    def compute_confidence(self, *args, **kwargs) -> None:
        """
        FORBIDDEN: Bounty Pipeline cannot compute confidence.

        Raises:
            ArchitecturalViolationError: Always - this is MCP's responsibility
        """
        raise ArchitecturalViolationError(
            "Bounty Pipeline cannot compute confidence scores. "
            "Confidence computation is MCP's responsibility (Phase-1, FROZEN). "
            "The confidence score in MCPFinding is read-only from MCP."
        )

    def override_classification(self, *args, **kwargs) -> None:
        """
        FORBIDDEN: Bounty Pipeline cannot override MCP classifications.

        Raises:
            ArchitecturalViolationError: Always - MCP is the authority
        """
        raise ArchitecturalViolationError(
            "Bounty Pipeline cannot override MCP classifications. "
            "MCP is the sole authority on finding classification. "
            "If you disagree with a classification, report it to MCP."
        )
