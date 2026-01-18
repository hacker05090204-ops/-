"""
Phase-17 Package Verifier

GOVERNANCE CONSTRAINT:
- Verify package contents match manifest
- Detect extra files
- Detect missing files
- No verification bypass
"""

from typing import Any


class PackageVerifier:
    """
    Package verifier with governance constraints.
    
    GOVERNANCE GUARANTEES:
    - Verify package matches manifest
    - Detect extra files not in manifest
    - Detect missing files from manifest
    - No verification bypass
    """
    
    def __init__(self) -> None:
        """Initialize verifier."""
        pass
    
    def verify_against_manifest(
        self,
        manifest_files: list[str],
        actual_files: list[str],
    ) -> dict[str, Any]:
        """
        Verify actual files against manifest.
        
        Args:
            manifest_files: Files listed in manifest
            actual_files: Actual files in package
            
        Returns:
            Verification result with extra/missing files
        """
        manifest_set = set(manifest_files)
        actual_set = set(actual_files)
        
        extra_files = list(actual_set - manifest_set)
        missing_files = list(manifest_set - actual_set)
        
        valid = len(extra_files) == 0 and len(missing_files) == 0
        
        return {
            "valid": valid,
            "extra_files": extra_files,
            "missing_files": missing_files,
            "manifest_count": len(manifest_files),
            "actual_count": len(actual_files),
        }
    
    def verify_checksums(
        self,
        manifest_checksums: dict[str, str],
        actual_checksums: dict[str, str],
    ) -> dict[str, Any]:
        """
        Verify file checksums.
        
        Args:
            manifest_checksums: Checksums from manifest
            actual_checksums: Actual file checksums
            
        Returns:
            Checksum verification result
        """
        mismatched = []
        
        for filename, expected in manifest_checksums.items():
            actual = actual_checksums.get(filename)
            if actual != expected:
                mismatched.append(filename)
        
        return {
            "valid": len(mismatched) == 0,
            "mismatched_files": mismatched,
        }
