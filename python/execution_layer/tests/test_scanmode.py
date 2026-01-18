"""
Phase-4.2 Track A: ScanMode Pre-Integration Tests

Tests for ScanMode enum and ScanContext - execution mode enforcement.
Tests written BEFORE implementation per governance requirements.

Constraints verified:
- PASSIVE mode does not block any request
- SAFE_ACTIVE mode blocks only via PayloadGuard
- ScanMode does not affect execution timing
- ScanMode does not retry, modify browser flow, or mask errors
- ScanContext is immutable
"""

import pytest
from dataclasses import FrozenInstanceError


class TestScanModeEnum:
    """Tests for ScanMode enumeration."""

    def test_scanmode_has_passive_mode(self):
        """ScanMode must have PASSIVE mode."""
        from execution_layer.scanmode import ScanMode
        assert hasattr(ScanMode, 'PASSIVE')
        assert ScanMode.PASSIVE.value == 'passive'

    def test_scanmode_has_safe_active_mode(self):
        """ScanMode must have SAFE_ACTIVE mode."""
        from execution_layer.scanmode import ScanMode
        assert hasattr(ScanMode, 'SAFE_ACTIVE')
        assert ScanMode.SAFE_ACTIVE.value == 'safe_active'

    def test_scanmode_only_has_two_modes(self):
        """ScanMode must only have PASSIVE and SAFE_ACTIVE modes."""
        from execution_layer.scanmode import ScanMode
        assert len(ScanMode) == 2

    def test_scanmode_is_comparable(self):
        """ScanMode values must be comparable."""
        from execution_layer.scanmode import ScanMode
        assert ScanMode.PASSIVE == ScanMode.PASSIVE
        assert ScanMode.SAFE_ACTIVE == ScanMode.SAFE_ACTIVE
        assert ScanMode.PASSIVE != ScanMode.SAFE_ACTIVE


class TestScanContext:
    """Tests for ScanContext - immutable execution context."""

    def test_scancontext_creation_with_passive(self):
        """ScanContext can be created with PASSIVE mode."""
        from execution_layer.scanmode import ScanMode, ScanContext
        ctx = ScanContext(mode=ScanMode.PASSIVE, execution_id='test-123')
        assert ctx.mode == ScanMode.PASSIVE
        assert ctx.execution_id == 'test-123'

    def test_scancontext_creation_with_safe_active(self):
        """ScanContext can be created with SAFE_ACTIVE mode."""
        from execution_layer.scanmode import ScanMode, ScanContext
        ctx = ScanContext(mode=ScanMode.SAFE_ACTIVE, execution_id='test-456')
        assert ctx.mode == ScanMode.SAFE_ACTIVE
        assert ctx.execution_id == 'test-456'

    def test_scancontext_is_immutable(self):
        """ScanContext must be immutable (frozen dataclass)."""
        from execution_layer.scanmode import ScanMode, ScanContext
        ctx = ScanContext(mode=ScanMode.PASSIVE, execution_id='test-789')
        with pytest.raises(FrozenInstanceError):
            ctx.mode = ScanMode.SAFE_ACTIVE

    def test_scancontext_execution_id_immutable(self):
        """ScanContext execution_id must be immutable."""
        from execution_layer.scanmode import ScanMode, ScanContext
        ctx = ScanContext(mode=ScanMode.PASSIVE, execution_id='test-abc')
        with pytest.raises(FrozenInstanceError):
            ctx.execution_id = 'modified'

    def test_scancontext_requires_execution_id(self):
        """ScanContext must require execution_id."""
        from execution_layer.scanmode import ScanMode, ScanContext
        with pytest.raises(TypeError):
            ScanContext(mode=ScanMode.PASSIVE)

    def test_scancontext_requires_mode(self):
        """ScanContext must require mode."""
        from execution_layer.scanmode import ScanContext
        with pytest.raises(TypeError):
            ScanContext(execution_id='test')


