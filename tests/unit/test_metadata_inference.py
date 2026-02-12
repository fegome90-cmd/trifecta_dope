"""Unit tests for scripts.metadata_inference module."""

from pathlib import Path
from unittest.mock import patch

from scripts.metadata_inference import get_worktrees_from_git


def test_get_worktrees_from_git_outside_repo():
    """Test parsing git worktree list output for worktrees outside repo."""
    # Mock git output with worktree outside repo
    # The WO ID comes from directory name (WO-0018), branch can have suffix (WO-0018B)
    git_output = """/dev/.worktrees/WO-0018 abc123 [feat/wo-WO-0018B]
/dev/repo feat/wo-WO-0019 def456"""

    with patch("subprocess.check_output", return_value=git_output):
        worktrees = get_worktrees_from_git(Path("/dev/repo"))

        # WO ID is extracted from directory name
        assert "WO-0018" in worktrees
        assert worktrees["WO-0018"]["path"] == "/dev/.worktrees/WO-0018"
        # Branch can have different suffix
        assert worktrees["WO-0018"]["branch"] == "feat/wo-WO-0018B"


def test_get_worktrees_from_git_relative_path():
    """Test parsing worktree with relative path."""
    git_output = """../.worktrees/WO-0010 abc123 [feat/wo-WO-0010]
/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope feat/wo-WO-0011 def456"""

    with patch("subprocess.check_output", return_value=git_output):
        worktrees = get_worktrees_from_git(
            Path("/Users/felipe_gonzalez/Developer/agent_h/trifecta_dope")
        )

        assert "WO-0010" in worktrees
        assert worktrees["WO-0010"]["path"] == "../.worktrees/WO-0010"
        assert worktrees["WO-0010"]["branch"] == "feat/wo-WO-0010"


def test_get_worktrees_from_git_multiple_outside():
    """Test parsing multiple worktrees outside repo."""
    git_output = """/home/user/.worktrees/WO-0001 abc111 [feat/wo-WO-0001]
/home/user/.worktrees/WO-0002 abc222 [feat/wo-WO-0002]
/home/user/project abc333 main"""

    with patch("subprocess.check_output", return_value=git_output):
        worktrees = get_worktrees_from_git(Path("/home/user/project"))

        assert len(worktrees) == 2
        assert "WO-0001" in worktrees
        assert "WO-0002" in worktrees
        assert worktrees["WO-0001"]["path"] == "/home/user/.worktrees/WO-0001"
        assert worktrees["WO-0002"]["path"] == "/home/user/.worktrees/WO-0002"


def test_get_worktrees_from_git_no_worktrees():
    """Test parsing when no worktrees exist."""
    git_output = "/home/user/project abc123 main"

    with patch("subprocess.check_output", return_value=git_output):
        worktrees = get_worktrees_from_git(Path("/home/user/project"))

        assert len(worktrees) == 0
