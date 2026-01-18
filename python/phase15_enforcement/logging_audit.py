"""
Phase 15 Logging Audit Module
Responsible for logging governance events to the immutable record.
"""
import logging
import json
from datetime import datetime
from typing import Any

# Configure structured logger
logger = logging.getLogger("governance_audit")
logger.setLevel(logging.INFO)

def log_event(event_type: str, details: dict[str, Any] | None = None) -> None:
    """
    Log a governance event.
    """
    if not event_type:
        raise ValueError("event_type cannot be empty")

    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": event_type,
        "details": details or {},
        "phase": "PHASE-15"
    }
    logger.info(json.dumps(payload))

def log_block(reason: str, context: dict[str, Any]) -> None:
    """
    Log a blocking event.
    """
    log_event("BLOCK_ACTION", {"reason": reason, "context": context})
