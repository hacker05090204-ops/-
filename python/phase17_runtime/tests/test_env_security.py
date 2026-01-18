"""
Phase-17 Tests: Environment Variable Security

GOVERNANCE CONSTRAINT:
- Env vars available to Phase-15
- Secrets NEVER in UI
- API keys NEVER displayed
- Credentials NEVER logged

Risk Mitigated: RISK-17-006 (Packaging Abuse)
"""

import pytest
import inspect


class TestEnvSecurity:
    """Tests verifying environment variable security."""

    def test_env_passthrough_exists(self) -> None:
        """Env passthrough module MUST exist."""
        from phase17_runtime.env_passthrough import EnvPassthrough
        
        passthrough = EnvPassthrough()
        assert passthrough is not None

    def test_env_vars_not_in_ui(self) -> None:
        """Env vars MUST NOT be exposed to UI."""
        from phase17_runtime.env_passthrough import EnvPassthrough
        
        passthrough = EnvPassthrough()
        
        assert passthrough.exposes_to_ui is False
        assert not hasattr(passthrough, "get_for_ui")
        assert not hasattr(passthrough, "display_env")

    def test_api_key_not_displayed(self) -> None:
        """API keys MUST NOT be displayed."""
        from phase17_runtime.env_passthrough import EnvPassthrough
        
        passthrough = EnvPassthrough()
        
        # Should filter sensitive keys
        assert passthrough.filters_sensitive_keys is True
        
        sensitive_keys = passthrough.get_sensitive_key_patterns()
        assert "API_KEY" in sensitive_keys or "api_key" in str(sensitive_keys).lower()

    def test_credentials_not_logged(self) -> None:
        """Credentials MUST NOT be logged."""
        from phase17_runtime.env_passthrough import EnvPassthrough
        
        passthrough = EnvPassthrough()
        
        assert passthrough.logs_credentials is False

    def test_env_available_to_phase15(self) -> None:
        """Env vars MUST be available to Phase-15."""
        from phase17_runtime.env_passthrough import EnvPassthrough
        
        passthrough = EnvPassthrough()
        
        # Phase-15 should be able to access env vars
        assert passthrough.available_to_phase15 is True

    def test_no_env_in_source_code(self) -> None:
        """Source MUST NOT hardcode sensitive env values."""
        from phase17_runtime import env_passthrough
        
        source = inspect.getsource(env_passthrough)
        
        # No hardcoded secrets
        assert "CVE_API_KEY=" not in source
        assert "api_key=" not in source.lower() or "api_key=None" in source.lower()

    def test_sensitive_keys_filtered(self) -> None:
        """Sensitive keys MUST be filtered from display."""
        from phase17_runtime.env_passthrough import EnvPassthrough
        
        passthrough = EnvPassthrough()
        
        # Test filtering
        test_env = {
            "PATH": "/usr/bin",
            "CVE_API_KEY": "secret123",
            "HOME": "/home/user",
            "SECRET_TOKEN": "token456",
        }
        
        filtered = passthrough.filter_for_display(test_env)
        
        assert "CVE_API_KEY" not in filtered
        assert "SECRET_TOKEN" not in filtered
        assert "PATH" in filtered
        assert "HOME" in filtered

    def test_no_env_dump_method(self) -> None:
        """Passthrough MUST NOT have env dump method."""
        from phase17_runtime.env_passthrough import EnvPassthrough
        
        passthrough = EnvPassthrough()
        
        assert not hasattr(passthrough, "dump_all")
        assert not hasattr(passthrough, "export_env")
        assert not hasattr(passthrough, "serialize_env")

    def test_env_access_logged(self) -> None:
        """Env access SHOULD be logged (without values)."""
        from phase17_runtime.env_passthrough import EnvPassthrough
        
        passthrough = EnvPassthrough()
        
        assert passthrough.logs_access is True
        assert passthrough.logs_values is False

    def test_no_env_modification(self) -> None:
        """Passthrough MUST NOT modify env vars."""
        from phase17_runtime.env_passthrough import EnvPassthrough
        
        passthrough = EnvPassthrough()
        
        assert not hasattr(passthrough, "set_env")
        assert not hasattr(passthrough, "modify_env")
        assert passthrough.modifies_env is False
