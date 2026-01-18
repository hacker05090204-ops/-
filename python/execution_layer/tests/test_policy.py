"""
Phase-4.2 Track D: Policy Engine Pre-Integration Tests

Tests for Policy Engine - policy-driven execution constraints.
Tests written BEFORE implementation per governance requirements.

Constraints verified:
- Immutable Policy model
- Single evaluation per execution
- Max requests enforcement
- Allowed domains enforcement
- Allowed methods enforcement
- No dynamic branching
- No runtime changes
- Auditable decisions
"""

import pytest
from dataclasses import FrozenInstanceError


class TestPolicyImmutability:
    """Tests for Policy immutability."""

    def test_policy_is_frozen(self):
        """Policy must be immutable (frozen dataclass)."""
        from execution_layer.policy import Policy
        policy = Policy(
            max_requests=10,
            allowed_domains=['example.com'],
            allowed_methods=['GET', 'POST']
        )
        with pytest.raises(FrozenInstanceError):
            policy.max_requests = 20

    def test_policy_allowed_domains_immutable(self):
        """Policy allowed_domains must be immutable."""
        from execution_layer.policy import Policy
        policy = Policy(
            max_requests=10,
            allowed_domains=['example.com'],
            allowed_methods=['GET']
        )
        with pytest.raises(FrozenInstanceError):
            policy.allowed_domains = ['malicious.com']

    def test_policy_allowed_methods_immutable(self):
        """Policy allowed_methods must be immutable."""
        from execution_layer.policy import Policy
        policy = Policy(
            max_requests=10,
            allowed_domains=['example.com'],
            allowed_methods=['GET']
        )
        with pytest.raises(FrozenInstanceError):
            policy.allowed_methods = ['DELETE']


class TestPolicyCreation:
    """Tests for Policy creation."""

    def test_policy_creation_with_all_fields(self):
        """Policy can be created with all fields."""
        from execution_layer.policy import Policy
        policy = Policy(
            max_requests=100,
            allowed_domains=['example.com', '*.test.com'],
            allowed_methods=['GET', 'POST', 'HEAD']
        )
        assert policy.max_requests == 100
        assert 'example.com' in policy.allowed_domains
        assert 'GET' in policy.allowed_methods

    def test_policy_requires_max_requests(self):
        """Policy must require max_requests."""
        from execution_layer.policy import Policy
        with pytest.raises(TypeError):
            Policy(
                allowed_domains=['example.com'],
                allowed_methods=['GET']
            )

    def test_policy_requires_allowed_domains(self):
        """Policy must require allowed_domains."""
        from execution_layer.policy import Policy
        with pytest.raises(TypeError):
            Policy(
                max_requests=10,
                allowed_methods=['GET']
            )

    def test_policy_requires_allowed_methods(self):
        """Policy must require allowed_methods."""
        from execution_layer.policy import Policy
        with pytest.raises(TypeError):
            Policy(
                max_requests=10,
                allowed_domains=['example.com']
            )


class TestPolicyEvaluatorSingleEvaluation:
    """Tests for single evaluation per execution."""

    def test_evaluator_tracks_request_count(self):
        """PolicyEvaluator must track request count."""
        from execution_layer.policy import Policy, PolicyEvaluator
        policy = Policy(
            max_requests=5,
            allowed_domains=['example.com'],
            allowed_methods=['GET']
        )
        evaluator = PolicyEvaluator(policy)
        
        # First request should be allowed
        result = evaluator.evaluate_request(
            domain='example.com',
            method='GET'
        )
        assert result.allowed is True
        assert evaluator.request_count == 1

    def test_evaluator_blocks_after_max_requests(self):
        """PolicyEvaluator must block after max_requests."""
        from execution_layer.policy import Policy, PolicyEvaluator
        policy = Policy(
            max_requests=3,
            allowed_domains=['example.com'],
            allowed_methods=['GET']
        )
        evaluator = PolicyEvaluator(policy)
        
        # First 3 requests should be allowed
        for i in range(3):
            result = evaluator.evaluate_request(
                domain='example.com',
                method='GET'
            )
            assert result.allowed is True, f"Request {i+1} should be allowed"
        
        # 4th request should be blocked
        result = evaluator.evaluate_request(
            domain='example.com',
            method='GET'
        )
        assert result.allowed is False
        assert 'max' in result.reason.lower()

    def test_evaluator_cannot_reset_count(self):
        """PolicyEvaluator must not allow resetting request count."""
        from execution_layer.policy import Policy, PolicyEvaluator
        policy = Policy(
            max_requests=5,
            allowed_domains=['example.com'],
            allowed_methods=['GET']
        )
        evaluator = PolicyEvaluator(policy)
        
        evaluator.evaluate_request(domain='example.com', method='GET')
        assert evaluator.request_count == 1
        
        # Should not have reset method
        assert not hasattr(evaluator, 'reset')
        assert not hasattr(evaluator, 'reset_count')


