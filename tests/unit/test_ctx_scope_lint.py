from pathlib import Path
import subprocess

import yaml


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=root, check=True)


def _write_wo(root: Path, wo_id: str, payload: dict) -> None:
    wo_dir = root / "_ctx" / "jobs" / "pending"
    wo_dir.mkdir(parents=True, exist_ok=True)
    (wo_dir / f"{wo_id}.yaml").write_text(yaml.safe_dump(payload, sort_keys=False))


def _run_scope_lint(
    root: Path,
    wo_id: str,
    mode: str | None = None,
    allow_dirty: bool = False,
    env: dict | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = ["uv", "run", "python", "scripts/ctx_scope_lint.py", wo_id, "--root", str(root)]
    if mode:
        cmd.extend(["--mode", mode])
    if allow_dirty:
        cmd.append("--allow-dirty")
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def _stage_file(root: Path, path: str) -> None:
    subprocess.run(["git", "add", path], cwd=root, check=True)


def _commit_all(root: Path, message: str = "baseline") -> None:
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=root, check=True)


# =============================================================================
# Existing tests (adapted to new staged-only default)
# =============================================================================


def test_missing_wo_prints_error_to_stderr_and_exit_1(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _init_git_repo(root)

    result = _run_scope_lint(root, "WO-MISSING", allow_dirty=True)

    assert result.returncode == 1
    assert "ERROR: missing WO" in result.stderr
    assert result.stdout == ""


def test_scope_violations_exit_1(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _init_git_repo(root)

    _write_wo(
        root,
        "WO-TEST",
        {
            "id": "WO-TEST",
            "scope": {"allow": ["allowed/*"], "deny": []},
        },
    )
    _commit_all(root)
    # Create a blocked file and STAGE it (staged-only mode)
    (root / "blocked.txt").write_text("violation")
    _stage_file(root, "blocked.txt")

    result = _run_scope_lint(root, "WO-TEST", allow_dirty=True)

    assert result.returncode == 1
    assert "SCOPE_VIOLATIONS:" in result.stdout
    assert "blocked.txt" in result.stdout


def test_allowed_changes_exit_0(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _init_git_repo(root)

    _write_wo(
        root,
        "WO-TEST",
        {
            "id": "WO-TEST",
            "scope": {"allow": ["allowed/*"], "deny": []},
        },
    )
    _commit_all(root)
    allowed = root / "allowed" / "file.txt"
    allowed.parent.mkdir(parents=True)
    allowed.write_text("ok")
    _stage_file(root, "allowed/file.txt")

    result = _run_scope_lint(root, "WO-TEST", allow_dirty=True)
    assert result.returncode == 0, result.stderr


def test_yaml_parse_error_returns_exit_1_with_controlled_message(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _init_git_repo(root)

    wo_dir = root / "_ctx" / "jobs" / "pending"
    wo_dir.mkdir(parents=True)
    (wo_dir / "WO-TEST.yaml").write_text("id: WO-TEST\nscope: [\n")

    result = _run_scope_lint(root, "WO-TEST", allow_dirty=True)
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode == 1
    assert "ERROR: failed to load WO YAML" in output
    assert "Traceback" not in output


# =============================================================================
# A1: Staged-only mode tests
# =============================================================================


def test_scope_lint_uses_staged_only_by_default(tmp_path: Path):
    """A1: Default mode should only check staged files."""
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _init_git_repo(root)

    _write_wo(
        root,
        "WO-TEST",
        {
            "id": "WO-TEST",
            "scope": {"allow": ["allowed/*"], "deny": []},
        },
    )
    _commit_all(root)

    # Create unstaged file (should be ignored in staged mode)
    (root / "blocked_unstaged.txt").write_text("violation")

    # Create staged file in allowed path
    allowed = root / "allowed" / "file.txt"
    allowed.parent.mkdir(parents=True)
    allowed.write_text("ok")
    _stage_file(root, "allowed/file.txt")

    # Default mode (staged) should pass
    result = _run_scope_lint(root, "WO-TEST", allow_dirty=True)
    assert result.returncode == 0, f"Expected pass, got: {result.stdout}\n{result.stderr}"


def test_scope_lint_mode_all_includes_unstaged_and_untracked(tmp_path: Path):
    """A1: --mode all should check all changes (legacy behavior)."""
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _init_git_repo(root)

    _write_wo(
        root,
        "WO-TEST",
        {
            "id": "WO-TEST",
            "scope": {"allow": ["allowed/*"], "deny": []},
        },
    )
    _commit_all(root)

    # Create unstaged file
    (root / "blocked_unstaged.txt").write_text("violation")

    # --mode all should detect the violation
    result = _run_scope_lint(root, "WO-TEST", mode="all", allow_dirty=True)
    assert result.returncode == 1
    assert "SCOPE_VIOLATIONS:" in result.stdout
    assert "blocked_unstaged.txt" in result.stdout


def test_scope_lint_deny_wins_over_allow(tmp_path: Path):
    """A1: Deny list should always win over allow list."""
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _init_git_repo(root)

    _write_wo(
        root,
        "WO-TEST",
        {
            "id": "WO-TEST",
            "scope": {
                "allow": ["*"],
                "deny": ["blocked/*"],
                "override": True,
                "override_reason": "Test case for deny wins over allow",
                "override_expires": "2099-12-31",
            },
        },
    )
    _commit_all(root)

    # Create file in denied path
    blocked = root / "blocked" / "file.txt"
    blocked.parent.mkdir(parents=True)
    blocked.write_text("denied")
    _stage_file(root, "blocked/file.txt")

    result = _run_scope_lint(root, "WO-TEST", allow_dirty=True)
    assert result.returncode == 1
    assert "SCOPE_VIOLATIONS:" in result.stdout


# =============================================================================
# A1: Dirty worktree tests
# =============================================================================


def test_scope_lint_dirty_blocks_close_by_default(tmp_path: Path):
    """A1: Dirty worktree should block WO close by default."""
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _init_git_repo(root)

    _write_wo(
        root,
        "WO-TEST",
        {
            "id": "WO-TEST",
            "scope": {
                "allow": ["*"],
                "deny": [],
                "override": True,
                "override_reason": "Test case for dirty worktree blocking",
                "override_expires": "2099-12-31",
            },
        },
    )
    _commit_all(root)

    # Create unstaged file (dirty worktree)
    (root / "dirty_file.txt").write_text("dirty")

    # Should fail due to dirty worktree
    result = _run_scope_lint(root, "WO-TEST")
    assert result.returncode == 1
    assert "DIRTY_WORKTREE_BLOCKS_CLOSE:" in result.stdout


def test_scope_lint_allow_dirty_allows_but_warns(tmp_path: Path):
    """A1: --allow-dirty should allow dirty worktree with warning."""
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _init_git_repo(root)

    _write_wo(
        root,
        "WO-TEST",
        {
            "id": "WO-TEST",
            "scope": {
                "allow": ["*"],
                "deny": [],
                "override": True,
                "override_reason": "Test case for allow dirty warning",
                "override_expires": "2099-12-31",
            },
        },
    )
    _commit_all(root)

    # Create unstaged file (dirty worktree)
    (root / "dirty_file.txt").write_text("dirty")

    # Should pass with --allow-dirty
    result = _run_scope_lint(root, "WO-TEST", allow_dirty=True)
    assert result.returncode == 0
    assert "DIRTY_WORKTREE_ALLOWED:" in result.stderr


def test_scope_lint_clean_worktree_with_staged_changes(tmp_path: Path):
    """A1: Clean worktree with staged changes should check scope on staged only."""
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _init_git_repo(root)

    _write_wo(
        root,
        "WO-TEST",
        {
            "id": "WO-TEST",
            "scope": {"allow": ["allowed/*"], "deny": []},
        },
    )
    _commit_all(root)

    # Create and stage allowed file
    allowed = root / "allowed" / "file.txt"
    allowed.parent.mkdir(parents=True)
    allowed.write_text("ok")
    _stage_file(root, "allowed/file.txt")

    # Should pass (staged file is in scope, worktree is clean)
    result = _run_scope_lint(root, "WO-TEST")
    assert result.returncode == 0, f"Expected pass: {result.stdout}\n{result.stderr}"


# =============================================================================
# A4: Wildcard override tests
# =============================================================================


def test_scope_wildcard_requires_override_fields(tmp_path: Path):
    """A4: Wildcard allow without override should fail."""
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _init_git_repo(root)

    _write_wo(
        root,
        "WO-TEST",
        {
            "id": "WO-TEST",
            "scope": {"allow": ["*"], "deny": []},  # Wildcard without override
        },
    )
    _commit_all(root)

    # Stage a file
    (root / "file.txt").write_text("test")
    _stage_file(root, "file.txt")

    # Should fail due to missing override
    result = _run_scope_lint(
        root,
        "WO-TEST",
        allow_dirty=True,
        env={**subprocess.os.environ, "WILDCARD_POLICY": "enforce"},
    )
    assert result.returncode == 1
    assert "WILDCARD_REQUIRES_OVERRIDE" in result.stderr


def test_scope_wildcard_with_valid_override_passes(tmp_path: Path):
    """A4: Wildcard with valid override should pass."""
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _init_git_repo(root)

    _write_wo(
        root,
        "WO-TEST",
        {
            "id": "WO-TEST",
            "scope": {
                "allow": ["*"],
                "deny": [],
                "override": True,
                "override_reason": "Initial project setup with broad scope allowed",
                "override_expires": "2099-12-31",
            },
        },
    )
    _commit_all(root)

    # Stage a file
    (root / "file.txt").write_text("test")
    _stage_file(root, "file.txt")

    # Should pass with valid override
    result = _run_scope_lint(
        root,
        "WO-TEST",
        allow_dirty=True,
        env={**subprocess.os.environ, "WILDCARD_POLICY": "enforce"},
    )
    assert result.returncode == 0, f"Expected pass: {result.stdout}\n{result.stderr}"


def test_scope_override_expires_enforced(tmp_path: Path):
    """A4: Expired override should fail."""
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _init_git_repo(root)

    _write_wo(
        root,
        "WO-TEST",
        {
            "id": "WO-TEST",
            "scope": {
                "allow": ["*"],
                "deny": [],
                "override": True,
                "override_reason": "This override has expired already",
                "override_expires": "2020-01-01",  # Past date
            },
        },
    )
    _commit_all(root)

    # Stage a file
    (root / "file.txt").write_text("test")
    _stage_file(root, "file.txt")

    # Should fail due to expired override
    result = _run_scope_lint(
        root,
        "WO-TEST",
        allow_dirty=True,
        env={**subprocess.os.environ, "WILDCARD_POLICY": "enforce"},
    )
    assert result.returncode == 1
    assert "OVERRIDE_EXPIRED" in result.stderr


def test_scope_override_expires_invalid_format_fails(tmp_path: Path):
    """A4: Invalid override_expires format should fail with clear error."""
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _init_git_repo(root)

    _write_wo(
        root,
        "WO-TEST",
        {
            "id": "WO-TEST",
            "scope": {
                "allow": ["*"],
                "deny": [],
                "override": True,
                "override_reason": "Test case for invalid date format",
                "override_expires": "not-a-date",  # Invalid format
            },
        },
    )
    _commit_all(root)

    (root / "file.txt").write_text("test")
    _stage_file(root, "file.txt")

    result = _run_scope_lint(
        root,
        "WO-TEST",
        allow_dirty=True,
        env={**subprocess.os.environ, "WILDCARD_POLICY": "enforce"},
    )
    assert result.returncode == 1
    assert "override_expires" in result.stderr or "valid ISO date" in result.stderr


def test_wildcard_policy_warn_does_not_fail(tmp_path: Path):
    """A4: With WILDCARD_POLICY=warn, missing override should warn but not fail."""
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _init_git_repo(root)

    _write_wo(
        root,
        "WO-TEST",
        {
            "id": "WO-TEST",
            "scope": {"allow": ["*"], "deny": []},  # Wildcard without override
        },
    )
    _commit_all(root)

    # Stage a file
    (root / "file.txt").write_text("test")
    _stage_file(root, "file.txt")

    # Should warn but pass with WILDCARD_POLICY=warn
    result = _run_scope_lint(
        root,
        "WO-TEST",
        allow_dirty=True,
        env={**subprocess.os.environ, "WILDCARD_POLICY": "warn"},
    )
    assert result.returncode == 0
    assert "WARNING" in result.stderr
    assert "WILDCARD_REQUIRES_OVERRIDE" in result.stderr


def test_wildcard_policy_enforce_fails(tmp_path: Path):
    """A4: With WILDCARD_POLICY=enforce, missing override should fail."""
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _init_git_repo(root)

    _write_wo(
        root,
        "WO-TEST",
        {
            "id": "WO-TEST",
            "scope": {"allow": ["*"], "deny": []},  # Wildcard without override
        },
    )
    _commit_all(root)

    # Stage a file
    (root / "file.txt").write_text("test")
    _stage_file(root, "file.txt")

    # Should fail with WILDCARD_POLICY=enforce
    result = _run_scope_lint(
        root,
        "WO-TEST",
        allow_dirty=True,
        env={**subprocess.os.environ, "WILDCARD_POLICY": "enforce"},
    )
    assert result.returncode == 1


def test_override_reason_too_short_fails(tmp_path: Path):
    """A4: Override reason must be >= 20 chars."""
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _init_git_repo(root)

    _write_wo(
        root,
        "WO-TEST",
        {
            "id": "WO-TEST",
            "scope": {
                "allow": ["*"],
                "deny": [],
                "override": True,
                "override_reason": "too short",  # < 20 chars
                "override_expires": "2099-12-31",
            },
        },
    )
    _commit_all(root)

    # Stage a file
    (root / "file.txt").write_text("test")
    _stage_file(root, "file.txt")

    # Should fail due to short override reason
    result = _run_scope_lint(
        root,
        "WO-TEST",
        allow_dirty=True,
        env={**subprocess.os.environ, "WILDCARD_POLICY": "enforce"},
    )
    assert result.returncode == 1
    assert "20 chars" in result.stderr


def test_non_wildcard_scope_ignores_override_check(tmp_path: Path):
    """A4: Non-wildcard scope should not require override fields."""
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _init_git_repo(root)

    _write_wo(
        root,
        "WO-TEST",
        {
            "id": "WO-TEST",
            "scope": {"allow": ["src/**"], "deny": []},  # Not a global wildcard
        },
    )
    _commit_all(root)

    # Stage a file in allowed path
    src = root / "src" / "file.py"
    src.parent.mkdir(parents=True)
    src.write_text("# test")
    _stage_file(root, "src/file.py")

    # Should pass without override fields
    result = _run_scope_lint(
        root,
        "WO-TEST",
        allow_dirty=True,
        env={**subprocess.os.environ, "WILDCARD_POLICY": "enforce"},
    )
    assert result.returncode == 0, f"Expected pass: {result.stdout}\n{result.stderr}"
