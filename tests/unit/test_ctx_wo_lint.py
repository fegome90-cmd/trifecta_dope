import json
import subprocess
import sys
from pathlib import Path


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _bootstrap_repo(tmp_path: Path) -> Path:
    root = tmp_path
    (root / "_ctx" / "jobs" / "pending").mkdir(parents=True, exist_ok=True)
    (root / "_ctx" / "jobs" / "running").mkdir(parents=True, exist_ok=True)
    (root / "_ctx" / "jobs" / "done").mkdir(parents=True, exist_ok=True)
    (root / "_ctx" / "jobs" / "failed").mkdir(parents=True, exist_ok=True)
    (root / "_ctx" / "jobs" / "legacy").mkdir(parents=True, exist_ok=True)
    (root / "_ctx" / "backlog").mkdir(parents=True, exist_ok=True)
    (root / "_ctx" / "dod").mkdir(parents=True, exist_ok=True)

    _write_json(
        root / "docs" / "backlog" / "schema" / "work_order.schema.json",
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["version", "id", "epic_id", "title", "priority", "status", "dod_id"],
            "properties": {
                "version": {"type": "integer"},
                "id": {"type": "string"},
                "epic_id": {"type": "string"},
                "title": {"type": "string"},
                "priority": {"type": "string"},
                "status": {"type": "string"},
                "dod_id": {"type": "string"},
            },
            "additionalProperties": True,
        },
    )
    _write_json(
        root / "docs" / "backlog" / "schema" / "backlog.schema.json",
        {"type": "object"},
    )
    _write_json(
        root / "docs" / "backlog" / "schema" / "dod.schema.json",
        {"type": "object"},
    )

    (root / "_ctx" / "backlog" / "backlog.yaml").write_text(
        "version: 1\n"
        "generated_at: now\n"
        "epics:\n"
        "  - id: E-0001\n"
        "    title: Epic\n"
        "    priority: P1\n"
        "    wo_queue: [WO-0001]\n",
        encoding="utf-8",
    )
    (root / "_ctx" / "dod" / "DOD-DEFAULT.yaml").write_text(
        "dod:\n  - id: DOD-DEFAULT\n    checklist: []\n",
        encoding="utf-8",
    )
    return root


def _valid_wo(status: str, wo_id: str = "WO-0001", dependencies: str = "") -> str:
    return (
        "version: 1\n"
        f"id: {wo_id}\n"
        "epic_id: E-0001\n"
        "title: Valid WO\n"
        "priority: P1\n"
        f"status: {status}\n"
        "owner: null\n"
        "scope:\n"
        "  allow: ['scripts/**']\n"
        "  deny: ['.env*']\n"
        "verify:\n"
        "  commands:\n"
        '    - "echo ok"\n'
        "dod_id: DOD-DEFAULT\n"
        f"{dependencies}"
    )


