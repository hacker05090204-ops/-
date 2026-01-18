"""
Hypothesis Generator - Creates testable security hypotheses

ARCHITECTURAL CONSTRAINTS:
    1. Hypotheses are NEVER marked as confirmed vulnerabilities
    2. testability_score measures ease of testing, NOT confidence
    3. mcp_classification is set by MCP, NEVER by this generator
    4. All hypotheses start with status UNTESTED
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from .types import (
    Hypothesis,
    HypothesisStatus,
    ExplorationAction,
    ActionType,
    MCPClassification,
)

logger = logging.getLogger(__name__)


# Invariant categories that hypotheses can target
INVARIANT_CATEGORIES = [
    "Authorization",
    "Monetary",
    "Workflow",
    "Trust",
    "DataIntegrity",
    "SessionManagement",
    "InputValidation",
    "RateLimiting",
]


@dataclass
class Target:
    """Target information for hypothesis generation."""
    domain: str
    endpoints: List[str] = None
    technologies: List[str] = None
    authentication_type: Optional[str] = None
    has_financial_features: bool = False
    has_workflow_features: bool = False
    
    def __post_init__(self):
        if self.endpoints is None:
            self.endpoints = []
        if self.technologies is None:
            self.technologies = []


class HypothesisGenerator:
    """Generates testable security hypotheses from target observations.
    
    ARCHITECTURAL CONSTRAINTS:
        - Hypotheses are NEVER confirmed vulnerabilities
        - testability_score is NOT confidence
        - mcp_classification is NEVER set by this class
        - All hypotheses start as UNTESTED
    """
    
    def __init__(self):
        self._hypothesis_templates = self._load_hypothesis_templates()
    
    def _load_hypothesis_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load hypothesis templates for different invariant categories."""
        return {
            "Authorization": {
                "templates": [
                    "Cross-user object access via {endpoint}",
                    "Privilege escalation through {endpoint}",
                    "Horizontal access control bypass at {endpoint}",
                    "Vertical privilege boundary violation at {endpoint}",
                ],
                "base_testability": 0.7,
            },
            "Monetary": {
                "templates": [
                    "Balance manipulation via {endpoint}",
                    "Double-spend possibility at {endpoint}",
                    "Transaction atomicity violation at {endpoint}",
                    "Negative balance creation at {endpoint}",
                ],
                "base_testability": 0.6,
            },
            "Workflow": {
                "templates": [
                    "Workflow step bypass at {endpoint}",
                    "Step ordering violation via {endpoint}",
                    "Workflow state manipulation at {endpoint}",
                ],
                "base_testability": 0.65,
            },
            "Trust": {
                "templates": [
                    "Client-controlled trust decision at {endpoint}",
                    "Server-side validation bypass at {endpoint}",
                ],
                "base_testability": 0.7,
            },
            "SessionManagement": {
                "templates": [
                    "Session fixation at {endpoint}",
                    "Session hijacking possibility at {endpoint}",
                    "Session user binding violation at {endpoint}",
                ],
                "base_testability": 0.75,
            },
            "InputValidation": {
                "templates": [
                    "Input length bounds violation at {endpoint}",
                    "Input type confusion at {endpoint}",
                ],
                "base_testability": 0.8,
            },
        }
    
    def generate_from_recon(self, target: Target) -> List[Hypothesis]:
        """Generate hypotheses from reconnaissance data.
        
        CRITICAL: Generated hypotheses are NOT confirmed vulnerabilities.
        They are testable propositions that MCP will judge.
        
        Args:
            target: Target information from reconnaissance
            
        Returns:
            List of hypotheses to test (all with status UNTESTED)
        """
        hypotheses = []
        
        for endpoint in target.endpoints:
            # Generate authorization hypotheses for all endpoints
            hypotheses.extend(
                self._generate_category_hypotheses("Authorization", endpoint, target)
            )
            
            # Generate session management hypotheses
            if target.authentication_type:
                hypotheses.extend(
                    self._generate_category_hypotheses("SessionManagement", endpoint, target)
                )
            
            # Generate monetary hypotheses for financial features
            if target.has_financial_features:
                hypotheses.extend(
                    self._generate_category_hypotheses("Monetary", endpoint, target)
                )
            
            # Generate workflow hypotheses for workflow features
            if target.has_workflow_features:
                hypotheses.extend(
                    self._generate_category_hypotheses("Workflow", endpoint, target)
                )
            
            # Generate input validation hypotheses for all endpoints
            hypotheses.extend(
                self._generate_category_hypotheses("InputValidation", endpoint, target)
            )
        
        logger.info(f"Generated {len(hypotheses)} hypotheses for {target.domain}")
        return hypotheses
    
    def _generate_category_hypotheses(
        self, 
        category: str, 
        endpoint: str, 
        target: Target
    ) -> List[Hypothesis]:
        """Generate hypotheses for a specific invariant category."""
        hypotheses = []
        
        templates = self._hypothesis_templates.get(category, {})
        template_strings = templates.get("templates", [])
        base_testability = templates.get("base_testability", 0.5)
        
        for template in template_strings:
            description = template.format(endpoint=endpoint)
            
            # Calculate testability based on target characteristics
            testability = self._calculate_testability(
                base_testability, category, target
            )
            
            hypothesis = Hypothesis(
                description=description,
                target_invariant_categories=[category],
                testability_score=testability,
                status=HypothesisStatus.UNTESTED,  # Always UNTESTED
                mcp_classification=None,  # NEVER set by Cyfer Brain
            )
            
            hypotheses.append(hypothesis)
        
        return hypotheses
    
    def _calculate_testability(
        self, 
        base: float, 
        category: str, 
        target: Target
    ) -> float:
        """Calculate testability score.
        
        NOTE: This is NOT a confidence score. It measures how easy
        the hypothesis is to test, not how likely it is to be a bug.
        """
        testability = base
        
        # Adjust based on target characteristics
        if category == "Monetary" and target.has_financial_features:
            testability += 0.1  # Easier to test if financial features exist
        
        if category == "Workflow" and target.has_workflow_features:
            testability += 0.1  # Easier to test if workflow features exist
        
        if category == "SessionManagement" and target.authentication_type:
            testability += 0.1  # Easier to test if auth exists
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, testability))
    
    def generate_from_signal(self, signal: MCPClassification) -> List[Hypothesis]:
        """Generate follow-up hypotheses from MCP SIGNAL classification.
        
        When MCP classifies something as SIGNAL (interesting but not proven),
        we generate related hypotheses to explore further.
        
        CRITICAL: We do NOT interpret SIGNAL as a bug. We generate more
        hypotheses for MCP to judge.
        
        Args:
            signal: MCP classification with classification="SIGNAL"
            
        Returns:
            List of follow-up hypotheses (all with status UNTESTED)
        """
        if not signal.is_signal():
            logger.warning("generate_from_signal called with non-SIGNAL classification")
            return []
        
        hypotheses = []
        
        # Generate variations based on the signal
        # These are exploratory hypotheses, NOT confirmed issues
        
        base_hypothesis = Hypothesis(
            description=f"Follow-up exploration for signal {signal.observation_id}",
            target_invariant_categories=[],  # Will be filled based on signal
            testability_score=0.6,
            status=HypothesisStatus.UNTESTED,
            mcp_classification=None,  # NEVER set by Cyfer Brain
        )
        
        hypotheses.append(base_hypothesis)
        
        logger.info(f"Generated {len(hypotheses)} follow-up hypotheses from signal")
        return hypotheses
    
    def prioritize(self, hypotheses: List[Hypothesis]) -> List[Hypothesis]:
        """Rank hypotheses by testability and coverage potential.
        
        NOTE: This prioritizes by TESTABILITY, not by likelihood of being a bug.
        We want to test easy-to-test hypotheses first for efficiency.
        
        Args:
            hypotheses: List of hypotheses to prioritize
            
        Returns:
            Sorted list with highest testability first
        """
        # Sort by testability_score (descending)
        # Higher testability = easier to test = test first
        sorted_hypotheses = sorted(
            hypotheses,
            key=lambda h: h.testability_score,
            reverse=True
        )
        
        return sorted_hypotheses
    
    def mark_untestable(self, hypothesis: Hypothesis, reason: str) -> Hypothesis:
        """Mark a hypothesis as untestable.
        
        This is used when a hypothesis cannot be tested within scope
        or due to other constraints.
        
        NOTE: Untestable does NOT mean "not a bug". It means we cannot
        test it, so MCP cannot judge it.
        """
        hypothesis.status = HypothesisStatus.RESOLVED
        # We don't set mcp_classification because MCP didn't classify it
        logger.info(f"Marked hypothesis {hypothesis.id} as untestable: {reason}")
        return hypothesis
