"""
Phase-9 Draft Report Generator

Generates DRAFT reports that humans MUST review, edit, and confirm.

SAFETY CONSTRAINTS (NON-NEGOTIABLE):
- Generates DRAFTS only, not final reports
- Human MUST review before use
- Human MUST edit as needed
- Human MUST confirm before any action
- NEVER auto-submits
- NEVER assigns severity (human does)
- NEVER classifies bugs (human does)

Human copies, edits, and submits manually.

Phase-9 is ASSISTIVE ONLY. Human always clicks YES/NO.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List
import uuid

from browser_assistant.types import (
    BrowserObservation,
    DraftReportContent,
)
from browser_assistant.boundaries import Phase9BoundaryGuard


class DraftReportGenerator:
    """
    Generates draft reports for human review.
    
    SECURITY: This generator creates DRAFTS only. It NEVER:
    - Submits reports
    - Assigns severity
    - Classifies vulnerabilities
    - Determines CVSS scores
    - Makes final decisions
    
    Human reviews, edits, and decides what to do with the draft.
    
    FORBIDDEN METHODS (do not add):
    - submit_report()
    - auto_submit()
    - assign_severity()
    - classify_vulnerability()
    - calculate_cvss()
    - finalize_report()
    - send_to_platform()
    """
    
    def __init__(self):
        """Initialize the draft generator."""
        Phase9BoundaryGuard.assert_human_confirmation_required()
        Phase9BoundaryGuard.assert_no_automation()
    
    def generate_draft(
        self,
        observations: List[BrowserObservation],
        title_hint: Optional[str] = None,
    ) -> DraftReportContent:
        """
        Generate a draft report from observations.
        
        Args:
            observations: Browser observations to include.
            title_hint: Optional hint for title (human will edit).
            
        Returns:
            DraftReportContent for human review.
            
        NOTE: This is a DRAFT only. Human MUST:
        - Review the content
        - Edit as needed
        - Assign severity
        - Classify the finding
        - Confirm before any action
        
        The draft is NEVER auto-submitted.
        """
        if not observations:
            return self._create_empty_draft()
        
        # Generate title suggestion
        title = title_hint or self._suggest_title(observations)
        
        # Generate description template
        description = self._generate_description_template(observations)
        
        # Generate observed behavior summary
        observed_behavior = self._summarize_observations(observations)
        
        # Collect observation IDs
        observation_ids = tuple(obs.observation_id for obs in observations)
        
        # Compute content hash
        content_hash = DraftReportContent.compute_hash(
            title=title,
            description=description,
            observed_behavior=observed_behavior,
            observations=observation_ids,
        )
        
        return DraftReportContent(
            draft_id=str(uuid.uuid4()),
            title_suggestion=title,
            description_template=description,
            observed_behavior=observed_behavior,
            related_observations=observation_ids,
            timestamp=datetime.now(),
            content_hash=content_hash,
            human_must_review=True,  # Always True
            human_must_edit=True,  # Always True
            human_must_confirm=True,  # Always True
            is_template_only=True,  # Always True
            no_auto_submission=True,  # Always True
            no_severity_assigned="Human must assign severity",
            no_classification_assigned="Human must classify",
        )
    
    def _create_empty_draft(self) -> DraftReportContent:
        """Create an empty draft template."""
        title = "[TITLE - Human must provide]"
        description = (
            "[DESCRIPTION - Human must provide]\n\n"
            "## Steps to Reproduce\n"
            "1. [Step 1]\n"
            "2. [Step 2]\n"
            "3. [Step 3]\n\n"
            "## Expected Behavior\n"
            "[Describe expected behavior]\n\n"
            "## Actual Behavior\n"
            "[Describe actual behavior]\n\n"
            "## Impact\n"
            "[Describe potential impact - Human must assess]"
        )
        observed_behavior = "No observations provided."
        
        content_hash = DraftReportContent.compute_hash(
            title=title,
            description=description,
            observed_behavior=observed_behavior,
            observations=(),
        )
        
        return DraftReportContent(
            draft_id=str(uuid.uuid4()),
            title_suggestion=title,
            description_template=description,
            observed_behavior=observed_behavior,
            related_observations=(),
            timestamp=datetime.now(),
            content_hash=content_hash,
            human_must_review=True,
            human_must_edit=True,
            human_must_confirm=True,
            is_template_only=True,
            no_auto_submission=True,
            no_severity_assigned="Human must assign severity",
            no_classification_assigned="Human must classify",
        )
    
    def _suggest_title(
        self,
        observations: List[BrowserObservation],
    ) -> str:
        """
        Suggest a title based on observations.
        
        NOTE: This is a SUGGESTION only. Human will edit.
        """
        # Get unique URLs
        urls = set(obs.url for obs in observations)
        
        # Get observation types
        types = set(obs.observation_type.value for obs in observations)
        
        if len(urls) == 1:
            url = list(urls)[0]
            # Extract path for title hint
            if "/" in url:
                path = url.split("/")[-1] or url.split("/")[-2]
                return f"[Finding on {path}] - Human must provide title"
        
        return "[Finding Title] - Human must provide"
    
    def _generate_description_template(
        self,
        observations: List[BrowserObservation],
    ) -> str:
        """
        Generate a description template.
        
        NOTE: This is a TEMPLATE only. Human will edit.
        """
        parts = [
            "## Summary",
            "[Human must provide summary of the finding]",
            "",
            "## Steps to Reproduce",
        ]
        
        # Add observation-based steps
        for i, obs in enumerate(observations[:5], 1):  # Limit to 5
            parts.append(f"{i}. Navigate to: {obs.url}")
            if obs.content:
                content_preview = obs.content[:100]
                if len(obs.content) > 100:
                    content_preview += "..."
                parts.append(f"   Observed: {content_preview}")
        
        parts.extend([
            "",
            "## Expected Behavior",
            "[Human must describe expected behavior]",
            "",
            "## Actual Behavior",
            "[Human must describe actual behavior]",
            "",
            "## Impact",
            "[Human must assess and describe impact]",
            "",
            "## Severity",
            "[Human must assign severity - NOT auto-assigned]",
            "",
            "## Classification",
            "[Human must classify - NOT auto-classified]",
        ])
        
        return "\n".join(parts)
    
    def _summarize_observations(
        self,
        observations: List[BrowserObservation],
    ) -> str:
        """
        Summarize observations.
        
        NOTE: This is a SUMMARY only, not an analysis.
        """
        parts = ["Observed browser activity:"]
        
        for obs in observations[:10]:  # Limit to 10
            parts.append(
                f"- [{obs.observation_type.value}] {obs.url}: "
                f"{obs.content[:50]}{'...' if len(obs.content) > 50 else ''}"
            )
        
        if len(observations) > 10:
            parts.append(f"... and {len(observations) - 10} more observations")
        
        return "\n".join(parts)
    
    def get_draft_by_id(
        self,
        draft_id: str,
        drafts: List[DraftReportContent],
    ) -> Optional[DraftReportContent]:
        """
        Find a draft by ID.
        
        Args:
            draft_id: ID of the draft.
            drafts: List of drafts to search.
            
        Returns:
            DraftReportContent if found, None otherwise.
        """
        for draft in drafts:
            if draft.draft_id == draft_id:
                return draft
        return None
    
    # ========================================================================
    # FORBIDDEN METHODS - DO NOT IMPLEMENT
    # ========================================================================
    # The following methods are FORBIDDEN and must NEVER be added:
    #
    # - submit_report() - Phase-9 NEVER submits
    # - auto_submit() - Phase-9 NEVER auto-submits
    # - assign_severity() - Phase-9 NEVER assigns severity
    # - classify_vulnerability() - Phase-9 NEVER classifies
    # - calculate_cvss() - Phase-9 NEVER calculates CVSS
    # - finalize_report() - Phase-9 NEVER finalizes
    # - send_to_platform() - Phase-9 NEVER sends
    # - generate_poc() - Phase-9 NEVER generates PoCs
    # - attach_evidence() - Phase-9 NEVER attaches (human does)
    # - auto_fill() - Phase-9 NEVER auto-fills
    # ========================================================================