class TestScanModeEvaluator:
    """Tests for ScanMode evaluation logic."""

    def test_passive_mode_allows_all_requests(self):
        """PASSIVE mode must not block any request."""
        from execution_layer.scanmode import ScanMode, ScanContext, ScanModeEvaluator
        ctx = ScanContext(mode=ScanMode.PASSIVE, execution_id='test-1')
        evaluator = ScanModeEvaluator(ctx)
        
        # PASSIVE should allow everything
        assert evaluator.should_enforce_guards() is False

    def test_safe_active_mode_enforces_guards(self):
        """SAFE_ACTIVE mode must enforce PayloadGuard."""
        from execution_layer.scanmode import ScanMode, ScanContext, ScanModeEvaluator
        ctx = ScanContext(mode=ScanMode.SAFE_ACTIVE, execution_id='test-2')
        evaluator = ScanModeEvaluator(ctx)
        
        # SAFE_ACTIVE should enforce guards
        assert evaluator.should_enforce_guards() is True

    def test_evaluator_is_read_only(self):
        """ScanModeEvaluator must be read-only (no state mutation)."""
        from execution_layer.scanmode import ScanMode, ScanContext, ScanModeEvaluator
        ctx = ScanContext(mode=ScanMode.PASSIVE, execution_id='test-3')
        evaluator = ScanModeEvaluator(ctx)
        
        # Evaluator should not have any mutation methods
        assert not hasattr(evaluator, 'set_mode')
        assert not hasattr(evaluator, 'update')
        assert not hasattr(evaluator, 'modify')

    def test_evaluator_does_not_retry(self):
        """ScanModeEvaluator must not have retry logic."""
        from execution_layer.scanmode import ScanMode, ScanContext, ScanModeEvaluator
        ctx = ScanContext(mode=ScanMode.SAFE_ACTIVE, execution_id='test-4')
        evaluator = ScanModeEvaluator(ctx)
        
        # No retry-related methods
        assert not hasattr(evaluator, 'retry')
        assert not hasattr(evaluator, 'should_retry')
        assert not hasattr(evaluator, 'retry_count')

    def test_evaluator_does_not_mask_errors(self):
        """ScanModeEvaluator must not mask errors."""
        from execution_layer.scanmode import ScanMode, ScanContext, ScanModeEvaluator
        ctx = ScanContext(mode=ScanMode.SAFE_ACTIVE, execution_id='test-5')
        evaluator = ScanModeEvaluator(ctx)
        
        # No error suppression methods
        assert not hasattr(evaluator, 'suppress_error')
        assert not hasattr(evaluator, 'ignore_error')
        assert not hasattr(evaluator, 'mask_error')

    def test_evaluator_deterministic(self):
        """ScanModeEvaluator must be deterministic."""
        from execution_layer.scanmode import ScanMode, ScanContext, ScanModeEvaluator
        
        # Same context should always produce same result
        ctx1 = ScanContext(mode=ScanMode.PASSIVE, execution_id='test-6')
        ctx2 = ScanContext(mode=ScanMode.PASSIVE, execution_id='test-6')
        
        eval1 = ScanModeEvaluator(ctx1)
        eval2 = ScanModeEvaluator(ctx2)
        
        assert eval1.should_enforce_guards() == eval2.should_enforce_guards()

    def test_evaluator_context_accessible(self):
        """ScanModeEvaluator must expose context for audit."""
        from execution_layer.scanmode import ScanMode, ScanContext, ScanModeEvaluator
        ctx = ScanContext(mode=ScanMode.SAFE_ACTIVE, execution_id='test-7')
        evaluator = ScanModeEvaluator(ctx)
        
        assert evaluator.context == ctx
        assert evaluator.context.mode == ScanMode.SAFE_ACTIVE


class TestScanModeNoSideEffects:
    """Tests ensuring ScanMode has no side effects on execution."""

    def test_scanmode_does_not_affect_timing(self):
        """ScanMode evaluation must not introduce timing delays."""
        import time
        from execution_layer.scanmode import ScanMode, ScanContext, ScanModeEvaluator
        
        ctx = ScanContext(mode=ScanMode.SAFE_ACTIVE, execution_id='timing-test')
        evaluator = ScanModeEvaluator(ctx)
        
        start = time.perf_counter()
        for _ in range(1000):
            evaluator.should_enforce_guards()
        elapsed = time.perf_counter() - start
        
        # 1000 evaluations should complete in under 100ms
        assert elapsed < 0.1

    def test_scanmode_no_network_calls(self):
        """ScanMode must not make network calls."""
        from execution_layer.scanmode import ScanMode, ScanContext, ScanModeEvaluator
        
        # ScanModeEvaluator should not have any network-related attributes
        ctx = ScanContext(mode=ScanMode.SAFE_ACTIVE, execution_id='network-test')
        evaluator = ScanModeEvaluator(ctx)
        
        assert not hasattr(evaluator, 'http')
        assert not hasattr(evaluator, 'request')
        assert not hasattr(evaluator, 'fetch')
        assert not hasattr(evaluator, 'socket')

    def test_scanmode_no_file_io(self):
        """ScanMode must not perform file I/O."""
        from execution_layer.scanmode import ScanMode, ScanContext, ScanModeEvaluator
        
        ctx = ScanContext(mode=ScanMode.SAFE_ACTIVE, execution_id='io-test')
        evaluator = ScanModeEvaluator(ctx)
        
        assert not hasattr(evaluator, 'file')
        assert not hasattr(evaluator, 'write')
        assert not hasattr(evaluator, 'read')
        assert not hasattr(evaluator, 'open')


class TestScanModeAuditability:
    """Tests for ScanMode audit trail support."""

    def test_scancontext_to_dict(self):
        """ScanContext must be serializable to dict for audit."""
        from execution_layer.scanmode import ScanMode, ScanContext
        ctx = ScanContext(mode=ScanMode.SAFE_ACTIVE, execution_id='audit-1')
        
        audit_dict = ctx.to_dict()
        assert audit_dict['mode'] == 'safe_active'
        assert audit_dict['execution_id'] == 'audit-1'

    def test_scancontext_repr(self):
        """ScanContext must have readable repr for logging."""
        from execution_layer.scanmode import ScanMode, ScanContext
        ctx = ScanContext(mode=ScanMode.PASSIVE, execution_id='repr-test')
        
        repr_str = repr(ctx)
        assert 'PASSIVE' in repr_str or 'passive' in repr_str
        assert 'repr-test' in repr_str
