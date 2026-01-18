"""
Phase-15 No Scoring or Ranking Tests

Tests that no scoring, ranking, or classification exists in code.
All tests must FAIL initially until implementation exists.

MANDATORY DECLARATION:
"Phase-15 may ONLY implement enforcement, validation, logging, and blocking."
"""

import pytest


FORBIDDEN_SCORING_WORDS = [
    "score", "scoring", "scored",
    "rank", "ranking", "ranked",
    "rate", "rating", "rated",
    "classify", "classification", "classified",
    "severity", "critical", "criticality",
    "priority", "prioritize",
    "weight", "weighted",
    "confidence", "certainty",
]


class TestNoScoring:
    """Tests that no scoring capability exists."""

    def test_no_scoring_functions(self) -> None:
        """Test that no scoring functions exist."""
        try:
            from phase15_governance import enforcer, validator, blocker, audit
            
            modules = [enforcer, validator, blocker, audit]
            for module in modules:
                for attr in dir(module):
                    attr_lower = attr.lower()
                    assert "score" not in attr_lower, f"Score function: {attr}"
                    assert "rank" not in attr_lower, f"Rank function: {attr}"
                    assert "rate" not in attr_lower, f"Rate function: {attr}"
        except ImportError:
            pytest.fail("Modules do not exist")

    def test_no_scoring_in_output(self) -> None:
        """Test that no scoring appears in output."""
        try:
            from phase15_governance.enforcer import enforce_rule
            from phase15_governance.errors import GovernanceBlockedError
            
            rule = {"type": "block_write", "target": "phase13"}
            context = {"action": "write", "target": "phase13", "human_initiated": True}
            
            try:
                enforce_rule(rule=rule, context=context)
            except GovernanceBlockedError as e:
                error_str = str(e).lower()
                for word in FORBIDDEN_SCORING_WORDS:
                    assert word not in error_str, f"Forbidden: {word}"
        except ImportError:
            pytest.fail("Implementation does not exist")


class TestNoRanking:
    """Tests that no ranking capability exists."""

    def test_no_ranking_functions(self) -> None:
        """Test that no ranking functions exist."""
        try:
            from phase15_governance import enforcer, validator, blocker, audit
            
            modules = [enforcer, validator, blocker, audit]
            for module in modules:
                assert not hasattr(module, "rank")
                assert not hasattr(module, "sort_by_importance")
                assert not hasattr(module, "prioritize")
                assert not hasattr(module, "order_by_severity")
        except ImportError:
            pytest.fail("Modules do not exist")

    def test_no_priority_assignment(self) -> None:
        """Test that no priority assignment exists."""
        try:
            from phase15_governance import enforcer
            import inspect
            source = inspect.getsource(enforcer)
            
            forbidden = ["priority", "high_priority", "low_priority", "urgent"]
            for word in forbidden:
                assert word not in source.lower(), f"Forbidden: {word}"
        except ImportError:
            pytest.fail("enforcer module does not exist")


class TestNoClassification:
    """Tests that no classification capability exists."""

    def test_no_classification_functions(self) -> None:
        """Test that no classification functions exist."""
        try:
            from phase15_governance import enforcer, validator, blocker
            
            modules = [enforcer, validator, blocker]
            for module in modules:
                assert not hasattr(module, "classify")
                assert not hasattr(module, "categorize")
                assert not hasattr(module, "label")
        except ImportError:
            pytest.fail("Modules do not exist")

    def test_no_severity_classification(self) -> None:
        """Test that no severity classification exists."""
        try:
            from phase15_governance import enforcer
            import inspect
            source = inspect.getsource(enforcer)
            
            forbidden = ["severity", "critical", "high", "medium", "low", "info"]
            for word in forbidden:
                # Allow "low" only if not in severity context
                if word == "low":
                    assert "severity" not in source.lower() or word not in source.lower()
                else:
                    assert word not in source.lower(), f"Forbidden: {word}"
        except ImportError:
            pytest.fail("enforcer module does not exist")

    def test_no_auto_severity_in_output(self) -> None:
        """Test that no auto-severity appears in output."""
        try:
            from phase15_governance.audit import log_event, get_entry
            
            entry_id = log_event(
                event_type="test",
                data={"test": "data"},
                attribution="SYSTEM"
            )
            entry = get_entry(entry_id)
            
            # Entry must not have severity fields
            assert "severity" not in entry
            assert "priority" not in entry
            assert "criticality" not in entry
        except ImportError:
            pytest.fail("Implementation does not exist")
