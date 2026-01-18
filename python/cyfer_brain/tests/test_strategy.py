"""
Tests for Strategy Engine

Property Tests:
    - Strategies are SELECTED from catalog, not learned
    - Strategy adaptation is based on MCP feedback only
"""

import pytest
from hypothesis import given, strategies as st, settings

from cyfer_brain.strategy import (
    StrategyEngine,
    Strategy,
    StrategyType,
    STRATEGY_CATALOG,
)
from cyfer_brain.types import (
    Hypothesis,
    MCPClassification,
    ExplorationStats,
)


class TestStrategyCatalog:
    """Tests for STRATEGY_CATALOG."""
    
    def test_catalog_is_not_empty(self):
        """Strategy catalog must have strategies."""
        assert len(STRATEGY_CATALOG) > 0
    
    def test_catalog_has_required_strategies(self):
        """Catalog must have essential strategies."""
        required = [
            "breadth_first",
            "depth_first",
            "auth_boundary",
            "financial_integrity",
            "workflow_bypass",
            "signal_followup",
            "coverage_expansion",
        ]
        
        for name in required:
            assert name in STRATEGY_CATALOG, f"Missing strategy: {name}"
    
    def test_all_strategies_are_valid(self):
        """All strategies in catalog must be valid Strategy objects."""
        for name, strategy in STRATEGY_CATALOG.items():
            assert isinstance(strategy, Strategy)
            assert strategy.name == name
            assert isinstance(strategy.strategy_type, StrategyType)
            assert strategy.max_depth > 0
            assert strategy.max_breadth > 0


class TestStrategyEngine:
    """Tests for StrategyEngine."""
    
    def test_engine_creation(self):
        """Test engine can be created."""
        engine = StrategyEngine()
        assert engine is not None
        assert engine.current_strategy is not None
    
    def test_generate_strategy_selects_from_catalog(self):
        """generate_strategy must select from catalog, not create new."""
        engine = StrategyEngine()
        
        strategy = engine.generate_strategy({"has_financial_features": True})
        
        # Strategy must be from catalog
        assert strategy.name in STRATEGY_CATALOG
        assert strategy == STRATEGY_CATALOG[strategy.name]
    
    def test_generate_strategy_for_financial_target(self):
        """Financial targets should get financial_integrity strategy."""
        engine = StrategyEngine()
        
        strategy = engine.generate_strategy({"has_financial_features": True})
        
        assert strategy.name == "financial_integrity"
        assert strategy.strategy_type == StrategyType.FINANCIAL_FOCUSED
    
    def test_generate_strategy_for_workflow_target(self):
        """Workflow targets should get workflow_bypass strategy."""
        engine = StrategyEngine()
        
        strategy = engine.generate_strategy({"has_workflow_features": True})
        
        assert strategy.name == "workflow_bypass"
    
    def test_generate_strategy_for_auth_target(self):
        """Auth targets should get auth_boundary strategy."""
        engine = StrategyEngine()
        
        strategy = engine.generate_strategy({"has_authentication": True})
        
        assert strategy.name == "auth_boundary"
    
    def test_generate_strategy_default(self):
        """Default strategy should be breadth_first."""
        engine = StrategyEngine()
        
        strategy = engine.generate_strategy({})
        
        assert strategy.name == "breadth_first"
    
    def test_switch_strategy_from_catalog(self):
        """switch_strategy must select from catalog."""
        engine = StrategyEngine()
        
        strategy = engine.switch_strategy("depth_first")
        
        assert strategy.name == "depth_first"
        assert strategy == STRATEGY_CATALOG["depth_first"]
    
    def test_switch_strategy_unknown_raises(self):
        """Switching to unknown strategy must raise ValueError."""
        engine = StrategyEngine()
        
        with pytest.raises(ValueError) as exc_info:
            engine.switch_strategy("nonexistent_strategy")
        
        assert "Unknown strategy" in str(exc_info.value)
    
    def test_strategies_used_tracking(self):
        """Engine must track which strategies have been used."""
        engine = StrategyEngine()
        
        engine.generate_strategy({"has_financial_features": True})
        engine.switch_strategy("auth_boundary")
        
        used = engine.get_used_strategies()
        
        assert "financial_integrity" in used
        assert "auth_boundary" in used


