"""
Integration Tests for CLI AGENTS.md Constitution Gate.

Ensures 'ctx build' enforces AGENTS.md presence and validity (Phase 1).
"""

from pathlib import Path
import subprocess


class TestCLIAgentsGate:
    """Test CLI behavior for AGENTS.md Constitution."""

    def test_build_fails_missing_agents_md(self, tmp_path: Path) -> None:
        """CLI should exit 1 if AGENTS.md is missing."""
        seg = tmp_path / "test_seg_missing"
        seg.mkdir()
        (seg / "skill.md").touch()
        ctx = seg / "_ctx"
        ctx.mkdir()
        (ctx / "agent_test_seg_missing.md").touch()
        (ctx / "prime_test_seg_missing.md").touch()
        (ctx / "session_test_seg_missing.md").touch()

        # Run CLI build
        cmd = ["uv", "run", "trifecta", "ctx", "build", "--segment", str(seg)]
        result = subprocess.run(cmd, capture_output=True, text=True)

        assert result.returncode == 1, "Exit code should be 1 for missing AGENTS.md"
        assert "Constitution Failed (AGENTS.md)" in result.stdout
        assert "missing AGENTS.md" in result.stdout

    def test_build_fails_empty_agents_md(self, tmp_path: Path) -> None:
        """CLI should exit 1 if AGENTS.md is empty."""
        seg = tmp_path / "test_seg_empty"
        seg.mkdir()
        (seg / "skill.md").touch()
        ctx = seg / "_ctx"
        ctx.mkdir()
        (ctx / "agent_test_seg_empty.md").touch()
        (ctx / "prime_test_seg_empty.md").touch()
        (ctx / "session_test_seg_empty.md").touch()

        # Create empty AGENTS.md
        (seg / "AGENTS.md").touch()

        # Run CLI build
        cmd = ["uv", "run", "trifecta", "ctx", "build", "--segment", str(seg)]
        result = subprocess.run(cmd, capture_output=True, text=True)

        assert result.returncode == 1, "Exit code should be 1 for empty AGENTS.md"
        assert "Constitution Failed (AGENTS.md)" in result.stdout
        assert "is empty" in result.stdout

    def test_build_passes_valid_agents_md(self, tmp_path: Path) -> None:
        """CLI should pass (or proceed past gate) if AGENTS.md is valid."""
        seg = tmp_path / "test_seg_valid"
        seg.mkdir()
        (seg / "skill.md").touch()
        ctx = seg / "_ctx"
        ctx.mkdir()
        (ctx / "agent_test_seg_valid.md").touch()
        (ctx / "prime_test_seg_valid.md").write_text("- [ref](doc.md)")
        (ctx / "session_test_seg_valid.md").touch()

        # Valid AGENTS.md
        (seg / "AGENTS.md").write_text("Policy: Strict")

        # Run CLI build
        cmd = ["uv", "run", "trifecta", "ctx", "build", "--segment", str(seg)]
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Note: It might fail later if UseCase logic fails due to empty context
        # But it should NOT fail with "Constitution Failed"
        assert "Constitution Failed (AGENTS.md)" not in result.stdout
