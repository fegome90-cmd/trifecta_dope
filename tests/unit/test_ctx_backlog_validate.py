import subprocess
from pathlib import Path

import yaml


def test_ctx_backlog_validate_ok():
    result = subprocess.run(
        ["python", "scripts/ctx_backlog_validate.py", "--fixtures"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0


def test_warns_on_legacy_dod_in_strict_mode():
    result = subprocess.run(
        ["python", "scripts/ctx_backlog_validate.py", "--fixtures", "--strict"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "WARN" in result.stdout
    assert "DOD-LEGACY" in result.stdout


def test_legacy_wos_tagged_when_using_legacy_dod():
    repo_root = Path(__file__).resolve().parents[2]
    wo_paths = [
        repo_root / "_ctx" / "jobs" / "done" / "WO-0008_job.yaml",
        repo_root / "_ctx" / "jobs" / "done" / "WO-0009_job.yaml",
    ]
    for path in wo_paths:
        data = yaml.safe_load(path.read_text())
        assert data.get("x_legacy") is True
