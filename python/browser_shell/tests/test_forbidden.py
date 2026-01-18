# PHASE-13 GOVERNANCE COMPLIANCE
# Tests for TASK-8.1, 8.2, 8.3: Forbidden Behaviors Verification
# Requirement: 8.1, 8.2, 8.3 (Forbidden Behaviors)
#
# MANDATORY DECLARATION:
# Phase-13 must not alter execution authority, human control,
# governance friction, audit invariants, or legal accountability.
#
# This module performs STATIC ANALYSIS to verify no forbidden
# capabilities exist in the Phase-13 implementation.

"""Tests for forbidden behaviors verification - static analysis tests."""

import pytest
import ast
import inspect
import os


# =============================================================================
# Helper Functions for Static Analysis
# =============================================================================

def get_all_browser_shell_modules():
    """Get all browser_shell module sources for analysis."""
    import browser_shell
    import browser_shell.audit_types
    import browser_shell.audit_storage
    import browser_shell.hash_chain
    import browser_shell.session
    import browser_shell.scope
    import browser_shell.decision
    import browser_shell.evidence
    import browser_shell.report
    import browser_shell.suggestion
    
    modules = [
        browser_shell.audit_types,
        browser_shell.audit_storage,
        browser_shell.hash_chain,
        browser_shell.session,
        browser_shell.scope,
        browser_shell.decision,
        browser_shell.evidence,
        browser_shell.report,
        browser_shell.suggestion,
    ]
    
    return modules


def get_all_method_names(modules):
    """Extract all method names from modules."""
    method_names = []
    for module in modules:
        source = inspect.getsource(module)
        tree = ast.parse(source)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                method_names.append(node.name)
            elif isinstance(node, ast.AsyncFunctionDef):
                method_names.append(node.name)
    
    return method_names


def get_all_imports(modules):
    """Extract all imports from modules."""
    imports = []
    for module in modules:
        source = inspect.getsource(module)
        tree = ast.parse(source)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
    
    return imports


# =============================================================================
# TASK-8.1: Forbidden Automation Verification Tests
# =============================================================================

class TestNoAutoSubmitMethod:
    """AST analysis confirms no auto_submit."""
    
    def test_no_auto_submit_method(self):
        """Verify no auto_submit method exists."""
        modules = get_all_browser_shell_modules()
        method_names = get_all_method_names(modules)
        
        forbidden = [m for m in method_names if 'auto_submit' in m.lower()]
        assert len(forbidden) == 0, f"Found forbidden auto_submit methods: {forbidden}"


class TestNoAutoNavigateMethod:
    """AST analysis confirms no auto_navigate."""
    
    def test_no_auto_navigate_method(self):
        """Verify no auto_navigate method exists."""
        modules = get_all_browser_shell_modules()
        method_names = get_all_method_names(modules)
        
        forbidden = [m for m in method_names if 'auto_navigate' in m.lower()]
        assert len(forbidden) == 0, f"Found forbidden auto_navigate methods: {forbidden}"


class TestNoAutoCaptureMethod:
    """AST analysis confirms no auto_capture."""
    
    def test_no_auto_capture_method(self):
        """Verify no auto_capture method exists."""
        modules = get_all_browser_shell_modules()
        method_names = get_all_method_names(modules)
        
        forbidden = [m for m in method_names if 'auto_capture' in m.lower()]
        assert len(forbidden) == 0, f"Found forbidden auto_capture methods: {forbidden}"


class TestNoAutoScopeExpand:
    """AST analysis confirms no auto_scope_expand."""
    
    def test_no_auto_scope_expand_method(self):
        """Verify no auto_scope_expand method exists."""
        modules = get_all_browser_shell_modules()
        method_names = get_all_method_names(modules)
        
        forbidden = [m for m in method_names if 'auto_scope' in m.lower() or 'expand_scope' in m.lower()]
        assert len(forbidden) == 0, f"Found forbidden scope expansion methods: {forbidden}"


class TestNoAutoSessionExtend:
    """AST analysis confirms no auto_session_extend."""
    
    def test_no_auto_session_extend_method(self):
        """Verify no auto_session_extend method exists."""
        modules = get_all_browser_shell_modules()
        method_names = get_all_method_names(modules)
        
        forbidden = [m for m in method_names if 'auto_session' in m.lower() or 'extend_session' in m.lower()]
        assert len(forbidden) == 0, f"Found forbidden session extension methods: {forbidden}"


class TestNoAutoRetry:
    """AST analysis confirms no auto_retry."""
    
    def test_no_auto_retry_method(self):
        """Verify no auto_retry method exists."""
        modules = get_all_browser_shell_modules()
        method_names = get_all_method_names(modules)
        
        forbidden = [m for m in method_names if 'auto_retry' in m.lower()]
        assert len(forbidden) == 0, f"Found forbidden auto_retry methods: {forbidden}"


