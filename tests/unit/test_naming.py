"""
Tests for normalize_segment_id function.

TDD Phase: RED -> GREEN
Tests the normalization rules:
- strip()
- spaces -> '-'
- allow [a-zA-Z0-9_-], rest -> '_'
- lowercase
- empty -> "segment"
"""

from src.domain.naming import normalize_segment_id


class TestNormalizeSegmentId:
    """Test suite for segment ID normalization."""

    def test_simple_lowercase(self) -> None:
        """Simple lowercase name should pass through."""
        assert normalize_segment_id("myproject") == "myproject"

    def test_uppercase_to_lowercase(self) -> None:
        """Uppercase should be converted to lowercase."""
        assert normalize_segment_id("MyProject") == "myproject"
        assert normalize_segment_id("MYPROJECT") == "myproject"

    def test_spaces_to_hyphens(self) -> None:
        """Spaces should be converted to hyphens."""
        assert normalize_segment_id("my project") == "my-project"
        assert normalize_segment_id("my  project") == "my--project"

    def test_strip_whitespace(self) -> None:
        """Leading/trailing whitespace should be stripped."""
        assert normalize_segment_id("  myproject  ") == "myproject"
        assert normalize_segment_id("  my project  ") == "my-project"

    def test_special_chars_to_underscore(self) -> None:
        """Special characters should be converted to underscore."""
        assert normalize_segment_id("my@project") == "my_project"
        assert normalize_segment_id("my#project!") == "my_project_"
        assert normalize_segment_id("my.project") == "my_project"

    def test_accents_to_underscore(self) -> None:
        """Accented characters should be converted to underscore."""
        assert normalize_segment_id("café") == "caf_"
        assert normalize_segment_id("niño") == "ni_o"

    def test_preserve_hyphens_and_underscores(self) -> None:
        """Hyphens and underscores should be preserved."""
        assert normalize_segment_id("my-project") == "my-project"
        assert normalize_segment_id("my_project") == "my_project"
        assert normalize_segment_id("my-_project") == "my-_project"

    def test_preserve_numbers(self) -> None:
        """Numbers should be preserved."""
        assert normalize_segment_id("project123") == "project123"
        assert normalize_segment_id("123project") == "123project"

    def test_empty_string_fallback(self) -> None:
        """Empty string should return 'segment'."""
        assert normalize_segment_id("") == "segment"

    def test_only_special_chars_fallback(self) -> None:
        """String with only special chars should become underscores or fallback."""
        # All special chars become underscores, then we have a non-empty result
        result = normalize_segment_id("@#$")
        assert result == "___"

    def test_only_whitespace_fallback(self) -> None:
        """String with only whitespace should return 'segment'."""
        assert normalize_segment_id("   ") == "segment"
        assert normalize_segment_id("\t\n") == "segment"

    def test_complex_mixed_case(self) -> None:
        """Complex real-world example."""
        assert normalize_segment_id("My Cool Project 2024!") == "my-cool-project-2024_"

    def test_path_like_input(self) -> None:
        """Should work with path-like strings (just the name part)."""
        # Note: caller should pass path.name, not full path
        assert normalize_segment_id("my-segment") == "my-segment"
