"""
Test that ctx stats is registered only once (no shadowing).

This is a regression test for the duplicate ctx_stats issue where
the command was registered twice, causing the second-registration
to shadow the first.
"""

from typer.testing import CliRunner

from src.infrastructure.cli import app

runner = CliRunner()


def test_ctx_stats_registered_once() -> None:
    """ctx stats should appear exactly once in command list."""
    result = runner.invoke(app, ["ctx", "--help"])
    assert result.exit_code == 0

    # Count occurrences of "stats" in the help output
    help_text = result.stdout
    stats_count = help_text.count("stats")

    # Should appear exactly once in the command list
    assert stats_count == 1, f"'stats' should appear once, found {stats_count} times:\n{help_text}"


def test_ctx_stats_command_exists() -> None:
    """ctx stats command should be recognized and produce output."""
    result = runner.invoke(app, ["ctx", "stats", "--segment", "/nonexistent/path"])

    # Command should be recognized (not "No such command")
    assert "No such command" not in result.output

    # Command should produce some output (even if empty stats for nonexistent segment)
    # Note: Currently returns exit_code=0 with empty stats - this documents current behavior
    assert result.output.strip(), "Command should produce some output"

    # Should show stats header (graceful handling of missing data)
    assert "Stats" in result.output or "No telemetry" in result.output or result.exit_code != 0, (
        f"Expected stats output or error. Got: exit_code={result.exit_code}, output={result.output[:200]}"
    )
