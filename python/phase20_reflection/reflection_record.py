"""
Phase-20 Reflection Record: Immutable Record Creation

Creates immutable reflection records.
NO update methods. NO delete methods. NO analysis methods.
"""

from datetime import datetime, timezone

from .types import ReflectionRecord
from .reflection_hash import hash_reflection


def create_reflection_record(
    session_id: str,
    reflection_text: str,
    phase15_digest: str,
    phase19_digest: str,
) -> ReflectionRecord:
    """
    Create an immutable reflection record.
    
    Args:
        session_id: UUID of the session.
        reflection_text: Free-form text from human. NOT ANALYZED.
        phase15_digest: SHA-256 digest of Phase-15 logs.
        phase19_digest: SHA-256 digest of Phase-19 export.
        
    Returns:
        Immutable ReflectionRecord.
        
    Note:
        - reflection_text is NOT validated for content
        - reflection_text is NOT analyzed for quality
        - reflection_text is NOT checked for keywords
        - Empty text is valid
        - Any text is valid
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    reflection_hash_value = hash_reflection(reflection_text)
    
    return ReflectionRecord(
        session_id=session_id,
        timestamp=timestamp,
        reflection_text=reflection_text,
        reflection_hash=reflection_hash_value,
        phase15_log_digest=phase15_digest,
        phase19_export_digest=phase19_digest,
        declined=False,
        decline_reason="",
        human_initiated=True,  # ALWAYS True
        actor="HUMAN",  # ALWAYS "HUMAN"
    )


# NO update_record function exists
# NO delete_record function exists
# NO analyze_record function exists
# NO score_record function exists
# NO validate_record function exists
