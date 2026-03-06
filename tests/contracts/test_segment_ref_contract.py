"""
Contract tests for SegmentRef.

Verifies that all use cases use the official resolver.

Author: Trifecta Team
Date: 2026-03-06
"""

import pytest
from pathlib import Path

from src.trifecta.domain.segment_ref import resolve_segment_ref, SegmentRef
from src.trifecta.domain.repo_ref import resolve_repo_ref, RepoRef
from src.trifecta.domain import contracts


class TestSegmentRefContract:
    """Tests for SegmentRef contract compliance."""

    def test_resolve_returns_segment_ref(self):
        """Verify resolve_segment_ref returns SegmentRef."""
        ref = resolve_segment_ref(Path.cwd())
        assert isinstance(ref, SegmentRef)

    def test_segment_ref_has_all_fields(self):
        """Verify SegmentRef has all required fields."""
        ref = resolve_segment_ref(Path.cwd())
        assert hasattr(ref, "repo_root")
        assert hasattr(ref, "repo_id")
        assert hasattr(ref, "segment_root")
        assert hasattr(ref, "segment_id")
        assert hasattr(ref, "runtime_dir")
        assert hasattr(ref, "registry_key")
        assert hasattr(ref, "telemetry_dir")
        assert hasattr(ref, "config_dir")
        assert hasattr(ref, "cache_dir")

    def test_segment_ref_is_immutable(self):
        """Verify SegmentRef is frozen (immutable)."""
        ref = resolve_segment_ref(Path.cwd())
        with pytest.raises(AttributeError):
            ref.segment_id = "modified"

    def test_repo_id_format(self):
        """Verify repo_id follows contract (hex string)."""
        ref = resolve_segment_ref(Path.cwd())
        assert contracts.validate_repo_id(ref.repo_id)

    def test_segment_id_format(self):
        """Verify segment_id follows contract."""
        ref = resolve_segment_ref(Path.cwd())
        assert contracts.validate_segment_id(ref.segment_id)

    def test_registry_key_format(self):
        """Verify registry_key follows contract."""
        ref = resolve_segment_ref(Path.cwd())
        assert contracts.validate_runtime_key(ref.registry_key)

    def test_paths_are_absolute(self):
        """Verify all paths are absolute."""
        ref = resolve_segment_ref(Path.cwd())
        assert ref.repo_root.is_absolute()
        assert ref.segment_root.is_absolute()
        assert ref.runtime_dir.is_absolute()
        assert ref.telemetry_dir.is_absolute()
        assert ref.config_dir.is_absolute()
        assert ref.cache_dir.is_absolute()

    def test_segment_id_contains_hash(self):
        """Verify segment_id contains hash portion."""
        ref = resolve_segment_ref(Path.cwd(), hash_length=8)
        assert "_" in ref.segment_id
        parts = ref.segment_id.split("_")
        assert len(parts) == 2
        assert len(parts[1]) == 8


class TestRepoRefContract:
    """Tests for RepoRef contract compliance."""

    def test_resolve_repo_ref(self):
        """Verify resolve_repo_ref returns RepoRef."""
        ref = resolve_repo_ref(Path.cwd())
        assert isinstance(ref, RepoRef)

    def test_repo_ref_has_required_fields(self):
        """Verify RepoRef has required fields."""
        ref = resolve_repo_ref(Path.cwd())
        assert hasattr(ref, "repo_root")
        assert hasattr(ref, "repo_id")

    def test_repo_ref_is_immutable(self):
        """Verify RepoRef is frozen."""
        ref = resolve_repo_ref(Path.cwd())
        with pytest.raises(AttributeError):
            ref.repo_id = "modified"

    def test_get_repo_id_helper(self):
        """Verify get_repo_id convenience function."""
        from src.trifecta.domain.repo_ref import get_repo_id

        repo_id = get_repo_id(Path.cwd())
        assert contracts.validate_repo_id(repo_id)


class TestDeprecationWarnings:
    """Tests for deprecated functions."""

    def test_deprecated_resolve_segment_ref(self):
        """Verify deprecated function emits warning."""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from src.trifecta.domain.segment_ref import resolve_segment_ref_deprecated

            resolve_segment_ref_deprecated(Path.cwd())
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
