"""
Tests for CLI FP North Star Gate.

Uses typer.testing.CliRunner for isolated CLI testing (no subprocess).
TDD Phase: RED -> GREEN
"""

from pathlib import Path
import json

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
        (segment / "AGENTS.md").write_text("# Constitution\n\nRule 1: Be strict.")
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
        (segment / "AGENTS.md").write_text("# Constitution\n\nRule 1: Be strict.")
        ctx = segment / "_ctx"
        ctx.mkdir()
        (ctx / "agent_missing_skill.md").write_text("# Agent")
        (ctx / "prime_missing_skill.md").write_text("# Prime")
        (ctx / "session_missing_skill.md").write_text("# Session")
        # Missing skill.md

        result = runner.invoke(app, ["ctx", "build", "--segment", str(segment)])

        assert result.exit_code != 0
        combined = (result.stdout or "").lower() + (result.stderr or "").lower()
        assert "trifecta_error_code: north_star_missing" in combined, (
            f"Should emit stable error code, got: {result.stdout}\n{result.stderr}"
        )
        assert "skill.md" in combined, (
            f"Should mention missing skill.md, got: {result.stdout}\n{result.stderr}"
        )

    def test_ctx_build_dot_matches_abs_cwd(self, tmp_path: Path, monkeypatch) -> None:
        """ctx build with --segment . must be equivalent to --segment <abs cwd>."""
        segment = tmp_path / "my_segment"
        segment.mkdir()
        (segment / "skill.md").write_text("# Skill")
        (segment / "AGENTS.md").write_text("# Constitution\n\nRule 1: Be strict.")
        ctx = segment / "_ctx"
        ctx.mkdir()
        (ctx / "agent_my_segment.md").write_text("# Agent")
        (ctx / "prime_my_segment.md").write_text(f"# Prime\n\n> **REPO_ROOT**: `{segment}`\n")
        (ctx / "session_my_segment.md").write_text("# Session")

        monkeypatch.chdir(segment)
        result_dot = runner.invoke(app, ["ctx", "build", "--segment", "."])
        result_abs = runner.invoke(app, ["ctx", "build", "--segment", str(segment)])

        assert result_dot.exit_code == result_abs.exit_code, (
            f"dot={result_dot.exit_code}, abs={result_abs.exit_code}\n"
            f"dot_out={result_dot.stdout}\nabs_out={result_abs.stdout}"
        )

    def test_ctx_build_invalid_segment_path_has_stable_card(self, tmp_path: Path) -> None:
        invalid = tmp_path / "missing_segment"
        result = runner.invoke(app, ["ctx", "build", "--segment", str(invalid)])
        combined = (result.stdout or "").lower() + (result.stderr or "").lower()

        assert result.exit_code != 0
        assert "trifecta_error_code: invalid_segment_path" in combined, combined

    def test_ctx_build_and_sync_use_config_segment_id_ssot(self, tmp_path: Path) -> None:
        """If config segment differs from directory name, build/sync must follow config segment_id."""
        segment = tmp_path / "dir_name"
        segment.mkdir()
        (segment / "skill.md").write_text("# Skill")
        (segment / "AGENTS.md").write_text("# Constitution\n\nRule 1: Be strict.")
        ctx = segment / "_ctx"
        ctx.mkdir()

        config = {
            "segment": "cfg-name",
            "scope": "tests",
            "repo_root": str(segment),
            "default_profile": "impl_patch",
            "last_verified": "2026-02-11",
        }
        (ctx / "trifecta_config.json").write_text(json.dumps(config))

        (ctx / "agent_cfg-name.md").write_text("# Agent")
        (ctx / "prime_cfg-name.md").write_text(f"# Prime\n\n> **REPO_ROOT**: `{segment}`\n")
        (ctx / "session_cfg-name.md").write_text("# Session")

        build_result = runner.invoke(app, ["ctx", "build", "--segment", str(segment)])
        sync_result = runner.invoke(app, ["ctx", "sync", "--segment", str(segment)])

        assert build_result.exit_code == 0, build_result.stdout + "\n" + str(build_result.stderr)
        assert sync_result.exit_code == 0, sync_result.stdout + "\n" + str(sync_result.stderr)

    def test_ctx_build_and_sync_emit_same_precondition_code(self, tmp_path: Path) -> None:
        """build/sync must classify the same structural precondition with same card code."""
        segment = tmp_path / "same_precondition"
        segment.mkdir()
        (segment / "AGENTS.md").write_text("# Constitution\n\nRule 1: Be strict.")
        (segment / "_ctx").mkdir()
        # Missing prime/agent/session by design

        build_result = runner.invoke(app, ["ctx", "build", "--segment", str(segment)])
        sync_result = runner.invoke(app, ["ctx", "sync", "--segment", str(segment)])

        build_combined = (build_result.stdout or "") + (build_result.stderr or "")
        sync_combined = (sync_result.stdout or "") + (sync_result.stderr or "")

        def extract_code(out: str) -> str:
            for line in out.splitlines():
                if line.startswith("TRIFECTA_ERROR_CODE:"):
                    return line.split(":", 1)[1].strip()
            return ""

        build_code = extract_code(build_combined)
        sync_code = extract_code(sync_combined)
        assert build_code, f"No build code found:\n{build_combined}"
        assert sync_code, f"No sync code found:\n{sync_combined}"
        assert build_code == sync_code, f"build={build_code}, sync={sync_code}"
