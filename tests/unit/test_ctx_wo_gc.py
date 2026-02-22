"""
Unit tests for ctx_wo_gc.py - WO Garbage Collection Script

Tests cover:
- Zombie detection
- Ghost detection
- Dirty worktree handling (no force by default)
- Dry-run mode (no mutations)
- Apply mode (mutations for clean worktrees)
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# Import the module under test
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from ctx_wo_gc import (
    GCReport,
    WorktreeInfo,
    check_worktree_dirty,
    classify_worktrees,
    get_wo_state,
    get_worktrees,
    remove_worktree,
    run_gc,
)


class TestWorktreeInfo:
    """Tests for WorktreeInfo dataclass."""

    def test_worktree_info_creation(self):
        """Test basic WorktreeInfo creation."""
        wt = WorktreeInfo(
            path="/path/to/.worktrees/WO-0001",
            head="abc123",
            branch="feat/wo-WO-0001",
            wo_id="WO-0001",
        )
        assert wt.wo_id == "WO-0001"
        assert wt.is_dirty is False
        assert wt.wo_state is None


class TestGetWoState:
    """Tests for get_wo_state function."""

    def test_get_wo_state_pending(self, tmp_path):
        """Test detecting WO in pending state."""
        jobs_dir = tmp_path / "_ctx" / "jobs"
        pending_dir = jobs_dir / "pending"
        pending_dir.mkdir(parents=True)
        (pending_dir / "WO-0001.yaml").write_text("id: WO-0001")

        state = get_wo_state(tmp_path, "WO-0001")
        assert state == "pending"

    def test_get_wo_state_running(self, tmp_path):
        """Test detecting WO in running state."""
        jobs_dir = tmp_path / "_ctx" / "jobs"
        running_dir = jobs_dir / "running"
        running_dir.mkdir(parents=True)
        (running_dir / "WO-0002.yaml").write_text("id: WO-0002")

        state = get_wo_state(tmp_path, "WO-0002")
        assert state == "running"

    def test_get_wo_state_done(self, tmp_path):
        """Test detecting WO in done state."""
        jobs_dir = tmp_path / "_ctx" / "jobs"
        done_dir = jobs_dir / "done"
        done_dir.mkdir(parents=True)
        (done_dir / "WO-0003.yaml").write_text("id: WO-0003")

        state = get_wo_state(tmp_path, "WO-0003")
        assert state == "done"

    def test_get_wo_state_not_found(self, tmp_path):
        """Test WO not found in any state."""
        state = get_wo_state(tmp_path, "WO-9999")
        assert state is None


class TestCheckWorktreeDirty:
    """Tests for check_worktree_dirty function."""

    def test_check_clean_worktree(self, tmp_path):
        """Test clean worktree detection."""
        wt_path = tmp_path / "worktree"
        wt_path.mkdir()

        # Mock git status to return empty
        with patch("ctx_wo_gc.run_command") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            result = check_worktree_dirty(str(wt_path))
            assert result is False

    def test_check_dirty_worktree(self, tmp_path):
        """Test dirty worktree detection."""
        wt_path = tmp_path / "worktree"
        wt_path.mkdir()

        # Mock git status to return changes
        with patch("ctx_wo_gc.run_command") as mock_run:
            mock_run.return_value = MagicMock(stdout="M file.txt\n", returncode=0)
            result = check_worktree_dirty(str(wt_path))
            assert result is True


class TestClassifyWorktrees:
    """Tests for classify_worktrees function."""

    def test_classify_zombie(self, tmp_path):
        """Test zombie detection (WO done but worktree exists)."""
        jobs_dir = tmp_path / "_ctx" / "jobs"
        done_dir = jobs_dir / "done"
        done_dir.mkdir(parents=True)
        (done_dir / "WO-0001.yaml").write_text("id: WO-0001")

        worktrees = [
            WorktreeInfo(
                path="/path/.worktrees/WO-0001",
                head="abc",
                branch="feat/wo-WO-0001",
                wo_id="WO-0001",
            )
        ]

        with patch("ctx_wo_gc.check_worktree_dirty", return_value=False):
            zombies, ghosts = classify_worktrees(tmp_path, worktrees)

        assert len(zombies) == 1
        assert len(ghosts) == 0
        assert zombies[0].wo_state == "done"

    def test_classify_ghost(self, tmp_path):
        """Test ghost detection (worktree without WO YAML)."""
        worktrees = [
            WorktreeInfo(
                path="/path/.worktrees/WO-0002",
                head="abc",
                branch="feat/wo-WO-0002",
                wo_id="WO-0002",
            )
        ]

        with patch("ctx_wo_gc.check_worktree_dirty", return_value=False):
            zombies, ghosts = classify_worktrees(tmp_path, worktrees)

        assert len(zombies) == 0
        assert len(ghosts) == 1
        assert ghosts[0].wo_state is None

    def test_classify_active_running(self, tmp_path):
        """Test active worktree (WO running)."""
        jobs_dir = tmp_path / "_ctx" / "jobs"
        running_dir = jobs_dir / "running"
        running_dir.mkdir(parents=True)
        (running_dir / "WO-0003.yaml").write_text("id: WO-0003")

        worktrees = [
            WorktreeInfo(
                path="/path/.worktrees/WO-0003",
                head="abc",
                branch="feat/wo-WO-0003",
                wo_id="WO-0003",
            )
        ]

        with patch("ctx_wo_gc.check_worktree_dirty", return_value=False):
            zombies, ghosts = classify_worktrees(tmp_path, worktrees)

        assert len(zombies) == 0
        assert len(ghosts) == 0


class TestRemoveWorktree:
    """Tests for remove_worktree function."""

    def test_remove_clean_worktree(self, tmp_path):
        """Test removing clean worktree."""
        wt = WorktreeInfo(
            path="/path/.worktrees/WO-0001",
            head="abc",
            branch="feat/wo-WO-0001",
            wo_id="WO-0001",
            is_dirty=False,
        )

        with patch("ctx_wo_gc.run_command") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            success, message = remove_worktree(tmp_path, wt, force=False)

        assert success is True
        assert "Removed" in message

    def test_remove_dirty_worktree_without_force(self, tmp_path):
        """Test that dirty worktree is NOT removed without force."""
        wt = WorktreeInfo(
            path="/path/.worktrees/WO-0002",
            head="abc",
            branch="feat/wo-WO-0002",
            wo_id="WO-0002",
            is_dirty=True,
        )

        success, message = remove_worktree(tmp_path, wt, force=False)

        assert success is False
        assert "dirty" in message.lower()
        assert "--force" in message

    def test_remove_dirty_worktree_with_force(self, tmp_path):
        """Test removing dirty worktree with force flag."""
        wt = WorktreeInfo(
            path="/path/.worktrees/WO-0003",
            head="abc",
            branch="feat/wo-WO-0003",
            wo_id="WO-0003",
            is_dirty=True,
        )

        with patch("ctx_wo_gc.run_command") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            success, message = remove_worktree(tmp_path, wt, force=True)

        assert success is True


class TestRunGc:
    """Tests for run_gc function."""

    def test_dry_run_no_mutations(self, tmp_path):
        """Test that dry-run mode doesn't make changes."""
        jobs_dir = tmp_path / "_ctx" / "jobs"
        done_dir = jobs_dir / "done"
        done_dir.mkdir(parents=True)
        (done_dir / "WO-0001.yaml").write_text("id: WO-0001")

        worktrees = [
            WorktreeInfo(
                path="/path/.worktrees/WO-0001",
                head="abc",
                branch="feat/wo-WO-0001",
                wo_id="WO-0001",
            )
        ]

        with patch("ctx_wo_gc.get_worktrees", return_value=worktrees):
            with patch("ctx_wo_gc.check_worktree_dirty", return_value=False):
                report = run_gc(tmp_path, dry_run=True, force_dirty=False)

        assert report.dry_run is True
        assert report.zombies_found == 1
        assert report.zombies_removed == 0  # No removal in dry-run

    def test_apply_mode_removes_clean_zombies(self, tmp_path):
        """Test that apply mode removes clean zombies."""
        jobs_dir = tmp_path / "_ctx" / "jobs"
        done_dir = jobs_dir / "done"
        done_dir.mkdir(parents=True)
        (done_dir / "WO-0001.yaml").write_text("id: WO-0001")

        worktrees = [
            WorktreeInfo(
                path="/path/.worktrees/WO-0001",
                head="abc",
                branch="feat/wo-WO-0001",
                wo_id="WO-0001",
                wo_state="done",
                is_dirty=False,
            )
        ]

        with patch("ctx_wo_gc.get_worktrees", return_value=worktrees):
            with patch("ctx_wo_gc.check_worktree_dirty", return_value=False):
                with patch("ctx_wo_gc.remove_worktree") as mock_remove:
                    mock_remove.return_value = (True, "Removed WO-0001")
                    report = run_gc(tmp_path, dry_run=False, force_dirty=False)

        assert report.dry_run is False
        assert report.zombies_found == 1
        assert report.zombies_removed == 1

    def test_apply_mode_skips_dirty_zombies(self, tmp_path):
        """Test that apply mode skips dirty zombies (without force)."""
        jobs_dir = tmp_path / "_ctx" / "jobs"
        done_dir = jobs_dir / "done"
        done_dir.mkdir(parents=True)
        (done_dir / "WO-0001.yaml").write_text("id: WO-0001")

        worktrees = [
            WorktreeInfo(
                path="/path/.worktrees/WO-0001",
                head="abc",
                branch="feat/wo-WO-0001",
                wo_id="WO-0001",
                wo_state="done",
                is_dirty=True,
            )
        ]

        with patch("ctx_wo_gc.get_worktrees", return_value=worktrees):
            with patch("ctx_wo_gc.check_worktree_dirty", return_value=True):
                report = run_gc(tmp_path, dry_run=False, force_dirty=False)

        assert report.zombies_found == 1
        assert report.zombies_removed == 0
        assert report.zombies_skipped_dirty == 1

    def test_json_report_generation(self, tmp_path):
        """Test JSON report generation."""
        json_path = tmp_path / "report.json"

        with patch("ctx_wo_gc.get_worktrees", return_value=[]):
            report = run_gc(tmp_path, dry_run=True, force_dirty=False, json_path=str(json_path))

        assert json_path.exists()
        data = json.loads(json_path.read_text())
        assert "timestamp" in data
        assert "summary" in data
        assert "actions" in data


class TestGCReport:
    """Tests for GCReport dataclass."""

    def test_report_defaults(self):
        """Test GCReport default values."""
        report = GCReport(
            timestamp="2026-02-21T00:00:00Z",
            repo_root="/path/to/repo",
            dry_run=True,
        )

        assert report.zombies_found == 0
        assert report.ghosts_found == 0
        assert report.zombies_removed == 0
        assert report.ghosts_removed == 0
        assert report.zombies_skipped_dirty == 0
        assert report.errors == []
        assert report.actions == []


# Integration-style tests (require git)
@pytest.mark.integration
class TestGCIntegration:
    """Integration tests that require git."""

    def test_detect_zombie_in_real_repo(self):
        """Test detecting zombies in a real repo context."""
        # This test would require setting up actual git worktrees
        # Skip in unit test runs
        pytest.skip("Integration test - requires git setup")
