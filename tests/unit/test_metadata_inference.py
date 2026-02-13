"""Unit tests for scripts.metadata_inference module."""
from pathlib import Path
from unittest.mock import patch
import pytest

from scripts.metadata_inference import (
    get_worktrees_from_git,
    parse_lock_file,
    is_lock_stale,
    is_lock_process_alive,
    check_lock_validity,
    InferenceResult,
    infer_metadata_from_system,
    verify_metadata_completeness,
    validate_inferred_metadata,
)


def test_get_worktrees_from_git_outside_repo():
    """Test parsing git worktree list output for worktrees outside repo."""
    # Real git worktree list output (format without --porcelain)
    git_output = """/dev/repo                               abc123def [feat/wo-WO-0011]
/dev/.worktrees/WO-0018A              123456789 [feat/wo-WO-0018A]
"""

    with patch("subprocess.check_output", return_value=git_output):
        worktrees = get_worktrees_from_git(Path("/dev/repo"))

        assert "WO-0018A" in worktrees
        assert worktrees["WO-0018A"]["path"] == "/dev/.worktrees/WO-0018A"
        assert worktrees["WO-0018A"]["branch"] == "feat/wo-WO-0018A"


def test_get_worktrees_from_git_relative_path():
    """Test parsing worktree with relative path."""
    git_output = """/Users/felipe/Developer/agent_h/trifecta_dope  def456 [feat/wo-WO-0011]
../.worktrees/WO-0010                                 abc123 [feat/wo-WO-0010]
"""

    with patch("subprocess.check_output", return_value=git_output):
        worktrees = get_worktrees_from_git(
            Path("/Users/felipe/Developer/agent_h/trifecta_dope")
        )

        assert "WO-0010" in worktrees
        assert worktrees["WO-0010"]["path"] == "../.worktrees/WO-0010"
        assert worktrees["WO-0010"]["branch"] == "feat/wo-WO-0010"


def test_get_worktrees_from_git_slug_wo_id_preserved():
    """WO IDs with slug/suffix format must be preserved fully."""
    git_output = """/repo abc123 [feat/wo-WO-0021-verdict-generator]
/repo/../.worktrees/WO-0021-verdict-generator def456 [feat/wo-WO-0021-verdict-generator]
"""

    with patch("subprocess.check_output", return_value=git_output):
        worktrees = get_worktrees_from_git(Path("/repo"))

        assert "WO-0021-verdict-generator" in worktrees
        assert worktrees["WO-0021-verdict-generator"]["branch"] == "feat/wo-WO-0021-verdict-generator"


def test_get_worktrees_from_git_empty_output():
    """Test parsing empty git worktree list."""
    with patch("subprocess.check_output", return_value=""):
        worktrees = get_worktrees_from_git(Path("/dev/repo"))
        assert worktrees == {}


def test_get_worktrees_from_git_malformed_output():
    """Test parsing malformed git worktree list output."""
    git_output = """malformed line
another bad line
"""

    with patch("subprocess.check_output", return_value=git_output):
        worktrees = get_worktrees_from_git(Path("/dev/repo"))
        assert worktrees == {}


def test_parse_lock_file_valid():
    """Test parsing a valid lock file."""
    import tempfile

    lock_content = """Locked by ctx_wo_take.py at 2025-02-10T15:30:00
PID: 12345
User: testuser
Hostname: testhost
"""

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.lock') as f:
        f.write(lock_content)
        lock_path = Path(f.name)

    try:
        metadata = parse_lock_file(lock_path)
        assert metadata["locked_at"] == "2025-02-10T15:30:00"
        assert metadata["pid"] == 12345
        assert metadata["user"] == "testuser"
        assert metadata["hostname"] == "testhost"
    finally:
        lock_path.unlink()


def test_parse_lock_file_not_found():
    """Test parsing non-existent lock file."""
    with pytest.raises(FileNotFoundError):
        parse_lock_file(Path("/nonexistent/lock.file"))


def test_parse_lock_file_malformed():
    """Test parsing a malformed lock file."""
    import tempfile

    lock_content = """invalid content
no proper format
"""

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.lock') as f:
        f.write(lock_content)
        lock_path = Path(f.name)

    try:
        metadata = parse_lock_file(lock_path)
        # Should return empty dict for malformed file
        assert metadata == {}
    finally:
        lock_path.unlink()


