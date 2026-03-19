from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))


def test_wo_finish_help():
    result = subprocess.run(
        ["python", "scripts/ctx_wo_finish.py", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_detect_merge_status_reports_merged_branch(monkeypatch):
    import helpers

    detect_merge_status = getattr(helpers, "detect_merge_status")

    def mock_run_command(cmd, cwd=None, check=False):
        result = Mock()
        result.returncode = 0 if cmd[-1] == "main" else 1
        return result

    monkeypatch.setattr(helpers, "run_command", mock_run_command)

    outcome = detect_merge_status(Path("/repo"), "feat/wo-WO-TEST", ("main", "origin/main"))

    assert outcome["merge_status"] == "merged"
    assert outcome["checked_refs"] == ("main", "origin/main")


def test_detect_merge_status_reports_unmerged_branch(monkeypatch):
    import helpers

    detect_merge_status = getattr(helpers, "detect_merge_status")

    def mock_run_command(cmd, cwd=None, check=False):
        result = Mock()
        result.returncode = 1
        return result

    monkeypatch.setattr(helpers, "run_command", mock_run_command)

    outcome = detect_merge_status(Path("/repo"), "feat/wo-WO-TEST", ("main", "origin/main"))

    assert outcome["merge_status"] == "unmerged"
    assert outcome["checked_refs"] == ("main", "origin/main")


def test_resolve_closeout_policy_cleans_official_worktree_for_merged_branch(monkeypatch):
    import helpers

    resolve_closeout_policy = getattr(helpers, "resolve_closeout_policy")
    monkeypatch.setattr(
        helpers,
        "get_preserved_worktree_path",
        lambda root, wo_id, current_path=None: root.parent / f"{wo_id.lower()}-baseline",
    )

    outcome = resolve_closeout_policy(
        root=Path("/repo"),
        wo_id="WO-TEST",
        merge_status="merged",
        official_worktree_path=Path("/repo/.worktrees/WO-TEST"),
    )

    assert outcome["action"] == "cleanup_official_worktree"
    assert outcome["preserved_path"] is None


def test_resolve_closeout_policy_preserves_for_unsupported_topology(monkeypatch):
    import helpers

    resolve_closeout_policy = getattr(helpers, "resolve_closeout_policy")
    monkeypatch.setattr(
        helpers,
        "get_preserved_worktree_path",
        lambda root, wo_id, current_path=None: root.parent / f"{wo_id.lower()}-baseline",
    )

    outcome = resolve_closeout_policy(
        root=Path("/repo"),
        wo_id="WO-TEST",
        merge_status="unmerged",
        official_worktree_path=Path("/tmp/custom-topology/WO-TEST"),
    )

    assert outcome["action"] == "preserve_baseline_checkout"
    assert str(outcome["preserved_path"]).endswith("wo-test-baseline")
