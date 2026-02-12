import subprocess
import sys
from pathlib import Path


def _create_wo(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "title: Unordered WO\n"
        "id: WO-1000\n"
        "version: 1\n"
        "epic_id: E-0001\n"
        "priority: P1\n"
        "status: pending\n"
        "scope:\n"
        "  allow: ['scripts/**']\n"
        "  deny: ['.env*']\n"
        "verify:\n"
        "  commands: ['echo ok']\n"
        "dod_id: DOD-DEFAULT\n",
        encoding="utf-8",
    )


def test_wo_fmt_check_detects_unformatted(tmp_path: Path) -> None:
    root = tmp_path
    wo = root / "_ctx" / "jobs" / "pending" / "WO-1000.yaml"
    _create_wo(wo)

    result = subprocess.run(
        [sys.executable, "scripts/ctx_wo_fmt.py", "--root", str(root), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Needs format" in result.stdout


def test_wo_fmt_write_then_check_passes(tmp_path: Path) -> None:
    root = tmp_path
    wo = root / "_ctx" / "jobs" / "pending" / "WO-1000.yaml"
    _create_wo(wo)

    write_result = subprocess.run(
        [sys.executable, "scripts/ctx_wo_fmt.py", "--root", str(root), "--write"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert write_result.returncode == 0

    check_result = subprocess.run(
        [sys.executable, "scripts/ctx_wo_fmt.py", "--root", str(root), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert check_result.returncode == 0

    lines = wo.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("version:")
    assert lines[1].startswith("id:")