def test_wo_lint_ignores_legacy_paths(tmp_path: Path) -> None:
    root = _bootstrap_repo(tmp_path)
    (root / "_ctx" / "jobs" / "pending" / "WO-0001.yaml").write_text(
        _valid_wo("pending"), encoding="utf-8"
    )
    (root / "_ctx" / "jobs" / "done" / "WO-9999_job.yaml").write_text(
        "invalid: [", encoding="utf-8"
    )

    result = subprocess.run(
        [sys.executable, "scripts/ctx_wo_lint.py", "--root", str(root), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    findings = json.loads(result.stdout)
    assert any(f["code"] == "WOI01" and f["severity"] == "INFO" for f in findings)
    assert not any(f["severity"] == "ERROR" for f in findings)


def test_wo_lint_flags_pending_missing_verify_commands(tmp_path: Path) -> None:
    root = _bootstrap_repo(tmp_path)
    (root / "_ctx" / "jobs" / "pending" / "WO-0001.yaml").write_text(
        "version: 1\n"
        "id: WO-0001\n"
        "epic_id: E-0001\n"
        "title: Missing Verify\n"
        "priority: P1\n"
        "status: pending\n"
        "scope:\n"
        "  allow: ['scripts/**']\n"
        "  deny: ['.env*']\n"
        "dod_id: DOD-DEFAULT\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/ctx_wo_lint.py", "--root", str(root), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    findings = json.loads(result.stdout)
    assert any(f["code"] == "WO009" for f in findings)


def test_wo_lint_flags_id_mismatch(tmp_path: Path) -> None:
    root = _bootstrap_repo(tmp_path)
    (root / "_ctx" / "jobs" / "pending" / "WO-0001.yaml").write_text(
        _valid_wo("pending").replace("id: WO-0001", "id: WO-0002"),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/ctx_wo_lint.py", "--root", str(root), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    findings = json.loads(result.stdout)
    assert any(f["code"] == "WO002" for f in findings)


def test_wo_lint_flags_status_folder_mismatch(tmp_path: Path) -> None:
    root = _bootstrap_repo(tmp_path)
    (root / "_ctx" / "jobs" / "pending" / "WO-0001.yaml").write_text(
        _valid_wo("running"),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/ctx_wo_lint.py", "--root", str(root), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    findings = json.loads(result.stdout)
    assert any(f["code"] == "WO004" for f in findings)


def test_wo_lint_flags_missing_dependency_reference(tmp_path: Path) -> None:
    root = _bootstrap_repo(tmp_path)
    (root / "_ctx" / "jobs" / "pending" / "WO-0001.yaml").write_text(
        _valid_wo("pending", dependencies="dependencies:\n  - WO-9999\n"),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/ctx_wo_lint.py", "--root", str(root), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    findings = json.loads(result.stdout)
    assert any(f["code"] == "WO012" for f in findings)


def test_wo_lint_flags_duplicate_id_across_states(tmp_path: Path) -> None:
    root = _bootstrap_repo(tmp_path)
    (root / "_ctx" / "jobs" / "pending" / "WO-0001.yaml").write_text(
        _valid_wo("pending", wo_id="WO-0001"),
        encoding="utf-8",
    )
    (root / "_ctx" / "jobs" / "running" / "WO-0001.yaml").write_text(
        _valid_wo("running", wo_id="WO-0001"),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/ctx_wo_lint.py", "--root", str(root), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    findings = json.loads(result.stdout)
    assert any(f["code"] == "WO003" for f in findings)


def test_wo_lint_accepts_alphanumeric_legacy_id(tmp_path: Path) -> None:
    root = _bootstrap_repo(tmp_path)
    (root / "_ctx" / "jobs" / "pending" / "WO-0018C.yaml").write_text(
        _valid_wo("pending", wo_id="WO-0018C"),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/ctx_wo_lint.py", "--root", str(root), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    findings = json.loads(result.stdout)
    assert findings == []


def test_wo_lint_reports_malformed_backlog_yaml(tmp_path: Path) -> None:
    root = _bootstrap_repo(tmp_path)
    (root / "_ctx" / "backlog" / "backlog.yaml").write_text("epics: [", encoding="utf-8")
    (root / "_ctx" / "jobs" / "pending" / "WO-0001.yaml").write_text(
        _valid_wo("pending"),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/ctx_wo_lint.py", "--root", str(root), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    findings = json.loads(result.stdout)
    assert any(f["code"] == "YAML000" for f in findings)


def test_wo_lint_reports_malformed_dod_yaml(tmp_path: Path) -> None:
    root = _bootstrap_repo(tmp_path)
    (root / "_ctx" / "dod" / "DOD-DEFAULT.yaml").write_text("dod: [", encoding="utf-8")
    (root / "_ctx" / "jobs" / "pending" / "WO-0001.yaml").write_text(
        _valid_wo("pending"),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/ctx_wo_lint.py", "--root", str(root), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    findings = json.loads(result.stdout)
    assert any(f["code"] == "YAML000" for f in findings)
