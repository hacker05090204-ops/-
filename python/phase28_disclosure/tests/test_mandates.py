import pytest
from ..types import PresentationPackage
from ..formatter import format_package
from ..exporter import export_package

# These tests will FAIL initially because the modules don't exist logic yet

def test_human_initiated_required():
    """Verify that export functions raise error if human_initiated is False."""
    try:
        from ..exporter import export_package
    except ImportError:
        pytest.skip("Exporter not implemented yet")

    with pytest.raises(Exception, match="Human initiation required"):
        export_package(None, None, human_initiated=False)

def test_disclaimer_presence():
    """Verify that formatting includes mandatory disclaimers."""
    try:
        from ..formatter import format_package
    except ImportError:
        pytest.skip("Formatter not implemented yet")
        
    result = format_package("some data", context="INTERNAL")
    assert "NOT VERIFIED" in result
    assert "reception" in result # Placeholder for actual check
