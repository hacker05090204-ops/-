"""
PHASE 04 TESTS — 2026 RE-IMPLEMENTATION
"""

import pytest
from enum import Enum
from dataclasses import FrozenInstanceError


class TestOperationStatusEnum:
    def test_exists(self):
        from phase04_execution import OperationStatus
        assert OperationStatus is not None

    def test_has_all_statuses(self):
        from phase04_execution import OperationStatus
        assert hasattr(OperationStatus, 'PENDING')
        assert hasattr(OperationStatus, 'APPROVED')
        assert hasattr(OperationStatus, 'REJECTED')
        assert hasattr(OperationStatus, 'EXECUTING')
        assert hasattr(OperationStatus, 'COMPLETED')
        assert hasattr(OperationStatus, 'FAILED')


class TestOperationRequest:
    def test_exists(self):
        from phase04_execution import OperationRequest
        assert OperationRequest is not None

    def test_creation(self):
        from phase04_execution import OperationRequest
        from phase02_actors import Actor, ActorType, Role
        actor = Actor("op-001", "Operator", ActorType.HUMAN, Role.OPERATOR)
        req = OperationRequest(
            request_id="req-001",
            actor=actor,
            operation_name="test_op",
            parameters={"key": "value"},
            requires_confirmation=True
        )
        assert req.request_id == "req-001"
        assert req.operation_name == "test_op"
        assert req.requires_confirmation is True

    def test_immutable(self):
        from phase04_execution import OperationRequest
        from phase02_actors import Actor, ActorType, Role
        actor = Actor("op-001", "Operator", ActorType.HUMAN, Role.OPERATOR)
        req = OperationRequest("req-001", actor, "test", {})
        with pytest.raises(FrozenInstanceError):
            req.operation_name = "modified"


class TestOperationResult:
    def test_exists(self):
        from phase04_execution import OperationResult
        assert OperationResult is not None

    def test_success_result(self):
        from phase04_execution import OperationResult, OperationStatus
        result = OperationResult(
            request_id="req-001",
            status=OperationStatus.COMPLETED,
            output="success"
        )
        assert result.status == OperationStatus.COMPLETED
        assert result.output == "success"

    def test_failure_result(self):
        from phase04_execution import OperationResult, OperationStatus
        result = OperationResult(
            request_id="req-001",
            status=OperationStatus.FAILED,
            error_message="Something went wrong"
        )
        assert result.status == OperationStatus.FAILED
        assert result.error_message == "Something went wrong"


class TestExecutionContext:
    def test_exists(self):
        from phase04_execution import ExecutionContext
        assert ExecutionContext is not None

    def test_creation(self):
        from phase04_execution import ExecutionContext
        from phase02_actors import Actor, ActorType, Role
        from phase03_trust import TrustZone
        actor = Actor("op-001", "Operator", ActorType.HUMAN, Role.OPERATOR)
        ctx = ExecutionContext(
            context_id="ctx-001",
            actor=actor,
            trust_zone=TrustZone.INTERNAL
        )
        assert ctx.context_id == "ctx-001"
        assert ctx.trust_zone == TrustZone.INTERNAL


class TestFactoryFunctions:
    def test_create_operation_request(self):
        from phase04_execution import create_operation_request
        from phase02_actors import Actor, ActorType, Role
        actor = Actor("op-001", "Operator", ActorType.HUMAN, Role.OPERATOR)
        req = create_operation_request(actor, "test_op", {"key": "value"})
        assert req.operation_name == "test_op"
        assert req.request_id is not None

    def test_create_operation_request_validates_name(self):
        from phase04_execution import create_operation_request
        from phase02_actors import Actor, ActorType, Role
        actor = Actor("op-001", "Operator", ActorType.HUMAN, Role.OPERATOR)
        with pytest.raises(ValueError):
            create_operation_request(actor, "", {})

    def test_create_result_success(self):
        from phase04_execution import create_result_success, OperationStatus
        result = create_result_success("req-001", "output_data")
        assert result.status == OperationStatus.COMPLETED
        assert result.output == "output_data"

    def test_create_result_failure(self):
        from phase04_execution import create_result_failure, OperationStatus
        result = create_result_failure("req-001", "error occurred")
        assert result.status == OperationStatus.FAILED
        assert result.error_message == "error occurred"


class TestPackageExports:
    def test_all_exports(self):
        from phase04_execution import (
            OperationStatus,
            OperationRequest,
            OperationResult,
            ExecutionContext,
            create_operation_request,
            create_execution_context,
            create_result_success,
            create_result_failure,
        )
        assert all([
            OperationStatus, OperationRequest, OperationResult,
            ExecutionContext, create_operation_request
        ])
