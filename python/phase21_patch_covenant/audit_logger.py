"""
Phase-21 Audit Logger: Append-only audit logging.

This module provides ONLY logging — NO analysis, NO modification.
"""

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Union

from .types import PatchRecord, PatchBinding


class PatchAuditLogger:
    """
    Append-only audit logger for patch operations.
    
    This logger:
    - Appends entries only (no modification)
    - Does NOT analyze content
    - Does NOT score entries
    - Does NOT delete entries
    """
    
    def __init__(self, log_path: Path) -> None:
        """
        Initialize audit logger.
        
        Args:
            log_path: Path to audit log file.
        """
        self._log_path = log_path
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log_patch_record(self, record: PatchRecord) -> None:
        """
        Log a patch record.
        
        This function:
        - Appends record to log
        - Does NOT analyze record
        - Does NOT modify existing entries
        
        Args:
            record: PatchRecord to log.
        """
        entry = {
            "type": "patch_record",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": asdict(record),
        }
        self._append_entry(entry)
    
    def log_patch_binding(self, binding: PatchBinding) -> None:
        """
        Log a patch binding.
        
        This function:
        - Appends binding to log
        - Does NOT analyze binding
        - Does NOT modify existing entries
        
        Args:
            binding: PatchBinding to log.
        """
        entry = {
            "type": "patch_binding",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": asdict(binding),
        }
        self._append_entry(entry)
    
    def log_validation_result(
        self,
        patch_id: str,
        passed: bool,
        blocked_symbols: tuple[str, ...],
    ) -> None:
        """
        Log a validation result.
        
        This function:
        - Appends result to log
        - Does NOT analyze result
        - Does NOT modify existing entries
        
        Args:
            patch_id: UUID of the patch.
            passed: Whether validation passed.
            blocked_symbols: Symbols that caused failure.
        """
        entry = {
            "type": "validation_result",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "patch_id": patch_id,
                "passed": passed,
                "blocked_symbols": list(blocked_symbols),
            },
        }
        self._append_entry(entry)
    
    def _append_entry(self, entry: dict) -> None:
        """
        Append entry to log file.
        
        This is APPEND-ONLY — no modification of existing entries.
        
        Args:
            entry: Log entry to append.
        """
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

