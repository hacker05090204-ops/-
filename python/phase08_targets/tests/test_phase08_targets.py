"""PHASE 08 TESTS"""
import pytest
from dataclasses import FrozenInstanceError

class TestTargetType:
    def test_exists(self):
        from phase08_targets import TargetType
        assert hasattr(TargetType, 'HOST')
        assert hasattr(TargetType, 'WEB_APPLICATION')

class TestTargetMetadata:
    def test_creation(self):
        from phase08_targets import TargetMetadata, TargetType
        target = TargetMetadata("t-001", "Test", TargetType.HOST, "192.168.1.1")
        assert target.name == "Test"

    def test_immutable(self):
        from phase08_targets import TargetMetadata, TargetType
        target = TargetMetadata("t-001", "Test", TargetType.HOST, "192.168.1.1")
        with pytest.raises(FrozenInstanceError):
            target.name = "modified"

class TestCreateTarget:
    def test_create_target(self):
        from phase08_targets import create_target, TargetType
        target = create_target("Test Host", TargetType.HOST, "192.168.1.1")
        assert target.name == "Test Host"

    def test_validates_name(self):
        from phase08_targets import create_target, TargetType
        with pytest.raises(ValueError):
            create_target("", TargetType.HOST, "192.168.1.1")

    def test_validates_address(self):
        from phase08_targets import create_target, TargetType
        with pytest.raises(ValueError):
            create_target("Test", TargetType.HOST, "")

class TestIsValidTarget:
    def test_valid(self):
        from phase08_targets import TargetMetadata, TargetType, is_valid_target
        target = TargetMetadata("t-001", "Test", TargetType.HOST, "192.168.1.1")
        assert is_valid_target(target) is True
