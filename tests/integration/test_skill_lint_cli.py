"""Integration tests for skill lint CLI command."""

import json
import subprocess
from pathlib import Path


def run_cli(args: list[str]) -> tuple[int, str, str]:
    """Run trifecta CLI and return exit code, stdout, stderr."""
    result = subprocess.run(
        ["uv", "run", "trifecta"] + args,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent,
    )
    return result.returncode, result.stdout, result.stderr


class TestSkillLintCLI:
    """Tests for 'trifecta skill lint' command."""

    def test_skill_command_exists(self):
        """Verify skill command group exists."""
        code, out, _ = run_cli(["skill", "--help"])
        assert code == 0
        assert "lint" in out

    def test_lint_help_shows_options(self):
        """Verify lint command help shows expected options."""
        code, out, _ = run_cli(["skill", "lint", "--help"])
        assert code == 0
        assert "--strict" in out
        assert "--format" in out

    def test_lint_fixtures_reports_correct_count(self):
        """Verify lint finds all fixture skills."""
        code, out, _ = run_cli(["skill", "lint", "tests/fixtures/skills/"])
        assert code == 0
        assert "3 skills found" in out
        assert "2 valid" in out
        assert "1 invalid" in out

    def test_lint_detects_invalid_skill(self):
        """Verify lint detects invalid skill metadata."""
        code, out, _ = run_cli(["skill", "lint", "tests/fixtures/skills/"])
        assert code == 0
        assert "(unnamed)" in out  # Invalid skill has no name
        assert "name cannot be empty" in out

    def test_lint_json_output_valid_json(self):
        """Verify JSON output is valid JSON."""
        code, out, _ = run_cli(["skill", "lint", "tests/fixtures/skills/", "--format", "json"])
        assert code == 0
        data = json.loads(out)
        assert "total" in data
        assert "valid" in data
        assert "invalid" in data
        assert "skills" in data
        assert data["total"] == 3

    def test_lint_json_output_structure(self):
        """Verify JSON output has correct structure."""
        code, out, _ = run_cli(["skill", "lint", "tests/fixtures/skills/", "--format", "json"])
        assert code == 0
        data = json.loads(out)

        # Check each skill has required fields
        for skill in data["skills"]:
            assert "path" in skill
            assert "name" in skill
            assert "valid" in skill
            assert "errors" in skill
            assert isinstance(skill["errors"], list)

    def test_lint_strict_mode_exits_with_error(self):
        """Verify --strict mode exits with code 1 when there are invalid skills."""
        code, out, _ = run_cli(["skill", "lint", "tests/fixtures/skills/", "--strict"])
        assert code == 1
        assert "1 invalid" in out

    def test_lint_strict_mode_exits_zero_on_valid_only(self):
        """Verify --strict mode exits 0 when all skills are valid."""
        code, out, _ = run_cli(["skill", "lint", "tests/fixtures/skills/valid/", "--strict"])
        assert code == 0
        assert "1 valid" in out

    def test_lint_specific_file(self):
        """Verify linting a specific SKILL.md file works."""
        code, out, _ = run_cli(["skill", "lint", "tests/fixtures/skills/valid/SKILL.md"])
        assert code == 0
        assert "valid-skill" in out

    def test_lint_default_path_is_skills(self):
        """Verify default path is skills/ directory."""
        # This test just verifies the command doesn't error on default path
        code, out, err = run_cli(["skill", "lint"])
        # Should not error, just report what it finds (or empty if no skills/)
        assert "Skill Lint Report" in out or "0 skills found" in out

    def test_lint_invalid_format_rejected(self):
        """Verify invalid format value is rejected with error."""
        code, out, err = run_cli(["skill", "lint", "tests/fixtures/skills/", "--format", "invalid"])
        assert code == 1
        assert "Invalid format" in out or "Invalid format" in err

    def test_lint_valid_formats_work(self):
        """Verify both valid format values work."""
        # text format
        code, out, _ = run_cli(["skill", "lint", "tests/fixtures/skills/", "--format", "text"])
        assert code == 0
        assert "Skill Lint Report" in out

        # json format
        code, out, _ = run_cli(["skill", "lint", "tests/fixtures/skills/", "--format", "json"])
        assert code == 0
        data = json.loads(out)
        assert "total" in data
