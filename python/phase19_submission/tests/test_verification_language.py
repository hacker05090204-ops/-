"""
Test: No Verification Language (RISK-E)

GOVERNANCE: No verification language in exports or UI.
"NOT VERIFIED" disclaimer MUST appear on every page/section.
"""

import pytest
import ast
from pathlib import Path


class TestForbiddenVerificationLanguage:
    """Verify no verification language exists."""

    def test_no_verification_words_in_code(self, forbidden_verification_words):
        """No verification words in non-test code (excluding governance context)."""
        phase19_dir = Path(__file__).parent.parent
        
        # Words that are forbidden in OUTPUT strings (not in code logic)
        output_forbidden_words = [
            "this is verified",
            "has been confirmed",
            "was validated",
            "high confidence",
            "definitely",
            "proven",
            "authenticated",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            
            # Parse AST to check string literals that would appear in output
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                # Check string constants that might be output
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    value_lower = node.value.lower()
                    
                    # Skip if it's the disclaimer (allowed)
                    if "not verified" in value_lower:
                        continue
                    
                    # Skip error messages and governance context
                    if "must be" in value_lower or "required" in value_lower:
                        continue
                    
                    # Check for forbidden output patterns
                    for pattern in output_forbidden_words:
                        if pattern in value_lower:
                            pytest.fail(
                                f"Forbidden verification pattern '{pattern}' in {py_file.name}"
                            )

    def test_no_confidence_language(self):
        """No confidence language in code."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_patterns = [
            "high confidence",
            "low confidence",
            "medium confidence",
            "confidence_score",
            "confidence_level",
            "certainty",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text().lower()
            
            for pattern in forbidden_patterns:
                assert pattern not in content, \
                    f"Forbidden confidence pattern '{pattern}' in {py_file.name}"


class TestDisclaimerEnforcement:
    """Verify disclaimer is enforced."""

    def test_disclaimer_constant_exists(self):
        """DISCLAIMER constant MUST exist."""
        from ..exporter import DISCLAIMER
        
        assert "NOT VERIFIED" in DISCLAIMER
        assert len(DISCLAIMER) > 0

    def test_disclaimer_in_exports(self):
        """Disclaimer MUST be included in all exports."""
        from ..exporter import ReportExporter, DISCLAIMER
        from ..types import Finding, ExportFormat
        
        findings = [
            Finding(
                finding_id="TEST-001",
                title="Test Finding",
                description="Test description",
            )
        ]
        
        exporter = ReportExporter()
        
        for fmt in ExportFormat:
            content = exporter.export(
                findings=findings,
                export_format=fmt,
                human_initiated=True,
            )
            assert DISCLAIMER in content, \
                f"Disclaimer missing in {fmt.value} export"


class TestNoApprovalLanguage:
    """Verify no approval language exists."""

    def test_no_approval_words(self):
        """No approval-related words in code."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_patterns = [
            "approved",
            "approval",
            "authorize",
            "authorized",
            "accept",
            "accepted",
            "endorse",
            "endorsed",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text().lower()
            
            for pattern in forbidden_patterns:
                # Allow in error class names and governance context
                if "error" in py_file.name or "governance" in content:
                    continue
                assert pattern not in content, \
                    f"Forbidden approval pattern '{pattern}' in {py_file.name}"


class TestNoRecommendationLanguage:
    """Verify no recommendation language exists."""

    def test_no_recommendation_words(self):
        """No recommendation-related words in function/variable names."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_patterns = [
            "recommend",
            "suggestion",
            "best_practice",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            tree = ast.parse(content)
            
            # Check function names
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    name_lower = node.name.lower()
                    for pattern in forbidden_patterns:
                        assert pattern not in name_lower, \
                            f"Forbidden function name '{node.name}' in {py_file.name}"
                elif isinstance(node, ast.Name):
                    name_lower = node.id.lower()
                    for pattern in forbidden_patterns:
                        assert pattern not in name_lower, \
                            f"Forbidden variable name '{node.id}' in {py_file.name}"
