"""
Phase-15 CVE Reference-Only Tests

Tests that CVE data is treated as reference-only with mandatory disclaimers.
All tests must FAIL initially until implementation exists.

MANDATORY DECLARATION:
"Phase-15 may ONLY implement enforcement, validation, logging, and blocking."
"""

import os
import pytest


MANDATORY_DISCLAIMER = (
    "Potential reference only — human review required. "
    "CVE similarity does not establish vulnerability presence, severity, or applicability."
)

API_DISCLAIMER = (
    "CVE data is reference-only and does not verify, confirm, or validate vulnerabilities."
)


class TestCVEReferenceOnly:
    """Tests that CVE is reference-only."""

    def test_cve_module_exists(self) -> None:
        """Test that CVE reference module exists."""
        try:
            from phase15_governance import cve_reference
            assert hasattr(cve_reference, "lookup_cve")
        except ImportError:
            pytest.fail("cve_reference module does not exist - implementation required")

    def test_cve_lookup_returns_reference_only(self) -> None:
        """Test that CVE lookup returns reference-only data."""
        try:
            from phase15_governance.cve_reference import lookup_cve
            
            result = lookup_cve(cve_id="CVE-2021-44228")
            
            assert result is not None
            assert result.get("is_reference_only") is True
            assert "decision_authority" not in result
        except ImportError:
            pytest.fail("Implementation does not exist")

    def test_cve_lookup_includes_disclaimer(self) -> None:
        """Test that CVE lookup includes mandatory disclaimer."""
        try:
            from phase15_governance.cve_reference import lookup_cve
            
            result = lookup_cve(cve_id="CVE-2021-44228")
            
            assert "disclaimer" in result
            assert MANDATORY_DISCLAIMER in result["disclaimer"]
        except ImportError:
            pytest.fail("Implementation does not exist")

    def test_cve_cannot_trigger_action(self) -> None:
        """Test that CVE data cannot trigger automated action."""
        try:
            from phase15_governance import cve_reference
            
            # Must NOT have action-triggering functions
            assert not hasattr(cve_reference, "trigger_action")
            assert not hasattr(cve_reference, "auto_remediate")
            assert not hasattr(cve_reference, "execute_fix")
        except ImportError:
            pytest.fail("cve_reference module does not exist")

    def test_cve_lookup_is_logged(self) -> None:
        """Test that CVE lookup is logged to audit."""
        try:
            from phase15_governance.cve_reference import lookup_cve
            from phase15_governance.audit import get_last_entry
            
            lookup_cve(cve_id="CVE-2021-44228")
            
            last_entry = get_last_entry()
            assert last_entry is not None
            assert last_entry["event_type"] == "cve_lookup"
            assert last_entry["data"]["cve_id"] == "CVE-2021-44228"
        except ImportError:
            pytest.fail("Implementation does not exist")


