"""
Phase-20 Reflection Logger: Audit Logging

Logs reflection records to audit trail.
NO content analysis. NO background threads. NO async processing.
"""

import json
from pathlib import Path
from typing import Optional

from .types import ReflectionRecord


# In-memory storage for session lookups (append-only)
_reflection_store: dict[str, list[ReflectionRecord]] = {}


def log_reflection(
    record: ReflectionRecord,
    audit_path: Optional[Path] = None,
) -> None:
    """
    Log a reflection record to the audit trail.
    
    Args:
        record: Immutable ReflectionRecord to log.
        audit_path: Optional path to audit file. If None, uses in-memory store.
        
    Note:
        - Logging is SYNCHRONOUS (no background threads)
        - Content is NOT analyzed during logging
        - Content is NOT indexed for search
        - Record is stored as-is in JSON format
    """
    # Store in memory for session lookups
    if record.session_id not in _reflection_store:
        _reflection_store[record.session_id] = []
    _reflection_store[record.session_id].append(record)
    
    # If audit path provided, append to file
    if audit_path is not None:
        _append_to_audit_file(record, audit_path)


def _append_to_audit_file(record: ReflectionRecord, audit_path: Path) -> None:
    """
    Append record to audit file in JSON Lines format.
    
    This is append-only. Records cannot be modified or deleted.
    """
    record_dict = {
        "session_id": record.session_id,
        "timestamp": record.timestamp,
        "reflection_text": record.reflection_text,
        "reflection_hash": record.reflection_hash,
        "phase15_log_digest": record.phase15_log_digest,
        "phase19_export_digest": record.phase19_export_digest,
        "declined": record.declined,
        "decline_reason": record.decline_reason,
        "human_initiated": record.human_initiated,
        "actor": record.actor,
    }
    
    with open(audit_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record_dict) + "\n")


def has_reflection_for_session(session_id: str) -> bool:
    """
    Check if a reflection exists for a session.
    
    Args:
        session_id: UUID of the session.
        
    Returns:
        True if any reflection (including decline) exists.
        
    Note:
        This does NOT analyze the reflection content.
        It only checks for existence.
    """
    return session_id in _reflection_store and len(_reflection_store[session_id]) > 0


def clear_store_for_testing() -> None:
    """
    Clear the in-memory store. FOR TESTING ONLY.
    
    This should only be called in test fixtures.
    """
    _reflection_store.clear()


# NO search_reflections function exists
# NO index_reflections function exists
# NO analyze_reflections function exists
