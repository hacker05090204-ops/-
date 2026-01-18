"""
Phase-21 Diff Generator: Human-readable diff generation.

This module provides ONLY diff generation — NO analysis or scoring.
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class DiffResult:
    """
    Immutable result of diff generation.
    
    Contains diff text and extracted symbols.
    NO scoring or quality fields.
    """
    
    diff_text: str
    """Human-readable diff text."""
    
    symbols_modified: tuple[str, ...]
    """Symbols extracted from diff (structural only)."""
    
    lines_added: int
    """Number of lines added."""
    
    lines_removed: int
    """Number of lines removed."""


def generate_diff(old_content: str, new_content: str) -> DiffResult:
    """
    Generate human-readable diff between old and new content.
    
    This function:
    - Creates unified diff format
    - Extracts modified symbols (structural only)
    - Does NOT analyze diff quality
    - Does NOT score changes
    - Does NOT recommend actions
    
    Args:
        old_content: Original content.
        new_content: New content.
        
    Returns:
        DiffResult with diff text and metadata.
    """
    import difflib
    
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile="a/file",
        tofile="b/file",
    )
    
    diff_text = "".join(diff)
    
    # Count added/removed lines
    lines_added = 0
    lines_removed = 0
    for line in diff_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            lines_added += 1
        elif line.startswith("-") and not line.startswith("---"):
            lines_removed += 1
    
    # Extract symbols (structural only — no semantic analysis)
    symbols = extract_symbols_from_diff(diff_text)
    
    return DiffResult(
        diff_text=diff_text,
        symbols_modified=tuple(symbols),
        lines_added=lines_added,
        lines_removed=lines_removed,
    )


def extract_symbols_from_diff(diff_text: str) -> list[str]:
    """
    Extract symbol names from diff text.
    
    This is STRUCTURAL extraction only:
    - Looks for function/class definitions
    - Does NOT analyze symbol meaning
    - Does NOT score symbol importance
    
    Args:
        diff_text: Unified diff text.
        
    Returns:
        List of symbol names found in diff.
    """
    symbols: list[str] = []
    
    # Pattern for Python function definitions
    func_pattern = re.compile(r"^[+-]\s*def\s+(\w+)\s*\(", re.MULTILINE)
    
    # Pattern for Python class definitions
    class_pattern = re.compile(r"^[+-]\s*class\s+(\w+)\s*[:\(]", re.MULTILINE)
    
    # Pattern for variable assignments
    var_pattern = re.compile(r"^[+-]\s*(\w+)\s*=", re.MULTILINE)
    
    for match in func_pattern.finditer(diff_text):
        symbols.append(match.group(1))
    
    for match in class_pattern.finditer(diff_text):
        symbols.append(match.group(1))
    
    for match in var_pattern.finditer(diff_text):
        name = match.group(1)
        # Skip common non-symbols
        if name not in {"self", "cls", "_", "__"}:
            symbols.append(name)
    
    # Remove duplicates while preserving order
    seen: set[str] = set()
    unique_symbols: list[str] = []
    for sym in symbols:
        if sym not in seen:
            seen.add(sym)
            unique_symbols.append(sym)
    
    return unique_symbols