class TestPolicyEvaluatorDomainEnforcement:
    """Tests for domain enforcement."""

    def test_allows_domain_in_policy(self):
        """PolicyEvaluator must allow domains in policy."""
        from execution_layer.policy import Policy, PolicyEvaluator
        policy = Policy(
            max_requests=10,
            allowed_domains=['example.com'],
            allowed_methods=['GET']
        )
        evaluator = PolicyEvaluator(policy)
        
        result = evaluator.evaluate_request(
            domain='example.com',
            method='GET'
        )
        assert result.allowed is True

    def test_blocks_domain_not_in_policy(self):
        """PolicyEvaluator must block domains not in policy."""
        from execution_layer.policy import Policy, PolicyEvaluator
        policy = Policy(
            max_requests=10,
            allowed_domains=['example.com'],
            allowed_methods=['GET']
        )
        evaluator = PolicyEvaluator(policy)
        
        result = evaluator.evaluate_request(
            domain='malicious.com',
            method='GET'
        )
        assert result.allowed is False
        assert 'domain' in result.reason.lower()

    def test_supports_wildcard_domains(self):
        """PolicyEvaluator must support wildcard domains."""
        from execution_layer.policy import Policy, PolicyEvaluator
        policy = Policy(
            max_requests=10,
            allowed_domains=['*.example.com'],
            allowed_methods=['GET']
        )
        evaluator = PolicyEvaluator(policy)
        
        result = evaluator.evaluate_request(
            domain='api.example.com',
            method='GET'
        )
        assert result.allowed is True


class TestPolicyEvaluatorMethodEnforcement:
    """Tests for method enforcement."""

    def test_allows_method_in_policy(self):
        """PolicyEvaluator must allow methods in policy."""
        from execution_layer.policy import Policy, PolicyEvaluator
        policy = Policy(
            max_requests=10,
            allowed_domains=['example.com'],
            allowed_methods=['GET', 'POST']
        )
        evaluator = PolicyEvaluator(policy)
        
        result = evaluator.evaluate_request(
            domain='example.com',
            method='POST'
        )
        assert result.allowed is True

    def test_blocks_method_not_in_policy(self):
        """PolicyEvaluator must block methods not in policy."""
        from execution_layer.policy import Policy, PolicyEvaluator
        policy = Policy(
            max_requests=10,
            allowed_domains=['example.com'],
            allowed_methods=['GET']
        )
        evaluator = PolicyEvaluator(policy)
        
        result = evaluator.evaluate_request(
            domain='example.com',
            method='DELETE'
        )
        assert result.allowed is False
        assert 'method' in result.reason.lower()

    def test_method_check_is_case_insensitive(self):
        """Method check must be case-insensitive."""
        from execution_layer.policy import Policy, PolicyEvaluator
        policy = Policy(
            max_requests=10,
            allowed_domains=['example.com'],
            allowed_methods=['GET']
        )
        evaluator = PolicyEvaluator(policy)
        
        result = evaluator.evaluate_request(
            domain='example.com',
            method='get'
        )
        assert result.allowed is True


class TestPolicyEvaluatorNoDynamicBranching:
    """Tests ensuring no dynamic branching."""

    def test_no_conditional_policy_changes(self):
        """PolicyEvaluator must not allow conditional policy changes."""
        from execution_layer.policy import Policy, PolicyEvaluator
        policy = Policy(
            max_requests=10,
            allowed_domains=['example.com'],
            allowed_methods=['GET']
        )
        evaluator = PolicyEvaluator(policy)
        
        # Should not have methods to change policy
        assert not hasattr(evaluator, 'set_policy')
        assert not hasattr(evaluator, 'update_policy')
        assert not hasattr(evaluator, 'modify_policy')

    def test_no_runtime_domain_changes(self):
        """PolicyEvaluator must not allow runtime domain changes."""
        from execution_layer.policy import Policy, PolicyEvaluator
        policy = Policy(
            max_requests=10,
            allowed_domains=['example.com'],
            allowed_methods=['GET']
        )
        evaluator = PolicyEvaluator(policy)
        
        assert not hasattr(evaluator, 'add_domain')
        assert not hasattr(evaluator, 'remove_domain')

    def test_no_runtime_method_changes(self):
        """PolicyEvaluator must not allow runtime method changes."""
        from execution_layer.policy import Policy, PolicyEvaluator
        policy = Policy(
            max_requests=10,
            allowed_domains=['example.com'],
            allowed_methods=['GET']
        )
        evaluator = PolicyEvaluator(policy)
        
        assert not hasattr(evaluator, 'add_method')
        assert not hasattr(evaluator, 'remove_method')


