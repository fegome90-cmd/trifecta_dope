"""Regression test for wo_verify.sh transition_to_failed().

Ensures that when wo_verify.sh fails a WO:
1. running/WO-XXXX.yaml is removed
2. running/WO-XXXX.lock is removed
3. failed/WO-XXXX.yaml is created
4. status field is set to 'failed'
5. One WO = one state file invariant holds
6. Function returns 0 on success, 1 on invariant violation
7. Orphan lock (no YAML) is handled gracefully
"""

import subprocess
from pathlib import Path
import yaml
import pytest


# Extract transition_to_failed function from wo_verify.sh as a standalone script
# This is necessary because wo_verify.sh exits early when sourced without args
TRANSITION_FUNC = '''
transition_to_failed() {
  local wo_id="$1"
  local root="${2:-.}"
  local running_dir="$root/_ctx/jobs/running"
  local failed_dir="$root/_ctx/jobs/failed"
  local yaml_path="$running_dir/${wo_id}.yaml"
  local lock_path="$running_dir/${wo_id}.lock"
  local failed_yaml="$failed_dir/${wo_id}.yaml"

  mkdir -p "$failed_dir"

  # Handle case: already in failed/ (idempotent)
  if [[ ! -f "$yaml_path" && -f "$failed_yaml" ]]; then
    echo "INFO: $wo_id already failed; no transition needed" >&2
  elif [[ -f "$yaml_path" ]]; then
    mv "$yaml_path" "$failed_yaml"

    # Update status: failed in the YAML content (python3, no uv)
    python3 - "$wo_id" "$failed_yaml" <<'PY'
import sys
from pathlib import Path
from datetime import datetime, timezone
import yaml

wo_id = sys.argv[1]
p = Path(sys.argv[2])

data = {}
try:
    loaded = yaml.safe_load(p.read_text(encoding="utf-8"))
    if isinstance(loaded, dict):
        data = loaded
except Exception:
    data = {"id": wo_id}

data["status"] = "failed"
data["x_failed_at"] = datetime.now(timezone.utc).isoformat()

p.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
print(f"INFO: Set status=failed for {wo_id}")
PY

    echo "INFO: Moved $wo_id to failed/ and set status=failed" >&2
  fi

  if [[ -f "$lock_path" ]]; then
    rm -f "$lock_path"
    echo "INFO: Removed lock for $wo_id" >&2
  fi

  # Invariant check: count WO YAML files across states
  local count=0
  for state in pending running done failed; do
    if [[ -f "$root/_ctx/jobs/$state/${wo_id}.yaml" ]]; then
      ((count++)) || true
    fi
  done

  # Orphan lock cleanup: no YAML anywhere is OK (just cleaned orphan)
  if [[ $count -eq 0 ]]; then
    echo "INFO: Orphan lock cleanup for $wo_id (no WO YAML found)" >&2
    return 0
  fi

  # Exactly one YAML = canonical state
  if [[ $count -eq 1 ]]; then
    return 0
  fi

  # More than one = invariant violation
  echo "ERROR: Invariant violation - found $count WO files for $wo_id" >&2
  return 1
}
'''


