"""Tests for deprecation warnings in segment_utils.py."""

import warnings
from pathlib import Path

from src.infrastructure.segment_utils import compute_segment_id, resolve_segment_root


class TestSegmentUtilsDeprecation:
    def test_resolve_segment_root_emits_deprecation_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            resolve_segment_root()

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "resolve_segment_root()" in str(w[0].message)
            assert "get_segment_root()" in str(w[0].message)
            assert "segment_resolver" in str(w[0].message)

    def test_compute_segment_id_emits_deprecation_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            compute_segment_id(Path("/tmp/test"))

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "compute_segment_id()" in str(w[0].message)
            assert "get_segment_fingerprint()" in str(
                w[0].message
            ) or "resolve_segment_ref()" in str(w[0].message)

    def test_resolve_segment_root_still_works(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = resolve_segment_root()
            assert result is not None
            assert result.is_absolute()

    def test_compute_segment_id_still_works(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = compute_segment_id(Path("/tmp/test"))
            assert result is not None
            assert len(result) == 8
            assert result.isalnum()
