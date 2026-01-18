"""
Phase-21 Symbol Validation Tests

Tests verifying allowlist/denylist enforcement.
"""

import pytest


class TestAllowlistEnforcement:
    """Tests verifying symbol allowlist enforcement."""

    def test_allowed_symbol_passes(self, sample_allowlist: frozenset) -> None:
        """Symbols in allowlist must pass validation."""
        from phase21_patch_covenant.symbol_validator import validate_symbols
        from phase21_patch_covenant.types import SymbolConstraints
        
        constraints = SymbolConstraints(
            allowlist=sample_allowlist,
            denylist=frozenset(),
            version="1.0.0",
        )
        
        result = validate_symbols(
            symbols=["allowed_function"],
            constraints=constraints,
        )
        
        assert result.passed is True
        assert result.blocked_symbols == ()

    def test_disallowed_symbol_fails(self, sample_allowlist: frozenset) -> None:
        """Symbols not in allowlist must fail validation."""
        from phase21_patch_covenant.symbol_validator import validate_symbols
        from phase21_patch_covenant.types import SymbolConstraints
        
        constraints = SymbolConstraints(
            allowlist=sample_allowlist,
            denylist=frozenset(),
            version="1.0.0",
        )
        
        result = validate_symbols(
            symbols=["not_in_allowlist"],
            constraints=constraints,
        )
        
        assert result.passed is False
        assert "not_in_allowlist" in result.blocked_symbols

    def test_multiple_symbols_all_allowed(self, sample_allowlist: frozenset) -> None:
        """All symbols must be in allowlist to pass."""
        from phase21_patch_covenant.symbol_validator import validate_symbols
        from phase21_patch_covenant.types import SymbolConstraints
        
        constraints = SymbolConstraints(
            allowlist=sample_allowlist,
            denylist=frozenset(),
            version="1.0.0",
        )
        
        result = validate_symbols(
            symbols=["allowed_function", "safe_method"],
            constraints=constraints,
        )
        
        assert result.passed is True

    def test_one_disallowed_fails_all(self, sample_allowlist: frozenset) -> None:
        """One disallowed symbol must fail entire validation."""
        from phase21_patch_covenant.symbol_validator import validate_symbols
        from phase21_patch_covenant.types import SymbolConstraints
        
        constraints = SymbolConstraints(
            allowlist=sample_allowlist,
            denylist=frozenset(),
            version="1.0.0",
        )
        
        result = validate_symbols(
            symbols=["allowed_function", "not_allowed"],
            constraints=constraints,
        )
        
        assert result.passed is False


class TestDenylistEnforcement:
    """Tests verifying symbol denylist enforcement."""

    def test_denied_symbol_fails(self, sample_denylist: frozenset) -> None:
        """Symbols in denylist must fail validation."""
        from phase21_patch_covenant.symbol_validator import validate_symbols
        from phase21_patch_covenant.types import SymbolConstraints
        
        constraints = SymbolConstraints(
            allowlist=frozenset({"any_symbol", "eval"}),  # Even if in allowlist
            denylist=sample_denylist,
            version="1.0.0",
        )
        
        result = validate_symbols(
            symbols=["eval"],
            constraints=constraints,
        )
        
        assert result.passed is False
        assert "eval" in result.blocked_symbols

    def test_denylist_takes_precedence(self, sample_allowlist: frozenset, sample_denylist: frozenset) -> None:
        """Denylist must take precedence over allowlist."""
        from phase21_patch_covenant.symbol_validator import validate_symbols
        from phase21_patch_covenant.types import SymbolConstraints
        
        # Symbol in both lists
        constraints = SymbolConstraints(
            allowlist=frozenset({"eval"}),  # In allowlist
            denylist=frozenset({"eval"}),   # Also in denylist
            version="1.0.0",
        )
        
        result = validate_symbols(
            symbols=["eval"],
            constraints=constraints,
        )
        
        # Denylist wins
        assert result.passed is False


class TestStaticLists:
    """Tests verifying lists are static."""

    def test_allowlist_is_frozenset(self) -> None:
        """Allowlist must be frozenset (immutable)."""
        from phase21_patch_covenant.types import SymbolConstraints
        
        constraints = SymbolConstraints(
            allowlist=frozenset({"func1"}),
            denylist=frozenset(),
            version="1.0.0",
        )
        
        assert isinstance(constraints.allowlist, frozenset)
        
        # Cannot modify
        with pytest.raises(AttributeError):
            constraints.allowlist.add("new_symbol")

    def test_denylist_is_frozenset(self) -> None:
        """Denylist must be frozenset (immutable)."""
        from phase21_patch_covenant.types import SymbolConstraints
        
        constraints = SymbolConstraints(
            allowlist=frozenset(),
            denylist=frozenset({"eval"}),
            version="1.0.0",
        )
        
        assert isinstance(constraints.denylist, frozenset)


class TestValidationResultNoScoring:
    """Tests verifying validation returns pass/fail only."""

    def test_result_has_no_score(self, sample_allowlist: frozenset) -> None:
        """Validation result must not have score field."""
        from phase21_patch_covenant.symbol_validator import validate_symbols
        from phase21_patch_covenant.types import SymbolConstraints
        
        constraints = SymbolConstraints(
            allowlist=sample_allowlist,
            denylist=frozenset(),
            version="1.0.0",
        )
        
        result = validate_symbols(
            symbols=["allowed_function"],
            constraints=constraints,
        )
        
        assert not hasattr(result, "score")
        assert not hasattr(result, "confidence")
        assert not hasattr(result, "quality")

    def test_result_is_binary(self, sample_allowlist: frozenset) -> None:
        """Validation result must be binary (pass/fail)."""
        from phase21_patch_covenant.symbol_validator import validate_symbols
        from phase21_patch_covenant.types import SymbolConstraints
        
        constraints = SymbolConstraints(
            allowlist=sample_allowlist,
            denylist=frozenset(),
            version="1.0.0",
        )
        
        result = validate_symbols(
            symbols=["allowed_function"],
            constraints=constraints,
        )
        
        assert isinstance(result.passed, bool)

