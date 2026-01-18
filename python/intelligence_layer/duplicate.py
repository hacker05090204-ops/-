"""
Phase-8 Duplicate Detector

Identifies similar findings across sessions using content-based similarity.

SAFETY CONSTRAINTS:
- This detector ONLY warns. It does NOT block or filter.
- Similarity is HEURISTIC, not authoritative.
- All scores are advisory only.
- No similarity score implies duplication certainty.
- Even 100% similarity does NOT guarantee duplication.
- Human verification is ALWAYS required.

FORBIDDEN CAPABILITIES:
- NO auto-reject based on similarity
- NO auto-defer based on similarity
- NO blocking of findings
- NO filtering of findings
- NO certainty claims
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Any
import difflib

from intelligence_layer.types import DuplicateWarning, SimilarFinding
from intelligence_layer.data_access import DataAccessLayer
from intelligence_layer.boundaries import BoundaryGuard


class DuplicateDetector:
    """
    Detects similar findings using content-based similarity.
    
    SAFETY: This detector ONLY warns. It does NOT block or filter.
    
    IMPORTANT: Similarity is HEURISTIC, not authoritative.
    - All scores are advisory only
    - No similarity score implies duplication certainty
    - Even 100% similarity does NOT guarantee duplication
    - Human verification is ALWAYS required
    
    FORBIDDEN METHODS (do not add):
    - auto_reject()
    - auto_defer()
    - block_finding()
    - filter_duplicates()
    - confirm_duplicate()
    - is_duplicate() - returns boolean certainty
    """
    
    def __init__(
        self,
        data_access: DataAccessLayer,
        similarity_threshold: float = 0.8,
    ):
        """
        Initialize the duplicate detector.
        
        Args:
            data_access: Read-only data access layer.
            similarity_threshold: Threshold for flagging similar findings (0.0-1.0).
                                  Default 0.8 (80% similarity).
        """
        BoundaryGuard.assert_read_only()
        BoundaryGuard.assert_human_authority()
        
        self._data_access = data_access
        self._threshold = max(0.0, min(1.0, similarity_threshold))
    
    def check_duplicates(
        self,
        finding_id: str,
        finding_content: str,
        target_id: str,
    ) -> DuplicateWarning:
        """
        Check for similar findings in history.
        
        Args:
            finding_id: ID of the finding to check.
            finding_content: Content/description of the finding.
            target_id: ID of the target.
            
        Returns:
            DuplicateWarning with similar findings (may be empty).
            
        NOTE: This method NEVER blocks. It returns a warning for
        human interpretation.
        
        IMPORTANT: Similarity scores are HEURISTIC estimates.
        They do NOT imply duplication certainty.
        """
        similar_findings: List[SimilarFinding] = []
        highest_similarity = 0.0
        
        # Get historical decisions for this target
        decisions = self._data_access.get_decisions(target_id=target_id)
        
        for decision in decisions:
            # Skip the same finding
            if isinstance(decision, dict):
                d_finding_id = decision.get("finding_id")
                d_decision_id = decision.get("decision_id")
                d_decision_type = decision.get("decision_type")
                d_content = decision.get("content", decision.get("description", ""))
            else:
                d_finding_id = getattr(decision, "finding_id", None)
                d_decision_id = getattr(decision, "decision_id", None)
                d_decision_type = getattr(decision, "decision_type", None)
                d_content = getattr(decision, "content", getattr(decision, "description", ""))
            
            if d_finding_id == finding_id:
                continue
            
            # Compute similarity
            similarity = self.compute_similarity(finding_content, str(d_content))
            
            if similarity >= self._threshold:
                # Get submission status if available
                submissions = self._data_access.get_submissions(decision_id=d_decision_id)
                submission_status = None
                submitted_at = None
                
                if submissions:
                    latest = submissions[-1]
                    if isinstance(latest, dict):
                        submission_status = latest.get("status")
                        submitted_at = latest.get("submitted_at")
                    else:
                        submission_status = getattr(latest, "status", None)
                        submitted_at = getattr(latest, "submitted_at", None)
                    
                    # Convert enum to string if needed
                    if hasattr(submission_status, "value"):
                        submission_status = submission_status.value
                    if isinstance(submitted_at, str):
                        submitted_at = datetime.fromisoformat(submitted_at)
                
                # Convert decision type to string if needed
                d_type_str = d_decision_type.value if hasattr(d_decision_type, "value") else d_decision_type
                
                similar_findings.append(SimilarFinding(
                    finding_id=d_finding_id,
                    decision_id=d_decision_id,
                    similarity_score=similarity,
                    decision_type=d_type_str,
                    submission_status=submission_status,
                    submitted_at=submitted_at,
                    score_disclaimer="Advisory only - does not imply certainty",
                ))
                
                if similarity > highest_similarity:
                    highest_similarity = similarity
        
        # Sort by similarity (highest first)
        similar_findings.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Build warning message
        if similar_findings:
            warning_message = (
                f"Found {len(similar_findings)} similar finding(s) with similarity >= {self._threshold:.0%}. "
                f"Highest similarity: {highest_similarity:.0%}. "
                f"Human decision required - similarity is heuristic only."
            )
        else:
            warning_message = (
                f"No similar findings found above {self._threshold:.0%} threshold. "
                f"Human decision required - absence of matches does not guarantee uniqueness."
            )
        
        return DuplicateWarning(
            finding_id=finding_id,
            similar_findings=tuple(similar_findings),
            highest_similarity=highest_similarity,
            warning_message=warning_message,
            similarity_disclaimer="Heuristic estimate - human verification required",
            is_heuristic=True,  # Always True
            human_decision_required=True,  # Always True
            no_accuracy_guarantee="No accuracy guarantee - human expertise required",
        )
    
    def compute_similarity(
        self,
        content_a: str,
        content_b: str,
    ) -> float:
        """
        Compute similarity score between two finding contents.
        
        Uses SequenceMatcher for content-based similarity.
        
        Args:
            content_a: First content string.
            content_b: Second content string.
            
        Returns:
            Float between 0.0 (no similarity) and 1.0 (identical content).
            
        WARNING: This is a HEURISTIC estimate only.
        - Score of 1.0 does NOT guarantee duplication
        - Score of 0.0 does NOT guarantee uniqueness
        - Human verification is ALWAYS required
        """
        if not content_a or not content_b:
            return 0.0
        
        # Normalize content for comparison
        a_normalized = content_a.lower().strip()
        b_normalized = content_b.lower().strip()
        
        # Use SequenceMatcher for similarity
        matcher = difflib.SequenceMatcher(None, a_normalized, b_normalized)
        return matcher.ratio()
    
    # ========================================================================
    # FORBIDDEN METHODS - DO NOT IMPLEMENT
    # ========================================================================
    # The following methods are FORBIDDEN and must NEVER be added:
    # - auto_reject()
    # - auto_defer()
    # - block_finding()
    # - filter_duplicates()
    # - confirm_duplicate()
    # - is_duplicate() - returns boolean certainty
    # - mark_as_duplicate()
    # - reject_duplicate()
    # ========================================================================
