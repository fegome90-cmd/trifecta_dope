"""
Tests for strict 3+1 validation with legacy as error and ambiguity detection.

TDD Phase: RED -> GREEN
"""

from pathlib import Path

import pytest

from src.infrastructure.validators import validate_segment_fp


class TestStrictValidation:
    """Test strict 3+1 gate with no legacy tolerance."""

    def test_legacy_agent_md_is_error(self, tmp_path: Path) -> None:
        """Legacy agent.md (no suffix) should be ERROR, not warning."""
        seg = tmp_path / "test_seg"
        seg.mkdir()
        (seg / "skill.md").touch()
        ctx = seg / "_ctx"
        ctx.mkdir()
        # Legacy naming
        (ctx / "agent.md").touch()
        (ctx / "prime_test_seg.md").touch()
        (ctx / "session_test_seg.md").touch()

        result = validate_segment_fp(seg)

        assert result.is_err(), "Legacy agent.md should cause validation ERROR"
        errors = result.unwrap_err()
        assert any("agent_test_seg.md" in err.lower() for err in errors), (
            f"Should mention missing agent_test_seg.md, got: {errors}"
        )

    def test_legacy_prime_md_is_error(self, tmp_path: Path) -> None:
        """Legacy prime.md (no suffix) should be ERROR."""
        seg = tmp_path / "test_seg"
        seg.mkdir()
        (seg / "skill.md").touch()
        ctx = seg / "_ctx"
        ctx.mkdir()
        (ctx / "agent_test_seg.md").touch()
        (ctx / "prime.md").touch()  # Legacy
        (ctx / "session_test_seg.md").touch()

        result = validate_segment_fp(seg)

        assert result.is_err()
        errors = result.unwrap_err()
        assert any("prime_test_seg.md" in err.lower() for err in errors)

    def test_ambiguous_multiple_prime_files(self, tmp_path: Path) -> None:
        """Multiple prime_*.md files should cause ERROR (ambiguity)."""
        seg = tmp_path / "test_seg"
        seg.mkdir()
        (seg / "skill.md").touch()
        ctx = seg / "_ctx"
        ctx.mkdir()
        (ctx / "agent_test_seg.md").touch()
        (ctx / "prime_test_seg.md").touch()
        (ctx / "prime_other.md").touch()  # Ambiguous!
        (ctx / "session_test_seg.md").touch()

        result = validate_segment_fp(seg)

        assert result.is_err(), "Multiple prime_*.md should cause ERROR"
        errors = result.unwrap_err()
        assert any("ambiguous" in err.lower() or "multiple" in err.lower() for err in errors), (
            f"Should mention ambiguity, got: {errors}"
        )

    def test_ambiguous_multiple_agent_files(self, tmp_path: Path) -> None:
        """Multiple agent_*.md files should cause ERROR."""
        seg = tmp_path / "test_seg"
        seg.mkdir()
        (seg / "skill.md").touch()
        ctx = seg / "_ctx"
        ctx.mkdir()
        (ctx / "agent_test_seg.md").touch()
        (ctx / "agent_other.md").touch()  # Ambiguous!
        (ctx / "prime_test_seg.md").touch()
        (ctx / "session_test_seg.md").touch()

        result = validate_segment_fp(seg)

        assert result.is_err()
        errors = result.unwrap_err()
        assert any("ambiguous" in err.lower() or "multiple" in err.lower() for err in errors)

    def test_wrong_suffix_in_prime(self, tmp_path: Path) -> None:
        """prime_*.md with wrong suffix should cause ERROR."""
        seg = tmp_path / "test_seg"
        seg.mkdir()
        (seg / "skill.md").touch()
        ctx = seg / "_ctx"
        ctx.mkdir()
        (ctx / "agent_test_seg.md").touch()
        (ctx / "prime_wrong_name.md").touch()  # Wrong suffix!
        (ctx / "session_test_seg.md").touch()

        result = validate_segment_fp(seg)

        assert result.is_err()
        errors = result.unwrap_err()
        # Should mention that prime_test_seg.md is missing
        assert any("prime_test_seg.md" in err.lower() for err in errors)

    def test_normalized_segment_id_with_spaces(self, tmp_path: Path) -> None:
        """Segment name with spaces should normalize to hyphens."""
        seg = tmp_path / "my project"
        seg.mkdir()
        (seg / "skill.md").touch()
        ctx = seg / "_ctx"
        ctx.mkdir()
        # Expected normalized ID: "my-project"
        (ctx / "agent_my-project.md").touch()
        (ctx / "prime_my-project.md").touch()
        (ctx / "session_my-project.md").touch()

        result = validate_segment_fp(seg)

        assert result.is_ok(), f"Should pass with normalized names, got errors: {result}"

    def test_normalized_segment_id_with_uppercase(self, tmp_path: Path) -> None:
        """Segment name with uppercase should normalize to lowercase."""
        seg = tmp_path / "MyProject"
        seg.mkdir()
        (seg / "skill.md").touch()
        ctx = seg / "_ctx"
        ctx.mkdir()
        # Expected normalized ID: "myproject"
        (ctx / "agent_myproject.md").touch()
        (ctx / "prime_myproject.md").touch()
        (ctx / "session_myproject.md").touch()

        result = validate_segment_fp(seg)

        assert result.is_ok(), f"Should pass with normalized names, got errors: {result}"
