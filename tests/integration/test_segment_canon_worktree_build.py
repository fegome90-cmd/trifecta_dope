"""Integration regression for segment canon authority in real git worktrees."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def repo_root() -> Path:
    """Find repository root by searching for pyproject.toml."""
    return Path(__file__).resolve().parents[2]


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_ctx_build_prefers_tracked_canon_over_transitional_config_in_worktree(
    tmp_path: Path,
) -> None:
    env = os.environ.copy()
    env["TRIFECTA_NO_TELEMETRY"] = "1"

    base = tmp_path / "segment-base"
    worktree = tmp_path / "renamed-worktree"
    base.mkdir()

    assert _run(["git", "init", "-q"], cwd=base, env=env).returncode == 0

    create = _run(["uv", "run", "trifecta", "create", "-s", str(base)], cwd=repo_root(), env=env)
    assert create.returncode == 0, create.stdout + create.stderr

    assert _run(["git", "add", "."], cwd=base, env=env).returncode == 0
    commit = _run(
        [
            "git",
            "-c",
            "user.name=Codex",
            "-c",
            "user.email=codex@example.com",
            "commit",
            "-qm",
            "bootstrap",
        ],
        cwd=base,
        env=env,
    )
    assert commit.returncode == 0, commit.stdout + commit.stderr

    wt_add = _run(["git", "worktree", "add", "-q", str(worktree), "HEAD"], cwd=base, env=env)
    assert wt_add.returncode == 0, wt_add.stdout + wt_add.stderr

    ctx = worktree / "_ctx"
    triplet = sorted(path.name for path in ctx.glob("*_segment-base.md"))
    assert triplet == [
        "agent_segment-base.md",
        "prime_segment-base.md",
        "session_segment-base.md",
    ]

    config = json.loads((ctx / "trifecta_config.json").read_text())
    assert config["segment"] == "segment-base"
    assert Path(config["repo_root"]).resolve() == base.resolve()
    assert worktree.resolve() != base.resolve()

    build_base = _run(
        ["uv", "run", "trifecta", "ctx", "build", "-s", str(base)],
        cwd=repo_root(),
        env=env,
    )
    assert build_base.returncode == 0, build_base.stdout + build_base.stderr

    build_worktree = _run(
        ["uv", "run", "trifecta", "ctx", "build", "-s", str(worktree)],
        cwd=repo_root(),
        env=env,
    )
    assert build_worktree.returncode == 0, build_worktree.stdout + build_worktree.stderr
