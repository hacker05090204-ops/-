"""
PHASE 01 TESTS — 2026 RE-IMPLEMENTATION

These tests validate the core constants module for Phase-01.
All tests are written BEFORE implementation (TDD approach).

Test Categories:
1. Existence Tests - Verify all constants are defined
2. Value Tests - Verify constants have correct values
3. Type Tests - Verify constants have correct types
4. Invariant Tests - Verify all invariants are True
5. Security Tests - Verify no forbidden behaviors
"""

import pytest
import sys
import importlib
from typing import Final


class TestPhase01ConstantsExist:
    """Test that all required constants are defined."""

    def test_system_id_exists(self):
        """SYSTEM_ID constant must exist."""
        from phase01_core.constants import SYSTEM_ID
        assert SYSTEM_ID is not None

    def test_system_name_exists(self):
        """SYSTEM_NAME constant must exist."""
        from phase01_core.constants import SYSTEM_NAME
        assert SYSTEM_NAME is not None

    def test_reimplementation_date_exists(self):
        """REIMPLEMENTATION_DATE constant must exist."""
        from phase01_core.constants import REIMPLEMENTATION_DATE
        assert REIMPLEMENTATION_DATE is not None

    def test_version_exists(self):
        """VERSION constant must exist."""
        from phase01_core.constants import VERSION
        assert VERSION is not None

    def test_version_tuple_exists(self):
        """VERSION_TUPLE constant must exist."""
        from phase01_core.constants import VERSION_TUPLE
        assert VERSION_TUPLE is not None

    def test_invariant_human_authority_exists(self):
        """INVARIANT_HUMAN_AUTHORITY constant must exist."""
        from phase01_core.constants import INVARIANT_HUMAN_AUTHORITY
        assert INVARIANT_HUMAN_AUTHORITY is not None

    def test_invariant_no_auto_exploit_exists(self):
        """INVARIANT_NO_AUTO_EXPLOIT constant must exist."""
        from phase01_core.constants import INVARIANT_NO_AUTO_EXPLOIT
        assert INVARIANT_NO_AUTO_EXPLOIT is not None

    def test_invariant_audit_required_exists(self):
        """INVARIANT_AUDIT_REQUIRED constant must exist."""
        from phase01_core.constants import INVARIANT_AUDIT_REQUIRED
        assert INVARIANT_AUDIT_REQUIRED is not None

    def test_invariant_no_scoring_exists(self):
        """INVARIANT_NO_SCORING constant must exist."""
        from phase01_core.constants import INVARIANT_NO_SCORING
        assert INVARIANT_NO_SCORING is not None

    def test_max_operation_timeout_exists(self):
        """MAX_OPERATION_TIMEOUT_SECONDS constant must exist."""
        from phase01_core.constants import MAX_OPERATION_TIMEOUT_SECONDS
        assert MAX_OPERATION_TIMEOUT_SECONDS is not None

    def test_require_human_confirmation_exists(self):
        """REQUIRE_HUMAN_CONFIRMATION constant must exist."""
        from phase01_core.constants import REQUIRE_HUMAN_CONFIRMATION
        assert REQUIRE_HUMAN_CONFIRMATION is not None

    def test_governance_version_exists(self):
        """GOVERNANCE_VERSION constant must exist."""
        from phase01_core.constants import GOVERNANCE_VERSION
        assert GOVERNANCE_VERSION is not None

    def test_reimplementation_marker_exists(self):
        """REIMPLEMENTATION_MARKER constant must exist."""
        from phase01_core.constants import REIMPLEMENTATION_MARKER
        assert REIMPLEMENTATION_MARKER is not None


