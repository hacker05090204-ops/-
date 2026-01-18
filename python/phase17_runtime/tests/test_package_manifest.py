"""
Phase-17 Tests: Package Manifest Verification

GOVERNANCE CONSTRAINT:
- Package contents MUST match manifest
- No hidden files
- No post-install hooks
- No undocumented content

Risk Mitigated: RISK-17-006 (Packaging Abuse)
"""

import pytest


class TestPackageManifest:
    """Tests verifying package manifest compliance."""

    def test_manifest_exists(self) -> None:
        """Package manifest MUST exist."""
        from phase17_runtime.packager import Packager
        
        packager = Packager()
        
        assert hasattr(packager, "manifest")
        assert packager.manifest is not None

    def test_manifest_lists_all_files(self) -> None:
        """Manifest MUST be able to list package files."""
        from phase17_runtime.packager import Packager
        
        packager = Packager()
        
        # Set manifest files (would be populated during build)
        packager.set_manifest_files(["__init__.py", "launcher.py", "lifecycle.py"])
        
        manifest = packager.get_manifest()
        
        assert "files" in manifest
        assert isinstance(manifest["files"], list)
        assert len(manifest["files"]) > 0

    def test_no_hidden_files_in_package(self) -> None:
        """Package MUST NOT contain hidden files not in manifest."""
        from phase17_runtime.packager import Packager
        
        packager = Packager()
        
        assert packager.has_hidden_files() is False

    def test_no_post_install_hooks(self) -> None:
        """Package MUST NOT have post-install hooks."""
        from phase17_runtime.packager import Packager
        
        packager = Packager()
        
        assert packager.has_post_install_hooks() is False
        assert not hasattr(packager, "post_install")
        assert not hasattr(packager, "run_after_install")

    def test_no_pre_install_hooks(self) -> None:
        """Package MUST NOT have pre-install hooks."""
        from phase17_runtime.packager import Packager
        
        packager = Packager()
        
        assert packager.has_pre_install_hooks() is False
        assert not hasattr(packager, "pre_install")
        assert not hasattr(packager, "run_before_install")

    def test_verifier_detects_extra_files(self) -> None:
        """Verifier MUST detect extra files not in manifest."""
        from phase17_runtime.verifier import PackageVerifier
        
        verifier = PackageVerifier()
        
        # Simulate extra file
        result = verifier.verify_against_manifest(
            manifest_files=["file1.py", "file2.py"],
            actual_files=["file1.py", "file2.py", "hidden.py"],
        )
        
        assert result["valid"] is False
        assert "hidden.py" in result["extra_files"]

    def test_verifier_detects_missing_files(self) -> None:
        """Verifier MUST detect missing files from manifest."""
        from phase17_runtime.verifier import PackageVerifier
        
        verifier = PackageVerifier()
        
        # Simulate missing file
        result = verifier.verify_against_manifest(
            manifest_files=["file1.py", "file2.py", "file3.py"],
            actual_files=["file1.py", "file2.py"],
        )
        
        assert result["valid"] is False
        assert "file3.py" in result["missing_files"]

    def test_verifier_passes_on_match(self) -> None:
        """Verifier MUST pass when files match manifest."""
        from phase17_runtime.verifier import PackageVerifier
        
        verifier = PackageVerifier()
        
        result = verifier.verify_against_manifest(
            manifest_files=["file1.py", "file2.py"],
            actual_files=["file1.py", "file2.py"],
        )
        
        assert result["valid"] is True
        assert result["extra_files"] == []
        assert result["missing_files"] == []

    def test_no_executable_scripts_hidden(self) -> None:
        """Package MUST NOT hide executable scripts."""
        from phase17_runtime.packager import Packager
        
        packager = Packager()
        
        assert packager.has_hidden_executables() is False

    def test_manifest_includes_checksums(self) -> None:
        """Manifest SHOULD include file checksums."""
        from phase17_runtime.packager import Packager
        
        packager = Packager()
        manifest = packager.get_manifest()
        
        # Checksums help verify integrity
        assert "checksums" in manifest or packager.supports_checksums is True