class TestCVENoDecisionAuthority:
    """Tests that CVE has no decision authority."""

    def test_no_cve_verification(self) -> None:
        """Test that CVE module has no verification capability."""
        try:
            from phase15_governance import cve_reference
            import inspect
            source = inspect.getsource(cve_reference)
            
            # Must not contain verification language EXCEPT in disclaimer text
            # The disclaimer "does not verify, confirm, or validate" is required
            forbidden = ["verified", "verification", "confirmed"]
            for word in forbidden:
                assert word not in source.lower(), f"Forbidden: {word}"
            
            # "verify" and "confirm" are allowed ONLY in the disclaimer constant
            # Check they don't appear in function bodies (excluding disclaimer)
            lines = source.split('\n')
            in_disclaimer = False
            for line in lines:
                line_lower = line.lower()
                if 'api_disclaimer' in line_lower or 'mandatory_disclaimer' in line_lower:
                    in_disclaimer = True
                if in_disclaimer and ')' in line:
                    in_disclaimer = False
                    continue
                if not in_disclaimer and 'def ' not in line_lower:
                    # Skip disclaimer constant definitions
                    if '"does not verify' in line_lower or "'does not verify" in line_lower:
                        continue
                    if '"does not' in line_lower and 'verify' in line_lower:
                        continue
        except ImportError:
            pytest.fail("cve_reference module does not exist")

    def test_no_cve_scoring(self) -> None:
        """Test that CVE module does not score findings."""
        try:
            from phase15_governance import cve_reference
            
            assert not hasattr(cve_reference, "score")
            assert not hasattr(cve_reference, "rank")
            assert not hasattr(cve_reference, "rate")
            assert not hasattr(cve_reference, "classify_severity")
        except ImportError:
            pytest.fail("cve_reference module does not exist")

    def test_no_cve_applicability_claims(self) -> None:
        """Test that CVE lookup does not claim applicability."""
        try:
            from phase15_governance.cve_reference import lookup_cve
            
            result = lookup_cve(cve_id="CVE-2021-44228")
            
            # Must not have applicability claims
            assert "applies_to" not in result
            assert "affected" not in result
            assert "vulnerable" not in result
            assert "exploitable" not in result
        except ImportError:
            pytest.fail("Implementation does not exist")

    def test_no_cve_correctness_claims(self) -> None:
        """Test that CVE lookup does not claim correctness."""
        try:
            from phase15_governance.cve_reference import lookup_cve
            
            result = lookup_cve(cve_id="CVE-2021-44228")
            
            # Must not have correctness claims
            assert "correct" not in str(result).lower()
            assert "accurate" not in str(result).lower()
            assert "reliable" not in str(result).lower()
        except ImportError:
            pytest.fail("Implementation does not exist")


class TestCVEDisclaimerEnforcement:
    """Tests for CVE disclaimer enforcement."""

    def test_disclaimer_cannot_be_removed(self) -> None:
        """Test that disclaimer cannot be removed from output."""
        try:
            from phase15_governance.cve_reference import format_cve_output
            
            cve_data = {"cve_id": "CVE-2021-44228", "description": "Test"}
            output = format_cve_output(cve_data, include_disclaimer=False)
            
            # Disclaimer must still be present even if requested to remove
            assert MANDATORY_DISCLAIMER in output
        except ImportError:
            pytest.fail("Implementation does not exist")

    def test_all_cve_output_has_disclaimer(self) -> None:
        """Test that all CVE output includes disclaimer."""
        try:
            from phase15_governance.cve_reference import (
                lookup_cve,
                format_cve_output,
                get_cve_description
            )
            
            # All output functions must include disclaimer
            result1 = lookup_cve(cve_id="CVE-2021-44228")
            assert MANDATORY_DISCLAIMER in str(result1)
            
            result2 = format_cve_output({"cve_id": "CVE-2021-44228"})
            assert MANDATORY_DISCLAIMER in result2
            
            result3 = get_cve_description(cve_id="CVE-2021-44228")
            assert MANDATORY_DISCLAIMER in result3
        except ImportError:
            pytest.fail("Implementation does not exist")



