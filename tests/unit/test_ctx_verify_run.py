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


def test_verify_run_executes_and_writes_verdict(tmp_path: Path):
    root = tmp_path / "repo"
    scripts_dir = root / "scripts"
    wo_dir = root / "_ctx" / "jobs" / "pending"
    scripts_dir.mkdir(parents=True)
    wo_dir.mkdir(parents=True)

    shutil.copy("scripts/ctx_verify_run.sh", scripts_dir / "ctx_verify_run.sh")
    shutil.copy("scripts/ctx_scope_lint.py", scripts_dir / "ctx_scope_lint.py")

    wo = {
        "version": 1,
        "id": "WO-TEST",
        "epic_id": "E-0001",
        "title": "verify smoke",
        "priority": "P2",
        "status": "pending",
        "dod_id": "DOD-DEFAULT",
        "scope": {"allow": ["*"], "deny": []},
        "verify": {"commands": ["echo ok"]},
    }
    (wo_dir / "WO-TEST.yaml").write_text(yaml.safe_dump(wo, sort_keys=False))

    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "init"], cwd=root, check=True)

    result = subprocess.run(
        ["uv", "run", "bash", "scripts/ctx_verify_run.sh", "WO-TEST", "--root", str(root)],
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
    shutil.copy("scripts/ctx_scope_lint.py", scripts_dir / "ctx_scope_lint.py")
    _init_git_repo(root)
    return root, wo_dir / f"{wo_id}.yaml"


def _run_verify(root: Path, wo_id: str = "WO-TEST") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "bash", "scripts/ctx_verify_run.sh", wo_id, "--root", str(root)],
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
    (root / "blocked.txt").write_text("x")

    result = _run_verify(root)
    assert result.returncode == 1
    assert "SCOPE_VIOLATIONS:" in result.stdout
    assert not (root / "_ctx" / "logs" / "WO-TEST" / "verdict.json").exists()


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
        "scope": {"allow": ["*"], "deny": []},
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
    assert "ERROR: failed to load verify.commands" in output
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
        "scope": {"allow": ["*"], "deny": []},
        "verify": {"commands": []},
    }
    wo_path.write_text(yaml.safe_dump(wo, sort_keys=False))

    result = _run_verify(root)
    output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode == 1
    assert "ERROR: verify.commands is empty" in output