class TestStrategyAdaptation:
    """Tests for strategy adaptation based on MCP feedback."""
    
    def test_adapt_on_bug_continues_current(self):
        """BUG classification should continue with current strategy."""
        engine = StrategyEngine()
        engine.generate_strategy({})  # breadth_first
        
        classification = MCPClassification(
            observation_id="obs-1",
            classification="BUG",
            invariant_violated="Authorization",
        )
        stats = ExplorationStats(bugs_found=1)
        
        strategy = engine.adapt_strategy(classification, stats)
        
        # Should stay with current strategy
        assert strategy.name == "breadth_first"
    
    def test_adapt_on_signal_may_switch(self):
        """Multiple SIGNAL classifications may switch to signal_followup."""
        engine = StrategyEngine()
        engine.generate_strategy({})
        
        classification = MCPClassification(
            observation_id="obs-1",
            classification="SIGNAL",
        )
        stats = ExplorationStats(signals_found=5)  # Above threshold
        
        strategy = engine.adapt_strategy(classification, stats)
        
        # Should switch to signal_followup
        assert strategy.name == "signal_followup"
    
    def test_adapt_on_coverage_gap_switches(self):
        """COVERAGE_GAP should switch to coverage_expansion."""
        engine = StrategyEngine()
        engine.generate_strategy({})
        
        classification = MCPClassification(
            observation_id="obs-1",
            classification="COVERAGE_GAP",
            coverage_gaps=["Monetary"],
        )
        stats = ExplorationStats()
        
        strategy = engine.adapt_strategy(classification, stats)
        
        assert strategy.name == "coverage_expansion"
    
    def test_adapt_on_consecutive_no_issues_switches(self):
        """Consecutive NO_ISSUE should eventually switch strategy."""
        engine = StrategyEngine()
        engine.generate_strategy({})
        initial = engine.current_strategy.name
        
        classification = MCPClassification(
            observation_id="obs-1",
            classification="NO_ISSUE",
        )
        stats = ExplorationStats(no_issues=10)
        
        # Simulate consecutive failures
        for _ in range(engine.FAILURE_THRESHOLD):
            strategy = engine.adapt_strategy(classification, stats)
        
        # Should have switched to different strategy
        assert strategy.name != initial


class TestStrategySelection:
    """Property tests for strategy selection."""
    
    @given(
        has_financial=st.booleans(),
        has_workflow=st.booleans(),
        has_auth=st.booleans(),
    )
    @settings(max_examples=20)
    def test_strategy_always_from_catalog(
        self, has_financial, has_workflow, has_auth
    ):
        """Generated strategy must always be from catalog."""
        engine = StrategyEngine()
        
        target_info = {
            "has_financial_features": has_financial,
            "has_workflow_features": has_workflow,
            "has_authentication": has_auth,
        }
        
        strategy = engine.generate_strategy(target_info)
        
        # Strategy must be from catalog
        assert strategy.name in STRATEGY_CATALOG
        assert strategy == STRATEGY_CATALOG[strategy.name]
    
    @given(
        classification_type=st.sampled_from(["BUG", "SIGNAL", "NO_ISSUE", "COVERAGE_GAP"]),
        signals_found=st.integers(min_value=0, max_value=20),
    )
    @settings(max_examples=30)
    def test_adapted_strategy_always_from_catalog(
        self, classification_type, signals_found
    ):
        """Adapted strategy must always be from catalog."""
        engine = StrategyEngine()
        engine.generate_strategy({})
        
        classification = MCPClassification(
            observation_id="obs-1",
            classification=classification_type,
        )
        stats = ExplorationStats(signals_found=signals_found)
        
        strategy = engine.adapt_strategy(classification, stats)
        
        # Adapted strategy must be from catalog
        assert strategy.name in STRATEGY_CATALOG


class TestHypothesisPrioritization:
    """Tests for hypothesis prioritization by strategy."""
    
    def test_prioritize_boosts_matching_hypotheses(self):
        """Strategy should boost matching hypotheses."""
        engine = StrategyEngine()
        engine.switch_strategy("auth_boundary")
        
        hypotheses = [
            Hypothesis(
                description="Auth test",
                target_invariant_categories=["Authorization"],
                testability_score=0.5,
            ),
            Hypothesis(
                description="Other test",
                target_invariant_categories=["InputValidation"],
                testability_score=0.6,
            ),
        ]
        
        prioritized = engine.prioritize_hypotheses(hypotheses)
        
        # Auth hypothesis should be first due to strategy boost
        assert prioritized[0].target_invariant_categories == ["Authorization"]
    
    def test_prioritize_preserves_all_hypotheses(self):
        """Prioritization must not lose any hypotheses."""
        engine = StrategyEngine()
        
        hypotheses = [
            Hypothesis(description=f"Test {i}", testability_score=0.5)
            for i in range(10)
        ]
        
        prioritized = engine.prioritize_hypotheses(hypotheses)
        
        assert len(prioritized) == len(hypotheses)
