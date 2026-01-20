"""PHASE 05 TESTS — 2026 RE-IMPLEMENTATION"""

import pytest
from dataclasses import FrozenInstanceError


class TestScannerTypeEnum:
    def test_exists(self):
        from phase05_scanner import ScannerType
        assert ScannerType is not None

    def test_has_types(self):
        from phase05_scanner import ScannerType
        assert hasattr(ScannerType, 'PORT_SCANNER')
        assert hasattr(ScannerType, 'VULNERABILITY_SCANNER')
        assert hasattr(ScannerType, 'WEB_SCANNER')


class TestScannerDefinition:
    def test_exists(self):
        from phase05_scanner import ScannerDefinition
        assert ScannerDefinition is not None

    def test_is_always_read_only(self):
        from phase05_scanner import ScannerDefinition, ScannerType
        scanner = ScannerDefinition(
            scanner_id="s-001",
            name="Test Scanner",
            scanner_type=ScannerType.PORT_SCANNER,
            description="A test scanner"
        )
        assert scanner.is_read_only is True

    def test_immutable(self):
        from phase05_scanner import ScannerDefinition, ScannerType
        scanner = ScannerDefinition("s-001", "Test", ScannerType.PORT_SCANNER, "desc")
        with pytest.raises(FrozenInstanceError):
            scanner.name = "modified"


class TestScanRequest:
    def test_requires_confirmation_default(self):
        from phase05_scanner import ScanRequest
        req = ScanRequest(
            request_id="req-001",
            scanner_id="s-001",
            target="192.168.1.1",
            parameters={}
        )
        assert req.requires_confirmation is True


class TestFactoryFunctions:
    def test_create_scanner_definition(self):
        from phase05_scanner import create_scanner_definition, ScannerType
        scanner = create_scanner_definition(
            name="Nmap",
            scanner_type=ScannerType.PORT_SCANNER,
            description="Port scanner"
        )
        assert scanner.name == "Nmap"
        assert scanner.is_read_only is True

    def test_create_scan_request(self):
        from phase05_scanner import create_scan_request
        req = create_scan_request("s-001", "192.168.1.1")
        assert req.target == "192.168.1.1"
        assert req.requires_confirmation is True

    def test_create_scan_request_validates_target(self):
        from phase05_scanner import create_scan_request
        with pytest.raises(ValueError):
            create_scan_request("s-001", "")


class TestPackageExports:
    def test_all_exports(self):
        from phase05_scanner import (
            ScannerType, ScanStatus, ScannerDefinition,
            ScanRequest, ScanResult, create_scanner_definition
        )
        assert all([ScannerType, ScanStatus, ScannerDefinition])
