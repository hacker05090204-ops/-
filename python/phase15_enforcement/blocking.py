"""
Phase 15 Blocking Module
Responsible for halting execution when governance violations occur.
"""
from typing import Any, NoReturn

def block_action(reason: str, metadata: dict[str, Any] | None = None) -> NoReturn:
    """
    Block an action by raising a non-recoverable exception.
    """
    raise PermissionError(f"GOVERNANCE BLOCK: {reason} | Metadata: {metadata or {}}")

def halt(reason: str) -> NoReturn:
    """
    Legacy halt alias for blocking.
    """
    block_action(reason)

def block_forbidden(forbidden_list: list[str], content: str = "") -> bool:
    """
    Check content for forbidden words and block if found.
    Args:
        forbidden_list: List of words to block.
        content: Text to check (optional for validation tests).
    """
    if not forbidden_list:
        raise ValueError("forbidden_list cannot be empty")
        
    for word in forbidden_list:
        if word.lower() in content.lower():
            block_action(f"Forbidden word detected: {word}")
    return False