class TestNoBatchApproval:
    """AST analysis confirms no batch_approve."""
    
    def test_no_batch_approve_method(self):
        """Verify no batch_approve method exists."""
        modules = get_all_browser_shell_modules()
        method_names = get_all_method_names(modules)
        
        forbidden = [m for m in method_names if 'batch_approve' in m.lower() or 'batch_confirm' in m.lower()]
        assert len(forbidden) == 0, f"Found forbidden batch approval methods: {forbidden}"


class TestNoRememberChoice:
    """AST analysis confirms no remember_choice."""
    
    def test_no_remember_choice_method(self):
        """Verify no remember_choice method exists."""
        modules = get_all_browser_shell_modules()
        method_names = get_all_method_names(modules)
        
        forbidden = [m for m in method_names if 'remember' in m.lower()]
        assert len(forbidden) == 0, f"Found forbidden remember methods: {forbidden}"


class TestNoBackgroundOps:
    """AST analysis confirms no background operations."""
    
    def test_no_background_methods(self):
        """Verify no background operation methods exist."""
        modules = get_all_browser_shell_modules()
        method_names = get_all_method_names(modules)
        
        forbidden = [m for m in method_names if 'background' in m.lower() and not m.startswith('_')]
        assert len(forbidden) == 0, f"Found forbidden background methods: {forbidden}"


class TestNoScheduledActions:
    """AST analysis confirms no scheduled actions."""
    
    def test_no_schedule_methods(self):
        """Verify no schedule methods exist."""
        modules = get_all_browser_shell_modules()
        method_names = get_all_method_names(modules)
        
        forbidden = [m for m in method_names if 'schedule' in m.lower() and not m.startswith('_')]
        assert len(forbidden) == 0, f"Found forbidden schedule methods: {forbidden}"


# =============================================================================
# TASK-8.2: Forbidden Learning Verification Tests
# =============================================================================

class TestNoMLImports:
    """AST analysis confirms no ML library imports."""
    
    def test_no_sklearn_import(self):
        """Verify no sklearn import."""
        modules = get_all_browser_shell_modules()
        imports = get_all_imports(modules)
        
        forbidden = [i for i in imports if 'sklearn' in i.lower()]
        assert len(forbidden) == 0, f"Found forbidden sklearn imports: {forbidden}"
    
    def test_no_tensorflow_import(self):
        """Verify no tensorflow import."""
        modules = get_all_browser_shell_modules()
        imports = get_all_imports(modules)
        
        forbidden = [i for i in imports if 'tensorflow' in i.lower()]
        assert len(forbidden) == 0, f"Found forbidden tensorflow imports: {forbidden}"
    
    def test_no_pytorch_import(self):
        """Verify no pytorch import."""
        modules = get_all_browser_shell_modules()
        imports = get_all_imports(modules)
        
        forbidden = [i for i in imports if 'torch' in i.lower()]
        assert len(forbidden) == 0, f"Found forbidden pytorch imports: {forbidden}"
    
    def test_no_keras_import(self):
        """Verify no keras import."""
        modules = get_all_browser_shell_modules()
        imports = get_all_imports(modules)
        
        forbidden = [i for i in imports if 'keras' in i.lower()]
        assert len(forbidden) == 0, f"Found forbidden keras imports: {forbidden}"


class TestNoBehaviorStorage:
    """AST analysis confirms no behavior persistence."""
    
    def test_no_behavior_storage_methods(self):
        """Verify no behavior storage methods exist."""
        modules = get_all_browser_shell_modules()
        method_names = get_all_method_names(modules)
        
        forbidden = [m for m in method_names if 'behavior' in m.lower() and ('store' in m.lower() or 'save' in m.lower())]
        assert len(forbidden) == 0, f"Found forbidden behavior storage methods: {forbidden}"


class TestNoPersonalizationCode:
    """AST analysis confirms no personalization."""
    
    def test_no_personalization_methods(self):
        """Verify no personalization methods exist."""
        modules = get_all_browser_shell_modules()
        method_names = get_all_method_names(modules)
        
        forbidden = [m for m in method_names if 'personalize' in m.lower() or 'personal' in m.lower()]
        assert len(forbidden) == 0, f"Found forbidden personalization methods: {forbidden}"


class TestNoOptimizationCode:
    """AST analysis confirms no optimization."""
    
    def test_no_optimization_methods(self):
        """Verify no optimization methods exist."""
        modules = get_all_browser_shell_modules()
        method_names = get_all_method_names(modules)
        
        # Exclude internal methods and check for optimization
        forbidden = [m for m in method_names if 'optimize' in m.lower() and not m.startswith('_')]
        assert len(forbidden) == 0, f"Found forbidden optimization methods: {forbidden}"


