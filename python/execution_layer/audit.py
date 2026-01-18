"""
Execution Layer Audit Log

Immutable, hash-chained log of all execution actions.

This system assists humans. It does not autonomously hunt, judge, or earn.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import secrets

from execution_layer.types import (
    SafeAction,
    ExecutionToken,
    ExecutionAuditRecord,
)
from execution_layer.errors import AuditIntegrityError


class ExecutionAuditLog:
    """Immutable, hash-chained audit log for all executions.
    
    PROPERTIES:
    - Append-only (no deletions)
    - Hash-chained (tamper-evident)
    - Records all actions with timestamp, actor, outcome
    - Links to evidence artifacts
    - Records human approval tokens
    """
    
    GENESIS_HASH = "0" * 64  # Genesis block hash
    
    def __init__(self) -> None:
        self._records: list[ExecutionAuditRecord] = []
        self._records_by_execution: dict[str, list[ExecutionAuditRecord]] = {}
    
    @property
    def last_hash(self) -> str:
        """Get hash of last record, or genesis hash if empty."""
        if not self._records:
            return self.GENESIS_HASH
        return self._records[-1].record_hash
    
    @property
    def record_count(self) -> int:
        """Get total number of records."""
        return len(self._records)
    
    def record(
        self,
        action: SafeAction,
        actor: str,
        outcome: str,
        token: ExecutionToken,
        evidence_bundle_id: Optional[str] = None,
        execution_id: Optional[str] = None,
    ) -> ExecutionAuditRecord:
        """Record an execution in the audit log (append-only)."""
        record_id = secrets.token_urlsafe(16)
        timestamp = datetime.now(timezone.utc)
        previous_hash = self.last_hash
        
        record_hash = ExecutionAuditRecord.compute_hash(
            record_id=record_id,
            timestamp=timestamp,
            action_type=action.action_type.value,
            actor=actor,
            action_hash=action.compute_hash(),
            outcome=outcome,
            previous_hash=previous_hash,
        )
        
        record = ExecutionAuditRecord(
            record_id=record_id,
            timestamp=timestamp,
            action_type=action.action_type.value,
            actor=actor,
            action=action,
            outcome=outcome,
            evidence_bundle_id=evidence_bundle_id,
            approval_token_id=token.token_id,
            previous_hash=previous_hash,
            record_hash=record_hash,
        )
        
        self._records.append(record)
        
        # Index by execution_id if provided
        if execution_id:
            if execution_id not in self._records_by_execution:
                self._records_by_execution[execution_id] = []
            self._records_by_execution[execution_id].append(record)
        
        return record

    def verify_chain(self) -> bool:
        """Verify hash chain integrity — detect tampering.
        
        Raises:
            AuditIntegrityError: If chain is broken
        """
        if not self._records:
            return True
        
        expected_previous = self.GENESIS_HASH
        
        for i, record in enumerate(self._records):
            # Verify previous hash link
            if record.previous_hash != expected_previous:
                raise AuditIntegrityError(
                    f"Hash chain broken at record {i}: "
                    f"expected previous_hash '{expected_previous}', "
                    f"got '{record.previous_hash}'"
                )
            
            # Verify record hash
            computed_hash = ExecutionAuditRecord.compute_hash(
                record_id=record.record_id,
                timestamp=record.timestamp,
                action_type=record.action_type,
                actor=record.actor,
                action_hash=record.action.compute_hash(),
                outcome=record.outcome,
                previous_hash=record.previous_hash,
            )
            
            if record.record_hash != computed_hash:
                raise AuditIntegrityError(
                    f"Record hash mismatch at record {i}: "
                    f"expected '{computed_hash}', got '{record.record_hash}'"
                )
            
            expected_previous = record.record_hash
        
        return True
    
    def get_records_for_execution(self, execution_id: str) -> list[ExecutionAuditRecord]:
        """Get all audit records for an execution."""
        return self._records_by_execution.get(execution_id, [])
    
    def get_all_records(self) -> list[ExecutionAuditRecord]:
        """Get all audit records."""
        return list(self._records)
    
    def get_records_by_actor(self, actor: str) -> list[ExecutionAuditRecord]:
        """Get all records by a specific actor."""
        return [r for r in self._records if r.actor == actor]
    
    def get_records_by_outcome(self, outcome: str) -> list[ExecutionAuditRecord]:
        """Get all records with a specific outcome."""
        return [r for r in self._records if r.outcome == outcome]
    
    def get_records_in_range(
        self,
        start: datetime,
        end: datetime,
    ) -> list[ExecutionAuditRecord]:
        """Get records within a time range."""
        return [
            r for r in self._records
            if start <= r.timestamp <= end
        ]
    
    def export_for_compliance(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> list[dict]:
        """Export audit records for compliance review."""
        records = self._records
        
        if start:
            records = [r for r in records if r.timestamp >= start]
        if end:
            records = [r for r in records if r.timestamp <= end]
        
        return [
            {
                "record_id": r.record_id,
                "timestamp": r.timestamp.isoformat(),
                "action_type": r.action_type,
                "actor": r.actor,
                "action_id": r.action.action_id,
                "action_target": r.action.target,
                "outcome": r.outcome,
                "evidence_bundle_id": r.evidence_bundle_id,
                "approval_token_id": r.approval_token_id,
                "record_hash": r.record_hash,
            }
            for r in records
        ]
