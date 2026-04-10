"""
Tests for CLI create command with normalized naming.

TDD Phase: RED -> GREEN
Ensures CLI generates files with correct normalized segment IDs.

UPDATED: Use correct CLI flags (-s for segment path).
"""

import json
from pathlib import Path

from typer.testing import CliRunner

from src.infrastructure.cli import app

runner = CliRunner()


def _current_create_surface_paths(segment_root: Path) -> dict[str, Path]:
    segment_id = segment_root.name
    ctx = segment_root / "_ctx"
    return {
        "AGENTS.md": segment_root / "AGENTS.md",
        "skill.md": segment_root / "skill.md",
        "readme_tf.md": segment_root / "readme_tf.md",
        "_ctx/trifecta_config.json": ctx / "trifecta_config.json",
        f"_ctx/agent_{segment_id}.md": ctx / f"agent_{segment_id}.md",
        f"_ctx/prime_{segment_id}.md": ctx / f"prime_{segment_id}.md",
        f"_ctx/session_{segment_id}.md": ctx / f"session_{segment_id}.md",
    }


def _snapshot_current_create_surfaces(segment_root: Path) -> dict[str, str | None]:
    snapshot: dict[str, str | None] = {}
    for label, path in _current_create_surface_paths(segment_root).items():
        snapshot[label] = path.read_text() if path.exists() else None
    return snapshot


def _write_current_create_surfaces(segment_root: Path, *, token: str) -> None:
    segment_id = segment_root.name
    for label, path in _current_create_surface_paths(segment_root).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if label == "_ctx/trifecta_config.json":
            path.write_text(
                json.dumps(
                    {
                        "segment": segment_id,
                        "scope": "tests",
                        "repo_root": str(segment_root),
                        "default_profile": "impl_patch",
                        "last_verified": "2026-03-19",
                    }
                )
                + "\n"
            )
        elif label == "skill.md":
            path.write_text(
                """---
name: test
description: Test segment
---
# Test
"""
            )
        else:
            path.write_text(f"{label}::{token}\n")


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

    def test_create_allows_true_bootstrap_when_directory_is_uninitialized(
        self, tmp_path: Path
    ) -> None:
        """True bootstrap is allowed when no canon exists and the dir is blank."""
        result = runner.invoke(app, ["create", "-s", str(tmp_path)])

        assert result.exit_code == 0, f"Create failed: {result.output}"
        for label, path in _current_create_surface_paths(tmp_path).items():
            assert path.exists(), f"{label} missing after bootstrap"

    def test_create_returns_already_initialized_without_writing(
        self, tmp_path: Path
    ) -> None:
        """Already-initialized segments must fail closed and write nothing."""
        _write_current_create_surfaces(tmp_path, token="initialized")
        before = _snapshot_current_create_surfaces(tmp_path)

        result = runner.invoke(app, ["create", "-s", str(tmp_path)])

        assert result.exit_code != 0, "create should fail closed for already initialized"
        assert "SEGMENT_ALREADY_INITIALIZED" in result.output
        assert _snapshot_current_create_surfaces(tmp_path) == before

    def test_create_fails_when_canonical_candidate_is_incomplete(
        self, tmp_path: Path
    ) -> None:
        """Incomplete canonical state must fail closed and preserve current files."""
        ctx = tmp_path / "_ctx"
        ctx.mkdir(parents=True, exist_ok=True)
        (ctx / f"agent_{tmp_path.name}.md").write_text("agent\n")
        (ctx / f"prime_{tmp_path.name}.md").write_text("prime\n")
        before = _snapshot_current_create_surfaces(tmp_path)

        result = runner.invoke(app, ["create", "-s", str(tmp_path)])

        assert result.exit_code != 0, "create should fail closed for incomplete canon"
        assert "SEGMENT_CANON_INCOMPLETE" in result.output
        assert _snapshot_current_create_surfaces(tmp_path) == before

    def test_create_fails_when_canonical_candidate_is_ambiguous(
        self, tmp_path: Path
    ) -> None:
        """Ambiguous canonical state must fail closed and preserve current files."""
        ctx = tmp_path / "_ctx"
        ctx.mkdir(parents=True, exist_ok=True)
        for suffix in ("alpha", "beta"):
            (ctx / f"agent_{suffix}.md").write_text("agent\n")
            (ctx / f"prime_{suffix}.md").write_text("prime\n")
            (ctx / f"session_{suffix}.md").write_text("session\n")
        before = _snapshot_current_create_surfaces(tmp_path)

        result = runner.invoke(app, ["create", "-s", str(tmp_path)])

        assert result.exit_code != 0, "create should fail closed for ambiguous canon"
        assert "SEGMENT_CANON_AMBIGUOUS" in result.output
        assert _snapshot_current_create_surfaces(tmp_path) == before

    def test_create_fails_when_canonical_candidate_is_contaminated(
        self, tmp_path: Path
    ) -> None:
        """Contaminated canonical state must fail closed and preserve current files."""
        ctx = tmp_path / "_ctx"
        ctx.mkdir(parents=True, exist_ok=True)
        _write_current_create_surfaces(tmp_path, token="contaminated")
        (ctx / "agent_shadow.md").write_text("shadow\n")
        before = _snapshot_current_create_surfaces(tmp_path)

        result = runner.invoke(app, ["create", "-s", str(tmp_path)])

        assert result.exit_code != 0, "create should fail closed for contaminated canon"
        assert "SEGMENT_CANON_CONTAMINATED" in result.output
        assert _snapshot_current_create_surfaces(tmp_path) == before

    def test_create_fails_when_local_config_contradicts_canonical_candidate(
        self, tmp_path: Path
    ) -> None:
        """Contradictory local config must fail closed and preserve current files."""
        ctx = tmp_path / "_ctx"
        ctx.mkdir(parents=True, exist_ok=True)
        _write_current_create_surfaces(tmp_path, token="contradiction")
        (ctx / "trifecta_config.json").write_text(
            """{
  "segment": "different-segment",
  "scope": "tests",
  "repo_root": "/tmp/elsewhere",
  "default_profile": "impl_patch",
  "last_verified": "2026-03-19"
}
"""
        )
        before = _snapshot_current_create_surfaces(tmp_path)

        result = runner.invoke(app, ["create", "-s", str(tmp_path)])

        assert result.exit_code != 0, "create should fail closed for contradictory config"
        assert "SEGMENT_CANON_CONTRADICTED_BY_LOCAL_CONFIG" in result.output
        assert _snapshot_current_create_surfaces(tmp_path) == before
