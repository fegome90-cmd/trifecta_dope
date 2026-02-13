"""
Integration tests for Naming Contract and Gate 3+1.

Verifies end-to-end flows:
1. create -> validate -> build (with spaces/normalization)
2. Fail-closed behavior for contamination (multiple prime files)
3. Fail-closed behavior for legacy files
"""

from pathlib import Path

from typer.testing import CliRunner

from src.domain.naming import normalize_segment_id
from src.infrastructure.cli import app

runner = CliRunner()


class TestNamingContractIntegration:
    """End-to-end tests for naming contract and strict validation gate."""

    def test_e2e_create_build_with_normalization(self, tmp_path: Path) -> None:
        """
        Scenario: User creates segment inside a directory matching normalized name.
        Expectation: create and build succeed.
        """
        segment_raw = "My Project"
        segment_id = normalize_segment_id(segment_raw)  # my-project

        # Create directory with matching name (required for strict validation)
        project_dir = tmp_path / segment_id
        project_dir.mkdir()

        # 1. Create (target path is the project dir)
        # Note: 'create' command now takes -s as the path and derives ID from dirname
        result = runner.invoke(app, ["create", "--segment", str(project_dir)])
        assert result.exit_code == 0

        # Verify filenames match segment_id
        ctx_dir = project_dir / "_ctx"
        assert (ctx_dir / f"agent_{segment_id}.md").exists()

        # Constitution gate requires AGENTS.md
        (project_dir / "AGENTS.md").write_text("# Constitution\n\nRule 1: Be strict.")

        # 2. Build (must pass path to project dir)
        build_result = runner.invoke(app, ["ctx", "build", "--segment", str(project_dir)])
        assert build_result.exit_code == 0, f"Build failed: {build_result.stdout}"

    def test_e2e_build_fails_on_contamination(self, tmp_path: Path) -> None:
        """
        Scenario: Rogue prime file triggers strict failure.
        """
        segment_name = "clean_project"
        seg_path = tmp_path / segment_name
        seg_path.mkdir()
        (seg_path / "skill.md").write_text("# Skill")
        ctx_dir = seg_path / "_ctx"
        ctx_dir.mkdir()
        (ctx_dir / f"agent_{segment_name}.md").write_text("# Agent")
        (ctx_dir / f"prime_{segment_name}.md").write_text("# Prime\n> **REPO_ROOT**: `/tmp`")
        (ctx_dir / f"session_{segment_name}.md").write_text("# Session")
        (seg_path / "AGENTS.md").write_text("# Constitution\n\nRule 1: Be strict.")

        # Pass initial build
        assert runner.invoke(app, ["ctx", "build", "--segment", str(seg_path)]).exit_code == 0

        # Determine contamination
        (ctx_dir / "prime_rogue.md").write_text("# Rogue")

        res = runner.invoke(app, ["ctx", "build", "--segment", str(seg_path)])
        assert res.exit_code != 0
        output = res.stdout or res.stderr or ""
        assert "TRIFECTA_ERROR_CODE:" in output, "Missing error card structure"
        assert "NORTH_STAR_AMBIGUOUS" in output or "AMBIGUOUS" in output, (
            f"Expected NORTH_STAR_AMBIGUOUS error code, got:\n{output[:500]}"
        )

    def test_e2e_build_fails_on_legacy_files(self, tmp_path: Path) -> None:
        """
        Scenario: Valid segment but with legacy 'agent.md' (no suffix).
        Expectation: Build fails (Strict 3+1).
        """
        segment_name = "legacy_test"
        seg_path = tmp_path / segment_name
        seg_path.mkdir()
        (seg_path / "skill.md").write_text("# Skill")
        ctx_dir = seg_path / "_ctx"
        ctx_dir.mkdir()

        # Valid structure (satisfies Gate)
        (ctx_dir / f"agent_{segment_name}.md").write_text("# Agent")
        (ctx_dir / f"prime_{segment_name}.md").write_text("# Prime\n> **REPO_ROOT**: `/tmp`")
        (ctx_dir / f"session_{segment_name}.md").write_text("# Session")
        (seg_path / "AGENTS.md").write_text("# Constitution\n\nRule 1: Be strict.")

        # Legacy filename (Contamination that triggers the specific Legacy Error)
        (ctx_dir / "agent.md").write_text("# Agent Legacy")

        # Build should FAIL (Strictly)
        build_result = runner.invoke(app, ["ctx", "build", "--segment", str(seg_path)])
        assert build_result.exit_code != 0

        # Verify strict fail logic (Fail-Closed message)
        assert "Legacy context files detected (Fail-Closed)" in build_result.stdout
        assert "rename to suffix format: rule 3+1" in build_result.stdout