class TestPhase01ConstantValues:
    """Test that constants have the correct values."""

    def test_system_name_value(self):
        """SYSTEM_NAME must be 'kali-mcp-toolkit'."""
        from phase01_core.constants import SYSTEM_NAME
        assert SYSTEM_NAME == "kali-mcp-toolkit"

    def test_reimplementation_date_value(self):
        """REIMPLEMENTATION_DATE must be '2026-01-20'."""
        from phase01_core.constants import REIMPLEMENTATION_DATE
        assert REIMPLEMENTATION_DATE == "2026-01-20"

    def test_version_value(self):
        """VERSION must be '1.0.0'."""
        from phase01_core.constants import VERSION
        assert VERSION == "1.0.0"

    def test_version_tuple_value(self):
        """VERSION_TUPLE must be (1, 0, 0)."""
        from phase01_core.constants import VERSION_TUPLE
        assert VERSION_TUPLE == (1, 0, 0)

    def test_invariant_human_authority_is_true(self):
        """INVARIANT_HUMAN_AUTHORITY must be True."""
        from phase01_core.constants import INVARIANT_HUMAN_AUTHORITY
        assert INVARIANT_HUMAN_AUTHORITY is True

    def test_invariant_no_auto_exploit_is_true(self):
        """INVARIANT_NO_AUTO_EXPLOIT must be True."""
        from phase01_core.constants import INVARIANT_NO_AUTO_EXPLOIT
        assert INVARIANT_NO_AUTO_EXPLOIT is True

    def test_invariant_audit_required_is_true(self):
        """INVARIANT_AUDIT_REQUIRED must be True."""
        from phase01_core.constants import INVARIANT_AUDIT_REQUIRED
        assert INVARIANT_AUDIT_REQUIRED is True

    def test_invariant_no_scoring_is_true(self):
        """INVARIANT_NO_SCORING must be True."""
        from phase01_core.constants import INVARIANT_NO_SCORING
        assert INVARIANT_NO_SCORING is True

    def test_require_human_confirmation_is_true(self):
        """REQUIRE_HUMAN_CONFIRMATION must be True."""
        from phase01_core.constants import REQUIRE_HUMAN_CONFIRMATION
        assert REQUIRE_HUMAN_CONFIRMATION is True

    def test_max_operation_timeout_positive(self):
        """MAX_OPERATION_TIMEOUT_SECONDS must be positive."""
        from phase01_core.constants import MAX_OPERATION_TIMEOUT_SECONDS
        assert MAX_OPERATION_TIMEOUT_SECONDS > 0
        assert MAX_OPERATION_TIMEOUT_SECONDS == 300

    def test_governance_version_value(self):
        """GOVERNANCE_VERSION must be '2026.1'."""
        from phase01_core.constants import GOVERNANCE_VERSION
        assert GOVERNANCE_VERSION == "2026.1"

    def test_reimplementation_marker_value(self):
        """REIMPLEMENTATION_MARKER must be 'REIMPL-2026'."""
        from phase01_core.constants import REIMPLEMENTATION_MARKER
        assert REIMPLEMENTATION_MARKER == "REIMPL-2026"


class TestPhase01ConstantTypes:
    """Test that constants have the correct types."""

    def test_system_id_is_string(self):
        """SYSTEM_ID must be a string."""
        from phase01_core.constants import SYSTEM_ID
        assert isinstance(SYSTEM_ID, str)

    def test_system_name_is_string(self):
        """SYSTEM_NAME must be a string."""
        from phase01_core.constants import SYSTEM_NAME
        assert isinstance(SYSTEM_NAME, str)

    def test_version_is_string(self):
        """VERSION must be a string."""
        from phase01_core.constants import VERSION
        assert isinstance(VERSION, str)

    def test_version_tuple_is_tuple(self):
        """VERSION_TUPLE must be a tuple of 3 integers."""
        from phase01_core.constants import VERSION_TUPLE
        assert isinstance(VERSION_TUPLE, tuple)
        assert len(VERSION_TUPLE) == 3
        assert all(isinstance(v, int) for v in VERSION_TUPLE)

    def test_invariants_are_bool(self):
        """All invariants must be bool."""
        from phase01_core.constants import (
            INVARIANT_HUMAN_AUTHORITY,
            INVARIANT_NO_AUTO_EXPLOIT,
            INVARIANT_AUDIT_REQUIRED,
            INVARIANT_NO_SCORING,
        )
        assert isinstance(INVARIANT_HUMAN_AUTHORITY, bool)
        assert isinstance(INVARIANT_NO_AUTO_EXPLOIT, bool)
        assert isinstance(INVARIANT_AUDIT_REQUIRED, bool)
        assert isinstance(INVARIANT_NO_SCORING, bool)

    def test_max_timeout_is_int(self):
        """MAX_OPERATION_TIMEOUT_SECONDS must be an int."""
        from phase01_core.constants import MAX_OPERATION_TIMEOUT_SECONDS
        assert isinstance(MAX_OPERATION_TIMEOUT_SECONDS, int)


