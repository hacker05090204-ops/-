"""
Phase-20 Decline: Human Decline Handling

Handles human decline to provide reflection.
Decline is ALWAYS allowed. Decline reason is NOT validated.
"""

from datetime import datetime, timezone

from .types import ReflectionRecord
from .reflection_hash import hash_reflection


def create_decline_record(
    session_id: str,
    reason: str,
    phase15_digest: str = "",
    phase19_digest: str = "",
) -> ReflectionRecord:
    """
    Create a decline record when human declines to reflect.
    
    Args:
        session_id: UUID of the session.
        reason: Free-form reason for decline. NOT VALIDATED.
        phase15_digest: SHA-256 digest of Phase-15 logs (optional).
        phase19_digest: SHA-256 digest of Phase-19 export (optional).
        
    Returns:
        Immutable ReflectionRecord with declined=True.
        
    Note:
        - Decline is ALWAYS allowed
        - Reason is NOT validated for content
        - Reason is NOT analyzed for quality
        - Empty reason is valid
        - Any reason is valid
        - System CANNOT block decline
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Hash of empty string for declined reflections
    reflection_hash_value = hash_reflection("")
    
    return ReflectionRecord(
        session_id=session_id,
        timestamp=timestamp,
        reflection_text="",  # Empty for decline
        reflection_hash=reflection_hash_value,
        phase15_log_digest=phase15_digest,
        phase19_export_digest=phase19_digest,
        declined=True,
        decline_reason=reason,  # NOT VALIDATED
        human_initiated=True,  # ALWAYS True
        actor="HUMAN",  # ALWAYS "HUMAN"
    )


# NO validate_decline_reason function exists
# NO block_decline function exists
# NO require_reason function exists
