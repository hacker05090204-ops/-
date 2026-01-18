"""
Phase-21 No Auto-Apply Tests

Tests verifying patches are NEVER auto-applied.
"""

import pytest


class TestNoAutoApplication:
    """Tests verifying no auto-application of patches."""

    def test_no_auto_apply_function_exists(self) -> None:
        """No auto_apply function should exist in module."""
        import phase21_patch_covenant
        
        # Check main module
        assert not hasattr(phase21_patch_covenant, "auto_apply")
        assert not hasattr(phase21_patch_covenant, "auto_apply_patch")
        assert not hasattr(phase21_patch_covenant, "apply_automatically")

    def test_no_scheduled_apply_function_exists(self) -> None:
        """No scheduled apply function should exist."""
        import phase21_patch_covenant
        
        assert not hasattr(phase21_patch_covenant, "schedule_apply")
        assert not hasattr(phase21_patch_covenant, "schedule_patch")
        assert not hasattr(phase21_patch_covenant, "delayed_apply")

    def test_no_background_apply_function_exists(self) -> None:
        """No background apply function should exist."""
        import phase21_patch_covenant
        
        assert not hasattr(phase21_patch_covenant, "background_apply")
        assert not hasattr(phase21_patch_covenant, "async_apply")
        assert not hasattr(phase21_patch_covenant, "deferred_apply")


class TestConfirmationRequired:
    """Tests verifying confirmation is always required."""

    def test_apply_requires_confirmation_record(
        self,
        sample_patch_content: str,
        sample_patch_id: str,
        sample_timestamp: str,
    ) -> None:
        """Apply must require a confirmation record."""
        from phase21_patch_covenant.patch_applicator import apply_patch
        from phase21_patch_covenant.confirmation import record_confirmation
        
        # Create confirmation record
        confirmation = record_confirmation(
            patch_id=sample_patch_id,
            timestamp=sample_timestamp,
            confirmed=True,
            reason="Approved after review.",
        )
        
        # Apply requires confirmation
        result = apply_patch(
            patch_content=sample_patch_content,
            confirmation=confirmation,
        )
        
        assert result.applied is True
        assert result.confirmation_hash is not None

    def test_apply_fails_without_confirmation(
        self,
        sample_patch_content: str,
    ) -> None:
        """Apply must fail without confirmation record."""
        from phase21_patch_covenant.patch_applicator import apply_patch
        
        with pytest.raises(ValueError, match="confirmation required"):
            apply_patch(
                patch_content=sample_patch_content,
                confirmation=None,
            )

    def test_apply_fails_with_rejection(
        self,
        sample_patch_content: str,
        sample_patch_id: str,
        sample_timestamp: str,
    ) -> None:
        """Apply must fail if confirmation is a rejection."""
        from phase21_patch_covenant.patch_applicator import apply_patch
        from phase21_patch_covenant.confirmation import record_rejection
        
        # Create rejection record
        rejection = record_rejection(
            patch_id=sample_patch_id,
            timestamp=sample_timestamp,
            reason="Rejected.",
        )
        
        with pytest.raises(ValueError, match="patch was rejected"):
            apply_patch(
                patch_content=sample_patch_content,
                confirmation=rejection,
            )


class TestNoRecommendations:
    """Tests verifying no recommendations are made."""

    def test_no_recommend_function_exists(self) -> None:
        """No recommend function should exist."""
        import phase21_patch_covenant
        
        assert not hasattr(phase21_patch_covenant, "recommend")
        assert not hasattr(phase21_patch_covenant, "recommend_action")
        assert not hasattr(phase21_patch_covenant, "suggest_action")
        assert not hasattr(phase21_patch_covenant, "should_accept")
        assert not hasattr(phase21_patch_covenant, "should_reject")

    def test_no_analysis_function_exists(self) -> None:
        """No analysis function should exist."""
        import phase21_patch_covenant
        
        assert not hasattr(phase21_patch_covenant, "analyze_patch")
        assert not hasattr(phase21_patch_covenant, "analyze_safety")
        assert not hasattr(phase21_patch_covenant, "score_patch")
        assert not hasattr(phase21_patch_covenant, "rate_patch")


class TestHumanAttributionPreserved:
    """Tests verifying human attribution is preserved."""

    def test_apply_result_has_human_initiated(
        self,
        sample_patch_content: str,
        sample_patch_id: str,
        sample_timestamp: str,
    ) -> None:
        """Apply result must have human_initiated=True."""
        from phase21_patch_covenant.patch_applicator import apply_patch
        from phase21_patch_covenant.confirmation import record_confirmation
        
        confirmation = record_confirmation(
            patch_id=sample_patch_id,
            timestamp=sample_timestamp,
            confirmed=True,
            reason="Approved.",
        )
        
        result = apply_patch(
            patch_content=sample_patch_content,
            confirmation=confirmation,
        )
        
        assert result.human_initiated is True

    def test_apply_result_has_actor_human(
        self,
        sample_patch_content: str,
        sample_patch_id: str,
        sample_timestamp: str,
    ) -> None:
        """Apply result must have actor='HUMAN'."""
        from phase21_patch_covenant.patch_applicator import apply_patch
        from phase21_patch_covenant.confirmation import record_confirmation
        
        confirmation = record_confirmation(
            patch_id=sample_patch_id,
            timestamp=sample_timestamp,
            confirmed=True,
            reason="Approved.",
        )
        
        result = apply_patch(
            patch_content=sample_patch_content,
            confirmation=confirmation,
        )
        
        assert result.actor == "HUMAN"

