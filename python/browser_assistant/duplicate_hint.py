"""
Phase-9 Duplicate Hint Engine

Warns about potential duplicates but NEVER blocks.

SAFETY CONSTRAINTS (NON-NEGOTIABLE):
- WARNS only, NEVER blocks
- Does NOT confirm duplication
- Does NOT auto-reject
- Does NOT filter findings
- Similarity is HEURISTIC, not authoritative

Human decides whether something is actually a duplicate.

Phase-9 is ASSISTIVE ONLY. Human always clicks YES/NO.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Any
import uuid
import difflib

from browser_assistant.types import (
    DuplicateHint,
)
from browser_assistant.boundaries import Phase9BoundaryGuard


class DuplicateHintEngine:
    """
    Warns about potential duplicate findings.
    
    SECURITY: This engine WARNS only. It NEVER:
    - Blocks any action
    - Auto-rejects findings
    - Confirms duplication
    - Filters findings
    - Makes decisions
    
    Human decides whether something is actually a duplicate.
    
    IMPORTANT: Similarity is HEURISTIC, not authoritative.
    - Scores are advisory only
    - No score implies duplication certainty
    - Human verification is always required
    - Even 100% similarity does NOT guarantee duplication
    
    FORBIDDEN METHODS (do not add):
    - block_duplicate()
    - auto_reject()
    - confirm_duplicate()
    - filter_duplicates()
    - is_duplicate() - returns boolean certainty
    """
    
    def __init__(
        self,
        similarity_threshold: float = 0.7,
    ):
        """
        Initialize the duplicate hint engine.
        
        Args:
            similarity_threshold: Threshold for flagging similar content (0.0-1.0).
                                  Default 0.7 (70% similarity).
        """
        Phase9BoundaryGuard.assert_human_confirmation_required()
        
        self._threshold = max(0.0, min(1.0, similarity_threshold))
        self._known_findings: List[dict] = []  # Simple in-memory store
        self._max_findings = 1000  # Prevent unbounded growth
    
    def check_for_duplicates(
        self,
        url: str,
        content: str,
        finding_id: Optional[str] = None,
    ) -> Optional[DuplicateHint]:
        """
        Check if content is similar to known findings.
        
        Args:
            url: URL where content was observed.
            content: Content to check for duplicates.
            finding_id: Optional ID to associate with this check.
            
        Returns:
            DuplicateHint if similar content found, None otherwise.
            
        NOTE: This method NEVER blocks. It returns a hint for
        human interpretation. Even if a hint is returned, the
        human decides whether to proceed.
        
        IMPORTANT: Similarity scores are HEURISTIC estimates.
        They do NOT imply duplication certainty.
        """
        if not content:
            return None
        
        highest_similarity = 0.0
        most_similar_id: Optional[str] = None
        similarity_reason = ""
        
        for known in self._known_findings:
            known_content = known.get("content", "")
            known_url = known.get("url", "")
            known_id = known.get("finding_id")
            
            # Compute content similarity
            content_similarity = self._compute_similarity(content, known_content)
            
            # Compute URL similarity (weighted less)
            url_similarity = self._compute_similarity(url, known_url)
            
            # Combined similarity (content weighted more)
            combined = (content_similarity * 0.8) + (url_similarity * 0.2)
            
            if combined > highest_similarity:
                highest_similarity = combined
                most_similar_id = known_id
                
                if content_similarity >= self._threshold:
                    similarity_reason = f"Content similarity: {content_similarity:.0%}"
                elif url_similarity >= self._threshold:
                    similarity_reason = f"URL similarity: {url_similarity:.0%}"
                else:
                    similarity_reason = f"Combined similarity: {combined:.0%}"
        
        # Only return hint if above threshold
        if highest_similarity >= self._threshold:
            return DuplicateHint(
                hint_id=str(uuid.uuid4()),
                current_url=url,
                similar_finding_id=most_similar_id,
                similarity_score=highest_similarity,
                similarity_reason=similarity_reason,
                timestamp=datetime.now(),
                human_confirmation_required=True,  # Always True
                is_heuristic=True,  # Always True
                does_not_block=True,  # Always True
                similarity_disclaimer="Heuristic estimate - human verification required",
            )
        
        return None
    
    def register_finding(
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
            finding_id: Optional ID (generated if not provided).
            
        Returns:
            Finding ID.
        """
        fid = finding_id or str(uuid.uuid4())
        
        # Enforce size limit
        if len(self._known_findings) >= self._max_findings:
            self._known_findings.pop(0)  # Remove oldest
        
        self._known_findings.append({
            "finding_id": fid,
            "url": url,
            "content": content,
            "registered_at": datetime.now(),
        })
        
        return fid
    
    def get_known_findings_count(self) -> int:
        """Get count of registered findings."""
        return len(self._known_findings)
    
    def clear_findings(self) -> int:
        """
        Clear all registered findings.
        
        Returns:
            Number of findings cleared.
        """
        count = len(self._known_findings)
        self._known_findings.clear()
        return count
    
    def _compute_similarity(
        self,
        text_a: str,
        text_b: str,
    ) -> float:
        """
        Compute similarity score between two texts.
        
        Uses SequenceMatcher for content-based similarity.
        
        Args:
            text_a: First text.
            text_b: Second text.
            
        Returns:
            Float between 0.0 (no similarity) and 1.0 (identical).
            
        WARNING: This is a HEURISTIC estimate only.
        - Score of 1.0 does NOT guarantee duplication
        - Score of 0.0 does NOT guarantee uniqueness
        - Human verification is ALWAYS required
        """
        if not text_a or not text_b:
            return 0.0
        
        # Normalize for comparison
        a_normalized = text_a.lower().strip()
        b_normalized = text_b.lower().strip()
        
        # Use SequenceMatcher
        matcher = difflib.SequenceMatcher(None, a_normalized, b_normalized)
        return matcher.ratio()
    
    # ========================================================================
    # FORBIDDEN METHODS - DO NOT IMPLEMENT
    # ========================================================================
    # The following methods are FORBIDDEN and must NEVER be added:
    #
    # - block_duplicate() - Phase-9 NEVER blocks
    # - auto_reject() - Phase-9 NEVER auto-rejects
    # - confirm_duplicate() - Phase-9 NEVER confirms
    # - filter_duplicates() - Phase-9 NEVER filters
    # - is_duplicate() - Phase-9 NEVER returns boolean certainty
    # - mark_as_duplicate() - Phase-9 NEVER marks
    # - reject_duplicate() - Phase-9 NEVER rejects
    # - remove_duplicate() - Phase-9 NEVER removes
    # ========================================================================