class TestPolicyEvaluatorAuditability:
    """Tests for audit trail support."""

    def test_evaluation_result_has_reason(self):
        """Evaluation result must include reason."""
        from execution_layer.policy import Policy, PolicyEvaluator
        policy = Policy(
            max_requests=10,
            allowed_domains=['example.com'],
            allowed_methods=['GET']
        )
        evaluator = PolicyEvaluator(policy)
        
        result = evaluator.evaluate_request(
            domain='malicious.com',
            method='GET'
        )
        assert result.reason is not None
        assert len(result.reason) > 0

    def test_evaluation_result_has_timestamp(self):
        """Evaluation result must include timestamp."""
        from execution_layer.policy import Policy, PolicyEvaluator
        policy = Policy(
            max_requests=10,
            allowed_domains=['example.com'],
            allowed_methods=['GET']
        )
        evaluator = PolicyEvaluator(policy)
        
        result = evaluator.evaluate_request(
            domain='example.com',
            method='GET'
        )
        assert result.timestamp is not None

    def test_evaluation_result_to_dict(self):
        """Evaluation result must be serializable to dict."""
        from execution_layer.policy import Policy, PolicyEvaluator
        policy = Policy(
            max_requests=10,
            allowed_domains=['example.com'],
            allowed_methods=['GET']
        )
        evaluator = PolicyEvaluator(policy)
        
        result = evaluator.evaluate_request(
            domain='example.com',
            method='GET'
        )
        audit_dict = result.to_dict()
        assert 'allowed' in audit_dict
        assert 'reason' in audit_dict
        assert 'timestamp' in audit_dict
        assert 'request_number' in audit_dict

    def test_policy_to_dict(self):
        """Policy must be serializable to dict for audit."""
        from execution_layer.policy import Policy
        policy = Policy(
            max_requests=10,
            allowed_domains=['example.com'],
            allowed_methods=['GET']
        )
        
        policy_dict = policy.to_dict()
        assert policy_dict['max_requests'] == 10
        assert 'example.com' in policy_dict['allowed_domains']
        assert 'GET' in policy_dict['allowed_methods']


class TestPolicyEvaluatorNoRetry:
    """Tests ensuring no retry logic."""

    def test_no_retry_method(self):
        """PolicyEvaluator must not have retry methods."""
        from execution_layer.policy import Policy, PolicyEvaluator
        policy = Policy(
            max_requests=10,
            allowed_domains=['example.com'],
            allowed_methods=['GET']
        )
        evaluator = PolicyEvaluator(policy)
        
        assert not hasattr(evaluator, 'retry')
        assert not hasattr(evaluator, 'should_retry')

    def test_evaluation_returns_immediately(self):
        """Policy evaluation must return immediately."""
        import time
        from execution_layer.policy import Policy, PolicyEvaluator
        policy = Policy(
            max_requests=1000,
            allowed_domains=['example.com'],
            allowed_methods=['GET']
        )
        evaluator = PolicyEvaluator(policy)
        
        start = time.perf_counter()
        for _ in range(100):
            evaluator.evaluate_request(
                domain='example.com',
                method='GET'
            )
        elapsed = time.perf_counter() - start
        
        # 100 evaluations should complete in under 50ms
        assert elapsed < 0.05


class TestPolicyEvaluatorDeterminism:
    """Tests for deterministic behavior."""

    def test_same_input_same_output(self):
        """Same input must produce same output."""
        from execution_layer.policy import Policy, PolicyEvaluator
        
        # Create two identical evaluators
        policy1 = Policy(
            max_requests=10,
            allowed_domains=['example.com'],
            allowed_methods=['GET']
        )
        policy2 = Policy(
            max_requests=10,
            allowed_domains=['example.com'],
            allowed_methods=['GET']
        )
        
        eval1 = PolicyEvaluator(policy1)
        eval2 = PolicyEvaluator(policy2)
        
        result1 = eval1.evaluate_request(domain='example.com', method='GET')
        result2 = eval2.evaluate_request(domain='example.com', method='GET')
        
        assert result1.allowed == result2.allowed

    def test_order_independent_for_same_request(self):
        """Evaluation order should not affect individual request decisions."""
        from execution_layer.policy import Policy, PolicyEvaluator
        policy = Policy(
            max_requests=10,
            allowed_domains=['example.com', 'test.com'],
            allowed_methods=['GET', 'POST']
        )
        evaluator = PolicyEvaluator(policy)
        
        # Different order, same requests
        result1 = evaluator.evaluate_request(domain='example.com', method='GET')
        result2 = evaluator.evaluate_request(domain='test.com', method='POST')
        
        assert result1.allowed is True
        assert result2.allowed is True

