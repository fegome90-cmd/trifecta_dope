from pathlib import Path
import json
import shutil
import subprocess

import yaml


def test_verify_run_help():
    result = subprocess.run(
        ["bash", "scripts/ctx_verify_run.sh", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_wo_verify_help():
    """A2: wo_verify.sh should have help."""
    result = subprocess.run(
        ["bash", "scripts/wo_verify.sh", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_repo_verify_help():
    """A2: repo_verify.sh should have help."""
    result = subprocess.run(
        ["bash", "scripts/repo_verify.sh", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_verify_run_executes_and_writes_verdict(tmp_path: Path):
    root = tmp_path / "repo"
    scripts_dir = root / "scripts"
    wo_dir = root / "_ctx" / "jobs" / "pending"
    scripts_dir.mkdir(parents=True)
    wo_dir.mkdir(parents=True)

    shutil.copy("scripts/ctx_verify_run.sh", scripts_dir / "ctx_verify_run.sh")
    shutil.copy("scripts/wo_verify.sh", scripts_dir / "wo_verify.sh")
    shutil.copy("scripts/ctx_scope_lint.py", scripts_dir / "ctx_scope_lint.py")

    wo = {
        "version": 1,
        "id": "WO-TEST",
        "epic_id": "E-0001",
        "title": "verify smoke",
        "priority": "P2",
        "status": "pending",
        "dod_id": "DOD-DEFAULT",
        "scope": {
            "allow": ["*"],
            "deny": [],
            "override": True,
            "override_reason": "Test case for verify smoke test",
            "override_expires": "2099-12-31",
        },
        "verify": {"commands": ["echo ok"]},
    }
    (wo_dir / "WO-TEST.yaml").write_text(yaml.safe_dump(wo, sort_keys=False))

    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=root, check=True)

    result = subprocess.run(
        ["uv", "run", "bash", "scripts/ctx_verify_run.sh", "WO-TEST", "--root", str(root), "--allow-dirty"],
        cwd=root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (root / "_ctx" / "logs" / "WO-TEST" / "verdict.json").exists()


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=root, check=True)


def _setup_verify_repo(tmp_path: Path, wo_id: str = "WO-TEST") -> tuple[Path, Path]:
    root = tmp_path / "repo"
    scripts_dir = root / "scripts"
    wo_dir = root / "_ctx" / "jobs" / "pending"
    scripts_dir.mkdir(parents=True)
    wo_dir.mkdir(parents=True)

    shutil.copy("scripts/ctx_verify_run.sh", scripts_dir / "ctx_verify_run.sh")
    shutil.copy("scripts/wo_verify.sh", scripts_dir / "wo_verify.sh")
    shutil.copy("scripts/ctx_scope_lint.py", scripts_dir / "ctx_scope_lint.py")
    _init_git_repo(root)
    return root, wo_dir / f"{wo_id}.yaml"


def _run_verify(root: Path, wo_id: str = "WO-TEST", allow_dirty: bool = True) -> subprocess.CompletedProcess[str]:
    cmd = ["uv", "run", "bash", "scripts/ctx_verify_run.sh", wo_id, "--root", str(root)]
    if allow_dirty:
        cmd.append("--allow-dirty")
    return subprocess.run(
        cmd,
        cwd=root,
        capture_output=True,
        text=True,
    )


def test_verify_run_missing_wo_exits_1(tmp_path: Path):
    root, _ = _setup_verify_repo(tmp_path, wo_id="WO-ANY")
    result = _run_verify(root, wo_id="WO-MISSING")
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode == 1
    assert "ERROR: missing WO" in output


def test_verify_run_fails_when_scope_lint_fails(tmp_path: Path):
    root, wo_path = _setup_verify_repo(tmp_path)
    wo = {
        "version": 1,
        "id": "WO-TEST",
        "epic_id": "E-0001",
        "title": "verify scope",
        "priority": "P2",
        "status": "pending",
        "dod_id": "DOD-DEFAULT",
        "scope": {"allow": ["allowed/*"], "deny": []},
        "verify": {"commands": ["echo ok"]},
    }
    wo_path.write_text(yaml.safe_dump(wo, sort_keys=False))
    # Stage everything first (WO file + scripts)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    # Create and stage blocked file
    (root / "blocked.txt").write_text("x")
    subprocess.run(["git", "add", "blocked.txt"], cwd=root, check=True)

    result = _run_verify(root, allow_dirty=True)
    # With staged mode and no wildcard, scope should fail
    assert result.returncode == 1
    # Scope lint writes verdict on failure now
    assert (root / "_ctx" / "logs" / "WO-TEST" / "verdict.json").exists()


def test_verify_run_fails_when_verify_command_fails_and_writes_fail_verdict(tmp_path: Path):
    root, wo_path = _setup_verify_repo(tmp_path)
    wo = {
        "version": 1,
        "id": "WO-TEST",
        "epic_id": "E-0001",
        "title": "verify fail",
        "priority": "P2",
        "status": "pending",
        "dod_id": "DOD-DEFAULT",
        "scope": {
            "allow": ["*"],
            "deny": [],
            "override": True,
            "override_reason": "Test case for command failure verdict",
            "override_expires": "2099-12-31",
        },
        "verify": {"commands": ["false"]},
    }
    wo_path.write_text(yaml.safe_dump(wo, sort_keys=False))

    result = _run_verify(root)
    verdict_path = root / "_ctx" / "logs" / "WO-TEST" / "verdict.json"
    verdict = json.loads(verdict_path.read_text())

    assert result.returncode == 1
    assert verdict_path.exists()
    assert verdict["status"] == "FAIL"


def test_verify_run_handles_invalid_yaml_with_controlled_error(tmp_path: Path):
    root, wo_path = _setup_verify_repo(tmp_path)
    wo_path.write_text("id: WO-TEST\nverify: [\n")

    result = _run_verify(root)
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode == 1
    # Invalid YAML is caught by scope lint first (which loads the WO)
    assert "ERROR: failed to load" in output
    assert "Traceback" not in output


def test_verify_run_handles_empty_verify_commands(tmp_path: Path):
    root, wo_path = _setup_verify_repo(tmp_path)
    wo = {
        "version": 1,
        "id": "WO-TEST",
        "epic_id": "E-0001",
        "title": "verify empty",
        "priority": "P2",
        "status": "pending",
        "dod_id": "DOD-DEFAULT",
        "scope": {
            "allow": ["*"],
            "deny": [],
            "override": True,
            "override_reason": "Test case for empty verify commands",
            "override_expires": "2099-12-31",
        },
        "verify": {"commands": []},
    }
    wo_path.write_text(yaml.safe_dump(wo, sort_keys=False))

    result = _run_verify(root)
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode == 1
    assert "ERROR: verify.commands is empty" in output


# =============================================================================
# A2: New tests for SSOT and gate separation
# =============================================================================


def test_verify_run_is_wrapper_for_wo_verify(tmp_path: Path):
    """A2: ctx_verify_run.sh should delegate to wo_verify.sh."""
    root = tmp_path / "repo"
    scripts_dir = root / "scripts"
    wo_dir = root / "_ctx" / "jobs" / "pending"
    scripts_dir.mkdir(parents=True)
    wo_dir.mkdir(parents=True)

    shutil.copy("scripts/ctx_verify_run.sh", scripts_dir / "ctx_verify_run.sh")
    shutil.copy("scripts/wo_verify.sh", scripts_dir / "wo_verify.sh")
    shutil.copy("scripts/ctx_scope_lint.py", scripts_dir / "ctx_scope_lint.py")

    wo = {
        "version": 1,
        "id": "WO-TEST",
        "scope": {
            "allow": ["*"],
            "deny": [],
            "override": True,
            "override_reason": "Test wrapper delegates to wo_verify",
            "override_expires": "2099-12-31",
        },
        "verify": {"commands": ["echo 'from wo_verify.sh'"]},
    }
    (wo_dir / "WO-TEST.yaml").write_text(yaml.safe_dump(wo, sort_keys=False))

    _init_git_repo(root)

    # Call ctx_verify_run.sh with --allow-dirty (untracked files exist)
    result = subprocess.run(
        ["uv", "run", "bash", "scripts/ctx_verify_run.sh", "WO-TEST", "--root", str(root), "--allow-dirty"],
        cwd=root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    # Check that wo_verify.sh was called (verdict.json exists)
    assert (root / "_ctx" / "logs" / "WO-TEST" / "verdict.json").exists()


def test_wo_verify_writes_verdict_on_scope_failure(tmp_path: Path):
    """A2: wo_verify.sh should write verdict.json even on scope failure."""
    root = tmp_path / "repo"
    scripts_dir = root / "scripts"
    wo_dir = root / "_ctx" / "jobs" / "pending"
    scripts_dir.mkdir(parents=True)
    wo_dir.mkdir(parents=True)

    shutil.copy("scripts/wo_verify.sh", scripts_dir / "wo_verify.sh")
    shutil.copy("scripts/ctx_scope_lint.py", scripts_dir / "ctx_scope_lint.py")

    wo = {
        "version": 1,
        "id": "WO-TEST",
        "scope": {
            "allow": ["allowed/*"],  # No wildcard, no override needed
            "deny": [],
        },
        "verify": {"commands": ["echo ok"]},
    }
    (wo_dir / "WO-TEST.yaml").write_text(yaml.safe_dump(wo, sort_keys=False))

    _init_git_repo(root)

    # Stage a blocked file
    (root / "blocked.txt").write_text("x")
    subprocess.run(["git", "add", "blocked.txt"], cwd=root, check=True)

    # Call wo_verify.sh directly
    result = subprocess.run(
        ["uv", "run", "bash", "scripts/wo_verify.sh", "WO-TEST", "--root", str(root)],
        cwd=root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    # Scope lint verdict should exist
    verdict_path = root / "_ctx" / "logs" / "WO-TEST" / "verdict.json"
    assert verdict_path.exists(), f"verdict.json should exist on scope failure"
    verdict = json.loads(verdict_path.read_text())
    assert verdict["status"] == "FAIL"
    assert verdict.get("failure_stage") == "scope_lint"


def test_wo_verify_with_allow_dirty_passes(tmp_path: Path):
    """A2: wo_verify.sh --allow-dirty should allow dirty worktree."""
    root = tmp_path / "repo"
    scripts_dir = root / "scripts"
    wo_dir = root / "_ctx" / "jobs" / "pending"
    scripts_dir.mkdir(parents=True)
    wo_dir.mkdir(parents=True)

    shutil.copy("scripts/wo_verify.sh", scripts_dir / "wo_verify.sh")
    shutil.copy("scripts/ctx_scope_lint.py", scripts_dir / "ctx_scope_lint.py")

    wo = {
        "version": 1,
        "id": "WO-TEST",
        "scope": {
            "allow": ["*"],
            "deny": [],
            "override": True,
            "override_reason": "Test allow-dirty flag passes with dirty",
            "override_expires": "2099-12-31",
        },
        "verify": {"commands": ["echo ok"]},
    }
    (wo_dir / "WO-TEST.yaml").write_text(yaml.safe_dump(wo, sort_keys=False))

    _init_git_repo(root)

    # Create dirty file (not staged)
    (root / "dirty_file.txt").write_text("dirty")

    # Call wo_verify.sh with --allow-dirty
    result = subprocess.run(
        ["uv", "run", "bash", "scripts/wo_verify.sh", "WO-TEST", "--root", str(root), "--allow-dirty"],
        cwd=root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Should pass with --allow-dirty: {result.stderr}"
    assert "DIRTY_WORKTREE_ALLOWED" in result.stderr
