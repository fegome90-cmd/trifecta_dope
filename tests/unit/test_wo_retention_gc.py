"""Unit tests for WO Evidence Retention GC script.

Tests cover:
- Dry-run mode (no deletion)
- Retention days respect
- Active WO protection (running/pending)
- Incomplete decision protection
- decision.md never deleted
"""

from __future__ import annotations

import importlib.util
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

# Load the script module dynamically
import sys as _sys

_SCRIPT_PATH = Path(__file__).parent.parent.parent / "scripts" / "wo_retention_gc.py"
_spec = importlib.util.spec_from_file_location("wo_retention_gc", _SCRIPT_PATH)
assert _spec is not None, f"Could not load spec from {_SCRIPT_PATH}"
wo_retention_gc = importlib.util.module_from_spec(_spec)
_sys.modules["wo_retention_gc"] = wo_retention_gc  # Register before exec for dataclasses
assert _spec.loader is not None, "Spec has no loader"
_spec.loader.exec_module(wo_retention_gc)

# Import functions from the loaded module
ACTIVE_STATES = wo_retention_gc.ACTIVE_STATES
ELIGIBLE_PATTERNS = wo_retention_gc.ELIGIBLE_PATTERNS
PROTECTED_FILES = wo_retention_gc.PROTECTED_FILES
RetentionReport = wo_retention_gc.RetentionReport
get_active_wo_ids = wo_retention_gc.get_active_wo_ids
get_file_age_days = wo_retention_gc.get_file_age_days
is_decision_incomplete = wo_retention_gc.is_decision_incomplete
is_eligible_for_cleanup = wo_retention_gc.is_eligible_for_cleanup
run_retention_gc = wo_retention_gc.run_retention_gc


@pytest.fixture
def temp_repo() -> Generator[Path, None, None]:
    """Create a temporary repository structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)

        # Create directory structure
        handoff_dir = repo_root / "_ctx" / "handoff"
        jobs_dir = repo_root / "_ctx" / "jobs"

        for state in ["pending", "running", "done", "failed"]:
            (jobs_dir / state).mkdir(parents=True)

        handoff_dir.mkdir(parents=True)

        # Initialize git repo
        os.system(f"cd {repo_root} && git init --quiet")

        yield repo_root


def create_old_file(path: Path, content: str = "test", days_old: int = 100) -> None:
    """Create a file with a specific age."""
    path.write_text(content)

    # Set mtime to days_old days ago
    old_time = datetime.now(timezone.utc) - timedelta(days=days_old)

    os.utime(path, (old_time.timestamp(), old_time.timestamp()))


def create_recent_file(path: Path, content: str = "test") -> None:
    """Create a recent file (today)."""
    path.write_text(content)


class TestGetActiveWoIds:
    """Tests for get_active_wo_ids function."""

    def test_no_active_wos(self, temp_repo: Path) -> None:
        """Should return empty set when no active WOs exist."""
        active_ids = get_active_wo_ids(temp_repo)
        assert active_ids == set()

    def test_running_wo_detected(self, temp_repo: Path) -> None:
        """Should detect WO in running state."""
        # Create a running WO
        running_yaml = temp_repo / "_ctx" / "jobs" / "running" / "WO-0001.yaml"
        running_yaml.write_text("wo_id: WO-0001\nstate: running\n")

        active_ids = get_active_wo_ids(temp_repo)
        assert active_ids == {"WO-0001"}

    def test_pending_wo_detected(self, temp_repo: Path) -> None:
        """Should detect WO in pending state."""
        pending_yaml = temp_repo / "_ctx" / "jobs" / "pending" / "WO-0002.yaml"
        pending_yaml.write_text("wo_id: WO-0002\nstate: pending\n")

        active_ids = get_active_wo_ids(temp_repo)
        assert active_ids == {"WO-0002"}

    def test_done_wo_not_detected(self, temp_repo: Path) -> None:
        """Should NOT detect WO in done state."""
        done_yaml = temp_repo / "_ctx" / "jobs" / "done" / "WO-0003.yaml"
        done_yaml.write_text("wo_id: WO-0003\nstate: done\n")

        active_ids = get_active_wo_ids(temp_repo)
        assert active_ids == set()

    def test_multiple_active_wos(self, temp_repo: Path) -> None:
        """Should detect multiple active WOs."""
        for state, wo_id in [("running", "WO-0001"), ("pending", "WO-0002")]:
            yaml_path = temp_repo / "_ctx" / "jobs" / state / f"{wo_id}.yaml"
            yaml_path.write_text(f"wo_id: {wo_id}\nstate: {state}\n")

        active_ids = get_active_wo_ids(temp_repo)
        assert active_ids == {"WO-0001", "WO-0002"}


class TestIsDecisionIncomplete:
    """Tests for is_decision_incomplete function."""

    def test_no_decision_file(self, temp_repo: Path) -> None:
        """Should return False when no decision.md exists."""
        wo_dir = temp_repo / "_ctx" / "handoff" / "WO-0001"
        wo_dir.mkdir(parents=True)

        assert is_decision_incomplete(wo_dir) is False

    def test_complete_decision(self, temp_repo: Path) -> None:
        """Should return False for complete decision."""
        wo_dir = temp_repo / "_ctx" / "handoff" / "WO-0001"
        wo_dir.mkdir(parents=True)

        decision = wo_dir / "decision.md"
        decision.write_text("""# Decision for WO-0001

