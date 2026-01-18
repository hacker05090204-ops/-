"""
Phase-17 Environment Passthrough

GOVERNANCE CONSTRAINT:
- Env vars available to Phase-15
- Secrets NEVER in UI
- API keys NEVER displayed
- Credentials NEVER logged
- No env modification
"""

import os
import re
from typing import Any


class EnvPassthrough:
    """
    Environment passthrough with governance constraints.
    
    GOVERNANCE GUARANTEES:
    - Env vars available to Phase-15
    - Secrets filtered from display
    - API keys never displayed
    - Credentials never logged
    - No env modification
    - Access logged (without values)
    """
    
    # Sensitive key patterns
    SENSITIVE_PATTERNS = [
        r".*API_KEY.*",
        r".*SECRET.*",
        r".*TOKEN.*",
        r".*PASSWORD.*",
        r".*CREDENTIAL.*",
        r".*PRIVATE.*",
        r".*AUTH.*",
    ]
    
    def __init__(self) -> None:
        """Initialize env passthrough."""
        # Security constraints
        self.exposes_to_ui = False
        self.filters_sensitive_keys = True
        self.logs_credentials = False
        self.modifies_env = False
        
        # Phase-15 access
        self.available_to_phase15 = True
        
        # Logging
        self.logs_access = True
        self.logs_values = False  # Never log values
    
    def get_sensitive_key_patterns(self) -> list[str]:
        """Get list of sensitive key patterns."""
        return self.SENSITIVE_PATTERNS.copy()
    
    def is_sensitive_key(self, key: str) -> bool:
        """
        Check if key is sensitive.
        
        Args:
            key: Environment variable name
            
        Returns:
            True if key matches sensitive pattern
        """
        for pattern in self.SENSITIVE_PATTERNS:
            if re.match(pattern, key, re.IGNORECASE):
                return True
        return False
    
    def filter_for_display(self, env: dict[str, str]) -> dict[str, str]:
        """
        Filter environment for safe display.
        
        Args:
            env: Environment dict
            
        Returns:
            Filtered env (sensitive keys removed)
        """
        filtered = {}
        for key, value in env.items():
            if not self.is_sensitive_key(key):
                filtered[key] = value
        return filtered
    
    def get_for_phase15(self, key: str) -> str | None:
        """
        Get env var for Phase-15 (secure access).
        
        Args:
            key: Environment variable name
            
        Returns:
            Value or None
        """
        # Log access (without value)
        if self.logs_access:
            from phase15_governance.audit import log_event
            log_event(
                event_type="ENV_ACCESS",
                data={"key": key, "value_logged": False},
                attribution="SYSTEM",
            )
        
        return os.environ.get(key)
