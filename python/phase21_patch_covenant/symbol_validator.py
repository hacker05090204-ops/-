"""
Phase-21 Symbol Validator: Static allowlist/denylist validation.

This module provides ONLY structural validation — NO semantic analysis.
"""

from .types import SymbolConstraints, ValidationResult


def validate_symbols(
    symbols: list[str],
    constraints: SymbolConstraints,
) -> ValidationResult:
    """
    Validate symbols against allowlist and denylist.
    
    This function:
    - Checks symbols against static lists
    - Returns pass/fail ONLY (no scoring)
    - Does NOT analyze symbol meaning
    - Does NOT recommend actions
    
    Denylist takes precedence over allowlist.
    
    Args:
        symbols: List of symbols to validate.
        constraints: Static symbol constraints.
        
    Returns:
        ValidationResult with pass/fail and blocked symbols.
    """
    blocked: list[str] = []
    
    for symbol in symbols:
        # Denylist check (takes precedence)
        if symbol in constraints.denylist:
            blocked.append(symbol)
            continue
        
        # Allowlist check
        if symbol not in constraints.allowlist:
            blocked.append(symbol)
    
    return ValidationResult(
        passed=len(blocked) == 0,
        blocked_symbols=tuple(blocked),
        constraint_version=constraints.version,
    )


def create_default_constraints() -> SymbolConstraints:
    """
    Create default symbol constraints.
    
    This is a STATIC configuration — no runtime modification.
    
    Returns:
        SymbolConstraints with default allowlist and denylist.
    """
    return SymbolConstraints(
        allowlist=frozenset({
            # Add allowed symbols here at build time
        }),
        denylist=frozenset({
            # Dangerous built-ins
            "eval",
            "exec",
            "compile",
            "__import__",
            # OS-level
            "os.system",
            "subprocess.call",
            "subprocess.run",
            "subprocess.Popen",
        }),
        version="1.0.0",
    )

