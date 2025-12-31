"""
Tests for CLI create command with normalized naming.

TDD Phase: RED -> GREEN
Ensures CLI generates files with correct normalized segment IDs.
"""

from pathlib import Path

from typer.testing import CliRunner

from src.infrastructure.cli import app

runner = CliRunner()


class TestCLICreateNaming:
    """Test that CLI create generates correctly named files."""

    def test_create_generates_normalized_agent_file(self, tmp_path: Path) -> None:
        """create should generate agent_<normalized_id>.md, not agent.md."""
        # CLI: --segment is the slug, --path is where to create
        result = runner.invoke(
            app, ["create", "--segment", "Test Segment", "--path", str(tmp_path)]
        )

        assert result.exit_code == 0, f"Create failed: {result.stdout}"

        # Normalized slug: "test-segment"
        expected_agent = tmp_path / "_ctx" / "agent_test-segment.md"
        assert expected_agent.exists(), (
            f"Expected {expected_agent}, files: {list((tmp_path / '_ctx').iterdir())}"
        )

    def test_create_generates_normalized_prime_file(self, tmp_path: Path) -> None:
        """create should generate prime_<normalized_id>.md."""
        result = runner.invoke(app, ["create", "--segment", "MyProject", "--path", str(tmp_path)])

        assert result.exit_code == 0, f"Create failed: {result.stdout}"

        # Normalized: "myproject"
        expected_prime = tmp_path / "_ctx" / "prime_myproject.md"
        assert expected_prime.exists(), f"Expected {expected_prime}"

    def test_create_generates_normalized_session_file(self, tmp_path: Path) -> None:
        """create should generate session_<normalized_id>.md."""
        result = runner.invoke(app, ["create", "--segment", "my_project", "--path", str(tmp_path)])

        assert result.exit_code == 0

        expected_session = tmp_path / "_ctx" / "session_my_project.md"
        assert expected_session.exists()

    def test_create_with_special_chars_normalizes(self, tmp_path: Path) -> None:
        """create should normalize special characters in segment name."""
        result = runner.invoke(app, ["create", "--segment", "my@project!", "--path", str(tmp_path)])

        assert result.exit_code == 0

        # Normalized: "my_project_"
        expected_agent = tmp_path / "_ctx" / "agent_my_project_.md"
        assert expected_agent.exists(), "Expected normalized naming"
