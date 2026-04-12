from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
UTILITY = REPO_ROOT / "scripts" / "skill-hub-runtime"
WRAPPER = REPO_ROOT / "scripts" / "skill-hub"
CARDS = REPO_ROOT / "scripts" / "skill-hub-cards"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_runtime(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, str(UTILITY), *args],
        text=True,
        capture_output=True,
        env=merged_env,
        check=False,
    )


def clone_governed_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    scripts_dir = repo_root / "scripts"
    scripts_dir.mkdir(parents=True)
    shutil.copy2(WRAPPER, scripts_dir / "skill-hub")
    shutil.copy2(CARDS, scripts_dir / "skill-hub-cards")
    return repo_root


def test_wrapper_chain_uses_only_governed_runtime_dependencies() -> None:
    text = WRAPPER.read_text()

    assert "skill_hub_info_card.py" not in text
    assert 'python3 "$TRIFECTA_ROOT/scripts/skill-hub-cards"' not in text
    assert 'CARDS_HELPER="$SCRIPT_DIR/skill-hub-cards"' in text
    assert 'python3 "$CARDS_HELPER"' in text


def test_promote_generates_targets_and_governed_receipt_schema_v2(tmp_path: Path) -> None:
    repo_root = clone_governed_repo(tmp_path)
    runtime_bin = tmp_path / "bin"
    receipt = tmp_path / "receipts" / "skill-hub-runtime.json"

    result = run_runtime(
        "promote",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(repo_root),
    )

    assert result.returncode == 0, result.stderr
    assert (runtime_bin / "skill-hub").exists()
    assert (runtime_bin / "skill-hub-cards").exists()
    assert receipt.exists()

    data = json.loads(receipt.read_text())
    artifacts = {item["name"]: item for item in data["artifacts"]}

    assert set(data) == {"schema_version", "tool", "promoted_at", "artifacts"}
    assert data["schema_version"] == 2
    assert data["tool"] == "skill-hub-runtime"
    assert set(artifacts) == {"skill-hub", "skill-hub-cards"}

    assert artifacts["skill-hub"] == {
        "name": "skill-hub",
        "kind": "promoted",
        "source_rel": "scripts/skill-hub",
        "target_name": "skill-hub",
        "sha256": sha256(repo_root / "scripts" / "skill-hub"),
    }
    assert artifacts["skill-hub-cards"] == {
        "name": "skill-hub-cards",
        "kind": "promoted",
        "source_rel": "scripts/skill-hub-cards",
        "target_name": "skill-hub-cards",
        "sha256": sha256(repo_root / "scripts" / "skill-hub-cards"),
    }

    assert sha256(runtime_bin / "skill-hub") == artifacts["skill-hub"]["sha256"]
    assert sha256(runtime_bin / "skill-hub-cards") == artifacts["skill-hub-cards"]["sha256"]

    wrapper_mode = (runtime_bin / "skill-hub").stat().st_mode
    assert wrapper_mode & stat.S_IXUSR
    cards_mode = (runtime_bin / "skill-hub-cards").stat().st_mode
    assert cards_mode & stat.S_IXUSR


def test_verify_fails_closed_when_governed_source_drifts(tmp_path: Path) -> None:
    repo_root = clone_governed_repo(tmp_path)
    runtime_bin = tmp_path / "bin"
    receipt = tmp_path / "receipts" / "skill-hub-runtime.json"

    promote = run_runtime(
        "promote",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(repo_root),
    )
    assert promote.returncode == 0, promote.stderr

    drifted = repo_root / "scripts" / "skill-hub"
    drifted.write_text(drifted.read_text() + "\n# governed source drift\n")

    verify = run_runtime(
        "verify",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(repo_root),
    )

    assert verify.returncode != 0
    assert "source hash mismatch for skill-hub" in (verify.stderr + verify.stdout).lower()


def test_verify_fails_closed_when_promoted_target_drifts(tmp_path: Path) -> None:
    repo_root = clone_governed_repo(tmp_path)
    runtime_bin = tmp_path / "bin"
    receipt = tmp_path / "receipts" / "skill-hub-runtime.json"

    promote = run_runtime(
        "promote",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(repo_root),
    )
    assert promote.returncode == 0, promote.stderr

    drifted = runtime_bin / "skill-hub"
    drifted.write_text(drifted.read_text() + "\n# promoted target drift\n")

    verify = run_runtime(
        "verify",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(repo_root),
    )

    assert verify.returncode != 0
    assert "hash mismatch for skill-hub" in (verify.stderr + verify.stdout).lower()


def test_verify_fails_closed_when_receipt_set_mismatches_governed_contract(tmp_path: Path) -> None:
    repo_root = clone_governed_repo(tmp_path)
    runtime_bin = tmp_path / "bin"
    receipt = tmp_path / "receipts" / "skill-hub-runtime.json"

    promote = run_runtime(
        "promote",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(repo_root),
    )
    assert promote.returncode == 0, promote.stderr

    data = json.loads(receipt.read_text())
    data["artifacts"] = [item for item in data["artifacts"] if item["name"] != "skill-hub-cards"]
    receipt.write_text(json.dumps(data))

    verify = run_runtime(
        "verify",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(repo_root),
    )

    assert verify.returncode != 0
    assert "artifact set mismatch" in (verify.stderr + verify.stdout).lower()


