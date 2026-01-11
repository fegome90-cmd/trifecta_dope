import shutil
import subprocess
from pathlib import Path


def test_real_wo_validates_and_can_be_taken(tmp_path):
    repo_root = Path(__file__).resolve().parents[2]
    fixture_root = repo_root / "tests" / "fixtures" / "ctx"
    sandbox_root = tmp_path / "ctx"
    shutil.copytree(fixture_root, sandbox_root)

    result = subprocess.run(
        [
            "python",
            "scripts/ctx_backlog_validate.py",
            "--root",
            str(sandbox_root),
            "--strict",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=repo_root,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    result = subprocess.run(
        [
            "python",
            "scripts/ctx_wo_take.py",
            "WO-0001",
            "--root",
            str(sandbox_root),
            "--owner",
            "tester",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=repo_root,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    running_path = sandbox_root / "_ctx" / "jobs" / "running" / "WO-0001.yaml"
    lock_path = sandbox_root / "_ctx" / "jobs" / "running" / "WO-0001.lock"
    assert running_path.exists()
    assert lock_path.exists()