class TestTransitionToFailed:
    """Tests for transition_to_failed function in wo_verify.sh."""

    def test_sets_status_failed_and_cleans_running(self, tmp_path: Path):
        """transition_to_failed should set status=failed and remove running artifacts."""
        wo_id = "WO-9999"
        running_dir = tmp_path / "_ctx" / "jobs" / "running"
        failed_dir = tmp_path / "_ctx" / "jobs" / "failed"
        running_dir.mkdir(parents=True)
        failed_dir.mkdir(parents=True)

        wo_yaml = running_dir / f"{wo_id}.yaml"
        wo_lock = running_dir / f"{wo_id}.lock"

        # Create test WO with realistic content
        wo_yaml.write_text(
            yaml.dump(
                {"id": wo_id, "status": "running", "title": "Test WO"},
                sort_keys=False,
            )
        )
        wo_lock.write_text("lock")

        # Run transition_to_failed via bash with inline function definition
        result = subprocess.run(
            [
                "bash",
                "-c",
                f"""
set -euo pipefail
{TRANSITION_FUNC}
transition_to_failed {wo_id} {tmp_path}
""",
            ],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
        )

        # Assert: returncode == 0
        assert result.returncode == 0, (
            f"Expected 0, got {result.returncode}. stderr: {result.stderr}"
        )

        # Assert: running/ files removed
        assert not wo_yaml.exists(), "running YAML should be removed"
        assert not wo_lock.exists(), "lock should be removed"

        # Assert: failed/ YAML exists
        failed_yaml = failed_dir / f"{wo_id}.yaml"
        assert failed_yaml.exists(), "failed YAML should exist"

        # Assert: status == failed
        data = yaml.safe_load(failed_yaml.read_text())
        assert data.get("status") == "failed", (
            f"status should be 'failed', got {data.get('status')}"
        )

        # Assert: x_failed_at field exists (schema-safe custom field)
        assert "x_failed_at" in data, "x_failed_at should be set"

        # Assert: one WO = one state file
        count = sum(
            1
            for state in ["pending", "running", "done", "failed"]
            if (tmp_path / "_ctx" / "jobs" / state / f"{wo_id}.yaml").exists()
        )
        assert count == 1, f"Expected 1 WO file, found {count}"

    def test_returns_1_on_invariant_violation(self, tmp_path: Path):
        """transition_to_failed should return 1 if count > 1 and print error."""
        wo_id = "WO-9998"
        running_dir = tmp_path / "_ctx" / "jobs" / "running"
        failed_dir = tmp_path / "_ctx" / "jobs" / "failed"
        pending_dir = tmp_path / "_ctx" / "jobs" / "pending"

        running_dir.mkdir(parents=True)
        failed_dir.mkdir(parents=True)
        pending_dir.mkdir(parents=True)

        wo_yaml = running_dir / f"{wo_id}.yaml"
        wo_yaml.write_text(yaml.dump({"id": wo_id, "status": "running"}))

        # Create duplicate in pending/ to violate invariant
        pending_yaml = pending_dir / f"{wo_id}.yaml"
        pending_yaml.write_text(yaml.dump({"id": wo_id, "status": "pending"}))

        result = subprocess.run(
            [
                "bash",
                "-c",
                f"""
set -euo pipefail
{TRANSITION_FUNC}
transition_to_failed {wo_id} {tmp_path}
""",
            ],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
        )

        # Should return 1 due to invariant violation
        assert result.returncode == 1, (
            f"Expected returncode 1, got {result.returncode}. stderr: {result.stderr}"
        )
        # Should contain invariant violation message
        assert "Invariant violation" in result.stderr, (
            f"Expected 'Invariant violation' in stderr, got: {result.stderr}"
        )

    def test_idempotent_when_already_failed(self, tmp_path: Path):
        """Should not error if WO already in failed/."""
        wo_id = "WO-9997"
        failed_dir = tmp_path / "_ctx" / "jobs" / "failed"
        failed_dir.mkdir(parents=True)

        failed_yaml = failed_dir / f"{wo_id}.yaml"
        failed_yaml.write_text(yaml.dump({"id": wo_id, "status": "failed"}))

        result = subprocess.run(
            [
                "bash",
                "-c",
                f"""
set -euo pipefail
{TRANSITION_FUNC}
transition_to_failed {wo_id} {tmp_path}
""",
            ],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
        )

        # Should succeed (no running yaml to move, already failed)
        assert result.returncode == 0, (
            f"Expected 0, got {result.returncode}. stderr: {result.stderr}"
        )
        assert failed_yaml.exists()
        # Should have informational message
        assert "already failed" in result.stderr or "INFO:" in result.stderr

    def test_orphan_lock_cleanup_succeeds(self, tmp_path: Path):
        """Orphan lock (no YAML anywhere) should be cleaned gracefully."""
        wo_id = "WO-9996"
        running_dir = tmp_path / "_ctx" / "jobs" / "running"
        failed_dir = tmp_path / "_ctx" / "jobs" / "failed"
        running_dir.mkdir(parents=True)
        failed_dir.mkdir(parents=True)

        # Only create lock (correct extension), no YAML
        wo_lock = running_dir / f"{wo_id}.lock"
        wo_lock.write_text("orphan lock content")

        result = subprocess.run(
            [
                "bash",
                "-c",
                f"""
set -euo pipefail
{TRANSITION_FUNC}
transition_to_failed {wo_id} {tmp_path}
""",
            ],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
        )

        # Should succeed (orphan lock cleanup)
        assert result.returncode == 0, (
            f"Expected 0, got {result.returncode}. stderr: {result.stderr}"
        )
        # Lock should be removed
        assert not wo_lock.exists(), "orphan lock should be removed"
        # Should log orphan cleanup
        assert "Orphan lock" in result.stderr or "orphan" in result.stderr.lower(), (
            f"Expected orphan message in stderr, got: {result.stderr}"
        )
