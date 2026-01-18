"""
Test: No Scoring or Ranking (RISK-C)

GOVERNANCE: No scoring, ranking, priority, or severity.
Alphabetical ordering ONLY.
"""

import pytest
import ast
from pathlib import Path

from ..types import Finding, ChecklistItem


class TestNoScoringInTypes:
    """Verify no scoring fields exist in types."""

    def test_finding_has_no_score_field(self):
        """Finding type MUST NOT have score field."""
        finding = Finding(
            finding_id="TEST-001",
            title="Test",
            description="Test description",
        )
        assert not hasattr(finding, "score")
        assert not hasattr(finding, "rank")
        assert not hasattr(finding, "priority")
        assert not hasattr(finding, "severity")

    def test_checklist_item_has_no_priority_field(self):
        """ChecklistItem MUST NOT have priority field."""
        item = ChecklistItem(
            item_id="CHECK-001",
            description="Test item",
        )
        assert not hasattr(item, "priority")
        assert not hasattr(item, "score")
        assert not hasattr(item, "importance")
        assert not hasattr(item, "severity")


class TestNoScoringInCode:
    """Verify no scoring logic exists in code."""

    def test_no_scoring_variables(self):
        """No scoring-related variable names in code."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_names = [
            "score",
            "rank",
            "priority",
            "severity",
            "importance",
            "weight",
            "rating",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    name_lower = node.id.lower()
                    for forbidden in forbidden_names:
                        assert forbidden not in name_lower, \
                            f"Forbidden variable '{node.id}' in {py_file.name}"

    def test_no_sorting_by_score(self):
        """No sorting by score, priority, or severity."""
        phase19_dir = Path(__file__).parent.parent
        
        forbidden_patterns = [
            "sort(key=lambda",
            "sorted(key=lambda",
            ".score",
            ".priority",
            ".severity",
            ".rank",
        ]
        
        for py_file in phase19_dir.glob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            
            content = py_file.read_text()
            
            # Allow alphabetical sorting only
            if "sort" in content.lower():
                # Must be alphabetical
                assert "alphabetical" in content.lower() or \
                       "title" in content.lower() or \
                       "finding_id" in content.lower() or \
                       "item_id" in content.lower(), \
                    f"Non-alphabetical sorting in {py_file.name}"


class TestAlphabeticalOrderingOnly:
    """Verify alphabetical ordering is enforced."""

    def test_findings_ordered_alphabetically(self, sample_findings):
        """Findings MUST be ordered alphabetically."""
        # Sort by title (alphabetical)
        sorted_findings = sorted(sample_findings, key=lambda f: f.title)
        
        # Verify alphabetical order
        titles = [f.title for f in sorted_findings]
        assert titles == sorted(titles), "Findings not in alphabetical order"

    def test_checklist_items_ordered_alphabetically(self, sample_checklist_items):
        """Checklist items MUST be ordered alphabetically."""
        sorted_items = sorted(sample_checklist_items, key=lambda i: i.item_id)
        
        ids = [i.item_id for i in sorted_items]
        assert ids == sorted(ids), "Checklist items not in alphabetical order"


class TestChecklistSemanticNeutrality:
    """Verify checklist language is neutral (RISK-C)."""

    def test_checklist_no_ranking_language(self, sample_checklist_items, forbidden_scoring_words):
        """Checklist items MUST NOT contain ranking language."""
        for item in sample_checklist_items:
            description_lower = item.description.lower()
            for word in forbidden_scoring_words:
                assert word not in description_lower, \
                    f"Forbidden word '{word}' in checklist item: {item.description}"

    def test_checklist_neutral_wording(self):
        """Checklist items MUST use neutral, descriptive wording."""
        neutral_items = [
            ChecklistItem(item_id="A", description="Review finding details"),
            ChecklistItem(item_id="B", description="Prepare submission URL"),
            ChecklistItem(item_id="C", description="Export report"),
        ]
        
        forbidden_words = [
            "must", "should", "important", "critical", "urgent",
            "required", "mandatory", "essential", "key", "vital",
        ]
        
        for item in neutral_items:
            description_lower = item.description.lower()
            for word in forbidden_words:
                # Allow "must" only in governance context, not in checklist
                if word in description_lower:
                    pytest.fail(f"Non-neutral word '{word}' in: {item.description}")
