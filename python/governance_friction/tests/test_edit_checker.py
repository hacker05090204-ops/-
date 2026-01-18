"""
Tests for Phase-10 forced edit checker.

Validates:
- Meaningful edits are required
- Whitespace-only changes are rejected
- No auto-edit capability exists
"""

import pytest

from governance_friction.edit_checker import ForcedEditChecker
from governance_friction.errors import ForcedEditViolation


class TestForcedEditChecker:
    """Test forced edit checker functionality."""
    
    def test_register_content(self, decision_id, original_content):
        """register_content should store original content."""
        checker = ForcedEditChecker()
        content_hash = checker.register_content(decision_id, original_content)
        
        assert content_hash is not None
        assert len(content_hash) == 64  # SHA-256 hex
        assert checker.get_original_content(decision_id) == original_content
    
    def test_identical_content_raises(self, decision_id, original_content):
        """Identical content should raise ForcedEditViolation."""
        checker = ForcedEditChecker()
        checker.register_content(decision_id, original_content)
        
        with pytest.raises(ForcedEditViolation) as exc_info:
            checker.require_edit(decision_id, original_content)
        
        assert exc_info.value.decision_id == decision_id
        assert "identical" in exc_info.value.reason.lower()
    
    def test_whitespace_only_change_raises(self, decision_id, original_content):
        """Whitespace-only changes should raise ForcedEditViolation."""
        checker = ForcedEditChecker()
        checker.register_content(decision_id, original_content)
        
        # Add trailing whitespace
        whitespace_edit = original_content + "   "
        
        with pytest.raises(ForcedEditViolation) as exc_info:
            checker.require_edit(decision_id, whitespace_edit)
        
        assert "whitespace" in exc_info.value.reason.lower()
    
    def test_newline_only_change_raises(self, decision_id, original_content):
        """Newline-only changes should raise ForcedEditViolation."""
        checker = ForcedEditChecker()
        checker.register_content(decision_id, original_content)
        
        # Add newlines
        newline_edit = original_content + "\n\n\n"
        
        with pytest.raises(ForcedEditViolation):
            checker.require_edit(decision_id, newline_edit)
    
    def test_meaningful_edit_succeeds(self, decision_id, original_content, edited_content):
        """Meaningful edits should succeed."""
        checker = ForcedEditChecker()
        checker.register_content(decision_id, original_content)
        
        result = checker.require_edit(decision_id, edited_content)
        
        assert result is True
    
    def test_empty_to_nonempty_succeeds(self, decision_id):
        """Changing from empty to non-empty should succeed."""
        checker = ForcedEditChecker()
        checker.register_content(decision_id, "")
        
        result = checker.require_edit(decision_id, "New content")
        
        assert result is True
    
    def test_unknown_decision_raises_keyerror(self):
        """Operations on unknown decision should raise KeyError."""
        checker = ForcedEditChecker()
        
        with pytest.raises(KeyError):
            checker.require_edit("unknown", "content")
    
    def test_clear_registration(self, decision_id, original_content):
        """clear_registration should remove stored content."""
        checker = ForcedEditChecker()
        checker.register_content(decision_id, original_content)
        
        checker.clear_registration(decision_id)
        
        assert checker.get_original_content(decision_id) is None


class TestForcedEditCheckerNoAutoEdit:
    """Test that no auto-edit capability exists."""
    
    def test_no_auto_edit_method(self):
        """ForcedEditChecker should not have auto_edit method."""
        checker = ForcedEditChecker()
        
        assert not hasattr(checker, "auto_edit")
        assert not hasattr(checker, "suggest_edit")
        assert not hasattr(checker, "bypass_edit")
        assert not hasattr(checker, "skip_edit")
    
    def test_no_edit_suggestion(self, decision_id, original_content):
        """Checker should not suggest edits."""
        checker = ForcedEditChecker()
        checker.register_content(decision_id, original_content)
        
        # No method to get suggested edits
        assert not hasattr(checker, "get_suggested_edit")
        assert not hasattr(checker, "generate_edit")


class TestWhitespaceNormalization:
    """Test whitespace normalization edge cases."""
    
    def test_tab_changes_rejected(self, decision_id):
        """Tab-only changes should be rejected."""
        checker = ForcedEditChecker()
        checker.register_content(decision_id, "content")
        
        with pytest.raises(ForcedEditViolation):
            checker.require_edit(decision_id, "content\t")
    
    def test_mixed_whitespace_rejected(self, decision_id):
        """Mixed whitespace changes should be rejected."""
        checker = ForcedEditChecker()
        checker.register_content(decision_id, "hello world")
        
        # Change space to tab
        with pytest.raises(ForcedEditViolation):
            checker.require_edit(decision_id, "hello\tworld")
    
    def test_content_with_different_words_succeeds(self, decision_id):
        """Content with different words should succeed."""
        checker = ForcedEditChecker()
        checker.register_content(decision_id, "hello world")
        
        result = checker.require_edit(decision_id, "hello universe")
        
        assert result is True
