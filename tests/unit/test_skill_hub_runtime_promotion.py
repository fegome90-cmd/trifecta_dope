from __future__ import annotations

import hashlib
import json
import os
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


def test_wrapper_chain_uses_only_governed_runtime_dependencies() -> None:
    text = WRAPPER.read_text()

    assert "skill_hub_info_card.py" not in text
    assert 'python3 "$TRIFECTA_ROOT/scripts/skill-hub-cards"' not in text
    assert 'CARDS_HELPER="$SCRIPT_DIR/skill-hub-cards"' in text
    assert 'python3 "$CARDS_HELPER"' in text


def test_promote_generates_targets_and_receipt(tmp_path: Path) -> None:
    runtime_bin = tmp_path / "bin"
    receipt = tmp_path / "receipts" / "skill-hub-runtime.json"

    result = run_runtime(
        "promote",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(REPO_ROOT),
    )

    assert result.returncode == 0, result.stderr
    assert (runtime_bin / "skill-hub").exists()
    assert receipt.exists()

    data = json.loads(receipt.read_text())
    artifacts = {item["name"]: item for item in data["artifacts"]}

    assert data["schema_version"] == 1
    assert data["tool"] == "skill-hub-runtime"
    assert data["repo_root"] == str(REPO_ROOT.resolve())
    assert data["repo_head"]
    assert set(artifacts) == {"skill-hub", "skill-hub-cards"}
    assert artifacts["skill-hub"]["source"] == str(WRAPPER)
    assert artifacts["skill-hub"]["target"] == str(runtime_bin / "skill-hub")
    assert artifacts["skill-hub-cards"]["source"] == str(CARDS)
    assert artifacts["skill-hub-cards"]["target"] == str(runtime_bin / "skill-hub-cards")
    assert artifacts["skill-hub-cards"]["kind"] == "promoted"
    assert artifacts["skill-hub"]["sha256"] == sha256(runtime_bin / "skill-hub")
    assert artifacts["skill-hub-cards"]["sha256"] == sha256(runtime_bin / "skill-hub-cards")

    wrapper_mode = (runtime_bin / "skill-hub").stat().st_mode
    assert wrapper_mode & stat.S_IXUSR
    cards_mode = (runtime_bin / "skill-hub-cards").stat().st_mode
    assert cards_mode & stat.S_IXUSR


def test_verify_fails_closed_when_promoted_target_drifts(tmp_path: Path) -> None:
    runtime_bin = tmp_path / "bin"
    receipt = tmp_path / "receipts" / "skill-hub-runtime.json"

    promote = run_runtime(
        "promote",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(REPO_ROOT),
    )
    assert promote.returncode == 0, promote.stderr

    drifted = runtime_bin / "skill-hub"
    drifted.write_text(drifted.read_text() + "\n# drift\n")

    verify = run_runtime(
        "verify",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(REPO_ROOT),
    )

    assert verify.returncode != 0
    assert "hash mismatch" in (verify.stderr + verify.stdout).lower()


def test_verify_fails_closed_when_promoted_cards_target_drifts(tmp_path: Path) -> None:
    runtime_bin = tmp_path / "bin"
    receipt = tmp_path / "receipts" / "skill-hub-runtime.json"

    promote = run_runtime(
        "promote",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(REPO_ROOT),
    )
    assert promote.returncode == 0, promote.stderr

    drifted = runtime_bin / "skill-hub-cards"
    drifted.write_text(drifted.read_text() + "\n# drift\n")

    verify = run_runtime(
        "verify",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(REPO_ROOT),
    )

    assert verify.returncode != 0
    assert "hash mismatch" in (verify.stderr + verify.stdout).lower()


def test_verify_fails_closed_when_receipt_metadata_mismatches(tmp_path: Path) -> None:
    runtime_bin = tmp_path / "bin"
    receipt = tmp_path / "receipts" / "skill-hub-runtime.json"

    promote = run_runtime(
        "promote",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(REPO_ROOT),
    )
    assert promote.returncode == 0, promote.stderr

    data = json.loads(receipt.read_text())
    data["repo_root"] = "/tmp/not-the-repo"
    receipt.write_text(json.dumps(data))

    verify = run_runtime(
        "verify",
        "--runtime-bin-dir",
        str(runtime_bin),
        "--receipt-path",
        str(receipt),
        "--repo-root",
        str(REPO_ROOT),
    )

    assert verify.returncode != 0
    assert "repo_root mismatch" in (verify.stderr + verify.stdout).lower()
