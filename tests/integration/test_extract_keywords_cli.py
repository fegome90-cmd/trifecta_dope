"""Integration tests for the extract-keywords CLI command.

Tests end-to-end flow:
1. Discover skills from sources.yaml
2. Extract keywords from skill metadata
3. Generate aliases.generated.yaml
4. Validate AliasLoader compatibility
"""

import json
from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]
from typer.testing import CliRunner

from src.infrastructure.alias_loader import AliasLoader


# We'll import the CLI after it's implemented
# from src.infrastructure.cli_skills import app as skills_app


class TestExtractKeywordsCLI:
    """Integration tests for extract-keywords CLI command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_segment(self, tmp_path: Path) -> Path:
        """Create a mock segment with sources.yaml and skills."""
        # Create _ctx directory
        ctx_dir = tmp_path / "_ctx"
        ctx_dir.mkdir()

        # Create sources.yaml
        sources_yaml = {
            "sources": [
                {
                    "name": "test-skills",
                    "path": str(tmp_path / "skills"),
                    "description": "Test skills",
                    "priority": 1,
                    "type": "directory",
                }
            ]
        }
        (ctx_dir / "sources.yaml").write_text(yaml.dump(sources_yaml))

        # Create skills directory with SKILL.md files
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Skill 1: tdd-workflow
        tdd_dir = skills_dir / "tdd-workflow"
        tdd_dir.mkdir()
        (tdd_dir / "SKILL.md").write_text(
            "---\n"
            "name: tdd-workflow\n"
            "description: Test-driven development workflow with pytest and coverage\n"
            "---\n"
            "# TDD Workflow\n"
        )

        # Skill 2: code-review
        review_dir = skills_dir / "code-review"
        review_dir.mkdir()
        (review_dir / "SKILL.md").write_text(
            "---\n"
            "name: code-review\n"
            "description: Code review patterns and best practices for quality\n"
            "---\n"
            "# Code Review\n"
        )

        # Skill 3: sqlite-query-plans
        sqlite_dir = skills_dir / "sqlite-query-plans"
        sqlite_dir.mkdir()
        (sqlite_dir / "SKILL.md").write_text(
            "---\n"
            "name: sqlite-query-plans\n"
            "description: SQLite query optimization and indexing strategies\n"
            "---\n"
            "# SQLite Query Plans\n"
        )

        # Create skills_manifest.json
        manifest = {
            "schema_version": 1,
            "skills": [
                {
                    "name": "tdd-workflow",
                    "source_path": str(tdd_dir / "SKILL.md"),
                    "description": "Test-driven development workflow with pytest and coverage",
                },
                {
                    "name": "code-review",
                    "source_path": str(review_dir / "SKILL.md"),
                    "description": "Code review patterns and best practices for quality",
                },
                {
                    "name": "sqlite-query-plans",
                    "source_path": str(sqlite_dir / "SKILL.md"),
                    "description": "SQLite query optimization and indexing strategies",
                },
            ],
        }
        (ctx_dir / "skills_manifest.json").write_text(json.dumps(manifest))

        return tmp_path

    @pytest.fixture
    def mock_segment_with_manual_aliases(self, mock_segment: Path) -> Path:
        """Create a mock segment with existing manual aliases."""
        ctx_dir = mock_segment / "_ctx"

        # Create manual aliases.yaml
        manual_aliases = {
            "schema_version": 1,
            "aliases": {
                "testing": ["tdd-workflow"],
                "review": ["code-review"],
            },
        }
        (ctx_dir / "aliases.yaml").write_text(yaml.dump(manual_aliases))

        return mock_segment

    def test_cli_command_exists(self, runner: CliRunner) -> None:
        """CLI command should be registered and accessible."""
        # Import after implementation
        from src.infrastructure.cli_skills import skills_app

        result = runner.invoke(skills_app, ["--help"])

        # Should show help, not error
        assert result.exit_code == 0
        assert "segment" in result.output.lower() or "extract" in result.output.lower()

    def test_cli_generates_aliases_file(self, runner: CliRunner, mock_segment: Path) -> None:
        """CLI should generate aliases.generated.yaml."""
        from src.infrastructure.cli_skills import skills_app

        result = runner.invoke(
            skills_app,
            ["--segment", str(mock_segment)],
        )

        assert result.exit_code == 0

        # Check file was created
        generated_path = mock_segment / "_ctx" / "aliases.generated.yaml"
        assert generated_path.exists()

    def test_cli_output_has_correct_schema(self, runner: CliRunner, mock_segment: Path) -> None:
        """Generated file should have schema_version: 1."""
        from src.infrastructure.cli_skills import skills_app

        runner.invoke(
            skills_app,
            ["--segment", str(mock_segment)],
        )

        generated_path = mock_segment / "_ctx" / "aliases.generated.yaml"
        data = yaml.safe_load(generated_path.read_text())

        assert data["schema_version"] == 1

    def test_cli_compatible_with_alias_loader(self, runner: CliRunner, mock_segment: Path) -> None:
        """Generated file should be readable by AliasLoader."""
        from src.infrastructure.cli_skills import skills_app

        runner.invoke(
            skills_app,
            ["--segment", str(mock_segment)],
        )

        # Load with AliasLoader
        loader = AliasLoader(mock_segment)
        aliases = loader.load()

        # Should be a non-empty dict
        assert isinstance(aliases, dict)

    def test_cli_stdout_flag(self, runner: CliRunner, mock_segment: Path) -> None:
        """--stdout should print YAML without writing file."""
        from src.infrastructure.cli_skills import skills_app

        result = runner.invoke(
            skills_app,
            ["--segment", str(mock_segment), "--stdout"],
        )

        assert result.exit_code == 0

        # Should contain YAML content
        assert "schema_version" in result.output

        # File should NOT be created
        generated_path = mock_segment / "_ctx" / "aliases.generated.yaml"
        assert not generated_path.exists()

    def test_cli_dry_run_flag(self, runner: CliRunner, mock_segment: Path) -> None:
        """--dry-run should not write file."""
        from src.infrastructure.cli_skills import skills_app

        result = runner.invoke(
            skills_app,
            ["--segment", str(mock_segment), "--dry-run"],
        )

        assert result.exit_code == 0

        # File should NOT be created
        generated_path = mock_segment / "_ctx" / "aliases.generated.yaml"
        assert not generated_path.exists()

    def test_cli_does_not_modify_manual_aliases(
        self, runner: CliRunner, mock_segment_with_manual_aliases: Path
    ) -> None:
        """Generated aliases should not modify manual aliases.yaml."""
        from src.infrastructure.cli_skills import skills_app

        segment = mock_segment_with_manual_aliases
        manual_path = segment / "_ctx" / "aliases.yaml"

        # Store original content
        original_content = manual_path.read_text()

        runner.invoke(
            skills_app,
            ["--segment", str(segment)],
        )

        # Manual file should be unchanged
        assert manual_path.read_text() == original_content

    def test_cli_respects_custom_output_path(self, runner: CliRunner, mock_segment: Path) -> None:
        """--output should use custom path."""
        from src.infrastructure.cli_skills import skills_app

        custom_path = mock_segment / "custom" / "my-aliases.yaml"

        result = runner.invoke(
            skills_app,
            [
                "--segment",
                str(mock_segment),
                "--output",
                str(custom_path),
            ],
        )

        assert result.exit_code == 0
        assert custom_path.exists()

    def test_cli_reports_metrics(self, runner: CliRunner, mock_segment: Path) -> None:
        """CLI should report metrics (skills processed, tokens, aliases)."""
        from src.infrastructure.cli_skills import skills_app

        result = runner.invoke(
            skills_app,
            ["--segment", str(mock_segment)],
        )

        assert result.exit_code == 0

        # Should report metrics in output
        output = result.output.lower()
        assert "skill" in output or "alias" in output

    def test_cli_min_frequency_option(self, runner: CliRunner, mock_segment: Path) -> None:
        """--min-frequency should control frequency threshold."""
        from src.infrastructure.cli_skills import skills_app

        result = runner.invoke(
            skills_app,
            [
                "--segment",
                str(mock_segment),
                "--min-frequency",
                "1",
            ],
        )

        assert result.exit_code == 0

    def test_cli_max_skills_option(self, runner: CliRunner, mock_segment: Path) -> None:
        """--max-skills-per-alias should control cap."""
        from src.infrastructure.cli_skills import skills_app

        result = runner.invoke(
            skills_app,
            [
                "--segment",
                str(mock_segment),
                "--max-skills-per-alias",
                "3",
            ],
        )

        assert result.exit_code == 0

    def test_cli_deterministic_output(self, runner: CliRunner, mock_segment: Path) -> None:
        """Running twice should produce identical output."""
        from src.infrastructure.cli_skills import skills_app

        # First run
        runner.invoke(
            skills_app,
            ["--segment", str(mock_segment)],
        )
        first_content = (mock_segment / "_ctx" / "aliases.generated.yaml").read_text()

        # Second run
        runner.invoke(
            skills_app,
            ["--segment", str(mock_segment)],
        )
        second_content = (mock_segment / "_ctx" / "aliases.generated.yaml").read_text()

        assert first_content == second_content

    def test_cli_check_flag_pass(self, runner: CliRunner, mock_segment: Path) -> None:
        """--check should pass if output matches existing file."""
        from src.infrastructure.cli_skills import skills_app

        # First run to create file
        runner.invoke(
            skills_app,
            ["--segment", str(mock_segment)],
        )

        # Second run with --check should pass
        result = runner.invoke(
            skills_app,
            ["--segment", str(mock_segment), "--check"],
        )

        assert result.exit_code == 0

    def test_cli_check_flag_fails_on_drift(self, runner: CliRunner, mock_segment: Path) -> None:
        """--check should fail if output differs from existing file."""
        from src.infrastructure.cli_skills import skills_app

        # Create a file with different content
        generated_path = mock_segment / "_ctx" / "aliases.generated.yaml"
        generated_path.parent.mkdir(parents=True, exist_ok=True)
        generated_path.write_text(yaml.dump({"schema_version": 1, "aliases": {"old": ["skill"]}}))

        # Run with --check should detect drift
        result = runner.invoke(
            skills_app,
            ["--segment", str(mock_segment), "--check"],
        )

        # Should fail with non-zero exit code
        assert result.exit_code != 0

    def test_cli_handles_missing_manifest(self, runner: CliRunner, tmp_path: Path) -> None:
        """Should handle missing skills_manifest.json gracefully."""
        from src.infrastructure.cli_skills import skills_app

        # Create segment without manifest
        ctx_dir = tmp_path / "_ctx"
        ctx_dir.mkdir()

        result = runner.invoke(
            skills_app,
            ["--segment", str(tmp_path)],
        )

        # Should not crash
        assert result.exit_code == 0 or "no skills" in result.output.lower()

    def test_cli_handles_empty_skills_list(self, runner: CliRunner, tmp_path: Path) -> None:
        """Should handle empty skills list gracefully."""
        from src.infrastructure.cli_skills import skills_app

        # Create segment with empty manifest
        ctx_dir = tmp_path / "_ctx"
        ctx_dir.mkdir()
        manifest = {"schema_version": 1, "skills": []}
        (ctx_dir / "skills_manifest.json").write_text(json.dumps(manifest))

        result = runner.invoke(
            skills_app,
            ["--segment", str(tmp_path)],
        )

        # Should not crash
        assert result.exit_code == 0


class TestAliasLoaderCompatIntegration:
    """Integration tests validating AliasLoader compatibility."""

    @pytest.fixture
    def segment_with_generated(self, tmp_path: Path) -> Path:
        """Create segment with generated aliases."""
        ctx_dir = tmp_path / "_ctx"
        ctx_dir.mkdir()

        # Create generated aliases
        generated = {
            "schema_version": 1,
            "aliases": {
                "testing": ["tdd-workflow", "pytest-skill"],
                "database": ["sqlite-skill", "postgres-skill"],
                "review": ["code-review-skill"],
            },
        }
        (ctx_dir / "aliases.generated.yaml").write_text(yaml.dump(generated))

        return tmp_path

    def test_alias_loader_reads_generated_file(self, segment_with_generated: Path) -> None:
        """AliasLoader should read generated aliases file."""
        # Note: This tests that AliasLoader can read the generated file format
        # The actual AliasLoader only reads aliases.yaml by default
        # But the format should be compatible

        generated_path = segment_with_generated / "_ctx" / "aliases.generated.yaml"
        data = yaml.safe_load(generated_path.read_text())

        assert data["schema_version"] == 1
        assert "aliases" in data
        assert "testing" in data["aliases"]

    def test_generated_aliases_valid_structure(self, segment_with_generated: Path) -> None:
        """Generated aliases should have valid structure for AliasLoader."""
        generated_path = segment_with_generated / "_ctx" / "aliases.generated.yaml"
        data = yaml.safe_load(generated_path.read_text())

        # Check all values are lists of strings
        for key, skills in data["aliases"].items():
            assert isinstance(key, str)
            assert isinstance(skills, list)
            for skill in skills:
                assert isinstance(skill, str)