def test_is_lock_stale():
    """Test lock staleness detection."""
    import tempfile
    import time

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.lock') as f:
        f.write("test")
        lock_path = Path(f.name)

    try:
        # Fresh lock should not be stale
        assert not is_lock_stale(lock_path, max_age_seconds=3600)

        # Lock should be stale with max_age=0
        assert is_lock_stale(lock_path, max_age_seconds=0)

        # Non-existent lock is stale
        assert is_lock_stale(Path("/nonexistent/lock"), max_age_seconds=3600)
    finally:
        lock_path.unlink()


def test_is_lock_process_alive():
    """Test process alive check for lock."""
    import tempfile

    # Use current process PID which should be alive
    lock_content = f"""Locked by ctx_wo_take.py at 2025-02-10T15:30:00
PID: {__import__('os').getpid()}
User: testuser
"""

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.lock') as f:
        f.write(lock_content)
        lock_path = Path(f.name)

    try:
        # Current process should be alive
        assert is_lock_process_alive(lock_path)
    finally:
        lock_path.unlink()


def test_is_lock_process_alive_dead():
    """Test process alive check with dead PID."""
    import tempfile

    # Use PID 99999 which is unlikely to exist
    lock_content = """Locked by ctx_wo_take.py at 2025-02-10T15:30:00
PID: 99999
User: testuser
"""

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.lock') as f:
        f.write(lock_content)
        lock_path = Path(f.name)

    try:
        # Dead process should return False
        assert not is_lock_process_alive(lock_path)
    finally:
        lock_path.unlink()


def test_check_lock_validity():
    """Test full lock validity check."""
    import tempfile

    lock_content = f"""Locked by ctx_wo_take.py at 2025-02-10T15:30:00
PID: {__import__('os').getpid()}
User: testuser
"""

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.lock') as f:
        f.write(lock_content)
        lock_path = Path(f.name)

    try:
        is_valid, metadata = check_lock_validity(lock_path, max_age_seconds=3600)
        assert is_valid
        assert metadata["user"] == "testuser"
    finally:
        lock_path.unlink()


def test_check_lock_validity_missing():
    """Test lock validity check with missing lock."""
    is_valid, metadata = check_lock_validity(Path("/nonexistent/lock"))
    assert not is_valid
    assert metadata is None


def test_inference_result_success():
    """Test InferenceResult.success_with factory."""
    inferred = {"status": "running", "owner": "test"}
    result = InferenceResult.success_with(inferred)

    assert result.success
    assert result.inferred == inferred
    assert result.errors == []
    assert result.warnings == []


def test_inference_result_failure():
    """Test InferenceResult.failure factory."""
    errors = ["error1", "error2"]
    warnings = ["warn1"]
    result = InferenceResult.failure(errors, warnings)

    assert not result.success
    assert result.inferred == {}
    assert result.errors == errors
    assert result.warnings == warnings


def test_verify_metadata_completeness_complete():
    """Test metadata completeness check with complete data."""
    wo_data = {
        "status": "running",
        "owner": "test",
        "branch": "feat/wo-WO-0001",
        "worktree": "../.worktrees/WO-0001",
        "started_at": "2025-02-10T15:30:00",
    }
    missing = verify_metadata_completeness(wo_data)
    assert missing == []


def test_verify_metadata_completeness_incomplete():
    """Test metadata completeness check with missing fields."""
    wo_data = {"status": "running"}
    missing = verify_metadata_completeness(wo_data)
    assert set(missing) == {"owner", "branch", "worktree", "started_at"}


def test_validate_inferred_metadata_valid():
    """Test validation of valid inferred metadata."""
    import tempfile
    from scripts.paths import get_lock_path

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir) / "repo"
        repo_root.mkdir()

        # Create required directories
        (repo_root / "_ctx" / "jobs" / "running").mkdir(parents=True)

        wo_data = {
            "worktree": "../.worktrees/WO-0001",
        }

        # Note: This test would need more setup (actual worktree, lock file)
        # For now, we just test the function signature
        is_valid, errors = validate_inferred_metadata("WO-0001", wo_data, repo_root)
        # Will fail validation due to missing worktree/lock, but that's expected
        assert not is_valid  # Expected without full setup
