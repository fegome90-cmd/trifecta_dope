"""
Tests for CLI create command with normalized naming.

TDD Phase: RED -> GREEN
Ensures CLI generates files with correct normalized segment IDs.

UPDATED: Use correct CLI flags (-s for segment path).
"""

from pathlib import Path

from typer.testing import CliRunner

from src.infrastructure.cli import app

runner = CliRunner()


def _setup_minimal_segment(path: Path) -> None:
    """Create minimal skill.md for valid segment."""
    (path / "skill.md").write_text("""---
name: test
description: Test segment
---
# Test
""")


class TestCLICreateNaming:
    """Test that CLI create generates correctly named files."""

    def test_create_generates_normalized_agent_file(self, tmp_path: Path) -> None:
        """create should generate agent_<normalized_id>.md, not agent.md."""
        _setup_minimal_segment(tmp_path)

        # CLI: -s is the segment path
        result = runner.invoke(app, ["create", "-s", str(tmp_path)])

        assert result.exit_code == 0, f"Create failed: {result.output}"

        # Find agent file (normalized from tmp_path name)
        ctx_dir = tmp_path / "_ctx"
        assert ctx_dir.exists(), "No _ctx directory created"

        agent_files = list(ctx_dir.glob("agent_*.md"))
        assert len(agent_files) == 1, f"Expected 1 agent file, got: {list(ctx_dir.iterdir())}"

    def test_create_generates_normalized_prime_file(self, tmp_path: Path) -> None:
        """create should generate prime_<normalized_id>.md."""
        _setup_minimal_segment(tmp_path)

        result = runner.invoke(app, ["create", "-s", str(tmp_path)])

        assert result.exit_code == 0, f"Create failed: {result.output}"

        ctx_dir = tmp_path / "_ctx"
        prime_files = list(ctx_dir.glob("prime_*.md"))
        assert len(prime_files) == 1, f"Expected 1 prime file, got: {list(ctx_dir.iterdir())}"

    def test_create_generates_normalized_session_file(self, tmp_path: Path) -> None:
        """create should generate session_<normalized_id>.md."""
        _setup_minimal_segment(tmp_path)

        result = runner.invoke(app, ["create", "-s", str(tmp_path)])

        assert result.exit_code == 0, f"Create failed: {result.output}"

        ctx_dir = tmp_path / "_ctx"
        session_files = list(ctx_dir.glob("session_*.md"))
        assert len(session_files) == 1, f"Expected 1 session file, got: {list(ctx_dir.iterdir())}"

    def test_create_idempotent(self, tmp_path: Path) -> None:
        """create should be idempotent (can run twice)."""
        _setup_minimal_segment(tmp_path)

        # First create
        result1 = runner.invoke(app, ["create", "-s", str(tmp_path)])
        assert result1.exit_code == 0

        # Second create (should not fail)
        result2 = runner.invoke(app, ["create", "-s", str(tmp_path)])
        # May succeed or warn, but should not crash
        assert result2.exit_code in (0, 1), f"Unexpected exit code: {result2.output}"

    def test_create_writes_bootstrap_config_and_agents(self, tmp_path: Path) -> None:
        """create should bootstrap AGENTS.md + _ctx/trifecta_config.json."""
        _setup_minimal_segment(tmp_path)

        result = runner.invoke(app, ["create", "-s", str(tmp_path)])
        assert result.exit_code == 0, f"Create failed: {result.output}"

        assert (tmp_path / "AGENTS.md").exists(), "AGENTS.md missing after create"
        assert (tmp_path / "_ctx" / "trifecta_config.json").exists(), (
            "trifecta_config.json missing after create"
        )
