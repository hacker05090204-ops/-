"""
Phase-20 Immutability Tests

These tests verify all Phase-20 records are immutable.
"""

import pytest


class TestReflectionRecordImmutability:
    """Tests for ReflectionRecord immutability."""

    def test_record_is_frozen_dataclass(
        self, session_id: str, sample_reflection_text: str
    ) -> None:
        """ReflectionRecord must be a frozen dataclass."""
        from phase20_reflection.reflection_record import create_reflection_record
        
        record = create_reflection_record(
            session_id=session_id,
            reflection_text=sample_reflection_text,
            phase15_digest="a" * 64,
            phase19_digest="b" * 64,
        )
        
        # Attempt to modify should raise FrozenInstanceError
        with pytest.raises(Exception):
            record.reflection_text = "modified"  # type: ignore

    def test_session_id_immutable(
        self, session_id: str, sample_reflection_text: str
    ) -> None:
        """session_id cannot be modified."""
        from phase20_reflection.reflection_record import create_reflection_record
        
        record = create_reflection_record(
            session_id=session_id,
            reflection_text=sample_reflection_text,
            phase15_digest="a" * 64,
            phase19_digest="b" * 64,
        )
        
        with pytest.raises(Exception):
            record.session_id = "new-id"  # type: ignore

    def test_timestamp_immutable(
        self, session_id: str, sample_reflection_text: str
    ) -> None:
        """timestamp cannot be modified."""
        from phase20_reflection.reflection_record import create_reflection_record
        
        record = create_reflection_record(
            session_id=session_id,
            reflection_text=sample_reflection_text,
            phase15_digest="a" * 64,
            phase19_digest="b" * 64,
        )
        
        with pytest.raises(Exception):
            record.timestamp = "2099-01-01T00:00:00Z"  # type: ignore

    def test_human_initiated_immutable(
        self, session_id: str, sample_reflection_text: str
    ) -> None:
        """human_initiated cannot be modified."""
        from phase20_reflection.reflection_record import create_reflection_record
        
        record = create_reflection_record(
            session_id=session_id,
            reflection_text=sample_reflection_text,
            phase15_digest="a" * 64,
            phase19_digest="b" * 64,
        )
        
        with pytest.raises(Exception):
            record.human_initiated = False  # type: ignore

    def test_actor_immutable(
        self, session_id: str, sample_reflection_text: str
    ) -> None:
        """actor cannot be modified."""
        from phase20_reflection.reflection_record import create_reflection_record
        
        record = create_reflection_record(
            session_id=session_id,
            reflection_text=sample_reflection_text,
            phase15_digest="a" * 64,
            phase19_digest="b" * 64,
        )
        
        with pytest.raises(Exception):
            record.actor = "SYSTEM"  # type: ignore


class TestBindingImmutability:
    """Tests for ReflectionBinding immutability."""

    def test_binding_is_frozen(
        self,
        sample_reflection_text: str,
        mock_phase15_digest: str,
        mock_phase19_digest: str,
    ) -> None:
        """ReflectionBinding must be frozen."""
        from phase20_reflection.reflection_hash import hash_reflection, create_binding
        
        reflection_hash = hash_reflection(sample_reflection_text)
        binding = create_binding(
            reflection_hash=reflection_hash,
            phase15_digest=mock_phase15_digest,
            phase19_digest=mock_phase19_digest,
        )
        
        with pytest.raises(Exception):
            binding.binding_hash = "tampered"  # type: ignore

    def test_binding_reflection_hash_immutable(
        self,
        sample_reflection_text: str,
        mock_phase15_digest: str,
        mock_phase19_digest: str,
    ) -> None:
        """binding.reflection_hash cannot be modified."""
        from phase20_reflection.reflection_hash import hash_reflection, create_binding
        
        reflection_hash = hash_reflection(sample_reflection_text)
        binding = create_binding(
            reflection_hash=reflection_hash,
            phase15_digest=mock_phase15_digest,
            phase19_digest=mock_phase19_digest,
        )
        
        with pytest.raises(Exception):
            binding.reflection_hash = "tampered"  # type: ignore


class TestNoUpdateMethods:
    """Tests verifying no update methods exist."""

    def test_no_update_record_function(self) -> None:
        """reflection_record module must not have update function."""
        from phase20_reflection import reflection_record
        
        assert not hasattr(reflection_record, "update_record")
        assert not hasattr(reflection_record, "update_reflection_record")
        assert not hasattr(reflection_record, "modify_record")

    def test_no_delete_record_function(self) -> None:
        """reflection_record module must not have delete function."""
        from phase20_reflection import reflection_record
        
        assert not hasattr(reflection_record, "delete_record")
        assert not hasattr(reflection_record, "delete_reflection_record")
        assert not hasattr(reflection_record, "remove_record")


class TestNoMutableContainers:
    """Tests verifying no mutable containers in records."""

    def test_record_has_no_list_fields(
        self, session_id: str, sample_reflection_text: str
    ) -> None:
        """Record must not have mutable list fields."""
        from phase20_reflection.reflection_record import create_reflection_record
        
        record = create_reflection_record(
            session_id=session_id,
            reflection_text=sample_reflection_text,
            phase15_digest="a" * 64,
            phase19_digest="b" * 64,
        )
        
        for field_name in record.__dataclass_fields__:
            value = getattr(record, field_name)
            assert not isinstance(value, list), f"Mutable list field: {field_name}"

    def test_record_has_no_dict_fields(
        self, session_id: str, sample_reflection_text: str
    ) -> None:
        """Record must not have mutable dict fields."""
        from phase20_reflection.reflection_record import create_reflection_record
        
        record = create_reflection_record(
            session_id=session_id,
            reflection_text=sample_reflection_text,
            phase15_digest="a" * 64,
            phase19_digest="b" * 64,
        )
        
        for field_name in record.__dataclass_fields__:
            value = getattr(record, field_name)
            assert not isinstance(value, dict), f"Mutable dict field: {field_name}"
