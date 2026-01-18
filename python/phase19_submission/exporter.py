"""
Phase-19 Report Exporter

GOVERNANCE CONSTRAINTS:
- Read-only access to Phase-15 data
- Static, non-executable formats only (PDF, TXT, MD)
- "NOT VERIFIED" disclaimer on every page/section
- Alphabetical ordering only
- No scoring, ranking, or verification language

This module exports human-readable reports from Phase-15 findings.
Human initiation is REQUIRED for all exports.
"""

from typing import List
from .types import Finding, ExportFormat, ExportRequest
from .errors import ForbiddenExportFormat, HumanInitiationRequired


# MANDATORY DISCLAIMER - MUST appear on every page/section
DISCLAIMER = """
================================================================================
                              NOT VERIFIED
================================================================================
This report contains UNVERIFIED findings. The information presented has NOT been
validated, confirmed, or authenticated. Human review and verification is required
before any action is taken. This system does not verify, validate, or confirm
any findings. All decisions must be made by a human.
================================================================================
"""


class ReportExporter:
    """
    Exports findings to human-readable reports.
    
    GOVERNANCE:
    - Human initiation required
    - Read-only access to findings
    - Static formats only
    - Disclaimer on every section
    - Alphabetical ordering only
    """
    
    def export(
        self,
        findings: List[Finding],
        export_format: ExportFormat,
        human_initiated: bool,
    ) -> str:
        """
        Export findings to specified format.
        
        Args:
            findings: List of findings to export (read-only)
            export_format: Target format (PDF, TXT, MD only)
            human_initiated: MUST be True
            
        Returns:
            Exported content as string
            
        Raises:
            HumanInitiationRequired: If human_initiated is False
            ForbiddenExportFormat: If format is not allowed
        """
        # GOVERNANCE: Require human initiation
        if not human_initiated:
            raise HumanInitiationRequired(
                "Export MUST be initiated by human action"
            )
        
        # GOVERNANCE: Validate format
        if export_format not in ExportFormat:
            raise ForbiddenExportFormat(
                f"Format not allowed: {export_format}"
            )
        
        # GOVERNANCE: Sort alphabetically by title (no scoring)
        sorted_findings = sorted(findings, key=lambda f: f.title.lower())
        
        # Generate content based on format
        if export_format == ExportFormat.TXT:
            return self._export_txt(sorted_findings)
        elif export_format == ExportFormat.MD:
            return self._export_md(sorted_findings)
        elif export_format == ExportFormat.PDF:
            # PDF returns text representation (actual PDF generation
            # would require external library, but content is same)
            return self._export_txt(sorted_findings)
        
        raise ForbiddenExportFormat(f"Unknown format: {export_format}")
    
    def _export_txt(self, findings: List[Finding]) -> str:
        """Export to plain text format."""
        lines = [DISCLAIMER]
        lines.append("\nFINDINGS REPORT\n")
        lines.append("=" * 80)
        lines.append(DISCLAIMER)  # Disclaimer after header too
        
        for finding in findings:
            lines.append(f"\nFinding ID: {finding.finding_id}")
            lines.append(f"Title: {finding.title}")
            lines.append(f"Description: {finding.description}")
            lines.append("-" * 40)
            lines.append(DISCLAIMER)  # Disclaimer after each finding
        
        lines.append("\n" + "=" * 80)
        lines.append("END OF REPORT")
        lines.append(DISCLAIMER)  # Final disclaimer
        
        return "\n".join(lines)
    
    def _export_md(self, findings: List[Finding]) -> str:
        """Export to Markdown format."""
        lines = [DISCLAIMER]
        lines.append("\n# Findings Report\n")
        lines.append(DISCLAIMER)
        
        for finding in findings:
            lines.append(f"\n## {finding.title}\n")
            lines.append(f"**Finding ID:** {finding.finding_id}\n")
            lines.append(f"**Description:** {finding.description}\n")
            lines.append("---")
            lines.append(DISCLAIMER)
        
        lines.append("\n---\n")
        lines.append("*End of Report*")
        lines.append(DISCLAIMER)
        
        return "\n".join(lines)