| Field | Value |
|-------|-------|
| **Status** | COMPLETE |

## Decision
[x] APPLY

### Justification
Applied successfully.
""")

        assert is_decision_incomplete(wo_dir) is False

    def test_incomplete_decision_action_required(self, temp_repo: Path) -> None:
        """Should return True for ACTION_REQUIRED status."""
        wo_dir = temp_repo / "_ctx" / "handoff" / "WO-0001"
        wo_dir.mkdir(parents=True)

        decision = wo_dir / "decision.md"
        decision.write_text("""# Decision for WO-0001

| Field | Value |
|-------|-------|
| **Status** | ACTION_REQUIRED |

## Decision
[ ] APPLY | [ ] DISCARD | [ ] MANUAL REVIEW
""")

        assert is_decision_incomplete(wo_dir) is True

    def test_incomplete_decision_unchecked(self, temp_repo: Path) -> None:
        """Should return True for unchecked decision boxes."""
        wo_dir = temp_repo / "_ctx" / "handoff" / "WO-0001"
        wo_dir.mkdir(parents=True)

        decision = wo_dir / "decision.md"
        decision.write_text("""# Decision for WO-0001

## Decision
[ ] APPLY
[ ] DISCARD
[ ] MANUAL REVIEW
""")

        assert is_decision_incomplete(wo_dir) is True


class TestIsEligibleForCleanup:
    """Tests for is_eligible_for_cleanup function."""

    def test_hashed_patch_eligible(self) -> None:
        """Hashed patch files should be eligible."""
        path = Path("_ctx/handoff/WO-0001/dirty.abc123.patch")
        assert is_eligible_for_cleanup(path) is True

    def test_checksum_file_eligible(self) -> None:
        """Checksum files should be eligible."""
        path = Path("_ctx/handoff/WO-0001/dirty.patch.sha256")
        assert is_eligible_for_cleanup(path) is True

    def test_symlink_patch_not_eligible(self) -> None:
        """The dirty.patch symlink should NOT be eligible."""
        path = Path("_ctx/handoff/WO-0001/dirty.patch")
        assert is_eligible_for_cleanup(path) is False

    def test_decision_md_not_eligible(self) -> None:
        """decision.md should NOT be eligible."""
        path = Path("_ctx/handoff/WO-0001/decision.md")
        assert is_eligible_for_cleanup(path) is False

    def test_handoff_md_not_eligible(self) -> None:
        """handoff.md should NOT be eligible."""
        path = Path("_ctx/handoff/WO-0001/handoff.md")
        assert is_eligible_for_cleanup(path) is False

    def test_verdict_json_not_eligible(self) -> None:
        """verdict.json should NOT be eligible."""
        path = Path("_ctx/handoff/WO-0001/verdict.json")
        assert is_eligible_for_cleanup(path) is False

    def test_diff_patch_not_eligible(self) -> None:
        """diff.patch should NOT be eligible."""
        path = Path("_ctx/handoff/WO-0001/diff.patch")
        assert is_eligible_for_cleanup(path) is False


class TestGetFileAgeDays:
    """Tests for get_file_age_days function."""

    def test_recent_file(self, temp_repo: Path) -> None:
        """Recent file should have age 0."""
        file_path = temp_repo / "recent.txt"
        create_recent_file(file_path)

        age = get_file_age_days(file_path)
        assert age == 0

    def test_old_file(self, temp_repo: Path) -> None:
        """Old file should have correct age."""
        file_path = temp_repo / "old.txt"
        create_old_file(file_path, days_old=100)

        age = get_file_age_days(file_path)
        assert age >= 99  # Allow for some timing variance


class TestRunRetentionGc:
    """Tests for run_retention_gc function."""

    def test_dry_run_no_deletion(self, temp_repo: Path) -> None:
        """Dry-run should not delete any files."""
        wo_dir = temp_repo / "_ctx" / "handoff" / "WO-0001"
        wo_dir.mkdir(parents=True)

        # Create an old hashed patch file
        old_patch = wo_dir / "dirty.abc123.patch"
        create_old_file(old_patch, days_old=100)

        # Run dry-run
        report = run_retention_gc(
            repo_root=temp_repo,
            dry_run=True,
            retention_days=90,
        )

        # File should still exist
        assert old_patch.exists()
        assert report.dry_run is True
        assert report.files_eligible == 1
        assert report.files_deleted == 0

    def test_apply_deletes_old_files(self, temp_repo: Path) -> None:
        """Apply mode should delete old eligible files."""
        wo_dir = temp_repo / "_ctx" / "handoff" / "WO-0001"
        wo_dir.mkdir(parents=True)

        # Create an old hashed patch file
        old_patch = wo_dir / "dirty.abc123.patch"
        create_old_file(old_patch, days_old=100)

        # Run apply
        report = run_retention_gc(
            repo_root=temp_repo,
            dry_run=False,
            retention_days=90,
        )

        # File should be deleted
        assert not old_patch.exists()
        assert report.dry_run is False
        assert report.files_eligible == 1
        assert report.files_deleted == 1

    def test_respects_retention_days(self, temp_repo: Path) -> None:
        """Files younger than retention_days should not be deleted."""
        wo_dir = temp_repo / "_ctx" / "handoff" / "WO-0001"
        wo_dir.mkdir(parents=True)

        # Create a file that's 30 days old
        recent_patch = wo_dir / "dirty.abc123.patch"
        create_old_file(recent_patch, days_old=30)

        # Run with 90-day retention
        report = run_retention_gc(
            repo_root=temp_repo,
            dry_run=False,
            retention_days=90,
        )

        # File should NOT be deleted (younger than 90 days)
        assert recent_patch.exists()
        assert report.files_eligible == 0
        assert report.files_deleted == 0

    def test_protects_active_wo(self, temp_repo: Path) -> None:
        """Files for active WOs should not be deleted."""
        # Create an active WO
        running_yaml = temp_repo / "_ctx" / "jobs" / "running" / "WO-0001.yaml"
        running_yaml.write_text("wo_id: WO-0001\nstate: running\n")

        wo_dir = temp_repo / "_ctx" / "handoff" / "WO-0001"
        wo_dir.mkdir(parents=True)

        # Create an old hashed patch file
        old_patch = wo_dir / "dirty.abc123.patch"
        create_old_file(old_patch, days_old=100)

        # Run apply
        report = run_retention_gc(
            repo_root=temp_repo,
            dry_run=False,
            retention_days=90,
        )

        # File should NOT be deleted (WO is active)
        assert old_patch.exists()
        assert report.files_protected_active == 1
        assert "WO-0001" in report.protected_wos

    def test_protects_incomplete_decision(self, temp_repo: Path) -> None:
        """Files for WOs with incomplete decisions should not be deleted."""
        wo_dir = temp_repo / "_ctx" / "handoff" / "WO-0001"
        wo_dir.mkdir(parents=True)

        # Create an incomplete decision
        decision = wo_dir / "decision.md"
        decision.write_text("Status: ACTION_REQUIRED\n[ ] APPLY")

        # Create an old hashed patch file
        old_patch = wo_dir / "dirty.abc123.patch"
        create_old_file(old_patch, days_old=100)

        # Run apply
        report = run_retention_gc(
            repo_root=temp_repo,
            dry_run=False,
            retention_days=90,
        )

        # File should NOT be deleted (decision incomplete)
        assert old_patch.exists()
        assert report.files_protected_incomplete == 1

    def test_never_deletes_decision_md(self, temp_repo: Path) -> None:
        """decision.md should never be deleted even if old."""
        wo_dir = temp_repo / "_ctx" / "handoff" / "WO-0001"
        wo_dir.mkdir(parents=True)

        # Create an old decision.md
        decision = wo_dir / "decision.md"
        create_old_file(decision, content="# Decision\n[x] COMPLETE", days_old=200)

        # Run apply with short retention
        report = run_retention_gc(
            repo_root=temp_repo,
            dry_run=False,
            retention_days=30,
        )

        # decision.md should still exist
        assert decision.exists()
        assert report.files_deleted == 0

    def test_json_report(self, temp_repo: Path) -> None:
        """Should write JSON report when path provided."""
        wo_dir = temp_repo / "_ctx" / "handoff" / "WO-0001"
        wo_dir.mkdir(parents=True)

        # Create an old hashed patch file
        old_patch = wo_dir / "dirty.abc123.patch"
        create_old_file(old_patch, days_old=100)

        json_path = temp_repo / "data" / "report.json"

        # Run with JSON output
        _ = run_retention_gc(
            repo_root=temp_repo,
            dry_run=True,
            retention_days=90,
            json_path=str(json_path),
        )

        # JSON file should exist
        assert json_path.exists()

        # Should be valid JSON
        data = json.loads(json_path.read_text())
        assert data["dry_run"] is True
        assert data["retention_days"] == 90
        assert "summary" in data

    def test_multiple_files(self, temp_repo: Path) -> None:
        """Should handle multiple files correctly."""
        wo_dir = temp_repo / "_ctx" / "handoff" / "WO-0001"
        wo_dir.mkdir(parents=True)

        # Create multiple files
        old_patch1 = wo_dir / "dirty.abc123.patch"
        old_patch2 = wo_dir / "dirty.def456.patch"
        old_checksum = wo_dir / "dirty.patch.sha256"
        recent_patch = wo_dir / "dirty.recent.patch"

        create_old_file(old_patch1, days_old=100)
        create_old_file(old_patch2, days_old=100)
        create_old_file(old_checksum, days_old=100)
        create_old_file(recent_patch, days_old=30)

        # Run apply
        report = run_retention_gc(
            repo_root=temp_repo,
            dry_run=False,
            retention_days=90,
        )

        # Old files should be deleted, recent should remain
        assert not old_patch1.exists()
        assert not old_patch2.exists()
        assert not old_checksum.exists()
        assert recent_patch.exists()
        assert report.files_deleted == 3


class TestProtectedFiles:
    """Tests to ensure protected files are never deleted."""

    @pytest.mark.parametrize("filename", PROTECTED_FILES)
    def test_protected_file_not_deleted(self, temp_repo: Path, filename: str) -> None:
        """Protected files should never be deleted."""
        wo_dir = temp_repo / "_ctx" / "handoff" / "WO-0001"
        wo_dir.mkdir(parents=True)

        protected_file = wo_dir / filename
        create_old_file(protected_file, days_old=200)

        # Run apply with short retention
        report = run_retention_gc(
            repo_root=temp_repo,
            dry_run=False,
            retention_days=30,
        )

        # Protected file should still exist
        assert protected_file.exists()
        assert report.files_deleted == 0


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_handoff_dir(self, temp_repo: Path) -> None:
        """Should handle empty handoff directory."""
        report = run_retention_gc(
            repo_root=temp_repo,
            dry_run=True,
            retention_days=90,
        )

        assert report.files_scanned == 0
        assert report.files_eligible == 0

    def test_no_handoff_dir(self, temp_repo: Path) -> None:
        """Should handle missing handoff directory."""
        # Remove handoff dir
        handoff_dir = temp_repo / "_ctx" / "handoff"
        if handoff_dir.exists():
            handoff_dir.rmdir()

        report = run_retention_gc(
            repo_root=temp_repo,
            dry_run=True,
            retention_days=90,
        )

        assert report.files_scanned == 0

    def test_non_wo_directory_ignored(self, temp_repo: Path) -> None:
        """Non-WO directories should be ignored."""
        handoff_dir = temp_repo / "_ctx" / "handoff"

        # Create a non-WO directory
        other_dir = handoff_dir / "other-dir"
        other_dir.mkdir(parents=True)

        old_file = other_dir / "dirty.abc123.patch"
        create_old_file(old_file, days_old=100)

        _ = run_retention_gc(
            repo_root=temp_repo,
            dry_run=False,
            retention_days=90,
        )

        # File should still exist (directory not a WO)
        assert old_file.exists()
