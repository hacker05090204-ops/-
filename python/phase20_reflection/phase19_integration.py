"""
Phase-20 Phase-19 Integration: Read-Only Integration

Provides read-only access to Phase-19 export digests.
Does NOT modify Phase-19. Does NOT add fields to Phase-19.
"""

import hashlib
from typing import Optional


def get_phase19_export_digest(export_data: Optional[bytes]) -> str:
    """
    Compute SHA-256 digest of Phase-19 export data.
    
    Args:
        export_data: Raw bytes of Phase-19 export, or None if no export.
        
    Returns:
        SHA-256 hex digest, or empty string if no export.
        
    Note:
        - This is READ-ONLY access to Phase-19
        - We do NOT modify Phase-19 exports
        - We do NOT add fields to Phase-19 types
        - We only compute a digest for binding
    """
    if export_data is None:
        return ""
    
    return hashlib.sha256(export_data).hexdigest()


def get_phase15_log_digest(log_data: Optional[bytes]) -> str:
    """
    Compute SHA-256 digest of Phase-15 log data.
    
    Args:
        log_data: Raw bytes of Phase-15 logs, or None if no logs.
        
    Returns:
        SHA-256 hex digest, or empty string if no logs.
        
    Note:
        - This is READ-ONLY access to Phase-15
        - We do NOT modify Phase-15 logs
        - We do NOT add fields to Phase-15 types
        - We only compute a digest for binding
    """
    if log_data is None:
        return ""
    
    return hashlib.sha256(log_data).hexdigest()


# NO modify_phase19_export function exists
# NO add_reflection_to_phase19 function exists
# NO modify_phase15_logs function exists
