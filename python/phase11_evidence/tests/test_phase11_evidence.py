"""PHASE 11 TESTS"""
import pytest

class TestEvidenceType:
    def test_exists(self):
        from phase11_evidence import EvidenceType
        assert hasattr(EvidenceType, 'SCREENSHOT')
        assert hasattr(EvidenceType, 'LOG')

class TestEvidence:
    def test_immutable(self):
        from phase11_evidence import Evidence, EvidenceType
        from dataclasses import FrozenInstanceError
        ev = Evidence("e-001", EvidenceType.LOG, "Test log", "system")
        with pytest.raises(FrozenInstanceError):
            ev.description = "modified"

class TestCreateEvidence:
    def test_creates_evidence(self):
        from phase11_evidence import create_evidence, EvidenceType
        ev = create_evidence(EvidenceType.LOG, "Error log", "server.log")
        assert ev.evidence_type == EvidenceType.LOG

    def test_validates_description(self):
        from phase11_evidence import create_evidence, EvidenceType
        with pytest.raises(ValueError):
            create_evidence(EvidenceType.LOG, "", "source")

class TestIsValidEvidence:
    def test_valid(self):
        from phase11_evidence import create_evidence, EvidenceType, is_valid_evidence
        ev = create_evidence(EvidenceType.LOG, "Test", "source")
        assert is_valid_evidence(ev) is True
