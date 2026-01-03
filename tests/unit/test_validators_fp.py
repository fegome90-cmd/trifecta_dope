"""
Tests for FP Validator Wrapper.

TDD Phase: RED -> GREEN
"""

from pathlib import Path


from src.infrastructure.validators import validate_segment_fp


class TestValidatorFP:
    """Test suite for validate_segment_fp function."""

    def test_valid_segment_returns_ok(self, tmp_path: Path) -> None:
        """Valid segment structure should return Ok(ValidationResult)."""
        seg = tmp_path / "valid_seg"
        seg.mkdir()
        (seg / "skill.md").touch()
        ctx = seg / "_ctx"
        ctx.mkdir()
        (ctx / "agent_valid_seg.md").touch()
        (ctx / "prime_valid_seg.md").touch()
        (ctx / "session_valid_seg.md").touch()

        result = validate_segment_fp(seg)

        assert result.is_ok(), f"Expected Ok, got Err: {result}"
        validation = result.unwrap()
        assert validation.valid is True
        assert validation.errors == []

    def test_invalid_segment_missing_skill_returns_err(self, tmp_path: Path) -> None:
        """Segment missing skill.md should return Err with error list."""
        seg = tmp_path / "invalid_seg"
        seg.mkdir()
        ctx = seg / "_ctx"
        ctx.mkdir()
        (ctx / "agent_invalid_seg.md").touch()
        (ctx / "prime_invalid_seg.md").touch()
        (ctx / "session_invalid_seg.md").touch()

        result = validate_segment_fp(seg)

        assert result.is_err(), "Expected Err for invalid segment"
        errors = result.unwrap_err()
        assert len(errors) > 0
        assert any("skill.md" in err.lower() for err in errors)

    def test_invalid_segment_missing_ctx_returns_err(self, tmp_path: Path) -> None:
        """Segment missing _ctx directory should return Err."""
        seg = tmp_path / "no_ctx_seg"
        seg.mkdir()
        (seg / "skill.md").touch()
        # No _ctx directory

        result = validate_segment_fp(seg)

        assert result.is_err(), "Expected Err for missing _ctx"
        errors = result.unwrap_err()
        assert any("_ctx" in err.lower() for err in errors)

    def test_nonexistent_path_returns_err(self, tmp_path: Path) -> None:
        """Non-existent path should return Err."""
        nonexistent = tmp_path / "does_not_exist"

        result = validate_segment_fp(nonexistent)

        assert result.is_err()
        errors = result.unwrap_err()
        assert len(errors) > 0
