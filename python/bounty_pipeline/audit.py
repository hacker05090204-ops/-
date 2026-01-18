"""
Audit Trail - Immutable, tamper-evident log of all actions.

This module implements an append-only, hash-chained audit trail
that records every action taken by Bounty Pipeline.

CRITICAL: Audit records are IMMUTABLE.
Once created, they cannot be modified or deleted.
Hash chaining provides tamper evidence.
"""

import hashlib
import json
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from bounty_pipeline.errors import AuditIntegrityError
from bounty_pipeline.types import AuditRecord


# Genesis hash for the first record in the chain
GENESIS_HASH = "0" * 64


@dataclass
class AuditExport:
    """Export of audit records for compliance review."""

    records: list[AuditRecord]
    start_time: datetime
    end_time: datetime
    total_records: int
    chain_verified: bool
    export_hash: str
    exported_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AuditTrail:
    """
    Immutable, tamper-evident audit trail.

    This trail:
    - Records every action with timestamp, actor, and outcome
    - Links to MCP proof and Cyfer Brain observation
    - Hash-chains all records for tamper evidence
    - Is append-only (no modifications or deletions)

    ARCHITECTURAL CONSTRAINT:
    Audit records are IMMUTABLE. Any attempt to modify
    or delete records raises AuditIntegrityError.
    """

    def __init__(self) -> None:
        """Initialize the audit trail."""
        self._records: list[AuditRecord] = []
        self._records_by_id: dict[str, AuditRecord] = {}
        self._records_by_finding: dict[str, list[AuditRecord]] = {}

    def record(
        self,
        action_type: str,
        actor: str,
        outcome: str,
        details: dict[str, Any],
        mcp_proof_link: Optional[str] = None,
        cyfer_brain_observation_link: Optional[str] = None,
        finding_id: Optional[str] = None,
    ) -> AuditRecord:
        """
        Record an action in the audit trail (append-only).

        Args:
            action_type: Type of action (e.g., "validation", "submission")
            actor: Who performed the action ("system" or human ID)
            outcome: Result of the action
            details: Additional details about the action
            mcp_proof_link: Optional link to MCP proof
            cyfer_brain_observation_link: Optional link to Cyfer Brain observation
            finding_id: Optional finding ID for indexing

        Returns:
            The created AuditRecord
        """
        # Get previous hash
        previous_hash = self._records[-1].record_hash if self._records else GENESIS_HASH

        # Generate record ID
        record_id = secrets.token_urlsafe(16)

        # Get timestamp
        timestamp = datetime.now(timezone.utc)

        # Compute hash
        record_hash = AuditRecord.compute_hash(
            record_id=record_id,
            timestamp=timestamp,
            action_type=action_type,
            actor=actor,
            outcome=outcome,
            details=details,
            previous_hash=previous_hash,
        )

        # Create record
        record = AuditRecord(
            record_id=record_id,
            timestamp=timestamp,
            action_type=action_type,
            actor=actor,
            outcome=outcome,
            details=details,
            mcp_proof_link=mcp_proof_link,
            cyfer_brain_observation_link=cyfer_brain_observation_link,
            previous_hash=previous_hash,
            record_hash=record_hash,
        )

        # Append to trail (immutable operation)
        self._records.append(record)
        self._records_by_id[record_id] = record

        # Index by finding if provided
        if finding_id:
            if finding_id not in self._records_by_finding:
                self._records_by_finding[finding_id] = []
            self._records_by_finding[finding_id].append(record)

        return record

    def verify_chain(self) -> bool:
        """
        Verify hash chain integrity — detect tampering.

        Returns:
            True if chain is valid

        Raises:
            AuditIntegrityError: If chain is broken
        """
        if not self._records:
            return True

        # Verify first record links to genesis
        if self._records[0].previous_hash != GENESIS_HASH:
            raise AuditIntegrityError(
                f"First record does not link to genesis hash. "
                f"Expected: {GENESIS_HASH}, Got: {self._records[0].previous_hash}"
            )

        # Verify each record's hash
        for i, record in enumerate(self._records):
            expected_hash = AuditRecord.compute_hash(
                record_id=record.record_id,
                timestamp=record.timestamp,
                action_type=record.action_type,
                actor=record.actor,
                outcome=record.outcome,
                details=record.details,
                previous_hash=record.previous_hash,
            )

            if record.record_hash != expected_hash:
                raise AuditIntegrityError(
                    f"Record {record.record_id} hash mismatch. "
                    f"Expected: {expected_hash}, Got: {record.record_hash}. "
                    f"Record may have been tampered with."
                )

            # Verify chain linkage (except first record)
            if i > 0:
                if record.previous_hash != self._records[i - 1].record_hash:
                    raise AuditIntegrityError(
                        f"Record {record.record_id} chain broken. "
                        f"Previous hash does not match preceding record. "
                        f"Chain may have been tampered with."
                    )

        return True

    def get_records_for_finding(self, finding_id: str) -> list[AuditRecord]:
        """
        Get all audit records related to a finding.

        Args:
            finding_id: The finding ID

        Returns:
            List of audit records for the finding
        """
        return self._records_by_finding.get(finding_id, [])

    def get_record(self, record_id: str) -> Optional[AuditRecord]:
        """
        Get a specific audit record by ID.

        Args:
            record_id: The record ID

        Returns:
            The audit record or None
        """
        return self._records_by_id.get(record_id)

    def get_all_records(self) -> list[AuditRecord]:
        """Get all audit records in order."""
        return list(self._records)

    def export_for_compliance(
        self, start: datetime, end: datetime
    ) -> AuditExport:
        """
        Export audit records for compliance review.

        Args:
            start: Start of time range
            end: End of time range

        Returns:
            AuditExport with records in range
        """
        # Filter records by time range
        filtered = [
            r for r in self._records
            if start <= r.timestamp <= end
        ]

        # Verify chain before export
        chain_verified = False
        try:
            self.verify_chain()
            chain_verified = True
        except AuditIntegrityError:
            chain_verified = False

        # Compute export hash
        export_content = json.dumps(
            [r.record_hash for r in filtered],
            sort_keys=True,
        )
        export_hash = hashlib.sha256(export_content.encode()).hexdigest()

        return AuditExport(
            records=filtered,
            start_time=start,
            end_time=end,
            total_records=len(filtered),
            chain_verified=chain_verified,
            export_hash=export_hash,
        )

    def get_records_by_actor(self, actor: str) -> list[AuditRecord]:
        """Get all records by a specific actor."""
        return [r for r in self._records if r.actor == actor]

    def get_records_by_action_type(self, action_type: str) -> list[AuditRecord]:
        """Get all records of a specific action type."""
        return [r for r in self._records if r.action_type == action_type]

    def get_latest_record(self) -> Optional[AuditRecord]:
        """Get the most recent audit record."""
        return self._records[-1] if self._records else None

    def __len__(self) -> int:
        """Get number of records in the trail."""
        return len(self._records)

    # =========================================================================
    # IMMUTABILITY ENFORCEMENT
    # =========================================================================

    def delete_record(self, *args, **kwargs) -> None:
        """
        FORBIDDEN: Cannot delete audit records.

        Raises:
            AuditIntegrityError: Always - audit is append-only
        """
        raise AuditIntegrityError(
            "Cannot delete audit records. "
            "Audit trail is append-only and immutable. "
            "This is a non-negotiable requirement for compliance."
        )

    def modify_record(self, *args, **kwargs) -> None:
        """
        FORBIDDEN: Cannot modify audit records.

        Raises:
            AuditIntegrityError: Always - audit is immutable
        """
        raise AuditIntegrityError(
            "Cannot modify audit records. "
            "Audit trail is immutable. "
            "This is a non-negotiable requirement for compliance."
        )

    def clear(self, *args, **kwargs) -> None:
        """
        FORBIDDEN: Cannot clear audit trail.

        Raises:
            AuditIntegrityError: Always - audit is append-only
        """
        raise AuditIntegrityError(
            "Cannot clear audit trail. "
            "Audit trail is append-only and immutable. "
            "This is a non-negotiable requirement for compliance."
        )