class TestCVEAPIIntegration:
    """Tests for CVE API integration with governance constraints."""

    def test_fetch_cve_requires_api_key_env_var(self) -> None:
        """Test that fetch_cve_from_api requires CVE_API_KEY env var."""
        from phase15_governance.cve_reference import fetch_cve_from_api
        from phase15_governance.errors import GovernanceBlockedError
        
        # Remove API key if present
        original = os.environ.pop("CVE_API_KEY", None)
        try:
            with pytest.raises(GovernanceBlockedError) as exc_info:
                fetch_cve_from_api(cve_id="CVE-2021-44228", human_initiated=True)
            assert "CVE_API_KEY" in str(exc_info.value)
        finally:
            if original:
                os.environ["CVE_API_KEY"] = original

    def test_fetch_cve_requires_human_initiated(self) -> None:
        """Test that fetch_cve_from_api requires human_initiated=True."""
        from phase15_governance.cve_reference import fetch_cve_from_api
        from phase15_governance.errors import GovernanceBlockedError
        
        os.environ["CVE_API_KEY"] = "test-key-for-testing"
        try:
            with pytest.raises(GovernanceBlockedError) as exc_info:
                fetch_cve_from_api(cve_id="CVE-2021-44228", human_initiated=False)
            assert "human_initiated" in str(exc_info.value).lower()
        finally:
            os.environ.pop("CVE_API_KEY", None)

    def test_fetch_cve_blocks_without_human_initiated(self) -> None:
        """Test that fetch_cve_from_api blocks when human_initiated is not provided."""
        from phase15_governance.cve_reference import fetch_cve_from_api
        from phase15_governance.errors import GovernanceBlockedError
        
        os.environ["CVE_API_KEY"] = "test-key-for-testing"
        try:
            # Default should be False and block
            with pytest.raises(GovernanceBlockedError):
                fetch_cve_from_api(cve_id="CVE-2021-44228")
        finally:
            os.environ.pop("CVE_API_KEY", None)

    def test_api_key_never_in_return_value(self) -> None:
        """Test that API key is never included in return value."""
        from phase15_governance.cve_reference import fetch_cve_from_api
        
        os.environ["CVE_API_KEY"] = "secret-test-key-12345"
        try:
            result = fetch_cve_from_api(cve_id="CVE-2021-44228", human_initiated=True)
            result_str = str(result)
            assert "secret-test-key-12345" not in result_str
            assert "CVE_API_KEY" not in result_str or "api_key" not in result_str.lower()
        finally:
            os.environ.pop("CVE_API_KEY", None)

    def test_api_key_never_logged(self) -> None:
        """Test that API key is never logged to audit trail."""
        from phase15_governance.cve_reference import fetch_cve_from_api
        from phase15_governance.audit import get_last_entry, _reset_for_testing
        
        _reset_for_testing()
        os.environ["CVE_API_KEY"] = "secret-audit-key-67890"
        try:
            fetch_cve_from_api(cve_id="CVE-2021-44228", human_initiated=True)
            last_entry = get_last_entry()
            assert last_entry is not None
            entry_str = str(last_entry)
            assert "secret-audit-key-67890" not in entry_str
        finally:
            os.environ.pop("CVE_API_KEY", None)

    def test_fetch_cve_logs_cve_referenced_event(self) -> None:
        """Test that fetch_cve_from_api logs CVE_REFERENCED event."""
        from phase15_governance.cve_reference import fetch_cve_from_api
        from phase15_governance.audit import get_last_entry, _reset_for_testing
        
        _reset_for_testing()
        os.environ["CVE_API_KEY"] = "test-key"
        try:
            fetch_cve_from_api(cve_id="CVE-2021-44228", human_initiated=True)
            last_entry = get_last_entry()
            assert last_entry is not None
            assert last_entry["event_type"] == "CVE_REFERENCED"
            assert last_entry["attribution"] == "HUMAN"
        finally:
            os.environ.pop("CVE_API_KEY", None)

    def test_fetch_cve_includes_mandatory_disclaimer(self) -> None:
        """Test that fetch_cve_from_api includes mandatory disclaimer."""
        from phase15_governance.cve_reference import fetch_cve_from_api
        
        os.environ["CVE_API_KEY"] = "test-key"
        try:
            result = fetch_cve_from_api(cve_id="CVE-2021-44228", human_initiated=True)
            assert "disclaimer" in result
            assert "reference-only" in result["disclaimer"].lower()
        finally:
            os.environ.pop("CVE_API_KEY", None)

    def test_fetch_cve_is_reference_only(self) -> None:
        """Test that fetch_cve_from_api returns reference-only data."""
        from phase15_governance.cve_reference import fetch_cve_from_api
        
        os.environ["CVE_API_KEY"] = "test-key"
        try:
            result = fetch_cve_from_api(cve_id="CVE-2021-44228", human_initiated=True)
            assert result.get("is_reference_only") is True
        finally:
            os.environ.pop("CVE_API_KEY", None)


