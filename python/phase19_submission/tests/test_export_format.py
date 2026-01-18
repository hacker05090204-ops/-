"""
Test: Export Format Enforcement (RISK-A)

GOVERNANCE: Only static, non-executable formats allowed.
ALLOWED: PDF, TXT, MD
FORBIDDEN: HTML with scripts, interactive formats, embeds
"""

import pytest
import ast
from pathlib import Path

from ..types import ExportFormat, ExportRequest, Finding
from ..errors import ForbiddenExportFormat


class TestAllowedExportFormats:
    """Verify only allowed formats are defined."""

    def test_only_static_formats_defined(self):
        """Only PDF, TXT, MD formats are defined."""
        allowed = {ExportFormat.PDF, ExportFormat.TXT, ExportFormat.MD}
        defined = set(ExportFormat)
        
        assert defined == allowed, f"Unexpected formats: {defined - allowed}"

    def test_pdf_format_exists(self):
        """PDF format is allowed."""
        assert ExportFormat.PDF.value == "pdf"

    def test_txt_format_exists(self):
        """TXT format is allowed."""
        assert ExportFormat.TXT.value == "txt"

    def test_md_format_exists(self):
        """MD format is allowed."""
        assert ExportFormat.MD.value == "md"


class TestForbiddenExportFormats:
    """Verify forbidden formats are not supported."""

    def test_no_html_format(self):
        """HTML format MUST NOT exist."""
        format_values = [f.value for f in ExportFormat]
        assert "html" not in format_values
        assert "htm" not in format_values

    def test_no_executable_formats(self):
        """Executable formats MUST NOT exist."""
        format_values = [f.value for f in ExportFormat]
        forbidden = ["exe", "sh", "bat", "py", "js", "rb"]
        
        for fmt in forbidden:
            assert fmt not in format_values, f"Forbidden format '{fmt}' exists"

    def test_no_interactive_formats(self):
        """Interactive formats MUST NOT exist."""
        format_values = [f.value for f in ExportFormat]
        forbidden = ["xlsx", "docx", "pptx", "odt"]
        
        for fmt in forbidden:
            assert fmt not in format_values, f"Forbidden format '{fmt}' exists"


class TestNoExecutableExportCode:
    """Verify no executable content generation in exports."""

    def test_no_script_generation(self):
        """No script generation in export code."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_patterns = [
            "<script",
            "javascript:",
            "onclick=",
            "onload=",
            "eval(",
            "exec(",
            "compile(",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            
            for pattern in forbidden_patterns:
                assert pattern not in content, \
                    f"Forbidden script pattern '{pattern}' in {py_file.name}"

    def test_no_embed_generation(self):
        """No embed or iframe generation."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_patterns = [
            "<iframe",
            "<embed",
            "<object",
            "<applet",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            
            for pattern in forbidden_patterns:
                assert pattern not in content, \
                    f"Forbidden embed pattern '{pattern}' in {py_file.name}"


class TestExportRequestValidation:
    """Verify export request validation."""

    def test_export_request_requires_valid_format(self, sample_findings):
        """Export request requires valid format."""
        request = ExportRequest(
            findings=sample_findings,
            export_format=ExportFormat.TXT,
            human_initiated=True,
        )
        assert request.export_format in ExportFormat

    def test_export_request_with_all_formats(self, sample_findings):
        """Export request works with all allowed formats."""
        for fmt in ExportFormat:
            request = ExportRequest(
                findings=sample_findings,
                export_format=fmt,
                human_initiated=True,
            )
            assert request.export_format == fmt