def test_verify_fails_closed_when_receipt_includes_extra_artifact(tmp_path: Path) -> None:
    repo_root = clone_governed_repo(tmp_path)
    runtime_bin = tmp_path / "bin"
    receipt = tmp_path / "receipts" / "skill-hub-runtime.json"

    promote = run_runtime(
        "promote",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(repo_root),
    )
    assert promote.returncode == 0, promote.stderr

    data = json.loads(receipt.read_text())
    data["artifacts"].append(
        {
            "name": "unexpected-helper",
            "kind": "promoted",
            "source_rel": "scripts/unexpected-helper",
            "target_name": "unexpected-helper",
            "sha256": "deadbeef",
        }
    )
    receipt.write_text(json.dumps(data))

    verify = run_runtime(
        "verify",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(repo_root),
    )

    assert verify.returncode != 0
    assert "artifact set mismatch" in (verify.stderr + verify.stdout).lower()


def test_verify_fails_closed_when_direct_runtime_dependency_outside_set_reappears(tmp_path: Path) -> None:
    repo_root = clone_governed_repo(tmp_path)
    runtime_bin = tmp_path / "bin"
    receipt = tmp_path / "receipts" / "skill-hub-runtime.json"

    promote = run_runtime(
        "promote",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(repo_root),
    )
    assert promote.returncode == 0, promote.stderr

    wrapper = repo_root / "scripts" / "skill-hub"
    wrapper.write_text(wrapper.read_text() + '\npython3 "$HOME/.local/bin/skill_hub_info_card.py"\n')

    verify = run_runtime(
        "verify",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(repo_root),
    )

    assert verify.returncode != 0
    assert "wrapper direct runtime dependency set mismatch" in (verify.stderr + verify.stdout).lower()


def test_verify_fails_closed_when_runtime_dependency_invariant_uses_non_adjacent_path(tmp_path: Path) -> None:
    repo_root = clone_governed_repo(tmp_path)
    runtime_bin = tmp_path / "bin"
    receipt = tmp_path / "receipts" / "skill-hub-runtime.json"

    promote = run_runtime(
        "promote",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(repo_root),
    )
    assert promote.returncode == 0, promote.stderr

    wrapper = repo_root / "scripts" / "skill-hub"
    wrapper.write_text(
        wrapper.read_text().replace('CARDS_HELPER="$SCRIPT_DIR/skill-hub-cards"', 'CARDS_HELPER="$TRIFECTA_ROOT/scripts/skill-hub-cards"')
    )

    verify = run_runtime(
        "verify",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(repo_root),
    )

    assert verify.returncode != 0
    assert "wrapper runtime dependency invariant mismatch for skill-hub-cards" in (
        verify.stderr + verify.stdout
    ).lower()


def test_verify_fails_closed_when_receipt_artifact_entry_is_malformed(tmp_path: Path) -> None:
    repo_root = clone_governed_repo(tmp_path)
    runtime_bin = tmp_path / "bin"
    receipt = tmp_path / "receipts" / "skill-hub-runtime.json"

    promote = run_runtime(
        "promote",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(repo_root),
    )
    assert promote.returncode == 0, promote.stderr

    data = json.loads(receipt.read_text())
    data["artifacts"] = ["broken"]
    receipt.write_text(json.dumps(data))

    verify = run_runtime(
        "verify",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(repo_root),
    )

    assert verify.returncode != 0
    assert "receipt artifact entry malformed at index 0" in (verify.stderr + verify.stdout).lower()


def test_promote_fails_closed_when_governed_wrapper_is_missing(tmp_path: Path) -> None:
    repo_root = clone_governed_repo(tmp_path)
    runtime_bin = tmp_path / "bin"
    receipt = tmp_path / "receipts" / "skill-hub-runtime.json"

    (repo_root / "scripts" / "skill-hub").unlink()

    promote = run_runtime(
        "promote",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(repo_root),
    )

    assert promote.returncode != 0
    assert "missing governed wrapper" in (promote.stderr + promote.stdout).lower()


def test_verify_does_not_fail_for_out_of_scope_document_churn(tmp_path: Path) -> None:
    repo_root = clone_governed_repo(tmp_path)
    runtime_bin = tmp_path / "bin"
    receipt = tmp_path / "receipts" / "skill-hub-runtime.json"

    promote = run_runtime(
        "promote",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(repo_root),
    )
    assert promote.returncode == 0, promote.stderr

    docs_dir = repo_root / "docs"
    docs_dir.mkdir(parents=True)
    (docs_dir / "note.md").write_text("# documentary churn outside SH-003 scope\n")

    verify = run_runtime(
        "verify",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(repo_root),
    )

    assert verify.returncode == 0, verify.stderr
    assert "verification ok" in verify.stdout.lower()