class TestNoPatternTracking:
    """AST analysis confirms no pattern storage."""
    
    def test_no_pattern_tracking_methods(self):
        """Verify no pattern tracking methods exist."""
        modules = get_all_browser_shell_modules()
        method_names = get_all_method_names(modules)
        
        forbidden = [m for m in method_names if 'track_pattern' in m.lower() or 'store_pattern' in m.lower()]
        assert len(forbidden) == 0, f"Found forbidden pattern tracking methods: {forbidden}"


# =============================================================================
# TASK-8.3: Forbidden Audit Modification Verification Tests
# =============================================================================

class TestNoAuditDelete:
    """AST analysis confirms no delete method in audit."""
    
    def test_no_audit_delete_method(self):
        """Verify no delete method in audit storage."""
        import browser_shell.audit_storage as audit_module
        
        source = inspect.getsource(audit_module)
        tree = ast.parse(source)
        
        method_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                method_names.append(node.name)
        
        forbidden = [m for m in method_names if 'delete' in m.lower()]
        assert len(forbidden) == 0, f"Found forbidden delete methods: {forbidden}"


class TestNoAuditUpdate:
    """AST analysis confirms no update method in audit."""
    
    def test_no_audit_update_method(self):
        """Verify no update method in audit storage."""
        import browser_shell.audit_storage as audit_module
        
        source = inspect.getsource(audit_module)
        tree = ast.parse(source)
        
        method_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                method_names.append(node.name)
        
        forbidden = [m for m in method_names if 'update' in m.lower()]
        assert len(forbidden) == 0, f"Found forbidden update methods: {forbidden}"


class TestNoAuditTruncate:
    """AST analysis confirms no truncate method in audit."""
    
    def test_no_audit_truncate_method(self):
        """Verify no truncate method in audit storage."""
        import browser_shell.audit_storage as audit_module
        
        source = inspect.getsource(audit_module)
        tree = ast.parse(source)
        
        method_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                method_names.append(node.name)
        
        forbidden = [m for m in method_names if 'truncate' in m.lower()]
        assert len(forbidden) == 0, f"Found forbidden truncate methods: {forbidden}"


class TestNoAuditDisable:
    """AST analysis confirms no disable method in audit."""
    
    def test_no_audit_disable_method(self):
        """Verify no disable method in audit storage."""
        import browser_shell.audit_storage as audit_module
        
        source = inspect.getsource(audit_module)
        tree = ast.parse(source)
        
        method_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                method_names.append(node.name)
        
        forbidden = [m for m in method_names if 'disable' in m.lower()]
        assert len(forbidden) == 0, f"Found forbidden disable methods: {forbidden}"


class TestNoAuditBypass:
    """AST analysis confirms no bypass path in audit."""
    
    def test_no_audit_bypass_method(self):
        """Verify no bypass method in audit storage."""
        import browser_shell.audit_storage as audit_module
        
        source = inspect.getsource(audit_module)
        tree = ast.parse(source)
        
        method_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                method_names.append(node.name)
        
        forbidden = [m for m in method_names if 'bypass' in m.lower() or 'skip' in m.lower()]
        assert len(forbidden) == 0, f"Found forbidden bypass methods: {forbidden}"


# =============================================================================
# Comprehensive Forbidden Capability Verification
# =============================================================================

class TestComprehensiveForbiddenCapabilities:
    """Comprehensive verification of all forbidden capabilities."""
    
    def test_no_execution_authority_methods(self):
        """Verify no execution authority methods exist."""
        modules = get_all_browser_shell_modules()
        method_names = get_all_method_names(modules)
        
        # Methods that would indicate execution authority
        forbidden_patterns = [
            'execute_action',
            'perform_action',
            'run_action',
            'do_action',
            'auto_execute',
        ]
        
        for pattern in forbidden_patterns:
            forbidden = [m for m in method_names if pattern in m.lower()]
            assert len(forbidden) == 0, f"Found forbidden execution methods matching '{pattern}': {forbidden}"
    
    def test_no_decision_authority_methods(self):
        """Verify no decision authority methods exist."""
        modules = get_all_browser_shell_modules()
        method_names = get_all_method_names(modules)
        
        # Methods that would indicate decision authority
        forbidden_patterns = [
            'decide_for_human',
            'auto_decide',
            'make_decision',
            'choose_for_user',
        ]
        
        for pattern in forbidden_patterns:
            forbidden = [m for m in method_names if pattern in m.lower()]
            assert len(forbidden) == 0, f"Found forbidden decision methods matching '{pattern}': {forbidden}"
    
    def test_governance_compliance_header_present(self):
        """Verify all modules have governance compliance header."""
        modules = get_all_browser_shell_modules()
        
        for module in modules:
            source = inspect.getsource(module)
            assert 'PHASE-13 GOVERNANCE COMPLIANCE' in source, f"Module {module.__name__} missing governance header"
            assert 'MANDATORY DECLARATION' in source, f"Module {module.__name__} missing mandatory declaration"
