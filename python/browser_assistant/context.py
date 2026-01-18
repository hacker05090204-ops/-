"""
Phase-9 Context Analyzer

Analyzes browser observations to produce HINTS, not conclusions.

SAFETY CONSTRAINTS (NON-NEGOTIABLE):
- Produces HINTS only, not classifications
- Does NOT determine if something is a vulnerability
- Does NOT assign severity
- Does NOT recommend actions
- Does NOT make decisions

Human interprets hints and decides what to do.

Phase-9 is ASSISTIVE ONLY. Human always clicks YES/NO.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
import re

from browser_assistant.types import (
    BrowserObservation,
    ObservationType,
    ContextHint,
    HintType,
    HintSeverity,
)
from browser_assistant.boundaries import Phase9BoundaryGuard


class ContextAnalyzer:
    """
    Analyzes browser observations to produce contextual hints.
    
    SECURITY: This analyzer produces HINTS only. It NEVER:
    - Classifies vulnerabilities
    - Assigns severity
    - Recommends actions
    - Makes decisions
    - Determines if something is a bug
    
    Human interprets the hints and decides what to do.
    
    FORBIDDEN METHODS (do not add):
    - classify_vulnerability()
    - is_vulnerability()
    - determine_severity()
    - recommend_action()
    - should_report()
    - is_exploitable()
    """
    
    # Pattern reminders - NOT vulnerability detection
    # These are patterns that humans commonly look for
    PATTERN_REMINDERS: Dict[str, Dict[str, Any]] = {
        "reflected_parameter": {
            "pattern": r"[?&]([^=]+)=([^&]*)",
            "title": "URL Parameter Detected",
            "description": "URL contains parameters. Consider testing for reflection.",
            "hint_type": HintType.PATTERN_REMINDER,
        },
        "form_action": {
            "pattern": r"<form[^>]*action=['\"]([^'\"]*)['\"]",
            "title": "Form Action Detected",
            "description": "Form with action attribute found. Consider reviewing form handling.",
            "hint_type": HintType.PATTERN_REMINDER,
        },
        "hidden_input": {
            "pattern": r"<input[^>]*type=['\"]hidden['\"][^>]*>",
            "title": "Hidden Input Detected",
            "description": "Hidden form input found. Consider reviewing hidden fields.",
            "hint_type": HintType.PATTERN_REMINDER,
        },
        "error_message": {
            "pattern": r"(error|exception|warning|failed|invalid|denied)",
            "title": "Potential Error Message",
            "description": "Content may contain error message. Consider reviewing error handling.",
            "hint_type": HintType.CONTEXT_INFO,
        },
        "redirect_param": {
            "pattern": r"[?&](redirect|return|next|url|goto|dest|destination)=",
            "title": "Redirect Parameter Detected",
            "description": "URL contains redirect-related parameter. Consider reviewing redirect handling.",
            "hint_type": HintType.PATTERN_REMINDER,
        },
        "file_param": {
            "pattern": r"[?&](file|path|doc|document|page|include)=",
            "title": "File Parameter Detected",
            "description": "URL contains file-related parameter. Consider reviewing file handling.",
            "hint_type": HintType.PATTERN_REMINDER,
        },
        "id_param": {
            "pattern": r"[?&](id|user_id|account|uid|pid)=\d+",
            "title": "Numeric ID Parameter Detected",
            "description": "URL contains numeric ID parameter. Consider reviewing access controls.",
            "hint_type": HintType.PATTERN_REMINDER,
        },
        "api_endpoint": {
            "pattern": r"/api/|/v\d+/|/rest/|/graphql",
            "title": "API Endpoint Detected",
            "description": "URL appears to be an API endpoint. Consider reviewing API security.",
            "hint_type": HintType.CONTEXT_INFO,
        },
        "auth_endpoint": {
            "pattern": r"/(login|signin|auth|oauth|token|session)",
            "title": "Authentication Endpoint Detected",
            "description": "URL appears to be authentication-related. Consider reviewing auth flow.",
            "hint_type": HintType.CONTEXT_INFO,
        },
        "admin_path": {
            "pattern": r"/(admin|dashboard|manage|control|panel)",
            "title": "Administrative Path Detected",
            "description": "URL appears to be administrative. Consider reviewing access controls.",
            "hint_type": HintType.CONTEXT_INFO,
        },
    }
    
    # Checklist items - reminders for common testing areas
    CHECKLIST_ITEMS: List[Dict[str, str]] = [
        {
            "trigger": "form",
            "title": "Form Testing Checklist",
            "description": "Consider: input validation, CSRF tokens, encoding, file uploads.",
        },
        {
            "trigger": "api",
            "title": "API Testing Checklist",
            "description": "Consider: authentication, authorization, rate limiting, input validation.",
        },
        {
            "trigger": "auth",
            "title": "Authentication Testing Checklist",
            "description": "Consider: password policy, session management, MFA, account lockout.",
        },
        {
            "trigger": "upload",
            "title": "File Upload Testing Checklist",
            "description": "Consider: file type validation, size limits, storage location, execution.",
        },
    ]
    
    def __init__(self):
        """Initialize the context analyzer."""
        Phase9BoundaryGuard.assert_passive_observation()
        Phase9BoundaryGuard.assert_human_confirmation_required()
        
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        for name, config in self.PATTERN_REMINDERS.items():
            self._compiled_patterns[name] = re.compile(
                config["pattern"],
                re.IGNORECASE,
            )
    
    def analyze_observation(
        self,
        observation: BrowserObservation,
    ) -> List[ContextHint]:
        """
        Analyze an observation and produce hints.
        
        Args:
            observation: The browser observation to analyze.
            
        Returns:
            List of context hints (may be empty).
            
        NOTE: These are HINTS only. They do NOT:
        - Classify vulnerabilities
        - Assign severity
        - Recommend actions
        - Make decisions
        """
        hints: List[ContextHint] = []
        
        # Analyze URL
        url_hints = self._analyze_url(observation)
        hints.extend(url_hints)
        
        # Analyze content
        content_hints = self._analyze_content(observation)
        hints.extend(content_hints)
        
        # Add checklist reminders based on context
        checklist_hints = self._get_checklist_hints(observation)
        hints.extend(checklist_hints)
        
        return hints
    
    def _analyze_url(
        self,
        observation: BrowserObservation,
    ) -> List[ContextHint]:
        """Analyze URL for pattern reminders."""
        hints: List[ContextHint] = []
        url = observation.url
        
        for name, pattern in self._compiled_patterns.items():
            config = self.PATTERN_REMINDERS[name]
            
            # Only check URL-related patterns
            if "param" in name or "endpoint" in name or "path" in name:
                if pattern.search(url):
                    hints.append(ContextHint(
                        hint_id=str(uuid.uuid4()),
                        hint_type=config["hint_type"],
                        hint_severity=HintSeverity.INFO,
                        title=config["title"],
                        description=config["description"],
                        related_observation_id=observation.observation_id,
                        timestamp=datetime.now(),
                        human_confirmation_required=True,
                        is_advisory_only=True,
                        no_auto_action=True,
                    ))
        
        return hints
    
    def _analyze_content(
        self,
        observation: BrowserObservation,
    ) -> List[ContextHint]:
        """Analyze content for pattern reminders."""
        hints: List[ContextHint] = []
        content = observation.content
        
        for name, pattern in self._compiled_patterns.items():
            config = self.PATTERN_REMINDERS[name]
            
            # Check content-related patterns
            if "form" in name or "input" in name or "error" in name:
                if pattern.search(content):
                    hints.append(ContextHint(
                        hint_id=str(uuid.uuid4()),
                        hint_type=config["hint_type"],
                        hint_severity=HintSeverity.INFO,
                        title=config["title"],
                        description=config["description"],
                        related_observation_id=observation.observation_id,
                        timestamp=datetime.now(),
                        human_confirmation_required=True,
                        is_advisory_only=True,
                        no_auto_action=True,
                    ))
        
        return hints
    
    def _get_checklist_hints(
        self,
        observation: BrowserObservation,
    ) -> List[ContextHint]:
        """Get relevant checklist reminders."""
        hints: List[ContextHint] = []
        combined = f"{observation.url} {observation.content}".lower()
        
        for item in self.CHECKLIST_ITEMS:
            if item["trigger"] in combined:
                hints.append(ContextHint(
                    hint_id=str(uuid.uuid4()),
                    hint_type=HintType.CHECKLIST_ITEM,
                    hint_severity=HintSeverity.INFO,
                    title=item["title"],
                    description=item["description"],
                    related_observation_id=observation.observation_id,
                    timestamp=datetime.now(),
                    human_confirmation_required=True,
                    is_advisory_only=True,
                    no_auto_action=True,
                ))
        
        return hints
    
    def get_context_summary(
        self,
        observations: List[BrowserObservation],
    ) -> str:
        """
        Generate a summary of observed context.
        
        Args:
            observations: List of observations to summarize.
            
        Returns:
            Human-readable summary string.
            
        NOTE: This is a SUMMARY only, not an analysis or recommendation.
        """
        if not observations:
            return "No observations recorded."
        
        # Count observation types
        type_counts: Dict[str, int] = {}
        unique_urls: set = set()
        
        for obs in observations:
            type_name = obs.observation_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
            unique_urls.add(obs.url)
        
        summary_parts = [
            f"Observed {len(observations)} events across {len(unique_urls)} unique URLs.",
        ]
        
        for type_name, count in sorted(type_counts.items()):
            summary_parts.append(f"  - {type_name}: {count}")
        
        return "\n".join(summary_parts)
    
    # ========================================================================
    # FORBIDDEN METHODS - DO NOT IMPLEMENT
    # ========================================================================
    # The following methods are FORBIDDEN and must NEVER be added:
    #
    # - classify_vulnerability() - Phase-9 does NOT classify
    # - is_vulnerability() - Phase-9 does NOT determine
    # - determine_severity() - Phase-9 does NOT assign severity
    # - recommend_action() - Phase-9 does NOT recommend
    # - should_report() - Phase-9 does NOT decide
    # - is_exploitable() - Phase-9 does NOT determine
    # - calculate_risk() - Phase-9 does NOT calculate risk
    # - prioritize_findings() - Phase-9 does NOT prioritize
    # - auto_classify() - Phase-9 does NOT auto-classify
    # - generate_poc() - Phase-9 does NOT generate PoCs
    # ========================================================================
