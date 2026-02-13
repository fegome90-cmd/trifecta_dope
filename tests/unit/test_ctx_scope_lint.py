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


def _run_scope_lint(root: Path, wo_id: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "python", "scripts/ctx_scope_lint.py", wo_id, "--root", str(root)],
        capture_output=True,
        text=True,
    )


def _commit_all(root: Path, message: str = "baseline") -> None:
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=root, check=True)


def test_missing_wo_prints_error_to_stderr_and_exit_1(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _init_git_repo(root)

    result = _run_scope_lint(root, "WO-MISSING")

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
    (root / "blocked.txt").write_text("violation")

    result = _run_scope_lint(root, "WO-TEST")

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

    result = _run_scope_lint(root, "WO-TEST")
    assert result.returncode == 0, result.stderr


def test_yaml_parse_error_returns_exit_1_with_controlled_message(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    _init_git_repo(root)

    wo_dir = root / "_ctx" / "jobs" / "pending"
    wo_dir.mkdir(parents=True)
    (wo_dir / "WO-TEST.yaml").write_text("id: WO-TEST\nscope: [\n")

    result = _run_scope_lint(root, "WO-TEST")
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode == 1
    assert "ERROR: failed to load WO YAML" in output
    assert "Traceback" not in output
