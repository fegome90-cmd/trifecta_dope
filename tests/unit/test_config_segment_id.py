"""
Tests for TrifectaConfig with segment_id derivation.

TDD Phase: RED -> GREEN
"""

from pathlib import Path

import pytest

from src.domain.models import TrifectaConfig


class TestTrifectaConfigSegmentId:
    """Test that TrifectaConfig derives segment_id correctly."""

    def test_segment_with_spaces_normalizes(self) -> None:
        """Segment with spaces should derive normalized segment_id."""
        config = TrifectaConfig(
            segment="My Project",
            scope="Test",
            repo_root="/tmp/test",
        )

        assert config.segment_id == "my-project"

    def test_segment_with_uppercase_normalizes(self) -> None:
        """Segment with uppercase should derive lowercase segment_id."""
        config = TrifectaConfig(
            segment="MyProject",
            scope="Test",
            repo_root="/tmp/test",
        )

        assert config.segment_id == "myproject"

    def test_segment_with_special_chars_normalizes(self) -> None:
        """Segment with special chars should derive safe segment_id."""
        config = TrifectaConfig(
            segment="my@project!",
            scope="Test",
            repo_root="/tmp/test",
        )

        assert config.segment_id == "my_project_"

    def test_segment_preserves_original(self) -> None:
        """Original segment value should be preserved."""
        config = TrifectaConfig(
            segment="My Cool Project",
            scope="Test",
            repo_root="/tmp/test",
        )

        assert config.segment == "My Cool Project"
        assert config.segment_id == "my-cool-project"

    def test_empty_segment_raises(self) -> None:
        """Empty segment should raise validation error."""
        with pytest.raises(ValueError, match="non-empty"):
            TrifectaConfig(
                segment="",
                scope="Test",
                repo_root="/tmp/test",
            )

    def test_whitespace_only_segment_raises(self) -> None:
        """Whitespace-only segment should raise validation error."""
        with pytest.raises(ValueError, match="non-empty"):
            TrifectaConfig(
                segment="   ",
                scope="Test",
                repo_root="/tmp/test",
            )
