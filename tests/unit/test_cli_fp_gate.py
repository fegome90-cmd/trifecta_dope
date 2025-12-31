"""
Tests for CLI FP North Star Gate.

Uses typer.testing.CliRunner for isolated CLI testing (no subprocess).
TDD Phase: RED -> GREEN
"""

from pathlib import Path

from typer.testing import CliRunner

from src.infrastructure.cli import app

runner = CliRunner()


class TestCLIFPGate:
    """Test suite for FP validation gate in CLI."""

    def test_ctx_build_fails_on_invalid_segment(self, tmp_path: Path) -> None:
        """ctx build should fail with clear error on invalid segment."""
        segment = tmp_path / "bad_segment"
        segment.mkdir()
        # Missing skill.md and _ctx

        result = runner.invoke(app, ["ctx", "build", "--segment", str(segment)])

        assert result.exit_code != 0, f"Expected non-zero exit, got {result.exit_code}"
        output = result.stdout.lower() + (result.stderr or "").lower()
        assert "validation" in output or "failed" in output or "error" in output, (
            f"Expected validation failure message, got: {result.stdout}"
        )

    def test_ctx_build_succeeds_on_valid_segment(self, tmp_path: Path) -> None:
        """ctx build should succeed on valid segment structure."""
        segment_name = "valid_test"
        segment = tmp_path / segment_name
        segment.mkdir()
        (segment / "skill.md").write_text("# Valid Skill")
        ctx = segment / "_ctx"
        ctx.mkdir()
        (ctx / f"agent_{segment_name}.md").write_text("# Agent")
        (ctx / f"prime_{segment_name}.md").write_text("# Prime")
        (ctx / f"session_{segment_name}.md").write_text("# Session")

        result = runner.invoke(app, ["ctx", "build", "--segment", str(segment)])

        # Should pass validation gate (may fail later for other reasons, but not validation)
        output = result.stdout.lower()
        assert "validation failed" not in output, f"Validation should pass, got: {result.stdout}"

    def test_ctx_build_shows_specific_errors(self, tmp_path: Path) -> None:
        """ctx build should list which files are missing."""
        segment = tmp_path / "missing_skill"
        segment.mkdir()
        ctx = segment / "_ctx"
        ctx.mkdir()
        (ctx / "agent_missing_skill.md").write_text("# Agent")
        (ctx / "prime_missing_skill.md").write_text("# Prime")
        (ctx / "session_missing_skill.md").write_text("# Session")
        # Missing skill.md

        result = runner.invoke(app, ["ctx", "build", "--segment", str(segment)])

        assert result.exit_code != 0
        assert "skill.md" in result.stdout.lower(), (
            f"Should mention missing skill.md, got: {result.stdout}"
        )
