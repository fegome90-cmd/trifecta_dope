"""Tests for verify.sh runtime-root contract."""

import os
import subprocess
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_verify_rejects_invalid_root_path() -> None:
    result = subprocess.run(
        ["bash", "scripts/verify.sh", "WO-TEST", "--check-only", "--root", "/no/such/path"],
        capture_output=True,
        text=True,
        cwd=repo_root(),
    )
    assert result.returncode == 1
    assert "invalid root path" in (result.stdout + result.stderr).lower()


def test_verify_writes_report_under_root_handoff_in_selftest(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)

    env = dict(os.environ)
    env["TRIFECTA_VERIFY_SELFTEST"] = "1"

    result = subprocess.run(
        [
            "bash",
            str(repo_root() / "scripts" / "verify.sh"),
            "WO-TEST",
            "--root",
            str(root),
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=env,
    )

    assert result.returncode == 0
    report = root / "_ctx" / "handoff" / "WO-TEST" / "verification_report.log"
    assert report.exists()