class TestPhase01ModulePackageExports:
    """Test that __init__.py re-exports all constants."""

    def test_package_exports_all_constants(self):
        """phase01_core package must export all constants."""
        from phase01_core import (
            SYSTEM_ID,
            SYSTEM_NAME,
            REIMPLEMENTATION_DATE,
            VERSION,
            VERSION_TUPLE,
            INVARIANT_HUMAN_AUTHORITY,
            INVARIANT_NO_AUTO_EXPLOIT,
            INVARIANT_AUDIT_REQUIRED,
            INVARIANT_NO_SCORING,
            MAX_OPERATION_TIMEOUT_SECONDS,
            REQUIRE_HUMAN_CONFIRMATION,
            GOVERNANCE_VERSION,
            REIMPLEMENTATION_MARKER,
        )
        # If we get here, all imports succeeded
        assert True


class TestPhase01NoForbiddenBehaviors:
    """Test that module has no forbidden behaviors."""

    def test_no_scoring_constant_is_true(self):
        """NO_SCORING invariant must prevent any scoring logic."""
        from phase01_core.constants import INVARIANT_NO_SCORING
        assert INVARIANT_NO_SCORING is True

    def test_human_authority_required(self):
        """HUMAN_AUTHORITY invariant must require human authorization."""
        from phase01_core.constants import INVARIANT_HUMAN_AUTHORITY
        assert INVARIANT_HUMAN_AUTHORITY is True

    def test_no_auto_exploit(self):
        """NO_AUTO_EXPLOIT invariant must prevent automatic exploitation."""
        from phase01_core.constants import INVARIANT_NO_AUTO_EXPLOIT
        assert INVARIANT_NO_AUTO_EXPLOIT is True

    def test_module_has_no_functions(self):
        """constants.py should have no callable functions (pure constants)."""
        from phase01_core import constants
        public_attrs = [a for a in dir(constants) if not a.startswith('_')]
        for attr_name in public_attrs:
            attr = getattr(constants, attr_name)
            # Allow type annotations (Final, etc.) but no functions
            if attr_name not in ('Final',):
                assert not callable(attr), f"{attr_name} should not be callable"


class TestPhase01NoSideEffectsOnImport:
    """Test that importing the module causes no side effects."""

    def test_import_does_not_create_files(self, tmp_path, monkeypatch):
        """Importing should not create any files."""
        import os
        monkeypatch.chdir(tmp_path)
        
        # Clear any cached imports
        modules_to_remove = [k for k in sys.modules.keys() if 'phase01' in k]
        for mod in modules_to_remove:
            del sys.modules[mod]
        
        initial_files = set(os.listdir(tmp_path))
        
        # Re-import
        import phase01_core.constants
        importlib.reload(phase01_core.constants)
        
        final_files = set(os.listdir(tmp_path))
        assert initial_files == final_files, "Import created files"

    def test_import_does_not_print(self, capsys):
        """Importing should not print anything."""
        # Clear cached imports
        modules_to_remove = [k for k in sys.modules.keys() if 'phase01' in k]
        for mod in modules_to_remove:
            del sys.modules[mod]
        
        import phase01_core.constants
        importlib.reload(phase01_core.constants)
        
        captured = capsys.readouterr()
        assert captured.out == "", "Import printed to stdout"
        assert captured.err == "", "Import printed to stderr"


class TestPhase01SystemIDFormat:
    """Test SYSTEM_ID has valid format."""

    def test_system_id_is_not_empty(self):
        """SYSTEM_ID must not be empty."""
        from phase01_core.constants import SYSTEM_ID
        assert len(SYSTEM_ID) > 0

    def test_system_id_is_uuid_like(self):
        """SYSTEM_ID should be a valid UUID format."""
        from phase01_core.constants import SYSTEM_ID
        import uuid
        # Should not raise
        uuid.UUID(SYSTEM_ID)