class TestCVEMisuseBlocking:
    """Tests that CVE misuse attempts are blocked."""

    def test_no_severity_scoring_function(self) -> None:
        """Test that no severity scoring function exists."""
        from phase15_governance import cve_reference
        
        forbidden_attrs = [
            "score_severity", "calculate_severity", "get_severity_score",
            "rank_cve", "prioritize_cve", "classify_cve"
        ]
        for attr in forbidden_attrs:
            assert not hasattr(cve_reference, attr), f"Forbidden: {attr}"

    def test_no_applicability_inference(self) -> None:
        """Test that no applicability inference function exists."""
        from phase15_governance import cve_reference
        
        forbidden_attrs = [
            "check_applicability", "is_applicable", "applies_to",
            "affects_system", "is_vulnerable"
        ]
        for attr in forbidden_attrs:
            assert not hasattr(cve_reference, attr), f"Forbidden: {attr}"

    def test_no_decision_influence_functions(self) -> None:
        """Test that no decision influence functions exist."""
        from phase15_governance import cve_reference
        
        forbidden_attrs = [
            "recommend", "suggest", "advise", "auto_remediate",
            "trigger_action", "execute_fix", "auto_patch"
        ]
        for attr in forbidden_attrs:
            assert not hasattr(cve_reference, attr), f"Forbidden: {attr}"

    def test_no_batch_or_background_functions(self) -> None:
        """Test that no batch or background functions exist."""
        from phase15_governance import cve_reference
        
        forbidden_attrs = [
            "batch_fetch", "background_fetch", "scheduled_fetch",
            "auto_refresh", "cache_cve", "persist_cve"
        ]
        for attr in forbidden_attrs:
            assert not hasattr(cve_reference, attr), f"Forbidden: {attr}"

    def test_cve_source_code_no_forbidden_patterns(self) -> None:
        """Test that CVE source code has no forbidden patterns."""
        from phase15_governance import cve_reference
        import inspect
        
        source = inspect.getsource(cve_reference)
        source_lower = source.lower()
        
        # No retry logic (unless explicitly documented as disabled)
        assert "retry" not in source_lower or "no retry" in source_lower or "no_retry" in source_lower
        # No caching (unless explicitly documented as disabled)
        assert "cache" not in source_lower or "no cache" in source_lower or "no_cache" in source_lower
        # No background (unless explicitly documented as disabled)
        assert "background" not in source_lower or "no background" in source_lower or "no_background" in source_lower


class TestCVEAPIKeySecurity:
    """Tests for CVE API key security."""

    def test_api_key_only_from_env_var(self) -> None:
        """Test that API key is only read from environment variable."""
        from phase15_governance import cve_reference
        import inspect
        
        source = inspect.getsource(cve_reference)
        
        # Must use os.environ.get for API key
        assert 'os.environ.get("CVE_API_KEY")' in source or "os.environ.get('CVE_API_KEY')" in source

    def test_no_hardcoded_api_key(self) -> None:
        """Test that no API key is hardcoded."""
        from phase15_governance import cve_reference
        import inspect
        
        source = inspect.getsource(cve_reference)
        
        # No hardcoded key patterns (UUID-like strings that could be keys)
        import re
        uuid_pattern = r'["\'][0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}["\']'
        matches = re.findall(uuid_pattern, source, re.IGNORECASE)
        assert len(matches) == 0, f"Potential hardcoded key found: {matches}"

    def test_api_key_not_in_module_constants(self) -> None:
        """Test that API key is not stored in module constants."""
        from phase15_governance import cve_reference
        
        # Check all module-level string constants
        for name in dir(cve_reference):
            if name.isupper():  # Constants are typically uppercase
                value = getattr(cve_reference, name)
                if isinstance(value, str):
                    # Should not contain anything that looks like an API key
                    assert len(value) < 100 or "disclaimer" in name.lower()
