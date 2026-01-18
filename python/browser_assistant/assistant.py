"""
Phase-9 Browser Assistant

Main orchestrator for the Browser-Integrated Assisted Hunting Layer.

SAFETY CONSTRAINTS (NON-NEGOTIABLE):
- ASSISTIVE ONLY - reduces human workload
- NO automation, NO autonomy, NO submission authority
- NO payload execution
- NO traffic injection
- NO request modification
- NO bug classification
- NO severity assignment
- NO report submission
- Human always clicks YES/NO

This assistant OBSERVES and HINTS. Human DECIDES and ACTS.

Phase-9 is ASSISTIVE ONLY. Human always clicks YES/NO.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Any

from browser_assistant.types import (
    BrowserObservation,
    ObservationType,
    ContextHint,
    DuplicateHint,
    ScopeWarning,
    DraftReportContent,
    AssistantOutput,
    HumanConfirmation,
    ConfirmationStatus,
)
from browser_assistant.errors import (
    HumanConfirmationRequired,
    ArchitecturalViolationError,
    AutomationAttemptError,
)
from browser_assistant.boundaries import Phase9BoundaryGuard
from browser_assistant.observer import BrowserObserver
from browser_assistant.context import ContextAnalyzer
from browser_assistant.duplicate_hint import DuplicateHintEngine
from browser_assistant.scope_check import ScopeChecker
from browser_assistant.draft_generator import DraftReportGenerator
from browser_assistant.confirmation import HumanConfirmationGate


class BrowserAssistant:
    """
    Main orchestrator for Phase-9 Browser Assistant.
    
    SECURITY: This assistant is ASSISTIVE ONLY. It NEVER:
    - Executes payloads
    - Injects traffic
    - Modifies requests
    - Classifies bugs
    - Assigns severity
    - Submits reports
    - Makes decisions
    - Acts without human confirmation
    
    Human OBSERVES hints and DECIDES what to do.
    Human ALWAYS clicks YES or NO.
    
    FORBIDDEN METHODS (do not add):
    - execute_payload()
    - inject_traffic()
    - modify_request()
    - classify_bug()
    - assign_severity()
    - submit_report()
    - auto_confirm()
    - bypass_human()
    """
    
    def __init__(
        self,
        authorized_domains: Optional[List[str]] = None,
        authorized_ip_ranges: Optional[List[str]] = None,
        excluded_paths: Optional[List[str]] = None,
        duplicate_threshold: float = 0.7,
    ):
        """
        Initialize the browser assistant.
        
        Args:
            authorized_domains: List of authorized domains for scope checking.
            authorized_ip_ranges: List of authorized IP ranges.
            excluded_paths: List of excluded paths.
            duplicate_threshold: Similarity threshold for duplicate hints.
        """
        # Document boundary constraints (no runtime validation to avoid
        # false positives from test framework imports)
        Phase9BoundaryGuard.assert_passive_observation()
        Phase9BoundaryGuard.assert_no_network_execution()
        Phase9BoundaryGuard.assert_no_automation()
        Phase9BoundaryGuard.assert_human_confirmation_required()
        Phase9BoundaryGuard.assert_read_only_access()
        
        # Initialize components
        self._observer = BrowserObserver()
        self._context_analyzer = ContextAnalyzer()
        self._duplicate_engine = DuplicateHintEngine(
            similarity_threshold=duplicate_threshold,
        )
        self._scope_checker = ScopeChecker(
            authorized_domains=authorized_domains,
            authorized_ip_ranges=authorized_ip_ranges,
            excluded_paths=excluded_paths,
        )
        self._draft_generator = DraftReportGenerator()
        self._confirmation_gate = HumanConfirmationGate()
        
        # Track generated drafts
        self._drafts: List[DraftReportContent] = []
    
    def receive_observation(
        self,
        observation_type: ObservationType,
        url: str,
        content: str,
        metadata: Optional[dict[str, str]] = None,
    ) -> AssistantOutput:
        """
        Receive a browser observation and generate hints.
        
        Args:
            observation_type: Type of observation.
            url: URL where observation occurred.
            content: Content of the observation.
            metadata: Additional context.
            
        Returns:
            AssistantOutput containing hints (requires confirmation).
            
        NOTE: The output requires human confirmation before acting.
        """
        # Record observation
        observation = self._observer.receive_observation(
            observation_type=observation_type,
            url=url,
            content=content,
            metadata=metadata,
        )
        
        # Generate context hints
        hints = self._context_analyzer.analyze_observation(observation)
        
        # Check for duplicates
        duplicate_hint = self._duplicate_engine.check_for_duplicates(
            url=url,
            content=content,
        )
        
        # Check scope
        scope_warning = self._scope_checker.check_scope(url)
        
        # Combine all hints
        all_hints = {
            "observation": observation,
            "context_hints": hints,
            "duplicate_hint": duplicate_hint,
            "scope_warning": scope_warning,
        }
        
        # Register output for confirmation
        output = self._confirmation_gate.register_output(
            output_type="observation_hints",
            content=all_hints,
        )
        
        return output
    
    def generate_draft_report(
        self,
        observation_ids: Optional[List[str]] = None,
        title_hint: Optional[str] = None,
    ) -> AssistantOutput:
        """
        Generate a draft report from observations.
        
        Args:
            observation_ids: IDs of observations to include (or all recent).
            title_hint: Optional hint for title.
            
        Returns:
            AssistantOutput containing draft (requires confirmation).
            
        NOTE: The draft requires human review, editing, and confirmation.
        Human must assign severity and classification.
        """
        # Get observations
        if observation_ids:
            observations = [
                self._observer.get_observation_by_id(oid)
                for oid in observation_ids
            ]
            observations = [o for o in observations if o is not None]
        else:
            observations = self._observer.get_observations(limit=10)
        
        # Generate draft
        draft = self._draft_generator.generate_draft(
            observations=observations,
            title_hint=title_hint,
        )
        
        # Store draft
        self._drafts.append(draft)
        
        # Register output for confirmation
        output = self._confirmation_gate.register_output(
            output_type="draft_report",
            content=draft,
        )
        
        return output
    
    def confirm_output(
        self,
        output_id: str,
        confirmed_by: str,
        approved: bool,
    ) -> HumanConfirmation:
        """
        Record human confirmation for an output.
        
        Args:
            output_id: ID of the output.
            confirmed_by: Human identifier.
            approved: True if YES, False if NO.
            
        Returns:
            HumanConfirmation record.
            
        NOTE: This is called when human clicks YES or NO.
        """
        return self._confirmation_gate.confirm(
            output_id=output_id,
            confirmed_by=confirmed_by,
            approved=approved,
        )
    
    def get_pending_confirmations(self) -> List[AssistantOutput]:
        """
        Get all outputs pending human confirmation.
        
        Returns:
            List of pending outputs.
        """
        return self._confirmation_gate.get_pending_outputs()
    
    def get_recent_observations(
        self,
        limit: int = 10,
    ) -> List[BrowserObservation]:
        """
        Get recent browser observations.
        
        Args:
            limit: Maximum observations to return.
            
        Returns:
            List of recent observations.
        """
        return self._observer.get_observations(limit=limit)
    
    def get_scope_summary(self) -> str:
        """
        Get summary of configured scope.
        
        Returns:
            Human-readable scope summary.
        """
        return self._scope_checker.get_scope_summary()
    
    def get_context_summary(self) -> str:
        """
        Get summary of observed context.
        
        Returns:
            Human-readable context summary.
        """
        observations = self._observer.get_observations(limit=100)
        return self._context_analyzer.get_context_summary(observations)
    
    def register_finding_for_duplicate_check(
        self,
        url: str,
        content: str,
        finding_id: Optional[str] = None,
    ) -> str:
        """
        Register a finding for future duplicate checks.
        
        Args:
            url: URL of the finding.
            content: Content of the finding.
            finding_id: Optional ID.
            
        Returns:
            Finding ID.
        """
        return self._duplicate_engine.register_finding(
            url=url,
            content=content,
            finding_id=finding_id,
        )
    
    def add_authorized_domain(self, domain: str) -> None:
        """Add a domain to authorized scope."""
        self._scope_checker.add_authorized_domain(domain)
    
    def add_excluded_path(self, path: str) -> None:
        """Add a path to excluded list."""
        self._scope_checker.add_excluded_path(path)
    
    def get_drafts(self) -> List[DraftReportContent]:
        """
        Get all generated drafts.
        
        Returns:
            List of draft reports.
        """
        return list(self._drafts)
    
    def clear_session(self) -> dict:
        """
        Clear all session data.
        
        Returns:
            Summary of cleared data.
        """
        obs_cleared = self._observer.clear_observations()
        findings_cleared = self._duplicate_engine.clear_findings()
        pending, confs = self._confirmation_gate.clear_all()
        drafts_cleared = len(self._drafts)
        self._drafts.clear()
        
        return {
            "observations_cleared": obs_cleared,
            "findings_cleared": findings_cleared,
            "pending_cleared": pending,
            "confirmations_cleared": confs,
            "drafts_cleared": drafts_cleared,
        }
    
    # ========================================================================
    # FORBIDDEN METHODS - DO NOT IMPLEMENT
    # ========================================================================
    # The following methods are FORBIDDEN and must NEVER be added:
    #
    # - execute_payload() - Phase-9 NEVER executes payloads
    # - inject_traffic() - Phase-9 NEVER injects traffic
    # - modify_request() - Phase-9 NEVER modifies requests
    # - classify_bug() - Phase-9 NEVER classifies bugs
    # - assign_severity() - Phase-9 NEVER assigns severity
    # - submit_report() - Phase-9 NEVER submits reports
    # - auto_confirm() - Phase-9 NEVER auto-confirms
    # - bypass_human() - Phase-9 NEVER bypasses human
    # - generate_poc() - Phase-9 NEVER generates PoCs
    # - record_video() - Phase-9 NEVER records video
    # - chain_findings() - Phase-9 NEVER chains findings
    # - auto_correlate() - Phase-9 NEVER auto-correlates
    # - send_to_platform() - Phase-9 NEVER sends to platform
    # - execute_script() - Phase-9 NEVER executes scripts
    # - navigate_browser() - Phase-9 NEVER navigates browser
    # ========================================================================
